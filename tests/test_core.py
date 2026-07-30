import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(ROOT))

import builder
from collector import clean_product_name, deduplicate_deals, declared_discount, discount_rate, first_image, infer_category
from manual_deal import valid_amazon_url
from notifier import candidates_for_x, message


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

    def test_product_name_removes_sale_copy(self):
        title = "★期間限定 最大60%OFF★ USB-C ドッキングステーション 新生活"
        self.assertEqual(clean_product_name(title), "USB-C ドッキングステーション")

    def test_product_name_is_bounded(self):
        self.assertLessEqual(len(clean_product_name("商品名" * 40)), 59)

    def test_amazon_url_validation(self):
        self.assertTrue(valid_amazon_url("https://www.amazon.co.jp/dp/B012345678"))
        self.assertTrue(valid_amazon_url("https://amzn.to/example"))
        self.assertTrue(valid_amazon_url("https://link.amazon/example"))
        self.assertFalse(valid_amazon_url("https://example.com/product"))

    def test_product_detail_page_and_structured_data(self):
        deal = {"id": "amazon-B012345678", "product_name": "テスト充電器", "brand": "Test",
                "merchant": "Amazon", "sale_price": 8000, "original_price": 10000,
                "discount_rate": 20, "verified_at": "2026-07-30", "affiliate_url": "https://example.test",
                "image_url": "", "is_demo": False}
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            paths = builder.build_deal_pages(Path(tmp), [deal], "https://example.test/")
            page = (Path(tmp) / "deals/amazon-b012345678/index.html").read_text(encoding="utf-8")
        self.assertEqual(paths[0][0], "https://example.test/deals/amazon-b012345678/")
        self.assertIn('"@type": "Product"', page)
        self.assertIn('rel="canonical"', page)

    def test_x_posts_only_new_or_lower_prices(self):
        deals = [{"id": "a", "discount_rate": 30, "sale_price": 7000, "is_demo": False},
                 {"id": "b", "discount_rate": 20, "sale_price": 9000, "is_demo": False}]
        self.assertEqual([x["id"] for x in candidates_for_x(deals, {"a": 8000, "b": 9000}, 10)], ["a"])

    def test_x_message_links_to_site(self):
        deal = {"id": "amazon-X", "discount_rate": 20, "product_name": "充電器",
                "sale_price": 8000, "merchant": "Amazon", "is_all_time_low": False}
        self.assertIn("https://example.test/deals/amazon-x/", message(deal, "https://example.test/"))
        self.assertIn("#PR", message(deal, "https://example.test/"))

    def test_x_failed_price_is_not_marked_as_sent(self):
        deals = [{"id": "a", "discount_rate": 30, "sale_price": 7000, "is_demo": False}]
        self.assertEqual(len(candidates_for_x(deals, {}, 10)), 1)
        self.assertEqual(len(candidates_for_x(deals, {"a": 7000}, 10)), 0)

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
        self.assertIn("商品を見る →", page)
        self.assertNotIn("観測最安値", page)
        self.assertIn("background:transparent;border:0", page)
        self.assertIn(".card.no-image .visual{display:none}", page)
        self.assertIn("white-space:nowrap", page)
        self.assertTrue((ROOT / "docs/privacy/index.html").exists())
        self.assertTrue((ROOT / "docs/sitemap.xml").exists())
        self.assertTrue((ROOT / "docs/googlee8e91df546a32cf3.html").exists())
        self.assertIsInstance(deals, list)


if __name__ == "__main__":
    unittest.main()
