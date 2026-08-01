from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).parent
MANUAL = ROOT / "data" / "manual_deals.json"


def set_status(asin: str, active: bool, reason: str = "") -> dict:
    deal_id = "amazon-" + asin.strip().upper()
    records = json.loads(MANUAL.read_text(encoding="utf-8"))
    for record in records:
        if record.get("id") == deal_id:
            record["is_active"] = active
            record["inactive_reason"] = "" if active else (reason.strip() or "sale_ended")
            record["status_updated_at"] = datetime.now(timezone.utc).date().isoformat()
            MANUAL.write_text(json.dumps(records, ensure_ascii=False, indent=2), encoding="utf-8")
            return record
    raise ValueError(f"Amazon deal not found: {deal_id}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Publish or hide a manually registered Amazon deal.")
    parser.add_argument("--asin", required=True)
    parser.add_argument("--status", choices=("active", "inactive"), required=True)
    parser.add_argument("--reason", default="")
    args = parser.parse_args()
    result = set_status(args.asin, args.status == "active", args.reason)
    print(json.dumps({"updated": result["id"], "is_active": result["is_active"]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
