from __future__ import annotations

import json
import os
from typing import Any

from openai import OpenAI

SYSTEM = """あなたは商品情報のファクト抽出器です。説明、評価、推薦、要約を禁止します。
入力本文に明記された事実だけをJSONで返してください。不明値はnullまたは空配列にします。
価格やクーポンを推測せず、出典本文にないスペックを補完しないでください。"""

SCHEMA = {
    "type": "object", "additionalProperties": False,
    "properties": {
        "product_name": {"type": ["string", "null"]},
        "original_price": {"type": ["integer", "null"]},
        "sale_price": {"type": ["integer", "null"]},
        "key_specs": {"type": "array", "items": {"type": "string"}, "maxItems": 4},
        "coupon_code": {"type": ["string", "null"]},
        "coupon_expires_at": {"type": ["string", "null"]},
    }, "required": ["product_name", "original_price", "sale_price", "key_specs", "coupon_code", "coupon_expires_at"]
}


def extract_facts(text: str) -> dict[str, Any]:
    if not os.getenv("OPENAI_API_KEY"):
        raise RuntimeError("OPENAI_API_KEY is not configured")
    response = OpenAI().responses.create(
        model="gpt-4o-mini", instructions=SYSTEM, input=text[:30000],
        text={"format": {"type": "json_schema", "name": "deal_facts", "strict": True, "schema": SCHEMA}},
    )
    return json.loads(response.output_text)

