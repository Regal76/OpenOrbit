"""P.E.T. guard combat resolves live hostile station targets through world damage."""
import sys
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'server'))
import cbs
import dunya
import pet
from profil import Profil


class PetCbsCombat(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.p = Profil(path=str(Path(self.tmp.name) / 'pilot.json'))
        self.sent = []
        self.w = dunya.World(self.p, self.sent.extend, lambda text: None, 4)
        self.c = cbs.Cbs(self.p, None, lambda text: None)
        self.a = self.c.ast(2)
        self.a.update(durum='kurulu', sahip='rakip', deflector={'acik': False})
        laser = next(k for k, d in cbs.MODS.items() if d.get('kod') == 'HULM-1')
        self.module = dict(loot=laser, seviye=0, can=10000, kalkan=5000, azami=10000)
        self.a['yuvalar'] = {'0': self.module}
        self.c.attach(self.w)
        self.uid = cbs.asset_id(2, 0)
        self.xy = cbs.position(2)
        self.w.hero = dunya.Mover(*self.xy)
        self.p.d['pet'] = pet.new_pet(self.p)
        self.p.pet_config()['lasers'] = [99000001]
        self.pet = pet.Pet(self.p, lambda text: None)
        self.w.pet = self.pet
        self.pet.attach(self.w)
        self.pet.launch()
        self.pet.d['disli'] = pet.GUARD           # launches passive; these cases cover Guard mode
        self.pet.mover = dunya.Mover(*self.xy)
        self.now = time.time()
        self.pet.tick_t = self.now
        self.pet.next_second = self.now + 100
        self.w.target, self.w.attacking = self.uid, True
        self.sent.clear()
        self.hit = patch.object(pet.random, 'random', return_value=0)
        self.hit.start()
        self.addCleanup(self.hit.stop)

    def fire(self, when=None):
        self.pet.tick(self.now if when is None else when)

    def test_guard_damages_owner_station_target_with_pet_attacker(self):
        ammo = self.p.d['cephane'][self.p.d['secili']['lazer']]
        self.fire()
        self.assertLess(self.module['can'] + self.module['kalkan'], 15000)
        self.assertEqual(self.pet.shooting, self.uid)
        self.assertEqual(self.p.d['cephane'][self.p.d['secili']['lazer']], ammo - 1)
        hit = next(f for name, f in self.sent if name == 'AttackHitCommand')
        self.assertEqual((hit['attackerId'], hit['victimId']), (self.pet.pid, self.uid))
        salvo = next(f for name, f in self.sent if name == 'AttackLaserRunCommand')
        self.assertEqual((salvo['attackerId'], salvo['targetId']), (self.pet.pid, self.uid))

    def test_station_uses_player_laser_damage_without_npc_bonus(self):
        self.p.d['esyalar']['99000001'] = 'equipment_weapon_laser_lf-3'
        with patch.object(pet.random, 'uniform', return_value=1):
            self.fire()
        hit = next(f for name, f in self.sent if name == 'AttackHitCommand')
        self.assertEqual(hit['damage'], 175)

    def test_sab_hits_only_station_shield(self):
        self.p.d['secili']['lazer'] = 'ammunition_laser_sab-50'
        self.p.d['cephane']['ammunition_laser_sab-50'] = 10
        with patch.object(pet.random, 'uniform', return_value=1):
            self.fire()
        self.assertEqual((self.module['can'], self.module['kalkan']), (10000, 4870))

    def test_guard_still_attacks_owner_npc_target_with_pet_attacker(self):
        npc = dunya.NPC(150300001, '84', *self.xy)
        self.w.npcs[npc.id] = npc
        npc.hp, npc.shield = 10000, 5000
        self.w.target = npc.id
        self.fire()
        self.assertLess(npc.hp + npc.shield, 15000)
        hit = next(f for name, f in self.sent if name == 'AttackHitCommand')
        self.assertEqual((hit['attackerId'], hit['victimId']), (self.pet.pid, npc.id))
        self.assertEqual(self.module['can'] + self.module['kalkan'], 15000)

    def test_combo_guard_damages_station(self):
        self.pet.d['disli'] = pet.COMBO_GUARD
        self.fire()
        self.assertLess(self.module['can'] + self.module['kalkan'], 15000)

    def test_guard_reacts_to_recent_station_attack_without_owner_firing(self):
        self.w.target, self.w.attacking = None, False
        self.w.last_asset_attacker = (self.uid, self.now)
        self.fire()
        self.assertLess(self.module['can'] + self.module['kalkan'], 15000)

    def test_guard_returns_fire_after_station_hits_pet_without_owner_firing(self):
        gun = dict(loot='module_ltm-lr', seviye=0, can=10000, kalkan=5000, azami=10000)
        self.a['yuvalar']['2'] = gun
        x, y = cbs.satellite_pos(2, 2)
        self.w.hero = dunya.Mover(x + 450, y)
        self.pet.mover = dunya.Mover(x + 300, y)
        self.pet.d.update(can=1000000, kalkan=0)
        self.w.target, self.w.attacking = None, False
        self.c.rival_fire(self.now)
        self.assertLess(self.pet.d['can'], 1000000)
        self.assertEqual(self.w.last_asset_attacker, (cbs.asset_id(2, 2), self.now))
        self.fire(self.now + .1)
        self.assertLess(gun['can'] + gun['kalkan'], 15000)
        self.assertEqual(self.pet.shooting, cbs.asset_id(2, 2))
        self.assertFalse(self.w.attacking)

    def test_stale_station_retaliation_is_not_a_target(self):
        self.w.target, self.w.attacking = None, False
        self.w.last_asset_attacker = (self.uid, self.now - 10)
        self.fire()
        self.assertEqual(self.module['can'] + self.module['kalkan'], 15000)

    def test_station_must_remain_attackable_on_each_tick(self):
        self.fire()
        self.module['can'], self.module['kalkan'] = 10000, 5000
        self.a['deflector']['acik'] = True
        self.sent.clear()
        self.fire(self.now + 2)
        self.assertEqual(self.module['can'] + self.module['kalkan'], 15000)
        self.assertIsNone(self.pet.shooting)
        self.assertTrue(any(name == 'AttackAbortLaserCommand' for name, f in self.sent))

    def test_noncombat_or_unavailable_pet_never_damages_station(self):
        for state in ('passive', 'inactive', 'dead', 'empty_fuel', 'unowned', 'no_lasers'):
            with self.subTest(state=state):
                original = self.p.d['pet']
                self.pet.active = state != 'inactive'
                original.update(disli=pet.PASSIVE if state == 'passive' else pet.GUARD,
                                yikik=state == 'dead', yakit=0 if state == 'empty_fuel' else 1000)
                self.p.pet_config()['lasers'] = [] if state == 'no_lasers' else [99000001]
                self.pet.next_shot = 0
                if state == 'unowned':
                    self.p.d['pet'] = None
                try:
                    self.fire()
                finally:
                    self.p.d['pet'] = original
                self.assertEqual(self.module['can'] + self.module['kalkan'], 15000)

    def test_friendly_shielded_dead_and_other_map_stations_are_not_targets(self):
        for state in ('friendly', 'shielded', 'dead', 'other_map'):
            with self.subTest(state=state):
                self.a['sahip'] = 'oyuncu' if state == 'friendly' else 'rakip'
                self.c.st['moduller']['157500000'] = self.module
                self.a['yuvalar'] = {'0': {'iid': 157500000, 'kurulum_bitis': 0} if state == 'friendly' else self.module}
                self.a['deflector']['acik'] = state == 'shielded'
                self.module['can'] = 0 if state == 'dead' else 10000
                self.w.map_id = 1 if state == 'other_map' else 4
                self.pet.next_shot = 0
                self.fire()
                self.assertEqual(self.module['kalkan'], 5000)
                self.assertFalse(any(name == 'AttackLaserRunCommand' for name, f in self.sent))

    def test_out_of_range_pet_approaches_before_firing(self):
        x, y = self.xy
        self.pet.mover = dunya.Mover(x + 900, y)
        self.fire()
        self.assertEqual(self.module['can'] + self.module['kalkan'], 15000)
        self.assertTrue(any(name == 'MoveCommand' and f['userId'] == self.pet.pid for name, f in self.sent))
        self.fire(self.now + 3)
        self.assertLess(self.module['can'] + self.module['kalkan'], 15000)

    def test_leaving_laser_range_aborts_existing_station_salvo(self):
        self.pet.shooting = self.uid
        self.pet.mover = dunya.Mover(self.xy[0] + 900, self.xy[1])
        self.sent.clear()
        self.fire(self.now + .1)
        self.assertIsNone(self.pet.shooting)
        self.assertTrue(any(name == 'AttackAbortLaserCommand' for name, f in self.sent))

    def test_empty_ammo_stops_station_salvo(self):
        self.fire()
        self.p.d['cephane'][self.p.d['secili']['lazer']] = 0
        self.sent.clear()
        self.fire(self.now + 2)
        self.assertIsNone(self.pet.shooting)
        self.assertTrue(any(name == 'AttackAbortLaserCommand' for name, f in self.sent))

    def test_station_outside_owner_combat_radius_is_not_chased(self):
        x, y = self.xy
        self.w.hero = dunya.Mover(x + 1100, y)
        self.fire()
        self.assertEqual(self.module['can'] + self.module['kalkan'], 15000)
        self.assertIsNone(self.pet.shooting)

    def test_fire_interval_and_dead_target_stop_salvo(self):
        self.fire()
        first = self.module['can'] + self.module['kalkan']
        self.fire(self.now + .1)
        self.assertEqual(self.module['can'] + self.module['kalkan'], first)
        self.module['can'] = 0
        self.sent.clear()
        self.fire(self.now + 2)
        self.assertIsNone(self.pet.shooting)
        self.assertTrue(any(name == 'AttackAbortLaserCommand' for name, f in self.sent))
    def test_station_hit_uses_pet_shield_and_reports_station_attacker(self):
        self.pet.d.update(can=10000, kalkan=5000)
        damage = self.pet.station_hit(1000, self.uid, atype=0, now=self.now)
        self.assertEqual(damage, 1000)
        self.assertEqual((self.pet.d['can'], self.pet.d['kalkan']), (9800, 4200))
        hit = next(f for name, f in self.sent if name == 'AttackHitCommand')
        self.assertEqual((hit['attackerId'], hit['victimId'], hit['attackType']['attackTypeValue']),
                         (self.uid, self.pet.pid, 0))
        self.assertTrue(any(name == 'PetShieldUpdateCommand' for name, f in self.sent))
        self.assertTrue(any(name == 'PetHitpointsUpdateCommand' for name, f in self.sent))

    def test_station_hit_caps_feedback_to_actual_damage_and_destroys_once(self):
        self.pet.d.update(can=10, kalkan=5)
        self.pet.shooting = self.uid
        self.assertEqual(self.pet.station_hit(1000, self.uid, atype=1, now=self.now), 15)
        self.assertEqual(self.pet.station_hit(1000, self.uid, atype=1, now=self.now), 0)
        self.assertFalse(self.pet.active)
        self.assertTrue(self.pet.d['yikik'])
        self.assertEqual(len([1 for name, f in self.sent if name == 'PetIsDestroyedCommand']), 1)
        self.assertTrue(any(name == 'AttackAbortLaserCommand' for name, f in self.sent))
        self.assertEqual(next(f['damage'] for name, f in self.sent if name == 'AttackHitCommand'), 15)

    def test_station_hit_rejects_unavailable_pet_or_world(self):
        for state in ('inactive', 'dead', 'unowned', 'hero_dead', 'jumping'):
            with self.subTest(state=state):
                original = self.p.d['pet']
                original.update(can=10000, kalkan=5000, yikik=state == 'dead')
                self.pet.active = state != 'inactive'
                self.w.hero_dead, self.w.jumping = state == 'hero_dead', state == 'jumping'
                if state == 'unowned':
                    self.p.d['pet'] = None
                try:
                    self.assertEqual(self.pet.station_hit(1000, self.uid, now=self.now), 0)
                finally:
                    self.p.d['pet'] = original
                self.assertEqual((original['can'], original['kalkan']), (10000, 5000))



if __name__ == '__main__':
    unittest.main()
