"""Server activation purchases one batch; native buy_* requires double click.

The filename retains the earlier audit history. This module tests the protocol
purchase stage, after the native UserItem guard has accepted a double click.
"""
import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'server'))
from profil import Profil
from magaza import Magaza


class QuickBuySingleClick(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.profile = Profil(path=str(Path(temporary.name) / 'profil.json'))
        with (ROOT / 'server/data/varsayilan/giris.json').open(encoding='utf8') as stream:
            defaults = json.load(stream)
        self.template = next(row for row in defaults['hazir'] if row['_m'] == 'MenuInitializationCommand')
        self.menu = self.profile.patch_template('MenuInitializationCommand', self.template)
        with (ROOT / 'server/data/varsayilan/yanitlar.json').open(encoding='utf8') as stream:
            replies = json.load(stream)
        self.shop = Magaza(self.profile, copy.deepcopy(replies), lambda *args: None)

    def dispatch(self, fields):
        # Mirrors the production dispatcher: unrouted requests never enter Magaza.handle.
        return self.shop.handle('MenuActionRequest', fields) if self.shop.handles('MenuActionRequest', fields) else []

    def check_purchase(self, action, source, item):
        loot = item[4:]
        quantity = self.profile.menu_status_cache[item]['counterValue']
        currency, unit_price = self.shop.buy_price(loot)
        self.profile.d['pilot'][currency] = 1000000
        before_ammo = self.profile.ammo(loot)
        messages = self.dispatch(dict(menuItemId=item, actionType=action, sourceType=source))
        self.assertEqual(self.profile.ammo(loot), before_ammo + quantity)
        self.assertEqual(self.profile.d['pilot'][currency], 1000000 - round(unit_price * quantity))
        statuses = [f for name, f in messages if name == 'MenuItemStatusCommand' and f['menuItemId'] == loot]
        self.assertEqual(len(statuses), 1)
        self.assertEqual(statuses[0]['counterValue'], before_ammo + quantity)

    def test_one_slotbar_activation_purchases_one_laser_batch(self):
        self.check_purchase(1, 1, 'buy_ammunition_laser_lcb-10')

    def test_one_slotbar_activation_purchases_one_rocket_batch(self):
        self.check_purchase(1, 1, 'buy_ammunition_rocket_plt-2021')

    def test_one_category_activation_purchases_one_batch(self):
        self.check_purchase(1, 0, 'buy_ammunition_laser_lcb-10')

    def test_quick_buy_initialization_uses_one_shot_without_mutating_recording(self):
        before = {item['status']['menuItemId']: item['actionStyle']
                  for category in self.template['categories'] for item in category['menuItems']}
        after = {item['status']['menuItemId']: item['actionStyle']
                 for category in self.menu['categories'] for item in category['menuItems']}
        buy_ids = [mid for mid in before if mid.startswith('buy_')]
        self.assertEqual(len(buy_ids), 8)
        for mid in buy_ids:
            self.assertEqual(before[mid], 2)
            self.assertEqual(after[mid], 0)
        for mid in before:
            if not mid.startswith('buy_'):
                self.assertEqual(after[mid], before[mid])

    def test_slotbar_insufficient_funds_does_not_grant_or_charge(self):
        loot = 'ammunition_laser_lcb-10'
        self.profile.d['pilot']['credits'] = 0
        before = self.profile.ammo(loot)
        fields = dict(menuItemId='buy_' + loot, actionType=1, sourceType=1)
        self.assertTrue(self.shop.handles('MenuActionRequest', fields))
        self.assertEqual(self.dispatch(fields), [])
        self.assertEqual(self.profile.ammo(loot), before)
        self.assertEqual(self.profile.d['pilot']['credits'], 0)

    def test_other_actions_and_regular_ammo_do_not_enter_purchase_route(self):
        for fields in (dict(menuItemId='buy_ammunition_laser_lcb-10', actionType=0),
                       dict(menuItemId='buy_ammunition_laser_lcb-10', actionType=2),
                       dict(menuItemId='buy_ammunition_laser_lcb-10'),
                       dict(menuItemId='ammunition_laser_lcb-10', actionType=1)):
            with self.subTest(fields=fields):
                self.assertFalse(self.shop.handles('MenuActionRequest', fields))


if __name__ == '__main__':
    unittest.main()
