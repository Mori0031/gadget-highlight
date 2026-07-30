from __future__ import annotations

import argparse
import json
import os
import re
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import requests
import yaml

ROOT = Path(__file__).parent
DATA = ROOT / "data"
USER_AGENT = "GADGET-Highlight/1.0 (+contact: daichiprojectwork@gmail.com)"


def load_local_env() -> None:
    path = ROOT / ".env"
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip() and not line.lstrip().startswith("#") and "=" in line:
            key, value = line.split("=", 1)
            os.environ.setdefault(key.strip(), value.strip())


def read_json(path: Path, fallback: Any) -> Any:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else fallback


def discount_rate(original: int, sale: int) -> int:
    return round((original - sale) / original * 100) if original > sale > 0 else 0


def declared_discount(*texts: str) -> int:
    combined = " ".join(texts)
    matches = re.findall(r"(?<!\d)(\d{1,2})\s*%\s*(?:OFF|オフ|引き)", combined, flags=re.IGNORECASE)
    return max((int(value) for value in matches if 5 <= int(value) < 100), default=0)


def first_image(item: dict[str, Any]) -> str:
    images = item.get("mediumImageUrls") or []
    if not images:
        return ""
    first = images[0]
    return first if isinstance(first, str) else first.get("imageUrl", "")


def collect_rakuten(config: dict[str, Any]) -> list[dict[str, Any]]:
    app_id, access_key = os.getenv("RAKUTEN_APPLICATION_ID"), os.getenv("RAKUTEN_ACCESS_KEY")
    if not app_id or not access_key:
        return []
    endpoint = "https://openapi.rakuten.co.jp/ichibams/api/IchibaItem/Search/20260701"
    session = requests.Session()
    site_url = str(config.get("site_url", "https://mori0031.github.io/gadget-highlight/"))
    session.headers.update({
        "User-Agent": USER_AGENT,
        "accessKey": access_key,
        "Origin": "https://mori0031.github.io",
        "Referer": site_url,
    })
    affiliate_id = os.getenv("RAKUTEN_AFFILIATE_ID", "")
    records: list[dict[str, Any]] = []
    for category in config["categories"]:
        for keyword in category["keywords"][:2]:
            params = {"applicationId": app_id, "accessKey": access_key,
                      "keyword": keyword, "hits": 30,
                      "sort": "-updateTimestamp", "formatVersion": 2, "imageFlag": 1}
            if affiliate_id:
                params["affiliateId"] = affiliate_id
            response = session.get(endpoint, params=params, timeout=30)
            if response.status_code >= 400:
                detail = response.text[:500].replace(access_key, "***")
                raise RuntimeError(f"Rakuten API returned {response.status_code}: {detail}")
            payload = response.json()
            for wrapped in payload.get("Items", payload.get("items", [])):
                item = wrapped.get("Item", wrapped)
                sale = int(item.get("itemPrice") or 0)
                rate = declared_discount(item.get("catchcopy", ""), item.get("itemName", ""))
                if rate < int(config["minimum_discount_rate"]):
                    continue
                original = round(sale / (1 - rate / 100))
                records.append({
                    "id": "rakuten-" + str(item.get("itemCode", "")).replace(":", "-"),
                    "product_name": item.get("itemName", ""), "category": category["id"],
                    "brand": item.get("shopName", ""), "original_price": original,
                    "sale_price": sale, "key_specs": [], "coupon_code": "",
                    "coupon_expires_at": "", "merchant": "楽天市場",
                    "affiliate_url": item.get("affiliateUrl") or item.get("itemUrl", ""),
                    "image_url": first_image(item),
                    "source_url": item.get("itemUrl", ""),
                    "verified_at": datetime.now(timezone.utc).date().isoformat(), "is_demo": False,
                })
            time.sleep(max(2, int(config["request_interval_seconds"])))
    return records


def amazon_status() -> str:
    required = ["AMAZON_PARTNER_TAG", "AMAZON_CREATORS_CREDENTIAL_ID", "AMAZON_CREATORS_CREDENTIAL_SECRET"]
    return "ready" if all(os.getenv(key) for key in required) else "credentials_required"


def collect_amazon(config: dict[str, Any]) -> list[dict[str, Any]]:
    if amazon_status() != "ready":
        return []
    client_id = os.environ["AMAZON_CREATORS_CREDENTIAL_ID"]
    client_secret = os.environ["AMAZON_CREATORS_CREDENTIAL_SECRET"]
    version = os.getenv("AMAZON_CREDENTIAL_VERSION", "2.3")
    if version.startswith("3"):
        token_response = requests.post(
            "https://api.amazon.co.jp/auth/o2/token",
            json={"grant_type": "client_credentials", "client_id": client_id,
                  "client_secret": client_secret, "scope": "creatorsapi::default"}, timeout=30,
        )
    else:
        token_response = requests.post(
            "https://creatorsapi.auth.us-west-2.amazoncognito.com/oauth2/token",
            data={"grant_type": "client_credentials", "client_id": client_id,
                  "client_secret": client_secret, "scope": "creatorsapi/default"}, timeout=30,
        )
    token_response.raise_for_status()
    token = token_response.json()["access_token"]
    authorization = f"Bearer {token}" if version.startswith("3") else f"Bearer {token}, Version {version}"
    headers = {"Authorization": authorization, "Content-Type": "application/json",
               "x-marketplace": "www.amazon.co.jp", "User-Agent": USER_AGENT}
    records: list[dict[str, Any]] = []
    for category in config["categories"]:
        for keyword in category["keywords"][:2]:
            body = {
                "partnerTag": os.environ["AMAZON_PARTNER_TAG"], "marketplace": "www.amazon.co.jp",
                "keywords": keyword, "searchIndex": "All", "itemCount": 10,
                "minSavingPercent": int(config["minimum_discount_rate"]),
                "resources": ["images.primary.medium", "itemInfo.title", "itemInfo.byLineInfo",
                              "itemInfo.features", "offersV2.listings.price", "offersV2.listings.dealDetails",
                              "offersV2.listings.merchantInfo"],
            }
            response = requests.post("https://creatorsapi.amazon/catalog/v1/searchItems",
                                     headers=headers, json=body, timeout=30)
            response.raise_for_status()
            for item in response.json().get("searchResult", {}).get("items", []):
                listings = item.get("offersV2", {}).get("listings", [])
                if not listings:
                    continue
                listing = next((x for x in listings if x.get("isBuyBoxWinner")), listings[0])
                price = listing.get("price", {})
                sale = int(round(float(price.get("money", {}).get("amount") or 0)))
                original = int(round(float(price.get("savingBasis", {}).get("money", {}).get("amount") or sale)))
                rate = int(price.get("savings", {}).get("percentage") or discount_rate(original, sale))
                if rate < int(config["minimum_discount_rate"]):
                    continue
                info = item.get("itemInfo", {})
                records.append({
                    "id": "amazon-" + item.get("asin", ""),
                    "product_name": info.get("title", {}).get("displayValue", ""),
                    "category": category["id"],
                    "brand": info.get("byLineInfo", {}).get("brand", {}).get("displayValue", ""),
                    "original_price": original, "sale_price": sale, "discount_rate": rate,
                    "key_specs": info.get("features", {}).get("displayValues", [])[:4],
                    "coupon_code": "", "coupon_expires_at": "", "merchant": "Amazon",
                    "affiliate_url": item.get("detailPageURL", ""),
                    "image_url": item.get("images", {}).get("primary", {}).get("medium", {}).get("url", ""),
                    "source_url": item.get("detailPageURL", ""),
                    "verified_at": datetime.now(timezone.utc).date().isoformat(), "is_demo": False,
                })
            time.sleep(max(2, int(config["request_interval_seconds"])))
    return records


def update_history(deals: list[dict[str, Any]]) -> list[dict[str, Any]]:
    path = DATA / "price_history.json"
    history = read_json(path, {})
    today = datetime.now(timezone.utc).date().isoformat()
    for deal in deals:
        price = int(deal.get("sale_price") or 0)
        if not price:
            continue
        series = history.setdefault(deal["id"], [])
        previous_prices = [int(point["price"]) for point in series]
        deal["previous_low"] = min(previous_prices) if previous_prices else price
        deal["is_all_time_low"] = bool(previous_prices and price < min(previous_prices))
        if not series or series[-1].get("date") != today or int(series[-1].get("price", 0)) != price:
            series.append({"date": today, "price": price})
        history[deal["id"]] = series[-365:]
        deal["discount_rate"] = discount_rate(int(deal["original_price"]), price)
    path.write_text(json.dumps(history, ensure_ascii=False, indent=2), encoding="utf-8")
    return deals


def main(use_demo: bool) -> None:
    load_local_env()
    config = yaml.safe_load((ROOT / "config.yml").read_text(encoding="utf-8"))
    manual = read_json(DATA / "manual_deals.json", [])
    if not use_demo:
        manual = [item for item in manual if not item.get("is_demo")]
    deals = manual + collect_amazon(config) + collect_rakuten(config)
    unique = {item["id"]: item for item in deals if item.get("id")}
    final = update_history(list(unique.values()))
    (DATA / "deals.json").write_text(json.dumps(final, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"deals": len(final), "amazon": amazon_status()}, ensure_ascii=False))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--no-demo", action="store_true")
    args = parser.parse_args()
    main(not args.no_demo)
