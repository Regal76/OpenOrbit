"""Real World PvP salvos spend finite upgrades and respect defender evasion."""
import sys
import tempfile
import time
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'server'))
import dunya
from profil import Profil


class PvpLaserResources(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.p = Profil(path=str(Path(temporary.name) / 'pilot.json'))
        self.p.d['ekipman']['laser'] = ['equipment_weapon_laser_lf-3']
        self.p.d['dron_ekipman'] = []
        self.p.d['yukseltmeler'] = {'0': [6, 3]}
        self.ammo = 'ammunition_laser_lcb-10'
        self.p.d['secili']['lazer'] = self.ammo
        self.p.d['cephane'][self.ammo] = 100
        self.sent = []
        self.w = dunya.World(self.p, self.sent.extend, lambda text: None, 4)
        self.now = time.time()
        self.target = self.w.hid + 1
        self.defender = SimpleNamespace(p=SimpleNamespace(mods=Mock(return_value={}), d={'pilot': {'factionId': 3}}))
        self.hit = Mock()
        for mocked in (patch.object(self.w, 'oyuncu', return_value=self.defender),
                       patch.object(dunya.AY, 'chance', return_value=1),
                       patch.object(self.w.items, 'aim', return_value=1)):
            mocked.start()
            self.addCleanup(mocked.stop)

    def fire(self, roll=0, pvp=True):
        with patch.object(dunya.random, 'random', return_value=roll):
            self.w.side_laser(self.now, self.target, self.w.hero_pos(self.now), self.hit, pvp=pvp)

    def test_fired_hit_spends_exactly_one_finite_laser_upgrade(self):
        with patch.object(self.w, 'lab_spend', wraps=self.w.lab_spend) as spend:
            self.fire()
        self.hit.assert_called_once()
        self.assertEqual(len(self.hit.call_args.args), 2)
        spend.assert_called_once_with(0)
        self.assertEqual(self.p.d['yukseltmeler']['0'], [6, 2])
        self.assertEqual(self.p.ammo(self.ammo), 99)

    def test_fired_miss_also_spends_exactly_one_upgrade(self):
        with patch.object(self.w, 'lab_spend', wraps=self.w.lab_spend) as spend:
            self.fire(roll=1)
        self.hit.assert_not_called()
        self.assertTrue(any(name == 'AttackMissedCommand' for name, fields in self.sent))
        spend.assert_called_once_with(0)
        self.assertEqual(self.p.d['yukseltmeler']['0'], [6, 2])
        self.assertEqual(self.p.ammo(self.ammo), 99)

    def test_defender_evasion_reduces_effective_laser_accuracy(self):
        self.defender.p.mods.return_value = {'kacinma': .8}
        self.fire(roll=.25)
        self.hit.assert_not_called()
        missed = [fields for name, fields in self.sent if name == 'AttackMissedCommand']
        self.assertEqual([fields['targetUserId'] for fields in missed], [self.target])
        self.assertEqual(self.p.d['yukseltmeler']['0'], [6, 2])

    def test_full_defender_evasion_blocks_even_low_roll(self):
        self.defender.p.mods.return_value = {'kacinma': 1}
        self.fire(roll=0)
        self.hit.assert_not_called()

    def test_partial_evasion_still_allows_roll_below_effective_accuracy(self):
        self.defender.p.mods.return_value = {'kacinma': .2}
        self.fire(roll=.25)
        self.hit.assert_called_once()

    def test_out_of_range_does_not_spend_ammo_or_upgrade(self):
        with patch.object(self.w, 'lab_spend', wraps=self.w.lab_spend) as spend:
            self.w.side_laser(self.now, self.target, (100000, 100000), self.hit, pvp=True)
        spend.assert_not_called()
        self.hit.assert_not_called()
        self.assertEqual(self.p.d['yukseltmeler']['0'], [6, 3])
        self.assertEqual(self.p.ammo(self.ammo), 100)

    def test_ammo_cooldown_does_not_spend_upgrade(self):
        ammo = 'ammunition_laser_rsb-75'
        self.p.d['secili']['lazer'] = ammo
        self.p.d['cephane'][ammo] = 100
        self.w.ammo_ready[ammo] = self.now + 10
        with patch.object(self.w, 'lab_spend', wraps=self.w.lab_spend) as spend:
            self.fire()
        spend.assert_not_called()
        self.hit.assert_not_called()
        self.assertEqual(self.p.ammo(ammo), 100)

    def test_no_ammo_does_not_spend_upgrade(self):
        self.p.d['cephane'][self.ammo] = 0
        with patch.object(self.w, 'lab_spend', wraps=self.w.lab_spend) as spend, \
                patch.object(self.w, 'ammo_out', return_value=(None, [])):
            self.fire()
        spend.assert_not_called()
        self.hit.assert_not_called()
        self.assertEqual(self.p.d['yukseltmeler']['0'], [6, 3])

    def test_last_upgrade_charge_disappears_after_shot(self):
        self.p.d['yukseltmeler']['0'][1] = 1
        self.fire()
        self.assertNotIn('0', self.p.d['yukseltmeler'])
        self.assertEqual(self.p.lab_bonus(0), 0)

    def test_non_pvp_side_laser_keeps_existing_callback_and_resource_behavior(self):
        self.defender.p.mods.return_value = {'kacinma': 1}
        self.fire(pvp=False)
        self.hit.assert_called_once()
        self.assertEqual(len(self.hit.call_args.args), 1)
        self.w.oyuncu.assert_not_called()
        self.assertEqual(self.p.d['yukseltmeler']['0'], [6, 3])


if __name__ == '__main__':
    unittest.main()
