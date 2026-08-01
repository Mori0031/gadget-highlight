from __future__ import annotations

import json
import os
import re
import base64
from datetime import datetime, timezone
from pathlib import Path

import requests
import yaml

ROOT = Path(__file__).parent
STATE = ROOT / "data" / "notified_deals.json"
STATUS = ROOT / "data" / "notification_status.json"


def load_local_env() -> None:
    path = ROOT / ".env"
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip() and not line.lstrip().startswith("#") and "=" in line:
            key, value = line.split("=", 1)
            os.environ.setdefault(key.strip(), value.strip())


def slug(deal: dict) -> str:
    return re.sub(r"[^a-zA-Z0-9_-]+", "-", str(deal.get("id", "deal"))).strip("-").lower()


def public_url(deal: dict, site_url: str) -> str:
    return f"{site_url.rstrip('/')}/deals/{slug(deal)}/"


def message(deal: dict, site_url: str) -> str:
    low = "｜最安値を更新" if deal.get("is_all_time_low") else ""
    return (f"【{deal['discount_rate']}%OFF】{deal['product_name']}{low}\n"
            f"¥{deal['sale_price']:,}｜{deal['merchant']}\n"
            f"{public_url(deal, site_url)}\n#PR #ガジェットセール")


def candidates_for_x(deals: list[dict], state: dict[str, int], minimum_discount: int) -> list[dict]:
    candidates = []
    for deal in deals:
        if deal.get("is_demo") or int(deal.get("discount_rate") or 0) < minimum_discount:
            continue
        price = int(deal.get("sale_price") or 0)
        previous = state.get(str(deal.get("id")))
        if price and (previous is None or price < int(previous)):
            candidates.append(deal)
    return sorted(candidates, key=lambda item: (not item.get("is_all_time_low"), -int(item.get("discount_rate") or 0)))


def post_payload(deal: dict, site_url: str, media_id: str = "") -> dict:
    payload = {"text": message(deal, site_url)}
    if media_id:
        payload["media"] = {"media_ids": [media_id]}
    return payload


def upload_x_image(deal: dict, auth) -> str:
    image_url = str(deal.get("image_url") or "")
    if not image_url.startswith("https://"):
        return ""
    try:
        image_response = requests.get(
            image_url,
            headers={"User-Agent": "GADGET-Highlight/1.0 (+https://mori0031.github.io/gadget-highlight/)"},
            timeout=20,
        )
        image_response.raise_for_status()
        media_type = image_response.headers.get("Content-Type", "").split(";", 1)[0].lower()
        allowed = {"image/jpeg", "image/png", "image/webp", "image/gif"}
        if media_type not in allowed or len(image_response.content) > 5 * 1024 * 1024:
            return ""
        upload = requests.post(
            "https://api.x.com/2/media/upload",
            json={
                "media": base64.b64encode(image_response.content).decode("ascii"),
                "media_category": "tweet_image",
                "media_type": media_type,
                "shared": False,
            },
            auth=auth,
            timeout=30,
        )
        if upload.status_code >= 400:
            print(f"::warning::X image upload failed for {deal['id']} ({upload.status_code}). Posting text only.")
            return ""
        return str(upload.json().get("data", {}).get("id") or "")
    except requests.RequestException as exc:
        print(f"::warning::Product image could not be prepared for {deal['id']}: {exc}")
        return ""


def main() -> None:
    load_local_env()
    deals = json.loads((ROOT / "data/deals.json").read_text(encoding="utf-8"))
    config = yaml.safe_load((ROOT / "config.yml").read_text(encoding="utf-8"))
    site_url = config["site_url"]
    state = json.loads(STATE.read_text(encoding="utf-8")) if STATE.exists() else {}
    minimum_discount = int(os.getenv("X_MIN_DISCOUNT", "10"))
    limit = max(0, int(os.getenv("X_MAX_POSTS_PER_RUN", "1")))
    candidates = candidates_for_x(deals, state, minimum_discount)[:limit]
    messages = [message(item, site_url) for item in candidates]
    (ROOT / "data/notifications.json").write_text(
        json.dumps(messages, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    if os.getenv("NOTIFY_DRY_RUN", "true").lower() != "false":
        STATUS.write_text(json.dumps({"status": "dry-run", "candidates": len(candidates)},
                                     ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"dry-run: {len(candidates)} X post(s)")
        return

    keys = [os.getenv(name) for name in
            ("X_API_KEY", "X_API_SECRET", "X_ACCESS_TOKEN", "X_ACCESS_TOKEN_SECRET")]
    if not all(keys):
        STATUS.write_text(json.dumps({"status": "warning", "error": "X API credentials are incomplete."},
                                     ensure_ascii=False, indent=2), encoding="utf-8")
        print("::warning::X posting is enabled but X API credentials are incomplete.")
        return
    from requests_oauthlib import OAuth1
    auth = OAuth1(*keys)
    posted = 0
    errors: list[dict] = []
    for deal in candidates:
        media_id = upload_x_image(deal, auth)
        response = requests.post("https://api.x.com/2/tweets", json=post_payload(deal, site_url, media_id),
                                 auth=auth, timeout=20)
        if response.status_code >= 400:
            detail = response.text[:500]
            errors.append({"deal_id": deal["id"], "status_code": response.status_code,
                           "detail": detail})
            print(f"::warning::X post failed for {deal['id']} ({response.status_code}): {detail}")
            continue
        state[str(deal["id"])] = int(deal["sale_price"])
        posted += 1
    STATE.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")
    STATUS.write_text(json.dumps({"status": "ok" if not errors else "warning", "posted": posted,
                                  "errors": errors,
                                  "checked_at": datetime.now(timezone.utc).isoformat()},
                                 ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"posted: {posted} X post(s); errors: {len(errors)}")


if __name__ == "__main__":
    main()
