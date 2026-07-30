from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).parent
MANUAL = ROOT / "data" / "manual_deals.json"
CATEGORIES = {"keyboard", "power", "pc", "audio", "smart-home", "diy", "saas"}
AMAZON_HOSTS = {"amazon.co.jp", "www.amazon.co.jp", "amzn.to", "amzn.asia"}


def valid_amazon_url(value: str) -> bool:
    parsed = urlparse(value)
    return parsed.scheme == "https" and parsed.hostname in AMAZON_HOSTS


def upsert_amazon(args: argparse.Namespace) -> dict:
    if not re.fullmatch(r"[A-Z0-9]{10}", args.asin.upper()):
        raise ValueError("ASIN must contain exactly 10 letters or numbers.")
    if not valid_amazon_url(args.url):
        raise ValueError("Use an Amazon.co.jp or SiteStripe short URL starting with https://.")
    if args.category not in CATEGORIES:
        raise ValueError("Unknown category.")
    if args.sale_price <= 0 or args.original_price <= args.sale_price:
        raise ValueError("Original price must be greater than the positive sale price.")
    if args.image_url and urlparse(args.image_url).scheme != "https":
        raise ValueError("Image URL must start with https://.")

    record = {
        "id": "amazon-" + args.asin.upper(),
        "product_name": args.title.strip(),
        "source_title": args.title.strip(),
        "category": args.category,
        "brand": args.brand.strip(),
        "original_price": args.original_price,
        "sale_price": args.sale_price,
        "key_specs": [],
        "coupon_code": args.coupon.strip(),
        "coupon_expires_at": args.expires.strip(),
        "merchant": "Amazon",
        "affiliate_url": args.url,
        "image_url": args.image_url.strip(),
        "source_url": args.url,
        "verified_at": datetime.now(timezone.utc).date().isoformat(),
        "is_demo": False,
    }
    existing = json.loads(MANUAL.read_text(encoding="utf-8")) if MANUAL.exists() else []
    records = {item["id"]: item for item in existing if item.get("id")}
    records[record["id"]] = record
    MANUAL.parent.mkdir(parents=True, exist_ok=True)
    MANUAL.write_text(json.dumps(list(records.values()), ensure_ascii=False, indent=2), encoding="utf-8")
    return record


def main() -> None:
    parser = argparse.ArgumentParser(description="Register a verified Amazon deal without scraping.")
    parser.add_argument("--asin", required=True)
    parser.add_argument("--title", required=True)
    parser.add_argument("--url", required=True)
    parser.add_argument("--category", required=True)
    parser.add_argument("--brand", default="")
    parser.add_argument("--original-price", type=int, required=True)
    parser.add_argument("--sale-price", type=int, required=True)
    parser.add_argument("--image-url", default="")
    parser.add_argument("--coupon", default="")
    parser.add_argument("--expires", default="")
    record = upsert_amazon(parser.parse_args())
    print(json.dumps({"registered": record["id"]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
