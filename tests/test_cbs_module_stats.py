"""Published CBS weapon properties and actual station firing boundaries."""
import sys, tempfile, time, unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'server'))
import cbs, dunya
from profil import Profil

# Official FR CBS FAQ (module table, edited 2023-01-05), corroborated DE/RU.
WEAPONS = {'module_ltm-lr': (59850, 590, .9), 'module_ltm-mr': (48450, 650, .7),
           'module_ltm-hr': (28500, 720, .6), 'module_ram-ma': (71250, 780, .7),
           'module_ram-la': (85500, 900, .5)}

class PublishedModuleStats(unittest.TestCase):
    def test_weapons_follow_published_damage_hp_range_accuracy_and_level_growth(self):
        for loot, (damage, reach, chance) in WEAPONS.items():
            with self.subTest(loot=loot):
                row = cbs.MODS[loot]
                self.assertEqual((row['menzil'], row['isabet']), (reach, chance))
                self.assertEqual(row['hasar'], [damage * (100 + 2*i) // 100 for i in range(16)])
                self.assertEqual(row['can'], [1560000 * (100 + 2*i) // 100 for i in range(16)])

    def test_hull_has_published_5850000_base_hp_and_7605000_at_level16(self):
        self.assertEqual(cbs.MODS['module_hulm-1']['can'], [5850000 * (100 + 2*i) // 100 for i in range(16)])

    def test_rival_defaults_do_not_secretly_reduce_weapon_damage_or_module_hp(self):
        self.assertEqual(cbs.D['rakip']['hasar_carpani'], 1)
        self.assertEqual(cbs.D['rakip']['can_carpani'], 1)

class StationWeaponFire(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        self.p = Profil(path=str(Path(self.tmp.name)/'pilot.json'))
        self.sent = []
        self.w = dunya.World(self.p, self.sent.extend, lambda _: None, 4)
        self.c = cbs.Cbs(self.p, None, lambda _: None)
        self.a = self.c.ast(2)
        self.a.update(durum='kurulu', sahip='rakip', rakip='Test', deflector={'acik':False}, yuvalar={})
        self.c.attach(self.w)
        self.now = time.time()
        self.p.d['gemi'].update(hitPoints=10000000, hitMax=10000000, shield=0, nanoHull=0)

    def equip(self, loot, level=0):
        row = dict(loot=loot, seviye=level, can=1560000, kalkan=0)
        self.a['yuvalar'] = {'2':row}
        self.sent.clear(); self.c.next_shot.clear()
        return cbs.satellite_pos(2, 2)

    def test_each_weapon_fires_at_its_published_boundary_but_not_beyond(self):
        for loot, (_, reach, _) in WEAPONS.items():
            with self.subTest(loot=loot):
                x,y = self.equip(loot)
                self.w.hero = dunya.Mover(x+reach+.01,y)
                with patch.object(cbs.random, 'random', return_value=1): self.c.rival_fire(self.now)
                self.assertEqual(self.sent, [])
                self.w.hero = dunya.Mover(x+reach,y)
                with patch.object(cbs.random, 'random', return_value=1): self.c.rival_fire(self.now)
                self.assertTrue(self.sent)
                before = len(self.sent)
                self.c.rival_fire(self.now+.01)
                self.assertEqual(len(self.sent), before)

    def test_each_rival_weapon_delivers_full_level16_damage_on_a_hit(self):
        for loot, (damage, _, _) in WEAPONS.items():
            with self.subTest(loot=loot):
                x,y = self.equip(loot, 15)
                self.w.hero = dunya.Mover(x,y)
                with patch.object(cbs.random, 'random', return_value=0), patch.object(dunya.AY, 'carpan', return_value=1):
                    self.c.rival_fire(self.now)
                hit = next(f for n,f in self.sent if n == 'AttackHitCommand')
                self.assertEqual(hit['damage'], damage*130//100)

    def test_each_weapon_misses_at_accuracy_threshold_without_hurting_player(self):
        for loot, (_,_,chance) in WEAPONS.items():
            with self.subTest(loot=loot):
                x,y = self.equip(loot)
                self.w.hero = dunya.Mover(x,y)
                before = self.p.d['gemi']['hitPoints']
                with patch.object(cbs.random, 'random', return_value=chance): self.c.rival_fire(self.now)
                self.assertEqual(self.p.d['gemi']['hitPoints'], before)
                self.assertTrue(any(n == 'AttackMissedCommand' for n,f in self.sent))

    def test_rocket_module_emits_native_rocket_instead_of_laser_and_rocket_damage_type(self):
        x,y = self.equip('module_ram-ma')
        self.w.hero = dunya.Mover(x,y)
        with patch.object(cbs.random, 'random', return_value=0): self.c.rival_fire(self.now)
        rockets = [f for n,f in self.sent if n == 'HellstormAttackCommand']
        self.assertEqual(len(rockets), 1)
        self.assertEqual((rockets[0]['attackerId'], rockets[0]['currentLoad'], rockets[0]['hit']), (cbs.asset_id(2,2),1,True))
        self.assertFalse(any(n == 'AttackLaserRunCommand' for n,f in self.sent))
        self.assertEqual(next(f['attackType']['attackTypeValue'] for n,f in self.sent if n == 'AttackHitCommand'), 0)

    def test_own_rocket_module_fires_at_npc_with_rocket_effect_and_damage_type(self):
        x,y = self.equip('module_ram-la')
        row = self.a['yuvalar']['2']
        self.a.pop('sahip'); self.a['yuvalar'] = {'2':{'iid':157500002,'kurulum_bitis':0}}
        self.c.st['moduller']['157500002'] = row
        tip = next(t for t,d in dunya.CFG['tipler'].items() if d.get('hiz',0)>0 and not d.get('dost'))
        npc = dunya.NPC(91001,tip,x+100,y)
        npc.hp=10000000; npc.shield=0; npc.engaged=True
        self.w.npcs[npc.id]=npc; self.c.raiders[npc.id]=2
        with patch.object(cbs.random,'random',return_value=0), patch.object(dunya.AY,'carpan',return_value=1):
            self.c.raid_fight(2,self.a,self.now)
        self.assertTrue(any(n == 'HellstormAttackCommand' and f['targetId']==npc.id for n,f in self.sent))
        self.assertEqual(next(f['attackType']['attackTypeValue'] for n,f in self.sent if n == 'AttackHitCommand'),0)
        self.assertEqual(next(f['damage'] for n,f in self.sent if n == 'AttackHitCommand'),85500)

    def test_npc_damage_cheat_and_anti_ai_floor_do_not_suppress_hostile_cbs_damage(self):
        x,y = self.equip('module_ltm-lr')
        self.w.hero = dunya.Mover(x,y)
        before = self.p.d['gemi']['hitPoints']
        with patch.object(cbs.random,'random',return_value=0), patch.object(dunya.AY,'carpan',return_value=0), patch.object(self.w.tech,'hp_floor',return_value=before+100000):
            self.c.rival_fire(self.now)
        self.assertEqual(self.p.d['gemi']['hitPoints'],before-59850)
        self.assertEqual(next(f['damage'] for n,f in self.sent if n=='AttackHitCommand'),59850)

    def test_owner_damage_cheat_does_not_amplify_station_turrets(self):
        x,y = self.equip('module_ltm-lr')
        row = self.a['yuvalar']['2']
        self.a.pop('sahip'); self.a['yuvalar']={'2':{'iid':157500002,'kurulum_bitis':0}}
        self.c.st['moduller']['157500002']=row
        tip=next(t for t,d in dunya.CFG['tipler'].items() if d.get('hiz',0)>0 and not d.get('dost'))
        npc=dunya.NPC(91001,tip,x+100,y);npc.hp=10000000;npc.shield=0;npc.engaged=True
        self.w.npcs[npc.id]=npc;self.c.raiders[npc.id]=2
        with patch.object(cbs.random,'random',return_value=0), patch.object(dunya.AY,'carpan',return_value=10):
            self.c.raid_fight(2,self.a,self.now)
        self.assertEqual(next(f['damage'] for n,f in self.sent if n=='AttackHitCommand'),59850)

    def test_spectrum_reduces_station_lasers_and_marks_beam_but_not_rockets(self):
        for loot,damage in [('module_ltm-lr',59850),('module_ram-ma',71250)]:
            with self.subTest(loot=loot):
                x,y=self.equip(loot);self.w.hero=dunya.Mover(x,y)
                with patch.object(self.p,'mods',return_value={'alinan_lazer':-.8}),patch.object(cbs.random,'random',return_value=0):
                    self.c.rival_fire(self.now)
                expected=int(damage*.2) if loot=='module_ltm-lr' else damage
                self.assertEqual(next(f['damage'] for n,f in self.sent if n=='AttackHitCommand'),expected)
                if loot=='module_ltm-lr':self.assertTrue(next(f['isDiminishedBySkillShield'] for n,f in self.sent if n=='AttackLaserRunCommand'))

    def test_ship_evasion_reduces_station_laser_and_rocket_hit_chance(self):
        for loot,(_,_,chance) in WEAPONS.items():
            with self.subTest(loot=loot):
                x,y=self.equip(loot);self.w.hero=dunya.Mover(x,y)
                with patch.object(self.p,'mods',return_value={'kacinma':.5}),patch.object(cbs.random,'random',return_value=chance*.75):
                    self.c.rival_fire(self.now)
                self.assertTrue(any(n=='AttackMissedCommand' for n,f in self.sent))
                self.assertFalse(any(n=='AttackHitCommand' for n,f in self.sent))

    def test_post_repair_protection_blocks_station_damage_until_it_expires(self):
        x,y=self.equip('module_ltm-lr');self.w.hero=dunya.Mover(x,y)
        before=self.p.d['gemi']['hitPoints']
        self.w.invuln_until=self.now+60
        with patch.object(cbs.random,'random',return_value=0):
            self.c.rival_fire(self.now)
        self.assertEqual(self.p.d['gemi']['hitPoints'],before)
        self.assertFalse(any(n=='AttackHitCommand' and f['damage']>0 for n,f in self.sent))
        self.sent.clear()
        with patch.object(cbs.random,'random',return_value=0):
            self.c.rival_fire(self.now+61)
        self.assertEqual(self.p.d['gemi']['hitPoints'],before-59850)


class PublishedNonweaponModuleStats(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        self.p = Profil(path=str(Path(self.tmp.name) / 'pilot.json'))
        self.c = cbs.Cbs(self.p, None, lambda _: None)
        self.a = self.c.ast(2)
        self.a.update(durum='kurulu', yuvalar={}, deflector={'acik': False})
        self.now = time.mktime((2026, 10, 25, 12, 0, 0, 0, 0, -1))

    def test_repair_and_booster_hp_follow_published_base_and_all_sixteen_levels(self):
        for loot in ('module_repm-1', 'module_honm-1', 'module_dmgm-1', 'module_xpm-1'):
            with self.subTest(loot=loot):
                self.assertEqual(cbs.MODS[loot]['can'], [1040000 * (100 + 2*i) // 100 for i in range(16)])
        for loot in ('module_honm-1', 'module_dmgm-1', 'module_xpm-1'):
            with self.subTest(loot=loot):
                # FAQ gives endpoints and rounded +.46% text; use equal steps between endpoints.
                self.assertEqual(cbs.MODS[loot]['booster_yuzde'], [round(3 + 7*i/15, 2) for i in range(16)])

    def test_deflector_level_changes_reported_and_actual_recharge_at_every_level(self):
        iid = cbs.ITEM_BASE + 1
        row = dict(loot='module_defm-1', seviye=0, can=1000, kalkan=0)
        self.c.st['moduller'][str(iid)] = row
        self.a['yuvalar']['1'] = dict(iid=iid)
        for level in range(16):
            for prime in (False, True):
                with self.subTest(level=level, prime=prime):
                    row['seviye'] = level
                    self.a['deflector'].update(acik=False, sn=0, son=self.now, kapali_bitis=self.now+3600)
                    expected = (600 if prime else 120) * (100 + level) / 100
                    with patch.object(cbs, 'prime_time', return_value=prime):
                        self.assertEqual(self.c.status_cmd(2, self.now)['deflectorShieldRate'], int(expected))
                        self.c.deflector_tick(2, self.a, self.now+60)
                    self.assertAlmostEqual(self.a['deflector']['sn'], expected)

    def test_shared_and_rival_deflector_levels_are_resolved_from_installed_module(self):
        for owner in ('shared', 'rival'):
            with self.subTest(owner=owner):
                row = dict(loot='module_defm-1', seviye=15, can=1000, kalkan=0)
                self.a.pop('sahip', None)
                if owner == 'rival':
                    self.a['sahip'] = 'rakip'; self.a['yuvalar']['1'] = row
                else:
                    self.a['yuvalar']['1'] = dict(iid=cbs.ORTAK_ITEM+1, modul=row)
                with patch.object(cbs, 'prime_time', return_value=False):
                    self.assertEqual(self.c.deflector_rate(self.now, aid=2), 138)

    def test_level16_deflector_charge_integrates_its_bonus_across_prime_boundary(self):
        iid = cbs.ITEM_BASE+1
        self.c.st['moduller'][str(iid)] = dict(loot='module_defm-1', seviye=15, can=1000, kalkan=0)
        self.a['yuvalar']['1'] = dict(iid=iid)
        start = time.mktime((2026, 10, 25, 17, 59, 50, 0, 0, -1))
        self.a['deflector'].update(acik=False, sn=0, son=start, kapali_bitis=start+1800)
        self.c.deflector_tick(2, self.a, start+20)
        self.assertAlmostEqual(self.a['deflector']['sn'], 138)
