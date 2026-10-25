"""CBS docking uses the HUD Hangar; no floating helper may obscure the map."""
import unittest
from unittest.mock import patch
import test_cbs_combat as base
cbs=base.cbs

class CbsHangarAction(unittest.TestCase):
    setUp=base.CbsCombat.setUp

    def test_attach_and_tick_do_not_create_a_floating_hangar(self):
        self.w.running=True
        msgs=self.c.attach(self.w)
        with patch.object(self.c,'tick_asteroid',return_value=[]),patch.object(self.c,'raid_tick',return_value=[]),patch.object(self.c,'rival_fire',return_value=[]):
            msgs+=self.c.tick(self.now)
        helpers=[f for n,f in msgs if n=='AssetCreateCommand' and f['type']['typeValue']==48]
        self.assertEqual(helpers,[])
        self.assertFalse(any(159500000<uid<159500024 for uid,kind in self.c.shown_assets))

    def test_own_cbs_exposes_docking_without_global_peace(self):
        self.assertTrue(self.c.can_dock(2));self.assertTrue(self.w.in_station(self.now))
        self.w.check_gates(self.now)
        beacon=next(f for n,f in self.sent if n=='BeaconCommand')
        self.assertTrue(beacon['inStation']);self.assertFalse(beacon['inPeaceArea'])
        self.assertIn(('EquipReadyCommand',{'ready':True}),self.sent)

    def test_allied_only_and_diplomacy_change_are_authoritative(self):
        self.a['klan']=22;self.p.d['klan']['diplomasi']=[dict(klan=22,tur=1)]
        self.assertTrue(self.w.in_station(self.now))
        for relation in [0,2,3]:
            self.p.d['klan']['diplomasi'][0]['tur']=relation
            self.assertFalse(self.w.in_station(self.now))

    def test_combat_death_jump_and_range_block_ship_changes(self):
        self.w.last_combat=self.now;self.assertFalse(self.w.in_station(self.now+.1))
        self.assertTrue(self.w.in_station(self.now+60));self.w.last_combat=0
        self.w.hero_dead=True;self.assertFalse(self.w.in_station(self.now))
        self.w.hero_dead=False;self.w.jumping=True;self.assertFalse(self.w.in_station(self.now))
        self.w.jumping=False;self.w.hero=cbs.dunya.Mover(self.x+601,self.y)
        self.assertFalse(self.w.in_station(self.now))

    def test_unbuilt_enemy_and_clanless_stations_do_not_dock(self):
        for state,owner in [('bos',None),('kurma',None),('kurulu','rakip')]:
            self.a.update(durum=state,sahip=owner)
            self.assertFalse(self.c.can_dock(2));self.assertFalse(self.w.in_station(self.now))
        self.a.update(durum='kurulu',sahip='oyuncu');self.p.d['klan']=None
        self.assertFalse(self.c.can_dock(2))

if __name__=='__main__':unittest.main()
