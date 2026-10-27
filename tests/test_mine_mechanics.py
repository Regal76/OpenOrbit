"""Mine lifecycle and resulting ship state, without a running game or account writes."""
import copy
import json
import sys
import tempfile
import time
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'server'))
import savas_esya as SE
from profil import Profil
from durum import Etkiler
from dunya import World, Mover, CLIENT_TWEEN
from magaza import Magaza

ACM = 'ammunition_mine_acm-01'
DDM = 'ammunition_mine_ddm-01'
SAB = 'ammunition_mine_sabm-01'
EMP = 'ammunition_mine_empm-01'
SLM = 'ammunition_mine_slm-01'
IM = 'ammunition_mine_im-01'
AGL = 'ammunition_mine_agl-m01'


class MineMechanics(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        config = patch.dict(SE.S['mayin'], {'npc_uyarlama': False})
        config.start()
        self.addCleanup(config.stop)
        self.now = time.time()
        self.w = self.world(101)
        self.other = self.world(102)
        self.shared = SimpleNamespace(uyeler=[self.w, self.other])
        self.w.ortak = self.other.ortak = self.shared
        self.other.pos = (1000, 1000)
        self.w.pos = (3000, 3000)

    def world(self, uid):
        p = Profil(path=str(Path(self.tmp.name) / ('%d.json' % uid)))
        p.d['gemi'].update(hitPoints=100000, hitMax=100000, shield=200000, shieldMax=200000, nanoHull=0)
        p.d['kalkan_emme'] = 0.8
        for loot in SE.PLAYER_MINES:
            p.d.setdefault('cephane', {})[loot] = 10
        w = SimpleNamespace(p=p, hid=uid, hero_dead=False, jumping=False, running=True, map_id='3', ortak=None)
        w.pos, w.sent, w.npcs, w.invulnerable = (1000, 1000), [], {}, False
        w.hero_etki = Etkiler()
        w.hero_pos = lambda now=None: w.pos
        w.send = lambda msgs: w.sent.extend(msgs)
        w.log = lambda text: None
        w.ammo_msgs = lambda loot: []
        w.in_peace = w.in_pvp_peace = lambda x, y: False
        w.stop_repair = lambda: None
        w.hit_npc = lambda *args, **kwargs: None
        w.stats_msgs = None
        w.hero_effect = lambda *args, **kwargs: World.hero_effect(w, *args, **kwargs)
        w.tech = SimpleNamespace(mine_protected=lambda now: False, hp_floor=lambda now: 0)
        w.abilities = SimpleNamespace(reveal=lambda: setattr(w, 'revealed', True))
        w.hero_death = lambda *args, **kwargs: setattr(w, 'hero_dead', True)
        w.items = SE.Esyalar(w)
        return w

    def mine(self, loot, owner=None, until=120, armed=0):
        owner = self.w.hid if owner is None else owner
        self.w.items.mines['test'] = dict(loot=loot, x=1000, y=1000, sahip=owner,
                                        kurulma=self.now + armed, bitis=self.now + until)

    def test_player_triggers_armed_damage_mine(self):
        self.mine(DDM)
        self.w.items.mine_tick(self.now)
        self.assertFalse(self.w.items.mines)
        self.assertLess(self.other.p.d['gemi']['hitPoints'], 100000)

    def test_npc_does_not_trigger_player_mine(self):
        self.other.pos = (5000, 5000)
        self.w.npcs[1] = SimpleNamespace(id=1, d={'hp': 10000, 'kalkan': 0}, hp=10000, shield=0, alive=True, mover=SimpleNamespace(pos=lambda now: (1000, 1000)))
        self.mine(DDM)
        self.w.items.mine_tick(self.now)
        self.assertIn('test', self.w.items.mines)

    def test_arming_and_expiry_do_not_damage_ships(self):
        self.mine(DDM, armed=5)
        self.w.items.mine_tick(self.now + 4.9)
        self.assertEqual(self.other.p.d['gemi']['hitPoints'], 100000)
        self.w.items.mine_tick(self.now + 120)
        self.assertFalse(self.w.items.mines)
        self.assertEqual(self.other.p.d['gemi']['hitPoints'], 100000)

    def test_acm_damage_is_one_hp_based_amount_split_by_shield_absorption(self):
        self.other.items.mine_hero(SE.MINES[ACM], 1, self.w.hid, self.now, ACM)
        self.assertEqual(self.other.p.d['gemi']['shield'], 184000)
        self.assertEqual(self.other.p.d['gemi']['hitPoints'], 96000)

    def test_acm_cannot_kill_but_ddm_can(self):
        g = self.other.p.d['gemi']
        g.update(hitPoints=100, shield=0)
        self.other.items.mine_hero(SE.MINES[ACM], 1, self.w.hid, self.now, ACM)
        self.assertEqual(g['hitPoints'], 1)
        self.other.items.mine_hero(SE.MINES[DDM], 1, self.w.hid, self.now, DDM)
        self.assertEqual(g['hitPoints'], 0)
        self.assertTrue(self.other.hero_dead)

    def test_ddm_uses_base_hull_and_pilot_hull_not_boosted_maximum(self):
        self.other.p.d['gemi'].update(hitMax=1000000, hitPoints=1000000)
        self.other.p.d['yetenekler'] = {'seviye': {'18b': 3}}
        self.other.items.mine_hero(SE.MINES[DDM], 1, self.w.hid, self.now, DDM)
        self.assertEqual(self.other.p.d['gemi']['hitPoints'], 918800)
        self.assertEqual(self.other.p.d['gemi']['shield'], 200000)

    def test_sab_boost_is_capped_at_the_whole_shield(self):
        # fandom SAB-M01: 50% of the shield, raised to at most 100% by the Skill Tree and Lance (wiki audit SILAHLAR-8)
        self.other.items.mine_hero(SE.MINES[SAB], 5, self.w.hid, self.now, SAB)
        self.assertEqual(self.other.p.d['gemi']['shield'], 0)
        self.assertEqual(self.other.p.d['gemi']['hitPoints'], 100000)

    def test_anti_mine_transmitter_prevents_player_trigger(self):
        self.other.tech.mine_protected = lambda now: True
        self.mine(DDM)
        self.w.items.mine_tick(self.now)
        self.assertIn('test', self.w.items.mines)

    def test_slm_slows_owner_as_well_as_other_players(self):
        self.w.pos = (1000, 1000)
        self.w.items.mine_hero(SE.MINES[SLM], 1, self.w.hid, self.now, SLM)
        self.assertAlmostEqual(self.w.hero_etki.slow(), 0.5)

    def test_infection_applies_and_refreshes_single_fifteen_minute_debuff(self):
        for _ in range(2):
            self.other.items.mine_hero(SE.MINES[IM], 1, self.w.hid, self.now, IM)
        effects = self.other.hero_etki.get('enfeksiyon')
        self.assertEqual(len(effects), 1)
        self.assertAlmostEqual(effects[0]['bitis'] - self.now, 900, delta=1)
        self.assertEqual(self.other.hero_etki.mods().get('lazer'), 0.1)
        self.assertEqual(self.other.hero_etki.mods().get('can_carpan'), 0.85)
        self.assertAlmostEqual(self.other.hero_etki.speed_factor(), 0.9)

    def test_lure_does_not_pull_agatus_from_outside_its_radius(self):
        destinations = []
        n = SimpleNamespace(alive=True, engaged=False, d={'ad': 'Agatus', 'hiz': 300},
                            mover=SimpleNamespace(pos=lambda now: (99999, 99999),
                                                  go=lambda *args: destinations.append(args) or 1000),
                            etki=Etkiler(), id=1)
        self.w.npcs[1] = n
        self.w.visible = set()
        self.mine(AGL)
        self.w.items.lure_tick(self.now)
        self.assertFalse(destinations)

    def test_emp_uncloaks_without_hull_or_shield_damage(self):
        self.other.p.d['cpu_gizli'] = True
        self.other.items.mine_hero(SE.MINES[EMP], 1, self.w.hid, self.now, EMP)
        self.assertFalse(self.other.p.d['cpu_gizli'])
        self.assertTrue(self.other.revealed)
        self.assertEqual(self.other.p.d['gemi']['hitPoints'], 100000)
        self.assertEqual(self.other.p.d['gemi']['shield'], 200000)

    def test_insta_shield_blocks_mine_damage(self):
        self.other.hero_etki.add('dokunulmaz', 3)
        self.other.items.mine_hero(SE.MINES[DDM], 1, self.w.hid, self.now, DDM)
        self.assertEqual(self.other.p.d['gemi']['hitPoints'], 100000)

    def test_deployment_keeps_lance_bonus_after_formation_switch(self):
        self.w.pos = (1000, 1000)
        self.w.p.d['formasyon'] = 3
        self.w.items.place_mine(DDM, self.now)
        self.assertEqual(self.w.p.ammo(DDM), 9)
        self.w.p.d['formasyon'] = 0
        self.w.pos = (5000, 5000)
        self.other.p.d['gemi'].update(hitPoints=1000000, hitMax=1000000)
        self.w.items.mine_tick(self.now + 5)
        self.assertEqual(self.other.p.d['gemi']['hitPoints'], 893200)

    def test_slowdown_mine_arms_after_one_second(self):
        self.w.pos = (1000, 1000)
        self.w.items.place_mine(SLM, self.now)
        self.w.pos = (5000, 5000)
        self.w.items.mine_tick(self.now + 0.9)
        self.assertEqual(self.other.hero_etki.slow(), 0)
        self.w.items.mine_tick(self.now + 1)
        self.assertEqual(self.other.hero_etki.slow(), 0.5)

    def test_shared_cooldown_does_not_consume_another_mine(self):
        self.w.items.place_mine(ACM, self.now)
        self.w.pos = (4000, 4000)
        self.w.items.place_mine(DDM, self.now + 1)
        self.assertEqual(self.w.p.ammo(DDM), 10)
        self.assertEqual(len(self.w.items.mines), 1)

    def test_infection_expires_and_is_not_cured_by_removing_slowdown(self):
        self.other.items.mine_hero(SE.MINES[IM], 1, self.w.hid, self.now, IM)
        self.other.hero_etki.remove('yavas')
        self.assertEqual(self.other.hero_etki.speed_factor(), 0.9)
        self.assertEqual(self.other.hero_etki.mods(self.now + 901), {})

    def test_pve_adaptation_still_triggers_mine_and_uses_shield_absorption(self):
        SE.S['mayin']['npc_uyarlama'] = True
        self.other.pos = (5000, 5000)
        npc = SimpleNamespace(id=1, d={'hp': 100000, 'kalkan': 200000, 'kalkan_emme': 0.7},
                              hp=100000, shield=200000, alive=True,
                              mover=SimpleNamespace(pos=lambda now: (1000, 1000)))
        self.w.npcs[1] = npc
        def apply_hit(uid, damage, kind, split):
            npc.shield -= split[0]
            npc.hp -= split[1]
        self.w.hit_npc = apply_hit
        self.mine(ACM)
        self.w.items.mine_tick(self.now)
        self.assertEqual((npc.hp, npc.shield), (94000, 186000))
        self.assertFalse(self.w.items.mines)


class InfectionLifecycle(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.p = Profil(path=str(Path(self.tmp.name) / 'profile.json'))
        with (ROOT / 'server/data/varsayilan/yanitlar.json').open() as stream:
            replies = json.load(stream)
        self.shop = Magaza(self.p, copy.deepcopy(replies), lambda *args: None)
        self.sent = []
        self.w = World(self.p, self.sent.extend, lambda *args: None, '3')
        self.w.stats_msgs = self.shop.apply_stats
        self.shop.apply_stats()
        self.p.set_hull(hp=self.p.d['gemi']['hitMax'])
        self.sent.clear()

    def test_apply_immediately_updates_real_stats_and_packets(self):
        baseline = self.p.d['gemi']['hitMax']
        self.w.hero_effect('enfeksiyon', 900)
        self.assertEqual(self.p.d['gemi']['hitMax'], int(baseline * 0.85))
        self.assertIn('HitpointInfoCommand', [name for name, fields in self.sent])
        self.assertIn('AttributeShipSpeedUpdateCommand', [name for name, fields in self.sent])

    def test_expiry_restores_real_stats_and_sends_hull_update(self):
        baseline = self.p.d['gemi']['hitMax']
        self.w.hero_effect('enfeksiyon', 900)
        self.sent.clear()
        future = time.time() + 901
        with patch('time.time', return_value=future):
            self.w.effects_tick(future)
        self.assertEqual(self.p.d['gemi']['hitMax'], baseline)
        self.assertIn('HitpointInfoCommand', [name for name, fields in self.sent])

    def test_expiry_refreshes_stats_even_if_a_profile_read_prunes_effect_first(self):
        baseline = self.p.d['gemi']['hitMax']
        self.w.hero_effect('enfeksiyon', 900)
        self.sent.clear()
        future = time.time() + 901
        with patch('time.time', return_value=future):
            self.p.mods()
            self.w.effects_tick(future)
        self.assertEqual(self.p.d['gemi']['hitMax'], baseline)
        self.assertIn('HitpointInfoCommand', [name for name, fields in self.sent])

    def test_map_change_carries_only_infection_with_remaining_duration(self):
        self.w.hero_effect('enfeksiyon', 900)
        expiry = self.w.hero_etki.get('enfeksiyon')[0]['bitis']
        self.w.hero_effect('yavas', 40, 0.5)
        self.w.stop()
        with patch('time.time', return_value=expiry - 600):
            new = World(self.p, self.sent.extend, lambda *args: None, '4')
            self.assertAlmostEqual(new.hero_etki.get('enfeksiyon')[0]['bitis'] - time.time(), 600)
        new.stats_msgs = self.shop.apply_stats
        self.assertEqual(len(new.hero_etki.get('enfeksiyon')), 1)
        self.assertEqual(new.hero_etki.get('enfeksiyon')[0]['bitis'], expiry)
        self.assertFalse(new.hero_etki.get('yavas'))
        self.assertAlmostEqual(self.p.mods()['hiz'], -0.1)

    def test_death_removes_infection_and_restores_maximum_without_healing(self):
        baseline = self.p.d['gemi']['hitMax']
        self.w.hero_effect('enfeksiyon', 900)
        self.p.set_hull(hp=0)
        self.sent.clear()
        self.w.hero_death([])
        self.assertFalse(self.w.hero_etki.get('enfeksiyon'))
        self.assertEqual(self.p.d['gemi']['hitMax'], baseline)
        self.assertEqual(self.p.d['gemi']['hitPoints'], 0)
        self.assertIn('HitpointInfoCommand', [name for name, fields in self.sent])
        self.w.stop()
        new = World(self.p, self.sent.extend, lambda *args: None, '4')
        self.assertFalse(new.hero_etki.get('enfeksiyon'))

    def test_hull_penalty_multiplies_boosted_hull_and_pilot_hull(self):
        self.p.d['formasyon'] = 11  # Heart: +20% hull, a real independent hull bonus
        self.p.d['yetenekler'] = {'seviye': {'18b': 3}}
        self.shop.apply_stats()
        baseline = self.p.d['gemi']['hitMax']
        self.assertEqual(baseline, 477200)
        self.w.hero_effect('enfeksiyon', 900)
        self.assertEqual(self.p.d['gemi']['hitMax'], 405620)

    def test_infection_mine_hits_before_hull_capacity_change(self):
        self.p.d['gemi'].update(hitPoints=356000, shield=200000, shieldMax=200000)
        self.p.d['kalkan_emme'] = 0.8
        self.w.items.mine_hero(SE.MINES[IM], 1, 999, time.time(), IM)
        hit = [fields for name, fields in self.sent if name == 'AttackHitCommand'][-1]
        self.assertEqual(hit['damage'], 71200)
        self.assertEqual(hit['victimHitpoints'], 341760)
        self.assertEqual(hit['victimShield'], 143040)
        self.assertEqual(self.p.d['gemi']['hitPoints'], 302600)
        self.assertEqual(self.p.d['gemi']['hitMax'], 302600)
        packet_names = [name for name, fields in self.sent]
        self.assertLess(packet_names.index('AttackHitCommand'), packet_names.index('HitpointInfoCommand'))

    def plague_visuals(self):
        return [fields for name, fields in self.sent
                if name == 'VisualModifierCommand' and fields['modifier'] == 57]

    def test_infection_starts_native_plague_visual_and_removes_it_after_pruned_expiry(self):
        self.w.hero_effect('enfeksiyon', 900, source=IM)
        self.assertTrue(self.plague_visuals(), 'infection must emit its native visual modifier')
        visual = self.plague_visuals()[-1]
        self.assertTrue(visual['activated'])
        self.assertEqual(visual['userId'], self.w.hid)
        self.assertEqual(visual['additionalAttribute'], '900')
        self.sent.clear()
        future = time.time() + 901
        with patch('time.time', return_value=future):
            self.p.mods()
            self.w.effects_tick(future)
        self.assertFalse(self.plague_visuals()[-1]['activated'])

    def test_infection_reinfection_replaces_visual_timer_and_death_removes_visual(self):
        self.w.hero_effect('enfeksiyon', 900, source=IM)
        with patch('time.time', return_value=time.time() + 50):
            self.w.hero_effect('enfeksiyon', 900, source=IM)
        self.assertEqual([v['activated'] for v in self.plague_visuals()], [True, False, True])
        self.assertEqual(self.plague_visuals()[-1]['additionalAttribute'], '900')
        self.sent.clear()
        self.w.hero_death([])
        self.assertFalse(self.plague_visuals()[-1]['activated'])

    def test_reload_replays_active_plague_with_remaining_timer(self):
        self.w.hero_effect('enfeksiyon', 900, source=IM)
        expiry = self.p._infection_effect['bitis']
        self.sent.clear()
        with patch('time.time', return_value=expiry - 600):
            self.w.resend()
        self.assertEqual(len(self.plague_visuals()), 1)
        self.assertTrue(self.plague_visuals()[0]['activated'])
        self.assertEqual(self.plague_visuals()[0]['additionalAttribute'], '600')

    def test_slow_mine_visual_clears_after_expiry_even_if_stat_read_prunes_effect(self):
        baseline_speed = self.p.d['gemi']['speed']
        self.w.items.mine_hero(SE.MINES[SLM], 1, 999, time.time(), SLM)
        messages = [fields['message'] for name, fields in self.sent if name == 'LegacyModule']
        self.assertIn('0|n|fx|start|SABOTEUR_DEBUFF|%d' % self.w.hid, messages)
        self.sent.clear()
        future = time.time() + 6
        with patch('time.time', return_value=future):
            self.p.mods()
            self.w.effects_tick(future)
        messages = [fields['message'] for name, fields in self.sent if name == 'LegacyModule']
        self.assertIn('0|n|fx|end|SABOTEUR_DEBUFF|%d' % self.w.hid, messages)
        self.assertEqual(self.p.d['gemi']['speed'], baseline_speed)

    def test_emp_early_slow_removal_clears_visual_but_preserves_infection(self):
        self.w.hero_effect('enfeksiyon', 900, source=IM)
        self.w.hero_effect('yavas', 5, 0.5, source=SLM)
        self.sent.clear()
        self.w.hero_etki.remove('yavas')
        self.w.effects_tick(time.time())
        self.assertFalse([v for v in self.plague_visuals() if not v['activated']])
        messages = [fields['message'] for name, fields in self.sent if name == 'LegacyModule']
        self.assertIn('0|n|fx|end|SABOTEUR_DEBUFF|%d' % self.w.hid, messages)

    def start_flight(self, now, target=(11000, 1000)):
        self.w.hero = Mover(1000, 1000)
        self.w.hero.go(*target, self.p.d['gemi']['speed'], now)
        self.sent.clear()

    def assert_retimed_move(self, now, position, target):
        self.assertEqual(self.w.hero_pos(now), position)
        self.assertEqual((self.w.hero.x1, self.w.hero.y1), target)
        remaining = ((target[0] - position[0]) ** 2 + (target[1] - position[1]) ** 2) ** 0.5
        duration = remaining / self.p.d['gemi']['speed']
        self.assertAlmostEqual(self.w.hero.t1, now + duration * CLIENT_TWEEN)
        moves = [fields for name, fields in self.sent if name == 'MoveCommand' and fields['userId'] == self.w.hid]
        self.assertEqual(len(moves), 1)
        self.assertEqual(moves[0], dict(userId=self.w.hid, x=target[0], y=target[1], timeToTarget=int(duration * 1000)))
        names = [name for name, fields in self.sent]
        self.assertLess(names.index('AttributeShipSpeedUpdateCommand'), names.index('MoveCommand'))

    def test_slow_mine_retimes_active_flight_and_pruned_expiry_without_repeated_moves(self):
        now = time.time()
        self.start_flight(now)
        baseline = self.p.d['gemi']['speed']
        position = self.w.hero_pos(now + 2)
        original_end = self.w.hero.t1
        with patch('time.time', return_value=now + 2):
            self.w.items.mine_hero(SE.MINES[SLM], 1, 999, time.time(), SLM)
        self.assert_retimed_move(now + 2, position, (11000, 1000))
        self.assertGreater(self.w.hero.t1, original_end)
        slowed_end = self.w.hero.t1
        position = self.w.hero_pos(now + 8)
        self.sent.clear()
        with patch('time.time', return_value=now + 8):
            self.p.mods()
            self.w.effects_tick(time.time())
        self.assertEqual(self.p.d['gemi']['speed'], baseline)
        self.assert_retimed_move(now + 8, position, (11000, 1000))
        self.assertLess(self.w.hero.t1, slowed_end)
        self.sent.clear()
        with patch('time.time', return_value=now + 8.25):
            self.w.effects_tick(time.time())
        self.assertFalse([v for name, v in self.sent if name == 'MoveCommand'])

    def test_infection_retimes_current_flight_and_later_flight_on_expiry(self):
        now = time.time()
        self.start_flight(now)
        position = self.w.hero_pos(now + 2)
        with patch('time.time', return_value=now + 2):
            self.w.items.mine_hero(SE.MINES[IM], 1, 999, time.time(), IM)
        self.assert_retimed_move(now + 2, position, (11000, 1000))
        with patch('time.time', return_value=now + 901):
            self.w.on_move(dict(targetX=20000, targetY=1000, positionX=11000, positionY=1000))
        position = self.w.hero_pos(now + 903)
        self.sent.clear()
        with patch('time.time', return_value=now + 903):
            self.w.effects_tick(time.time())
        self.assert_retimed_move(now + 903, position, (20000, 1000))

    def test_reinfection_and_overlapping_weaker_slow_do_not_restart_unchanged_speed(self):
        now = time.time()
        self.start_flight(now)
        with patch('time.time', return_value=now + 1):
            self.w.hero_effect('enfeksiyon', 900, source=IM)
            self.w.hero_effect('yavas', 5, 0.5, source=SLM)
        end = self.w.hero.t1
        self.sent.clear()
        with patch('time.time', return_value=now + 2):
            self.w.hero_effect('enfeksiyon', 900, source=IM)
            self.w.hero_effect('yavas', 10, 0.2, source='other-slow')
        self.assertEqual(self.w.hero.t1, end)
        self.assertFalse([v for name, v in self.sent if name == 'MoveCommand'])
        position = self.w.hero_pos(now + 7)
        self.sent.clear()
        with patch('time.time', return_value=now + 7):
            self.w.effects_tick(time.time())
        self.assert_retimed_move(now + 7, position, (11000, 1000))
        self.assertLess(self.w.hero.t1, end)

    def test_completed_or_inactive_flight_does_not_restart_on_status_change(self):
        now = time.time()
        for state in ('arrived', 'jumping', 'dead'):
            with self.subTest(state=state):
                self.w.hero_etki.remove()
                self.shop.apply_stats()
                self.start_flight(now, (1100, 1000))
                event = now + 10 if state == 'arrived' else now + 0.1
                self.w.jumping = state == 'jumping'
                self.w.hero_dead = state == 'dead'
                before = (self.w.hero.x0, self.w.hero.y0, self.w.hero.x1, self.w.hero.y1, self.w.hero.t0, self.w.hero.t1)
                with patch('time.time', return_value=event):
                    self.w.hero_effect('yavas', 5, 0.5, source=SLM)
                self.assertEqual((self.w.hero.x0, self.w.hero.y0, self.w.hero.x1, self.w.hero.y1, self.w.hero.t0, self.w.hero.t1), before)
                self.assertFalse([v for name, v in self.sent if name == 'MoveCommand'])
                self.w.jumping = self.w.hero_dead = False

    def test_zero_speed_clamp_pauses_in_place_and_restores_original_destination(self):
        now = time.time()
        self.start_flight(now)
        position = self.w.hero_pos(now + 2)
        with patch('time.time', return_value=now + 2):
            self.w.hero_effect('yavas', 5, 1, source=SLM)
        self.assertEqual(self.p.d['gemi']['speed'], 0)
        self.assertEqual(self.w.hero_pos(now + 4), position)
        moves = [v for name, v in self.sent if name == 'MoveCommand']
        self.assertEqual(moves[-1], dict(userId=self.w.hid, x=int(position[0]), y=int(position[1]), timeToTarget=0))
        self.sent.clear()
        with patch('time.time', return_value=now + 8):
            self.w.effects_tick(time.time())
        self.assert_retimed_move(now + 8, position, (11000, 1000))

    def test_emp_early_mine_slow_removal_retimes_moving_ship_immediately(self):
        now = time.time()
        self.start_flight(now)
        with patch('time.time', return_value=now + 1):
            self.w.hero_effect('yavas', 5, 0.5, source=SLM)
        position = self.w.hero_pos(now + 2)
        self.sent.clear()
        self.p.d['cephane'][SE.S['emp']['menu']] = 1
        with patch('time.time', return_value=now + 2):
            self.w.items.emp(time.time())
        self.assert_retimed_move(now + 2, position, (11000, 1000))

    def test_move_request_during_zero_speed_replaces_pending_target_without_teleporting(self):
        now = time.time()
        self.start_flight(now)
        position = self.w.hero_pos(now + 2)
        with patch('time.time', return_value=now + 2):
            self.w.hero_effect('yavas', 5, 1, source=SLM)
        with patch('time.time', return_value=now + 3):
            self.w.on_move(dict(targetX=9000, targetY=2000, positionX=9999, positionY=9999))
        self.assertEqual(self.w.hero_pos(now + 4), position)
        self.sent.clear()
        with patch('time.time', return_value=now + 8):
            self.w.effects_tick(time.time())
        self.assert_retimed_move(now + 8, position, (9000, 2000))


class MineReplay(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.worlds = []
        self.now = time.time()
        self.owner, self.owner_sent = self.world(31001)
        self.owner.running = True
        self.owner.ortak.katil(self.owner)
        self.owner.items.mines['M31001_1'] = dict(loot=DDM, x=7000, y=7000, sahip=31001,
                                                kurulma=self.now - 10, bitis=self.now + 100,
                                                maxSkill1=True, maxSkill5b=False)
        self.late, self.late_sent = self.world(31002)
        self.addCleanup(self.clean_worlds)

    def world(self, uid):
        p = Profil(path=str(Path(self.tmp.name) / ('%d.json' % uid)))
        p.d['pilot']['userId'] = uid
        sent = []
        world = World(p, sent.extend, lambda *args: None, '3', paylas=True)
        self.worlds.append(world)
        return world, sent

    def clean_worlds(self):
        for world in self.worlds:
            world.stop()

    def test_late_client_resend_receives_each_live_shared_mine_without_rebroadcast(self):
        self.late.running = True
        self.late.ortak.katil(self.late)
        self.owner_sent.clear()
        self.late.resend()
        mines = [fields for name, fields in self.late_sent if name == 'AddMineCommand']
        self.assertEqual(mines, [dict(hash='M31001_1', x=7000, y=7000, typeId=4,
                                     maxSkill1=True, maxSkill5b=False)])
        self.assertFalse([fields for name, fields in self.owner_sent if name == 'AddMineCommand'])

    def test_snapshot_excludes_expired_removed_foreign_map_and_foreign_alien_mines(self):
        sample = self.owner.items.mines['M31001_1']
        self.owner.items.mines['expired'] = dict(sample, bitis=self.now)
        self.owner.items.mines['removed'] = dict(sample)
        del self.owner.items.mines['removed']
        self.owner.items.mines['U900_1'] = dict(sample, sahip=900)
        self.late.items.mines['U901_1'] = dict(sample, sahip=901, maxSkill1=False)
        foreign, _ = self.world(31003)
        foreign.map_id = '4'
        foreign.running = True
        foreign.ortak.katil(foreign)
        foreign.items.mines['M31003_1'] = dict(sample, sahip=31003)
        mines = self.late.items.mine_snapshot(self.now)
        self.assertEqual({fields['hash'] for name, fields in mines}, {'M31001_1', 'U901_1'})
        self.assertEqual(len(mines), 2)

    def test_start_replays_shared_mine_to_joiner_once_without_threads(self):
        class NoLoopThread:
            def __init__(self, *args, **kwargs):
                pass
            def start(self):
                pass
        with patch('dunya.threading.Thread', NoLoopThread):
            self.late.start()
        mines = [fields for name, fields in self.late_sent if name == 'AddMineCommand']
        self.assertEqual([fields['hash'] for fields in mines], ['M31001_1'])
        self.assertFalse([fields for name, fields in self.owner_sent if name == 'AddMineCommand'])

    def test_replay_uses_placement_skill_visual_after_owner_resets_bio(self):
        self.owner.p.d['cephane'][SLM] = 1
        self.owner.p.d['konum'].update(x=9000, y=9000)
        self.owner.hero.go(9000, 9000, 0, self.now)
        self.owner.p.d['yetenekler'] = {'seviye': {'1': 5, '5b': 3}}
        self.owner.items.place_mine(SLM, self.now)
        placed = [fields for name, fields in self.owner_sent if name == 'AddMineCommand'][-1]
        self.owner.p.d['yetenekler'] = {'seviye': {}}
        replay = [fields for name, fields in self.late.items.mine_snapshot(self.now) if fields['hash'] == placed['hash']]
        self.assertEqual(replay, [placed])
        self.assertTrue(replay[0]['maxSkill1'])
        self.assertTrue(replay[0]['maxSkill5b'])

    def test_new_visible_ship_replays_infection_without_rebroadcast_or_lost_expiry(self):
        self.owner.hero_effect('enfeksiyon', 900, source=IM)
        expiry = self.owner.p._infection_effect['bitis']
        self.owner_sent.clear()
        with patch('time.time', return_value=expiry - 600):
            messages = self.owner.gorunum_msgs(time.time())
        plague = [v for name, v in messages if name == 'VisualModifierCommand' and v['modifier'] == 57]
        self.assertEqual(len(plague), 1)
        self.assertTrue(plague[0]['activated'])
        self.assertEqual(plague[0]['additionalAttribute'], '600')
        self.assertFalse(self.owner_sent)
        with patch('time.time', return_value=expiry + 1):
            self.assertFalse([v for name, v in self.owner.gorunum_msgs(time.time()) if name == 'VisualModifierCommand'])
            self.owner.effects_tick(time.time())
        stops = [v for name, v in self.owner_sent if name == 'VisualModifierCommand' and v['modifier'] == 57]
        self.assertEqual([v['activated'] for v in stops], [False])

    def test_mine_speed_change_broadcasts_same_remaining_move_to_visible_peer(self):
        with (ROOT / 'server/data/varsayilan/yanitlar.json').open() as stream:
            shop = Magaza(self.owner.p, json.load(stream), lambda *args: None)
        self.owner.stats_msgs = shop.apply_stats
        shop.apply_stats()
        self.late.running = True
        self.late.ortak.katil(self.late)
        self.late.oyuncular[self.owner.hid] = None
        now = time.time()
        self.owner.hero = Mover(1000, 1000)
        self.owner.hero.go(11000, 1000, self.owner.p.d['gemi']['speed'], now)
        self.owner_sent.clear()
        self.late_sent.clear()
        with patch('time.time', return_value=now + 2):
            self.owner.hero_effect('yavas', 5, 0.5, source=SLM)
        moves = [v for name, v in self.owner_sent if name == 'MoveCommand']
        self.assertEqual(len(moves), 1)
        self.assertEqual([v for name, v in self.late_sent if name == 'MoveCommand'], moves)


if __name__ == '__main__':
    unittest.main()
