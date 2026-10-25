"""Hero SAB/CBO salvos preserve CBS shield leech and normal damage separately."""
import sys
import tempfile
import time
import unittest
from contextlib import ExitStack
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'server'))
import cbs
import dunya
from profil import Profil


class CbsLaserShield(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.p = Profil(path=str(Path(temporary.name) / 'pilot.json'))
        self.sent = []
        self.w = dunya.World(self.p, self.sent.extend, lambda _: None, 4)
        self.c = cbs.Cbs(self.p, None, lambda _: None)
        self.module = dict(loot='module_hulm-1', seviye=0, can=100000, kalkan=5000, azami=100000)
        self.c.ast(2).update(durum='kurulu', sahip='rakip', yuvalar={'0': self.module}, deflector={'acik': False})
        self.c.attach(self.w)
        self.uid = cbs.asset_id(2)
        self.w.target = self.uid
        self.w.hero = dunya.Mover(*cbs.position(2))
        self.p.d['ekipman']['laser'] = ['equipment_weapon_laser_lf-4'] * 2
        self.p.d['ekipman_seviye'] = {}
        self.p.d['dron_ekipman'] = []
        self.p.d['gemi'].update(shield=100, shieldMax=1000)
        stack = ExitStack()
        self.addCleanup(stack.close)
        stack.enter_context(patch.object(dunya.random, 'random', return_value=0))
        stack.enter_context(patch.object(dunya.random, 'uniform', return_value=1))
        stack.enter_context(patch.object(self.p, 'mods', return_value={}))
        stack.enter_context(patch.object(self.p, 'lab_bonus', return_value=0))
        self.sent.clear()

    def fire(self, ammo):
        self.p.d['secili']['lazer'] = ammo
        self.p.d['cephane'][ammo] = 100
        self.w.asset_laser(time.time())
        self.assertEqual(self.p.ammo(ammo), 98)
        return [f for name, f in self.sent if name == 'AttackHitCommand']

    def test_sab_drains_station_shield_and_returns_actual_drain(self):
        hits = self.fire('ammunition_laser_sab-50')
        self.assertEqual((self.module['can'], self.module['kalkan']), (100000, 4200))
        self.assertEqual(self.p.d['gemi']['shield'], 900)
        self.assertEqual([hit['damage'] for hit in hits], [800])
        self.assertEqual((hits[0]['attackerId'], hits[0]['victimId']), (self.w.hid, self.uid))

    def test_sab_caps_target_drain_and_attacker_shield_without_hull_damage(self):
        self.module['kalkan'] = 300
        self.p.d['gemi']['shield'] = 900
        hits = self.fire('ammunition_laser_sab-50')
        self.assertEqual((self.module['can'], self.module['kalkan']), (100000, 0))
        self.assertEqual(self.p.d['gemi']['shield'], 1000)
        self.assertEqual([hit['damage'] for hit in hits], [300])
        self.assertEqual(next(f['shieldNow'] for n, f in self.sent if n == 'AttributeShieldUpdateCommand'), 1000)

    def test_cbo_applies_shield_leech_then_normal_damage_with_correct_feedback(self):
        hits = self.fire('ammunition_laser_cbo-100')
        self.assertEqual((self.module['can'], self.module['kalkan']), (99760, 3640))
        self.assertEqual(self.p.d['gemi']['shield'], 500)
        self.assertEqual([hit['damage'] for hit in hits], [400, 1200])
        self.assertEqual((hits[-1]['victimHitpoints'], hits[-1]['victimShield']), (99760, 3640))
        self.assertFalse(any(name == 'AssetInfoCommand' for name, _ in self.sent))

    def test_cbo_depleted_shield_does_not_discard_normal_hull_damage_or_overheal(self):
        self.module['kalkan'] = 200
        hits = self.fire('ammunition_laser_cbo-100')
        self.assertEqual((self.module['can'], self.module['kalkan']), (98800, 0))
        self.assertEqual(self.p.d['gemi']['shield'], 300)
        self.assertEqual([hit['damage'] for hit in hits], [200, 1200])
