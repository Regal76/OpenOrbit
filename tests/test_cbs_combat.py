"""CBS target inspection and combat safety must be independent of docking."""
import sys, tempfile, time, unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'server'))
import cbs, dunya
from profil import Profil

class CbsCombat(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.p=Profil(path=str(Path(self.tmp.name)/'pilot.json'))
        self.p.d['pilot'].update(clanId=11,factionId=1)
        self.p.d['klan']=dict(id=11,ad='Owners',etiket='OWN',firma=1,diplomasi=[],uyeler={cbs.KL.ad(self.p):{}})
        self.sent=[]
        self.w=dunya.World(self.p,self.sent.extend,lambda t:None,4)
        self.c=cbs.Cbs(self.p,None,lambda t:None)
        self.a=self.c.ast(2);self.a.update(durum='kurulu',klan=11)
        self.c.attach(self.w)
        self.x,self.y=cbs.position(2);self.w.hero=dunya.Mover(self.x,self.y)
        self.now=time.time()
        for slot,loot in [(0,next(k for k,d in cbs.MODS.items() if d.get('kod')=='HULM-1')),(2,next(k for k,d in cbs.MODS.items() if d.get('silah')))]:
            iid=157500000+slot
            row=dict(loot=loot,seviye=0,can=10000,kalkan=5000)
            self.c.st['moduller'][str(iid)]=row
            self.a['yuvalar'][str(slot)]=dict(iid=iid,kurulum_bitis=0)

    def test_docking_does_not_grant_pvp_immunity_or_native_dmz_flag(self):
        self.assertTrue(self.w.in_station())
        self.assertTrue(self.w.in_peace(self.x,self.y)) # unprovoked NPC protection remains
        self.assertFalse(self.w.in_pvp_peace(self.x,self.y))
        self.w.check_gates(self.now)
        beacon=next(f for name,f in self.sent if name=='BeaconCommand')
        self.assertTrue(beacon['inStation'])
        self.assertFalse(beacon['inPeaceArea'])
        self.assertFalse(self.w.beacon_msg(self.now)[1]['inPeaceArea'])

    def test_home_station_and_portal_remain_pvp_safe(self):
        self.w.station=dict(posX=5000,posY=5000,peaceRadius=500,type=1)
        self.assertTrue(self.w.in_pvp_peace(5000,5000))
        gate=self.w.gates[0]
        self.assertTrue(self.w.in_pvp_peace(gate['x'],gate['y']))

    def test_own_hub_and_module_can_be_selected_without_ship_selection_packet(self):
        for slot in [0,2]:
            with self.subTest(slot=slot):
                uid=cbs.asset_id(2,slot)
                self.w.select({'targetId':uid})
                self.assertEqual(self.w.target,uid)
                info=self.sent[-1]
                self.assertEqual(info[0],'AssetInfoCommand')
                self.assertEqual((info[1]['assetId'],info[1]['hitpoints'],info[1]['shieldEnergy']),(uid,10000,5000))
                self.assertFalse(any(n=='ShipSelectionCommand' for n,f in self.sent))

    def test_friendly_assets_selectable_but_not_damageable(self):
        uid=cbs.asset_id(2,2)
        self.assertIsNotNone(self.c.asset_pos(uid))
        self.assertTrue(self.c.asset_attackable(uid))
        self.assertTrue(self.c.asset_hit(uid,1000))
        self.assertEqual(self.c.module(157500002)['can'],10000)

    def test_stale_invalid_cross_map_and_dead_asset_ids_are_rejected(self):
        uid=cbs.asset_id(2,2)
        self.c.module(157500002)['can']=0
        for bad in [uid,uid+1,-1,None,'oops',cbs.asset_id(3,0),cbs.ASSET_BASE+201]:
            with self.subTest(uid=bad):
                self.assertIsNone(self.c.asset_pos(bad))
                self.assertEqual(self.c.asset_select(bad),[])

    def test_passive_repairs_do_not_steal_native_selection_from_another_module(self):
        self.w.target=cbs.asset_id(2,2)
        updates=[self.c.info_cmd(2,0),self.c.info_cmd(2,2)]
        with patch.object(self.c,'tick_asteroid',return_value=updates),patch.object(self.c,'raid_tick',return_value=[]),patch.object(self.c,'rival_fire',return_value=[]):
            out=self.c.tick(self.now)
        self.assertEqual([f['assetId'] for n,f in out if n=='AssetInfoCommand'],[self.w.target])
        self.assertIn(cbs.asset_id(2),[f['assetId'] for n,f in out if n=='AttackHitAssetCommand'])

    def test_zero_shield_energy_still_updates_native_shield_bar(self):
        self.c.module(157500002)['kalkan']=0
        info=self.c.asset_select(cbs.asset_id(2,2))[0][1]
        self.assertTrue(info['shielded'])
        self.assertEqual(info['shieldEnergy'],0)

    def test_shielded_rival_is_selectable_but_cannot_be_damaged(self):
        self.a['sahip']='rakip'
        self.a['yuvalar']['2']=dict(self.c.module(157500002))
        self.a['deflector']['acik']=True
        uid=cbs.asset_id(2,2)
        self.assertIsNotNone(self.c.asset_pos(uid))
        self.assertTrue(self.c.asset_select(uid))
        self.assertTrue(self.c.asset_attackable(uid))
        self.c.asset_hit(uid,1000)
        self.assertEqual(self.a['yuvalar']['2']['can'],10000)

if __name__=='__main__':unittest.main()

class PlayerDamage(unittest.TestCase):
    setUp = CbsCombat.setUp
    def test_player_hit_ignores_npc_damage_cheat_and_anti_ai_floor(self):
        from types import SimpleNamespace
        attacker=SimpleNamespace(hid=self.w.hid+1,p=self.p)
        g=self.p.d['gemi'];g.update(hitPoints=10000,hitMax=10000,shield=5000,shieldMax=5000,nanoHull=0)
        self.p.d['kalkan_emme']=.8
        with patch.object(dunya.AY,'carpan',return_value=0),patch.object(self.w.tech,'hp_floor',return_value=20000):
            msgs=self.w.hurt_hero(1000,now=self.now,source_player=attacker)
        self.assertEqual((g['hitPoints'],g['shield']),(9800,4200))
        hit=next(f for n,f in msgs if n=='AttackHitCommand')
        self.assertEqual(hit['attackerId'],attacker.hid)

    def test_player_shield_only_hit_preserves_hull_and_nano(self):
        from types import SimpleNamespace
        attacker=SimpleNamespace(hid=self.w.hid+1,p=self.p)
        g=self.p.d['gemi'];g.update(hitPoints=10000,shield=700,shieldMax=5000,nanoHull=100)
        msgs=self.w.hurt_hero(1000,now=self.now,source_player=attacker,shield_only=True)
        self.assertEqual((g['hitPoints'],g['shield'],g['nanoHull']),(10000,0,100))
        self.assertEqual(next(f['damage'] for n,f in msgs if n=='AttackHitCommand'),700)

    def test_player_kill_screen_has_player_cause_and_killer_name(self):
        from types import SimpleNamespace
        attacker=SimpleNamespace(hid=self.w.hid+1,p=SimpleNamespace(d={'pilot':{'userName':'EnemyPilot'}},mods=lambda: {}))
        self.p.d['gemi'].update(hitPoints=1,shield=0,nanoHull=0)
        msgs=self.w.hurt_hero(1000,now=self.now,source_player=attacker)
        screen=next(f for n,f in msgs if n=='KillScreenPostCommand')
        self.assertEqual(screen['cause']['cause'],0)
        self.assertEqual(screen['killerName'],'EnemyPilot')
