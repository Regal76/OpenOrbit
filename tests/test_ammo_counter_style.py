"""Ammo stock must replace captured counter colors at login and during play."""
import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'server'))

from profil import Profil


class AmmoCounterStyleTest(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.profile = Profil(path=str(Path(temporary.name) / 'profil.json'))
        with (ROOT / 'server/data/varsayilan/giris.json').open(encoding='utf8') as source:
            defaults = json.load(source)
        self.template = next(row for row in defaults['hazir'] if row['_m'] == 'MenuInitializationCommand')
        self.template['categories'] = [category for category in self.template['categories']
                                       if category['categoryId'] in ('lasers', 'rockets', 'mines')]
        self.original = copy.deepcopy(self.template)

    @staticmethod
    def statuses(menu):
        return {item['status']['menuItemId']: item['status']
                for category in menu['categories'] for item in category['menuItems']}

    def initialize(self):
        return self.statuses(self.profile.patch_template('MenuInitializationCommand', self.template))

    def test_initialization_recolors_owned_ammo_without_changing_template_or_bar_maximum(self):
        counts = {'ammunition_laser_mcb-25': 132, 'ammunition_laser_ucb-100': 15091,
                  'ammunition_laser_rsb-75': 1, 'ammunition_rocket_plt-2021': 1600}
        self.profile.d['cephane'].update(counts)
        statuses = self.initialize()
        original_statuses = self.statuses(self.original)
        for item, count in counts.items():
            with self.subTest(item=item, count=count):
                status = statuses[item]
                self.assertEqual(status['counterStyle'], 4)
                self.assertEqual(status['counterValue'], count)
                self.assertTrue(status['available'])
                self.assertTrue(status['activatable'])
                self.assertEqual(status['maxCounterValue'], 200 if 'rocket_' in item else 1000)
                self.assertEqual(self.profile.menu_status_cache[item], original_statuses[item])
        self.assertEqual(self.template, self.original)

    def test_empty_ammo_replaces_captured_blue_with_red(self):
        item = 'ammunition_laser_lcb-10'
        self.profile.d['cephane'][item] = 0
        status = self.initialize()[item]
        self.assertEqual(status['counterStyle'], 1)
        self.assertEqual(status['counterValue'], 0)
        self.assertFalse(status['available'])
        self.assertFalse(status['activatable'])
        self.assertEqual(status['maxCounterValue'], 1000)
        self.assertEqual(self.template, self.original)

    def test_live_depletion_and_restock_update_color_without_mutating_cached_status(self):
        item = 'ammunition_laser_mcb-25'
        self.profile.d['cephane'][item] = 26
        initial = self.initialize()[item]
        cached = copy.deepcopy(self.profile.menu_status_cache[item])
        self.profile.add_ammo(item, -26)
        empty = self.profile.menu_status(item)
        self.assertEqual(empty['counterStyle'], 1)
        self.assertEqual(empty['counterValue'], 0)
        self.assertFalse(empty['activatable'])
        self.profile.add_ammo(item, 1)
        restocked = self.profile.menu_status(item)
        self.assertEqual(restocked['counterStyle'], 4)
        self.assertEqual(restocked['counterValue'], 1)
        self.assertTrue(restocked['available'])
        self.assertTrue(restocked['activatable'])
        self.assertEqual(initial['counterStyle'], 4)
        self.assertEqual(initial['counterValue'], 26)
        self.assertEqual(restocked['maxCounterValue'], 1000)
        self.assertEqual(self.profile.menu_status_cache[item], cached)
        self.assertEqual(self.template, self.original)

    def test_owned_mines_replace_captured_red_at_login_and_live_restock(self):
        import savas_esya as SE
        self.profile.d['konum']['mapId'] = 3
        for item in SE.PLAYER_MINES:
            self.profile.d['cephane'][item] = 7
        statuses = self.initialize()
        for item in SE.PLAYER_MINES:
            with self.subTest(item=item):
                status = statuses[item]
                self.assertEqual(status['counterStyle'], 4)
                self.assertEqual(status['counterValue'], 7)
                self.assertTrue(status['activatable'])
                self.profile.add_ammo(item, -7)
                self.assertEqual(self.profile.menu_status(item)['counterStyle'], 1)
                self.profile.add_ammo(item, 1)
                self.assertEqual(self.profile.menu_status(item)['counterStyle'], 4)
        self.assertEqual(self.template, self.original)

    def test_owned_mine_counter_remains_stock_colored_on_blocked_home_map(self):
        item = 'ammunition_mine_im-01'
        self.profile.d['konum']['mapId'] = 1
        self.profile.d['cephane'][item] = 4
        status = self.initialize()[item]
        self.assertEqual(status['counterStyle'], 4)
        self.assertEqual(status['counterValue'], 4)
        self.assertFalse(status['activatable'])


if __name__ == '__main__':
    unittest.main(verbosity=2)
