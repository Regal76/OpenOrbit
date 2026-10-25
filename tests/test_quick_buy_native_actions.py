"""Execute native action selection, then route the resulting purchase request."""
import importlib.util
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / '_trial/drone-deps'))
try:
    import unicorn
    import pefile
except ImportError:
    unicorn = None
import test_quick_buy_single_click as base


@unittest.skipUnless(unicorn is not None and (ROOT/'DarkOrbit_Version1.1.115/GameAssembly.dll').exists(),
                     'Shipped .115 native fixture, pefile and Unicorn required')
class QuickBuyNativeActions(unittest.TestCase):
    setUp = base.QuickBuySingleClick.setUp
    dispatch = base.QuickBuySingleClick.dispatch
    check_purchase = base.QuickBuySingleClick.check_purchase

    @classmethod
    def setUpClass(cls):
        spec = importlib.util.spec_from_file_location('quick_buy_native_audit', ROOT/'tools/quick_buy_native_audit.py')
        cls.native = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.native)

    def test_original_selection_shapes_explain_server_route_mismatch(self):
        n = self.native
        self.assertEqual(n.probe('selection', 'categoryBar', False)['actionType'], 0)
        self.assertEqual(n.probe('selection', 'categoryBar', True)['actionType'], 1)
        self.assertEqual(n.probe('selection', 'standardSlotBar', False)['actionType'], 1)

    def test_one_shot_double_click_purchases_exactly_one_batch_from_every_bar(self):
        item = next(item for category in self.menu['categories'] for item in category['menuItems']
                    if item['status']['menuItemId'] == 'buy_ammunition_laser_lcb-10')
        self.assertEqual(item['actionStyle'], 0)
        # Protocol ActionStyle.ONE_SHOT=0 resolves to the native oneShot string.
        for bar in ('categoryBar', 'standardSlotBar', 'premiumSlotBar'):
            with self.subTest(bar=bar):
                fields = self.native.probe('oneShot', bar, True)
                self.assertEqual(fields['actionType'], 1)
                self.check_purchase(fields['actionType'], fields['sourceType'], item['status']['menuItemId'])


if __name__ == '__main__':
    unittest.main()
