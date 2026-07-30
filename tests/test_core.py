import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(ROOT))

import builder
from collector import discount_rate


class CoreTests(unittest.TestCase):
    def test_discount_rate(self):
        self.assertEqual(discount_rate(15000, 10500), 30)
        self.assertEqual(discount_rate(10000, 10000), 0)

    def test_site_generation(self):
        builder.build()
        page = (ROOT / "docs/index.html").read_text(encoding="utf-8")
        deals = json.loads((ROOT / "data/deals.json").read_text(encoding="utf-8"))
        self.assertIn("GADGET Highlight", page)
        self.assertIn("コードをコピー", page)
        self.assertNotIn("価格が、", page)
        self.assertIn("font-size:clamp(1.15rem,2.2vw,1.8rem)", page)
        self.assertIn("広告・アフィリエイト表記", page)
        self.assertTrue((ROOT / "docs/privacy/index.html").exists())
        self.assertTrue((ROOT / "docs/sitemap.xml").exists())
        self.assertEqual(len(deals), 4)


if __name__ == "__main__":
    unittest.main()
