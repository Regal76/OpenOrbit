"""The native category SELECT action must select ammo on the first click."""
import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'server'))
from profil import Profil
from dunya import World


class AmmoCategorySelection(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.p = Profil(path=str(Path(tmp.name) / 'pilot.json'))
        self.sent = []
        self.w = World(self.p, self.sent.extend, lambda *_: None, 4)
        template = next(m for m in json.loads((ROOT / 'server/data/varsayilan/giris.json').read_text())['hazir']
                        if m['_m'] == 'MenuInitializationCommand')
        self.p.patch_template('MenuInitializationCommand', template)

    def test_single_category_click_selects_each_ammunition_kind_without_spending(self):
        for kind, item in [('lazer', 'ammunition_laser_mcb-50'),
                           ('roket', 'ammunition_rocket_plt-2026'),
                           ('fircatici', 'ammunition_rocketlauncher_hstrm-01'),
                           ('slug', 'ammunition_slug_ths-d01'),
                           ('gsp', 'ammunition_spool_gsp-30')]:
            with self.subTest(kind=kind):
                self.p.d['secili'][kind] = None
                self.p.d['cephane'][item] = 100
                self.sent.clear()
                self.w.menu_action(dict(menuItemId=item, actionType=0, sourceType=0))
                self.assertEqual(self.p.d['secili'][kind], item)
                self.assertEqual(self.p.ammo(item), 100)
                self.assertTrue(any(n == 'MenuItemStatusCommand' and f['menuItemId'] == item and f['selected']
                                    for n, f in self.sent))
                self.assertFalse(self.w.attacking)

    def test_category_select_does_not_toggle_running_laser_attack(self):
        item = 'ammunition_laser_lcb-10'
        self.p.d['secili']['lazer'] = item
        self.p.d['cephane'][item] = 100
        self.p.d['ayarlar'].setdefault('gameplaySettingsModule', {})['quickslotStopAttack'] = True
        self.w.attacking = True
        self.w.menu_action(dict(menuItemId=item, actionType=0, sourceType=0))
        self.assertTrue(self.w.attacking)
        self.assertFalse(any(n == 'AttackAbortLaserCommand' for n, f in self.sent))

    def test_empty_ammo_and_unsupported_action_do_not_change_selection(self):
        item = 'ammunition_laser_mcb-50'
        self.p.d['secili']['lazer'] = 'ammunition_laser_lcb-10'
        for action, count in [(0, 0), (2, 100), (None, 100)]:
            self.p.d['cephane'][item] = count
            self.w.menu_action(dict(menuItemId=item, actionType=action, sourceType=0))
            self.assertEqual(self.p.d['secili']['lazer'], 'ammunition_laser_lcb-10')

    def test_regular_slot_activation_still_selects_immediately(self):
        item = 'ammunition_rocket_plt-2026'
        self.p.d['cephane'][item] = 100
        self.w.menu_action(dict(menuItemId=item, actionType=1, sourceType=1))
        self.assertEqual(self.p.d['secili']['roket'], item)

if __name__ == '__main__':
    unittest.main()
