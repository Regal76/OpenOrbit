"""CBS map reload, docking and NPC geometry using temporary real pilot profiles."""
import copy
import math
import sys
import tempfile
import threading
import time
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'server'))
import cbs
import dunya
import game
from profil import Profil
from magaza import Magaza


class StationBehavior(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.p = Profil(path=str(Path(self.tmp.name) / 'pilot.json'))
        self.p.d['pilot'].update(clanId=11, factionId=1)
        self.p.d['klan'] = dict(id=11, ad='Owners', etiket='OWN', firma=1, diplomasi=[], uyeler={cbs.KL.ad(self.p):{}})
        self.p.d['konum'].update(mapId=4, x=4410, y=8908)
        self.sent = []
        self.w = dunya.World(self.p, self.sent.extend, lambda text: None, 4)
        self.c = cbs.Cbs(self.p, None, lambda text: None)
        self.a = self.c.ast(2)
        self.a.update(durum='kurulu', klan=11)
        self.c.attach(self.w)
        self.x, self.y = cbs.position(2)
        self.w.hero = dunya.Mover(self.x, self.y)
        self.now = time.time()

    def npc(self, x, y):
        tip = next(t for t, d in dunya.CFG['tipler'].items() if d.get('hiz', 0) > 0 and not d.get('dost'))
        n = dunya.NPC(91001, tip, x, y)
        n.d = dict(n.d, aggressiv=False, hasar=0)
        n.next_think = 0
        self.w.npcs[n.id] = n
        return n


    def test_all_cbs_layouts_clear_portals_static_assets_and_map_edges(self):
        moved = []
        for aid, row in cbs.AST.items():
            with self.subTest(asteroid=aid):
                mid = row['harita']
                w, h = cbs.H.map_size(mid)
                original = (int(w*row['x_yuzde']/100), int(h*row['y_yuzde']/100))
                obstacles = [(g['x'],g['y'],1700) for g in cbs.H.GATES.get(mid, [])]
                world = game.SABLON.map_world(mid)
                obstacles += [(m['posX'],m['posY'],1200) for m in world.get('giris',[]) if m['_m']=='AssetCreateCommand']
                obstacles += [(m['posX'],m['posY'],m['peaceRadius']+700) for m in world.get('hazir',[]) if m['_m']=='SpaceStationCommand']
                x,y = cbs.position(aid)
                self.assertTrue(700 <= x <= w-700 and 700 <= y <= h-700)
                for ox,oy,separation in obstacles:
                    self.assertGreaterEqual(math.hypot(x-ox,y-oy),separation)
                if (700 <= original[0] <= w-700 and 700 <= original[1] <= h-700
                        and all(math.hypot(original[0]-ox,original[1]-oy)>=sep for ox,oy,sep in obstacles)):
                    self.assertEqual((x,y),original)
                elif (x,y)!=original:
                    moved.append(aid)
        self.assertTrue(moved)

    def test_spawn_random_retry_fallback_remains_outside_station(self):
        # Force the old map-centre fallback to coincide with a test CBS.
        self.w.map_w, self.w.map_h = 2*self.x, 2*self.y
        with patch.object(dunya.random, 'uniform', side_effect=[self.x,self.y]*50):
            x,y = self.w.random_spot()
        self.assertGreater(math.hypot(x-self.x,y-self.y),1100)

    def test_ready_after_gate_repair_recreates_cbs_assets_and_near_ui(self):
        # The real session reload branch must restore assets cleared by refreshMap.
        self.c.near = 2
        self.w.reload_pending = True
        session = game.Session.__new__(game.Session)
        session.world, session.profil, session.cbs = self.w, self.p, self.c
        session.map_pending, session.ready_n, session.state_lock = False, 1, threading.RLock()
        session.secrets = set()
        session.send = lambda msgs, *args, **kwargs: self.sent.extend(msgs)
        empty = lambda: []
        session.magaza = SimpleNamespace(login_msgs=empty)
        session.pet = SimpleNamespace(login_msgs=empty, on_ready=lambda: None)
        session.basarim = SimpleNamespace(title_msgs=empty)
        session.yeni = SimpleNamespace(login_msgs=empty)
        session.ek = SimpleNamespace(login_msgs=empty, on_ready=lambda: None)
        with patch.object(game, 'login_batch', return_value=[]), patch.object(game.GM, 'list_cmd', return_value=('Unused', {})), patch.object(game, 'log'):
            session.on_packet('ReadyRequest', 0, {}, None)
        created = [f['assetId'] for name, f in self.sent if name == 'AssetCreateCommand']
        self.assertIn(157000200, created)
        self.assertIsNone(self.c.near)

    def test_reattach_repeats_all_satellites_without_old_remove_commands(self):
        for slot in range(2, 10):
            self.a['yuvalar'][str(slot)] = dict(iid=157500000 + slot)
            self.c.st['moduller'][str(157500000 + slot)] = dict(loot='module_laser_ltm-lr', seviye=0, can=1000, kalkan=1000)
        # Use a real module loot available in the loaded game data.
        loot = next(k for k, d in cbs.MODS.items() if d.get('silah'))
        for m in self.c.st['moduller'].values():
            m['loot'] = loot
        self.c.attach(self.w)
        msgs = self.c.attach(self.w)
        self.assertEqual(len([1 for name, f in msgs if name == 'AssetCreateCommand']), 9)
        self.assertFalse([1 for name, f in msgs if name == 'AssetRemoveCommand'])

    def test_native_module_footprints_have_clearance_from_hub_and_each_other(self):
        # Native bundle: satellites 210x210; hub including side pieces fits 276x297.
        # pixelsToUnits=1. Require a visible 30-unit gap between bounding boxes.
        positions = [(self.x, self.y, 276, 297)] + [(*cbs.satellite_pos(2, s), 210, 210) for s in range(2, 10)]
        for i, (x, y, w, h) in enumerate(positions):
            for tx, ty, tw, th in positions[i + 1:]:
                gap = max(abs(tx-x) - (w+tw)/2, abs(ty-y) - (h+th)/2)
                self.assertGreaterEqual(gap, 30)

    def test_own_completed_cbs_allows_equipment_and_station_beacon(self):
        self.assertTrue(self.w.in_station())
        self.w.check_gates(self.now)
        beacon = next(f for name, f in self.sent if name == 'BeaconCommand')
        self.assertTrue(beacon['inStation'])
        self.assertIn(('EquipReadyCommand', {'ready': True}), self.sent)

    def test_singleplayer_alliance_can_dock_but_nap_and_enemy_cannot(self):
        self.a['klan'] = 22
        for relation, expected in [(1, True), (2, False), (3, False), (0, False)]:
            with self.subTest(relation=relation):
                self.p.d['klan']['diplomasi'] = [dict(klan=22, tur=relation)]
                self.assertEqual(self.w.in_station(), expected)

    def test_multiplayer_alliance_uses_shared_clan_relation(self):
        self.a['klan'] = 22
        with patch.object(cbs, 'ortak', return_value=self.p), patch.dict(cbs.KL.KLANLAR, {11:self.p.d['klan'],22:dict(id=22,ad='Allies',etiket='ALL',firma=1)}, clear=True):
            # Mark shared migration complete before reading the real shared store.
            self.p.d['cbs']['ortak'] = True
            self.p.d['klan']['diplomasi'] = [dict(klan=22,tur=1)]
            self.assertTrue(self.w.in_station())
            self.p.d['klan']['diplomasi'][0]['tur'] = 3
            self.assertFalse(self.w.in_station())

    def test_empty_building_and_rival_station_do_not_allow_equipment(self):
        for state, owner in [('bos',None),('kurma',None),('kurulu','rakip')]:
            with self.subTest(state=state,owner=owner):
                self.a.update(durum=state,sahip=owner)
                self.assertFalse(self.w.in_station())

    def test_combat_updates_equipment_readiness_without_moving(self):
        self.w.check_gates(self.now)
        self.sent.clear()
        self.w.last_combat = self.now
        self.assertFalse(self.w.in_station())
        self.w.check_gates(self.now + 1)
        self.assertIn(('EquipReadyCommand', {'ready': False}), self.sent)
        self.sent.clear()
        self.w.check_gates(self.now + 60)
        self.assertIn(('EquipReadyCommand', {'ready': True}), self.sent)

    def test_random_spawn_avoids_cbs_before_attach_and_after_random_retries(self):
        self.w.asset_targets = None
        with patch.object(dunya.random, 'uniform', side_effect=[self.x, self.y, 15000, 9000]):
            x, y = self.w.random_spot()
        self.assertGreater(math.hypot(x-self.x, y-self.y), 1100)

    def test_ordinary_roaming_segment_cannot_cross_station(self):
        # Both endpoints are safe to roam; straight path between them cuts the CBS.
        n = self.npc(self.x-600, self.y+500)
        self.w.hero = dunya.Mover(500, 8000)
        with patch.object(dunya.random, 'uniform', side_effect=[1200, 0, 3]), patch.object(self.w, 'spot_away', return_value=(self.x+1800,self.y)):
            self.w.think(n, self.now)
        tx, ty = n.mover.x1, n.mover.y1
        sx, sy = self.x-600, self.y+500
        dx, dy = tx-sx, ty-sy
        fraction = max(0, min(1, ((self.x-sx)*dx+(self.y-sy)*dy)/(dx*dx+dy*dy))) if dx or dy else 0
        self.assertGreaterEqual(math.hypot(sx+fraction*dx-self.x, sy+fraction*dy-self.y), 600)

    def test_aggressive_npc_drops_unprovoked_attack_at_cbs(self):
        n = self.npc(self.x + 850, self.y)
        n.engaged = True
        self.w.think(n, self.now)
        self.assertFalse(n.engaged)

    def test_player_initiated_npc_can_follow_into_cbs(self):
        n = self.npc(self.x + 850, self.y)
        self.w.hit_npc(n.id, 1, 1)
        self.w.think(n, self.now + .01)
        self.assertTrue(n.engaged)
        self.assertLess(math.hypot(n.mover.x1-self.x,n.mover.y1-self.y), 600)

    def test_cbs_turret_hit_does_not_allow_npc_to_chase_player_into_station(self):
        n = self.npc(self.x + 850, self.y)
        self.w.hit_npc(n.id, 1, 1, attacker=157000202, engage=False)
        n.engaged = True
        self.w.think(n, self.now + .01)
        self.assertFalse(n.engaged)



    def test_actual_hangar_ship_change_at_own_and_allied_cbs(self):
        shop = Magaza(self.p,copy.deepcopy(game.SABLON.yanitlar),lambda text: None)
        sid = self.p.add_ship('ship_liberator')
        session = game.Session.__new__(game.Session)
        session.world,session.profil,session.magaza,session.secrets = self.w,self.p,shop,set()
        session.send = lambda msgs,*args,**kwargs: self.sent.extend(msgs)
        with patch.object(game,'log'):
            session.on_packet('HangarShipActivateShipRequest',0,dict(shipId=sid),None)
        self.assertEqual(self.p.d['aktif_gemi'],str(sid))
        self.assertTrue(self.w.reload_pending)
        self.a['klan'] = 22
        self.p.d['klan']['diplomasi'] = [dict(klan=22,tur=1)]
        with patch.object(game,'log'):
            session.on_packet('HangarShipActivateShipRequest',0,dict(shipId=1),None)
        self.assertEqual(self.p.d['aktif_gemi'],'1')
        self.w.last_combat = time.time()
        with patch.object(game,'log'):
            session.on_packet('HangarShipActivateShipRequest',0,dict(shipId=sid),None)
        self.assertEqual(self.p.d['aktif_gemi'],'1')
        replies = [f['result'] for name,f in self.sent if name=='HangarShipActivateShipCommand']
        self.assertEqual(replies,[1,1,0])

    def test_past_life_or_other_players_hit_does_not_allow_station_chase(self):
        for owner,when in [(self.w.hid,self.now-60),(self.w.hid+1,self.now+1)]:
            with self.subTest(owner=owner):
                n = self.npc(self.x+850,self.y)
                n.engaged,n.station_retaliation = True,{owner:when}
                self.w.death_time = self.now-.1
                self.w.think(n,self.now+.01)
                self.assertFalse(n.engaged)

    def test_unprovoked_pursuit_cannot_cut_across_cbs_to_player_beyond_it(self):
        n = self.npc(self.x-800, self.y+400)
        n.engaged, n.spread, n.keep = True, 0, 250
        self.w.hero = dunya.Mover(self.x+800,self.y+400)
        self.w.think(n,self.now)
        self.assertFalse(n.engaged)

    def test_rejected_escape_route_stops_previous_motion_into_station(self):
        n = self.npc(self.x-850,self.y)
        n.engaged = True
        n.mover.go(self.x,self.y,n.speed(),self.now)
        with patch.object(dunya.random,'uniform',side_effect=[1200,0]), patch.object(self.w,'spot_away',return_value=(self.x+1800,self.y)):
            self.w.think(n,self.now)
        self.assertLessEqual(n.mover.x1,self.x-850)

    def test_disengaging_clears_permission_to_follow_into_station(self):
        n = self.npc(self.x+850,self.y)
        self.w.hit_npc(n.id,1,1)
        self.w.disengage(n,self.now)
        n.engaged = True
        self.w.think(n,self.now+.01)
        self.assertFalse(n.engaged)

    def test_beacon_refresh_keeps_cbs_station_flag(self):
        self.assertTrue(self.w.beacon_msg(self.now)[1]['inStation'])

    def test_player_shooting_from_inside_cbs_can_be_attacked_back(self):
        n = self.npc(self.x+400,self.y)       # inside npc_menzil (450)
        n.d['hasar'] = 100
        self.w.hit_npc(n.id,1,1)
        self.w.think(n,self.now+.01)
        self.assertTrue(any(name=='AttackLaserRunCommand' and f['attackerId']==n.id for name,f in self.sent))



    def test_second_player_hit_preserves_shared_npc_retaliation_against_first(self):
        import ortak_harita
        p2 = Profil(path=str(Path(self.tmp.name)/'second.json'))
        p2.d['pilot']['userId'] = self.w.hid+1
        p2.d['konum'].update(mapId=4,x=self.x+100,y=self.y)
        second = dunya.World(p2,lambda msgs: None,lambda text: None,4)
        shared = ortak_harita.Harita('4')
        self.w.ortak,second.ortak = shared,shared
        self.w.lock,second.lock = shared.lock,shared.lock
        self.w.npcs,second.npcs = shared.npcs,shared.npcs
        shared.uyeler = [self.w,second]
        n = self.npc(self.x+550,self.y)
        self.w.hit_npc(n.id,1,1)
        self.assertIs(n.foe,self.w)
        second.hit_npc(n.id,1,1)
        self.assertIs(n.foe,self.w)
        self.w.think(n,time.time())
        self.assertTrue(n.engaged)
        self.assertIs(n.foe,self.w)

    def launcher_npc(self):
        # Actual configured Annihilator: native three-projectile launcher salvo.
        n = dunya.NPC(91002,'114',self.x+400,self.y)       # inside npc_menzil (450)
        self.w.npcs[n.id] = n
        return n

    def test_npc_launcher_can_retaliate_after_player_fires_inside_cbs(self):
        n = self.launcher_npc()
        self.w.hit_npc(n.id,1,1)
        self.w.alien.rocket(n,self.now+.01)
        salvos = [f for name,f in self.sent if name=='HellstormAttackCommand']
        self.assertEqual(len(salvos),1)
        self.assertEqual((salvos[0]['attackerId'],salvos[0]['targetId'],salvos[0]['currentLoad']), (91002,self.w.hid,3))
        self.assertEqual(salvos[0]['rocketType']['typeValue'],23)  # ECO-10 ammunition enum
        self.assertEqual(len(self.w.timers),1)

    def test_unprovoked_npc_launcher_cannot_fire_into_cbs(self):
        n = self.launcher_npc()
        n.engaged = True
        self.w.alien.rocket(n,self.now+.01)
        self.assertFalse(any(name=='HellstormAttackCommand' for name,f in self.sent))
        self.assertFalse(self.w.timers)

    def test_npc_launcher_retaliates_after_player_fires_from_portal_zone(self):
        # Reversed on purpose (player report 2026-10-26, user-approved rule): in every protected zone (station, portal, layout safe
        # zone) the alien the pilot attacked keeps fighting him; the old version of this test expected portal peace to hold.
        gate = self.w.gates[0]
        self.w.hero = dunya.Mover(gate['x'],gate['y'])
        n = self.launcher_npc()
        n.mover = dunya.Mover(gate['x']+400,gate['y'])       # inside npc_menzil (450)
        self.w.hit_npc(n.id,1,1)
        self.w.alien.rocket(n,self.now+.01)
        salvos = [f for name,f in self.sent if name=='HellstormAttackCommand']
        self.assertEqual(len(salvos),1)
        self.assertEqual((salvos[0]['attackerId'],salvos[0]['targetId']), (91002,self.w.hid))
        self.assertEqual(len(self.w.timers),1)

    def test_unprovoked_npc_launcher_cannot_fire_into_portal_zone(self):
        gate = self.w.gates[0]
        self.w.hero = dunya.Mover(gate['x'],gate['y'])
        n = self.launcher_npc()
        n.mover = dunya.Mover(gate['x']+400,gate['y'])
        n.engaged = True
        self.w.alien.rocket(n,self.now+.01)
        self.assertFalse(any(name=='HellstormAttackCommand' for name,f in self.sent))
        self.assertFalse(self.w.timers)

    def test_npc_abilities_preserve_death_jump_spawn_and_both_cloaks(self):
        n = self.launcher_npc()
        self.w.hero = dunya.Mover(self.x+2000,self.y)
        n.mover = dunya.Mover(self.x+2500,self.y)
        self.w.hit_npc(n.id,1,1)
        changes = [(self.w,'hero_dead',True),(self.w,'jumping',True),(self.w,'invuln_until',self.now+60)]
        for obj,key,value in changes:
            with self.subTest(protection=key):
                before = getattr(obj,key)
                setattr(obj,key,value)
                self.w.alien.rocket(n,self.now+.01)
                self.assertFalse(self.w.timers)
                setattr(obj,key,before)
        for data,key in [(self.p.d,'cpu_gizli'),(self.w.abilities.flags,'gizlen')]:
            with self.subTest(protection=key):
                data[key] = True
                self.w.alien.rocket(n,self.now+.01)
                self.assertFalse(self.w.timers)
                data[key] = False

    def test_player_shooting_from_portal_zone_can_be_attacked_back(self):
        # Reversed on purpose (player report 2026-10-26, user-approved rule): the portal zone no longer overrides the pilot's own attack.
        gate = self.w.gates[0]
        self.w.hero = dunya.Mover(gate['x'], gate['y'])
        n = self.npc(gate['x'] + 400, gate['y'])
        n.d['hasar'] = 100
        self.w.hit_npc(n.id, 1, 1)
        self.w.think(n, self.now + .01)
        self.assertTrue(n.engaged)
        self.assertTrue(any(name == 'AttackLaserRunCommand' and f['attackerId'] == n.id for name, f in self.sent))

    def test_unprovoked_npc_drops_attack_at_portal_zone_and_other_npcs_stay_out(self):
        gate = self.w.gates[0]
        self.w.hero = dunya.Mover(gate['x'], gate['y'])
        shot, other = self.npc(gate['x'] + 400, gate['y']), self.npc(gate['x'] - 400, gate['y'])
        other.id = 91003
        self.w.npcs = {shot.id: shot, other.id: other}
        for n in (shot, other):
            n.d['hasar'] = 100
            n.engaged = True
        self.w.hit_npc(shot.id, 1, 1)
        self.sent.clear()
        self.w.think(shot, self.now + .01)
        self.w.think(other, self.now + .01)
        self.assertTrue(shot.engaged)
        self.assertFalse(other.engaged)
        self.assertEqual({f['attackerId'] for name, f in self.sent if name == 'AttackLaserRunCommand'}, {shot.id})


if __name__ == '__main__':
    unittest.main()
