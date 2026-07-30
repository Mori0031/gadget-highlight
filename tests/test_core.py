import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(ROOT))

import builder
from collector import deduplicate_deals, declared_discount, discount_rate, first_image, infer_category


class CoreTests(unittest.TestCase):
    def test_discount_rate(self):
        self.assertEqual(discount_rate(15000, 10500), 30)
        self.assertEqual(discount_rate(10000, 10000), 0)

    def test_declared_discount(self):
        self.assertEqual(declared_discount("期間限定 30%OFF", "商品名"), 30)
        self.assertEqual(declared_discount("ポイント10倍", "商品名"), 0)

    def test_japanese_discount_phrases(self):
        self.assertEqual(declared_discount("期間限定 半額セール"), 50)
        self.assertEqual(declared_discount("3割引"), 30)

    def test_rakuten_image_uses_original_asset(self):
        item = {"mediumImageUrls": ["https://example.test/image.jpg?_ex=128x128"]}
        self.assertEqual(first_image(item), "https://example.test/image.jpg")

    def test_category_is_inferred_from_product(self):
        self.assertEqual(infer_category("USB-C ドッキングステーション", "audio"), "pc")
        self.assertEqual(infer_category("ワイヤレスイヤホン", "pc"), "audio")

    def test_duplicate_image_keeps_lower_price(self):
        deals = [
            {"id": "a", "image_url": "https://example.test/a.jpg?_ex=128x128", "sale_price": 9000},
            {"id": "b", "image_url": "https://example.test/a.jpg", "sale_price": 8000},
        ]
        self.assertEqual([item["id"] for item in deduplicate_deals(deals)], ["b"])

    def test_site_generation(self):
        builder.build()
        page = builder.OUTPUT.read_text(encoding="utf-8")
        deals = json.loads((ROOT / "data/deals.json").read_text(encoding="utf-8"))
        self.assertIn("GADGET Highlight", page)
        self.assertIn("コードをコピー", page)
        self.assertNotIn("価格が、", page)
        self.assertIn("font-size:clamp(1.15rem,2.2vw,1.8rem)", page)
        self.assertIn("広告・アフィリエイト表記", page)
        self.assertIn("最安値を表示", page)
        self.assertIn("-webkit-line-clamp:2", page)
        self.assertIn("background:transparent;border:0", page)
        self.assertTrue((ROOT / "docs/privacy/index.html").exists())
        self.assertTrue((ROOT / "docs/sitemap.xml").exists())
        self.assertGreater(len(deals), 0)


if __name__ == "__main__":
    unittest.main()
