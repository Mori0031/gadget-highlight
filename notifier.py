from __future__ import annotations

import json
import os
from pathlib import Path

import requests

ROOT = Path(__file__).parent


def load_local_env() -> None:
    path = ROOT / ".env"
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip() and not line.lstrip().startswith("#") and "=" in line:
            key, value = line.split("=", 1)
            os.environ.setdefault(key.strip(), value.strip())


def message(deal: dict) -> str:
    low = " 過去最安値更新" if deal.get("is_all_time_low") else ""
    return f"【{deal['discount_rate']}%OFF】{deal['product_name']}{low}\n¥{deal['sale_price']:,}｜{deal['merchant']}\n{deal['affiliate_url']}\n#PR #ガジェットセール"


def main() -> None:
    load_local_env()
    deals = json.loads((ROOT / "data/deals.json").read_text(encoding="utf-8"))
    candidates = [item for item in deals if item.get("is_all_time_low") and not item.get("is_demo")]
    (ROOT / "data/notifications.json").write_text(json.dumps([message(x) for x in candidates], ensure_ascii=False, indent=2), encoding="utf-8")
    if os.getenv("NOTIFY_DRY_RUN", "true").lower() != "false":
        print(f"dry-run: {len(candidates)} notification(s)")
        return
    discord = os.getenv("DISCORD_WEBHOOK_URL")
    for deal in candidates:
        text = message(deal)
        if discord:
            requests.post(discord, json={"content": text, "allowed_mentions": {"parse": []}}, timeout=20).raise_for_status()
        keys = [os.getenv(name) for name in ("X_API_KEY", "X_API_SECRET", "X_ACCESS_TOKEN", "X_ACCESS_TOKEN_SECRET")]
        if all(keys):
            from requests_oauthlib import OAuth1
            auth = OAuth1(*keys)
            requests.post("https://api.x.com/2/tweets", json={"text": text}, auth=auth, timeout=20).raise_for_status()


if __name__ == "__main__":
    main()
