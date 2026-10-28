"""Rockets and Hellstorm must resolve CBS targets without treating them as NPCs."""
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
import savas_esya as SE
from profil import Profil


class CbsRockets(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.p = Profil(path=str(Path(self.tmp.name) / 'pilot.json'))
        self.sent = []
        self.w = dunya.World(self.p, self.sent.extend, lambda *_: None, 4)
        self.c = cbs.Cbs(self.p, None, lambda *_: None)
        self.a = self.c.ast(2)
        loot = next(k for k, v in cbs.MODS.items() if v.get('kod') == 'HULM-1')
        self.m = dict(loot=loot, seviye=0, can=100000, kalkan=5000, azami=100000)
        self.a.update(durum='kurulu', sahip='rakip', yuvalar={'0': self.m}, deflector={'acik': False})
        self.c.attach(self.w)
        self.uid = cbs.asset_id(2, 0)
        self.w.target = self.uid
        self.w.hero = dunya.Mover(*cbs.position(2))
        self.p.d['ekipman']['rocket'] = ['equipment_weapon_rocketlauncher_hst-2']
        self.now = time.time()
        self.stack = ExitStack()
        self.addCleanup(self.stack.close)
        self.stack.enter_context(patch('savas_esya.random.random', return_value=0))
        self.stack.enter_context(patch('savas_esya.random.uniform', return_value=1))
        self.stack.enter_context(patch.object(self.p, 'mods', return_value={'npc': 10}))
        self.stack.enter_context(patch.object(self.p, 'lab_bonus', return_value=0))
        self.stack.enter_context(patch.object(self.p, 'ship_row', return_value={}))

    def rocket(self, ammo='ammunition_rocket_r-310'):
        self.p.d['secili']['roket'] = ammo
        self.p.d['cephane'][ammo] = 3
        self.w.rocket({'targetId': self.uid})

    def launcher(self, ammo='ammunition_rocketlauncher_hstrm-01'):
        self.now += 5.0
        self.p.d['fircatici_dolu'] = [ammo, 5]
        self.w.items.launcher_fire(self.now)

    def land(self):
        timers, self.w.timers = self.w.timers, []
        for _, callback in timers:
            callback()

    def test_ordinary_rocket_fires_visual_then_delayed_non_npc_damage(self):
        self.rocket()
        self.assertTrue(any(n == 'LegacyModule' and '|v|' in str(f) for n, f in self.sent))
        self.assertEqual(self.m['can'] + self.m['kalkan'], 105000)
        self.land()
        self.assertEqual(self.m['can'] + self.m['kalkan'], 104000)
        self.assertEqual(self.p.ammo('ammunition_rocket_r-310'), 2)
        self.assertGreater(self.w.rocket_ready, self.now)

    def test_launcher_keeps_full_native_salvo_and_delayed_damage(self):
        self.launcher()
        salvos = [f for n, f in self.sent if n == 'HellstormAttackCommand']
        self.assertEqual(len(salvos), 1)
        self.assertEqual((salvos[0]['targetId'], salvos[0]['currentLoad']), (self.uid, 5))
        self.assertEqual(self.p.d['fircatici_dolu'][1], 0)
        self.assertEqual(len(self.w.timers), 5)
        self.assertAlmostEqual(self.w.timers[0][0] - time.time(), 1.0, delta=.1)
        self.assertEqual(self.m['can'] + self.m['kalkan'], 105000)
        self.land()
        self.assertEqual(self.m['can'] + self.m['kalkan'], 85000)

    def test_all_launcher_ammo_preserves_its_native_type_and_damage(self):
        # With salvo split into per-rocket impacts (commit 99a74b0), on a 5000-shield
        # module CBR and PIR-100 drain part of the shield on rocket 0 and the rest of the
        # shield is absorbed by rocket 0's normal damage, leaving 0 shield for subsequent
        # rockets' shield-drain to consume.
        for suffix, expected_loss in [('hstrm-01', 20000), ('ubr-100', 37500), ('eco-10', 10000),
                                      ('sar-01', 5000), ('sar-02', 5000), ('cbr', 18000),
                                      ('bdr1212', 20000), ('pir-100', 20000), ('obr-100', 30000)]:
            with self.subTest(ammo=suffix):
                self.m.update(can=100000, kalkan=5000)
                self.sent.clear()
                self.launcher('ammunition_rocketlauncher_' + suffix)
                salvo = next(f for n, f in self.sent if n == 'HellstormAttackCommand')
                self.assertEqual(salvo['currentLoad'], 5)
                self.land()
                self.assertEqual(self.m['can'] + self.m['kalkan'], 105000 - expected_loss)

    def test_ordinary_reload_prevents_second_shot(self):
        self.rocket()
        self.assertEqual(self.p.ammo('ammunition_rocket_r-310'), 2)
        self.w.rocket({'targetId': self.uid})
        self.assertEqual(self.p.ammo('ammunition_rocket_r-310'), 2)
        self.land()
        self.assertEqual(self.m['can'] + self.m['kalkan'], 104000)

    def test_shield_drain_heals_only_actual_remaining_shield(self):
        self.p.d['gemi'].update(shield=100, shieldMax=20000)
        self.launcher('ammunition_rocketlauncher_sar-02')
        self.assertEqual(len(self.w.timers), 5)
        self.land()
        self.assertEqual((self.m['can'], self.m['kalkan']), (100000, 0))
        self.assertEqual(self.p.d['gemi']['shield'], 5100)

    def test_auto_cpus_fire_both_weapons_at_asset_uid(self):
        self.p.d['secili']['roket'] = 'ammunition_rocket_r-310'
        self.p.add_ammo('ammunition_rocket_r-310', 3)
        self.p.d['fircatici_dolu'] = ['ammunition_rocketlauncher_hstrm-01', 5]
        with patch.object(SE, 'toggled', return_value=True):
            self.w.items.auto_weapons(self.uid, self.now)
        self.assertTrue(any(n == 'HellstormAttackCommand' for n, f in self.sent))
        self.land()
        self.assertEqual(self.m['can'] + self.m['kalkan'], 84000)

    def test_auto_weapons_still_apply_npc_bonuses_to_npc_objects(self):
        n = dunya.NPC(42, '84', *cbs.position(2))
        n.d = dict(n.d, hp=1000000, kalkan=0)
        n.hp, n.shield = 1000000, 0
        self.w.npcs[n.id] = n
        self.w.target = n.id
        self.p.d['secili']['roket'] = 'ammunition_rocket_r-310'
        self.p.d['cephane']['ammunition_rocket_r-310'] = 3
        self.p.d['fircatici_dolu'] = ['ammunition_rocketlauncher_hstrm-01', 5]
        with patch.object(SE, 'toggled', return_value=True):
            self.w.items.auto_weapons(n, self.now)
        self.land()
        self.assertEqual(n.hp, 769000)
        self.assertEqual(self.m['can'] + self.m['kalkan'], 105000)

    def test_empty_ordinary_rocket_falls_back_to_damage_ammo(self):
        self.p.d['secili']['roket'] = 'ammunition_rocket_r-310'
        self.p.d['cephane'] = {'ammunition_rocket_r-310': 0, 'ammunition_rocket_plt-2021': 2,
                               'ammunition_specialammo_wiz-x': 3}
        self.w.rocket({'targetId': self.uid})
        self.land()
        self.assertEqual(self.p.d['secili']['roket'], 'ammunition_rocket_plt-2021')
        self.assertEqual(self.p.ammo('ammunition_rocket_plt-2021'), 1)
        self.assertEqual(self.p.ammo('ammunition_specialammo_wiz-x'), 3)
        self.assertEqual(self.m['can'] + self.m['kalkan'], 101000)

    def test_effect_only_specials_do_not_spend_ammo_or_cooldown(self):
        for ammo in ['ammunition_specialammo_wiz-x', 'ammunition_specialammo_dcr-250', 'ammunition_specialammo_pld-8',
                     'ammunition_specialammo_r-ic3', 'ammunition_specialammo_rc-100']:
            with self.subTest(ammo=ammo):
                self.rocket(ammo)
                self.assertEqual(self.p.ammo(ammo), 3)
                self.assertFalse(self.w.timers)

    def test_special_hull_damage_ignores_shield_and_npc_bonus(self):
        self.rocket('ammunition_specialammo_sp-100x')
        self.assertTrue(self.w.timers)
        self.land()
        self.assertEqual((self.m['can'], self.m['kalkan']), (92800, 5000))

    def test_special_shield_steal_uses_actual_drain(self):
        self.p.d['gemi'].update(shield=100, shieldMax=20000)
        self.rocket('ammunition_specialammo_sr-5')
        self.assertTrue(self.w.timers)
        self.land()
        self.assertEqual((self.m['can'], self.m['kalkan']), (100000, 0))
        self.assertEqual(self.p.d['gemi']['shield'], 2600)

    def test_rejected_assets_do_not_spend_ammo_or_loaded_rockets(self):
        for state in ['shielded', 'friendly', 'dead', 'cross_map', 'jumping', 'hero_dead', 'range']:
            with self.subTest(state=state):
                self.a['sahip'] = 'rakip'; self.a['deflector']['acik'] = False
                self.m['can'] = 100000; self.w.map_id = 4
                self.w.jumping = self.w.hero_dead = False
                self.w.hero = dunya.Mover(*cbs.position(2))
                if state == 'shielded': self.a['deflector']['acik'] = True
                if state == 'friendly': self.a['sahip'] = None
                if state == 'dead': self.m['can'] = 0
                if state == 'cross_map': self.w.map_id = 1
                if state == 'jumping': self.w.jumping = True
                if state == 'hero_dead': self.w.hero_dead = True
                if state == 'range': self.w.hero = dunya.Mover(0, 0)
                self.p.d['secili']['roket'] = 'ammunition_rocket_r-310'
                self.p.add_ammo('ammunition_rocket_r-310', 3)
                before = self.p.ammo('ammunition_rocket_r-310')
                self.w.rocket({'targetId': self.uid})
                self.launcher()
                self.assertEqual(self.p.ammo('ammunition_rocket_r-310'), before)
                self.assertEqual(self.p.d['fircatici_dolu'][1], 5)
                self.assertFalse(self.w.timers)

    def test_impact_revalidates_shield_map_and_attacker_state(self):
        for state in ['shielded', 'cross_map', 'jumping', 'hero_dead']:
            with self.subTest(state=state):
                self.a['deflector']['acik'] = False; self.w.map_id = 4
                self.w.jumping = self.w.hero_dead = False
                self.w.rocket_ready = 0
                self.rocket()
                self.launcher()
                self.assertTrue(self.w.timers)
                if state == 'shielded': self.a['deflector']['acik'] = True
                if state == 'cross_map': self.w.map_id = 1
                if state == 'jumping': self.w.jumping = True
                if state == 'hero_dead': self.w.hero_dead = True
                self.land()
                self.assertEqual(self.m['can'] + self.m['kalkan'], 105000)


if __name__ == '__main__':
    unittest.main()
