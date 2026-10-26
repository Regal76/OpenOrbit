"""Installed CBS modules must alter real combat, reward and repair results.

Rules: official Clan Battle Station FAQ, https://board-en.darkorbit.com/threads/clan-battle-station-faq.819/
"""
import sys
import tempfile
import time
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'server'))
import cbs
import dunya
import kapi
import game
import gorev
import booster
import etkinlik_kapi
from profil import Profil


class CbsBonuses(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.p = Profil(path=str(Path(self.tmp.name) / 'pilot.json'))
        self.p.d['pilot'].update(clanId=11, factionId=1)
        self.p.d['klan'] = dict(id=11, ad='Owners', etiket='OWN', firma=1, diplomasi=[], uyeler={cbs.KL.ad(self.p): {}})
        self.c = cbs.Cbs(self.p, None, lambda *_: None)
        self.p.cbs_mods = self.c.mods  # game.Session installs this same callback
        self.w = dunya.World(self.p, lambda _: None, lambda _: None, 4)
        self.now = time.time()
        self.aids = list(cbs.AST)[:7]
        self.iid = cbs.ITEM_BASE

    def install(self, aid, loot, level=15, age=72000, pending=False):
        a = self.c.ast(aid)
        a.update(durum='kurulu', klan=11, kurulus=self.now - age)
        self.iid += 1
        row = dict(loot=loot, seviye=level, can=100000, kalkan=0)
        self.c.st['moduller'][str(self.iid)] = row
        a['yuvalar'][str(len(a['yuvalar']) + 2)] = dict(iid=self.iid, kurulum_bitis=self.now + 50 if pending else self.now - age)
        return row

    def test_xp_and_honor_stack_across_stations_in_actual_npc_reward(self):
        for aid in self.aids[:2]:
            self.install(aid, 'module_xpm-1')
            self.install(aid, 'module_honm-1')
        npc = SimpleNamespace(d={'odul':dict(ep=10000, onur=1000, kredi=0, uridyum=0)})
        with patch.object(dunya.AY, 'carpan', return_value=1), patch.object(self.w, 'x1_reward', return_value=1):
            reward = self.w.kill_reward(npc)
        self.assertEqual((reward['ep'], reward['onur']), (12000, 1200))

    def test_station_xp_and_honor_cap_is_independent_of_other_bonuses(self):
        for aid in self.aids:
            self.install(aid, 'module_xpm-1')
            self.install(aid, 'module_honm-1')
        with patch.object(self.p, 'formation', return_value={'ep': .2, 'onur': .1}):
            mods = self.p.mods()
        self.assertAlmostEqual(mods['ep'], .7)
        self.assertAlmostEqual(mods['onur'], .6)

    def test_booster_ramps_from_one_percent_over_twenty_hours_for_both_end_levels(self):
        aid = self.aids[0]
        row = self.install(aid, 'module_dmgm-1', level=0, age=0)
        for level, middle, top in [(0, 2, 3), (15, 5.5, 10)]:
            row['seviye'] = level
            self.assertEqual(self.c.booster_pct(aid, 'hasar', self.now), 1)
            self.assertEqual(self.c.booster_pct(aid, 'hasar', self.now + 36000), middle)
            self.assertEqual(self.c.booster_pct(aid, 'hasar', self.now + 72000), top)

    def test_damage_bonus_affects_real_laser_damage_only_on_station_map(self):
        aid = self.aids[0]
        self.install(aid, 'module_dmgm-1')
        self.p.d['konum']['mapId'] = cbs.AST[aid]['harita']
        with patch.object(dunya.random, 'uniform', return_value=1):
            boosted = self.w.laser_damage('ammunition_laser_lcb-10')[0]
            self.p.d['konum']['mapId'] = 9999
            base = self.w.laser_damage('ammunition_laser_lcb-10')[0]
        self.assertGreater(base, 0)
        self.assertAlmostEqual(boosted, base * 1.1, delta=2)
        self.assertNotIn('roket', self.c.mods())

    def test_damage_bonus_affects_ordinary_rocket_and_launcher_damage(self):
        aid = 2  # station on this world's map (1-4)
        self.install(aid, 'module_dmgm-1')
        self.p.d['konum']['mapId'] = 4
        tip = next(t for t, d in dunya.CFG['tipler'].items() if d.get('hiz', 0) > 0 and not d.get('dost'))
        npc = dunya.NPC(91001, tip, 5000, 5000)
        npc.hp, npc.shield = 1000000, 0
        self.w.npcs[npc.id] = npc
        self.w.hero = dunya.Mover(5000, 5000)
        self.w.target = npc.id
        ammo = 'ammunition_rocket_r-310'
        self.p.d['secili']['roket'] = ammo
        self.p.d['cephane'][ammo] = 10
        self.p.d['ekipman']['rocket'] = ['equipment_weapon_rocketlauncher_hst-2']
        with patch.object(dunya.random, 'random', return_value=0), patch.object(dunya.random, 'uniform', return_value=1):
            self.w.rocket({'targetId': npc.id})
            timers, self.w.timers = self.w.timers, []
            for _, callback in timers:
                callback()
            self.assertEqual(npc.hp, 998900)  # R-310: 1000 + 10%
            self.p.d['fircatici_dolu'] = ['ammunition_rocketlauncher_hstrm-01', 5]
            self.w.items.launcher_fire(self.now)
            timers, self.w.timers = self.w.timers, []
            for _, callback in timers:
                callback()
            self.assertEqual(npc.hp, 976900)  # five HSTRM-01: 20,000 + 10%

    def test_other_clan_station_does_not_grant_boosters(self):
        aid = self.aids[0]
        self.install(aid, 'module_xpm-1')
        self.c.ast(aid)['klan'] = 22
        self.assertEqual(self.c.mods(), {})

    def test_destroyed_pending_removed_and_building_boosters_grant_no_bonus(self):
        aid = self.aids[0]
        row = self.install(aid, 'module_xpm-1', pending=True)
        self.assertNotIn('ep', self.c.mods())
        slot = next(iter(self.c.ast(aid)['yuvalar'].values()))
        slot['kurulum_bitis'] = 0
        row['can'] = 0
        self.assertNotIn('ep', self.c.mods())
        row['can'] = 100
        self.c.ast(aid)['durum'] = 'kurma'
        self.assertNotIn('ep', self.c.mods())
        self.c.ast(aid).update(durum='kurulu', yuvalar={})
        self.assertNotIn('ep', self.c.mods())

    def test_player_without_clan_does_not_retain_station_boosters(self):
        self.install(self.aids[0], 'module_xpm-1')
        self.p.d['pilot']['clanId'] = 0
        self.p.d['klan'] = None
        self.assertEqual(self.c.mods(), {})

    def test_pending_repair_module_does_not_heal_until_installation_finishes(self):
        aid = self.aids[0]
        self.install(aid, 'module_repm-1', level=0, pending=True)
        hull = self.install(aid, 'module_hulm-1', level=0)
        a = self.c.ast(aid)
        a['son_hasar'] = self.now
        self.c.repair_tick(aid, a, self.now)
        self.assertEqual(hull['can'], 100000)
        self.c.repair_tick(aid, a, self.now + 50)
        self.assertEqual(hull['can'], 102600)

    def test_repair_module_heals_all_live_modules_even_during_combat(self):
        aid = self.aids[0]
        rep = self.install(aid, 'module_repm-1', level=0)
        hull = self.install(aid, 'module_hulm-1', level=0)
        dead = self.install(aid, 'module_dmgm-1')
        dead['can'] = 0
        self.c.ast(aid)['son_hasar'] = self.now
        self.c.repair_tick(aid, self.c.ast(aid), self.now)
        self.assertEqual((rep['can'], hull['can'], dead['can']), (102600, 102600, 0))

    def test_gate_completion_grants_global_cbs_xp_and_honor_once(self):
        self.install(self.aids[0], 'module_xpm-1')
        self.install(self.aids[0], 'module_honm-1')
        gates = kapi.Kapilar(self.p, lambda _: None)
        received = []
        before_ep, before_hon = self.p.d['pilot']['ep'], self.p.d['pilot']['honourPoints']
        with patch('takvim.is_active', return_value=False), patch.object(kapi.AY, 'carpan', return_value=1):
            gates.finish('alpha', reward_msgs=lambda tot, **kw: received.append(kw) or [])
        base = kapi.KAPI['alpha']['odul']
        expected_ep, expected_hon = int(base['ep'] * 1.1), int(base['onur'] * 1.1)
        self.assertEqual(self.p.d['pilot']['ep'] - before_ep, expected_ep)
        self.assertEqual(self.p.d['pilot']['honourPoints'] - before_hon, expected_hon)
        self.assertEqual((received[0]['ep'], received[0]['onur']), (expected_ep, expected_hon))

    def test_dispatch_gate_completion_excludes_station_boosters(self):
        self.install(self.aids[0], 'module_xpm-1')
        self.install(self.aids[0], 'module_honm-1')
        before = self.p.d['pilot']['ep'], self.p.d['pilot']['honourPoints']
        with patch.object(kapi.AY, 'carpan', return_value=1):
            kapi.Kapilar(self.p, lambda _: None).finish('alpha', dispatch=True)
        base = kapi.KAPI['alpha']['odul']
        self.assertEqual((self.p.d['pilot']['ep'] - before[0], self.p.d['pilot']['honourPoints'] - before[1]), (base['ep'], base['onur']))


    def test_quest_completion_combines_qr_and_cbs_once_and_preserves_currencies(self):
        self.install(self.aids[0], 'module_xpm-1')
        self.install(self.aids[0], 'module_honm-1')
        booster.add(self.p, 'booster_qr-01', hours=1)
        session = game.Session.__new__(game.Session)
        session.profil, session.world = self.p, self.w
        session.magaza = SimpleNamespace(prize=lambda loot, n, src: [])  # item rewards (Log Disk ...) are outside this check
        quests = gorev.Gorevler(self.p, lambda _: None)
        quests.grant = session.quest_reward
        before = dict(self.p.d['pilot'])
        # Presentation list needs unrelated quest templates; reward route stays real.
        with patch.object(quests, 'list_cmd', return_value=('QuestList', {})), patch.object(game.AY, 'carpan', return_value=1):
            messages = quests.complete(110005)
        pilot = self.p.d['pilot']
        self.assertEqual(pilot['ep'] - before['ep'], 293260)  # 133300 * QR(2) * CBS(1.1)
        self.assertEqual(pilot['honourPoints'] - before['honourPoints'], 2200)
        self.assertEqual(pilot['credits'] - before['credits'], 200000)  # QR applies, CBS does not
        self.assertEqual(pilot['uridium'] - before['uridium'], 50)  # neither applies
        ep_messages = [f for n, f in messages if n == 'LegacyModule' and '|ST|EP|' in str(f)]
        self.assertEqual(len(ep_messages), 1)
        self.assertIn('293260', str(ep_messages[0]))

    def test_event_gate_completion_credits_and_reports_global_cbs_bonuses_once(self):
        self.install(self.aids[0], 'module_xpm-1')
        self.install(self.aids[0], 'module_honm-1')
        before = dict(self.p.d['pilot'])
        reported = []
        # Standard EP/HON boosters already have a separate policy; preserve it.
        booster.add(self.p, 'booster_ep-b01', hours=1)
        with patch.object(etkinlik_kapi.AY, 'carpan', return_value=1):
            etkinlik_kapi.EtkinlikKapilari(self.p, lambda _: None).finish(
                'dogum_gunu', reward_msgs=lambda tot, **kw: reported.append(kw) or [])
        pilot = self.p.d['pilot']
        self.assertEqual(pilot['ep'] - before['ep'], 243466)  # floor(221333 * 1.1)
        self.assertEqual(pilot['honourPoints'] - before['honourPoints'], 22138)
        self.assertEqual(pilot['uridium'] - before['uridium'], 2012)
        self.assertEqual(pilot['credits'], before['credits'])
        self.assertEqual(reported, [dict(ep=243466, onur=22138, uridyum=2012)])

    def test_quest_and_event_reward_bases_remain_unchanged_without_cbs(self):
        session = game.Session.__new__(game.Session)
        session.profil, session.world = self.p, self.w
        before = dict(self.p.d['pilot'])
        with patch.object(game.AY, 'carpan', return_value=1):
            session.quest_reward('currency_experience', 133300)
            session.quest_reward('currency_honour', 1000)
            etkinlik_kapi.EtkinlikKapilari(self.p, lambda _: None).finish('dogum_gunu')
        self.assertEqual(self.p.d['pilot']['ep'] - before['ep'], 354633)
        self.assertEqual(self.p.d['pilot']['honourPoints'] - before['honourPoints'], 21126)
