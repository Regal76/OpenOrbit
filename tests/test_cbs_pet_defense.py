"""Each CBS turret may shoot a hostile live PET without duplicating fire."""
import unittest
from unittest.mock import patch
import test_cbs_module_stats as base
import pet
cbs,dunya=base.cbs,base.dunya

class CbsPetDefense(unittest.TestCase):
    setUp=base.StationWeaponFire.setUp
    equip=base.StationWeaponFire.equip

    def add_pet(self,x,y):
        self.p.d['pet']=pet.new_pet(self.p)
        self.pet=pet.Pet(self.p,lambda *_:None)
        self.pet.attach(self.w);self.w.pet=self.pet
        self.pet.active=True;self.pet.mover=dunya.Mover(x,y)
        self.pet.d.update(can=1000000,kalkan=100000,yakit=1000,yikik=False)

    def test_station_hits_pet_when_owner_is_out_of_range(self):
        x,y=self.equip('module_ltm-lr');self.w.hero=dunya.Mover(x+1500,y)
        self.add_pet(x+100,y)
        hp=self.p.d['gemi']['hitPoints'];total=self.pet.d['can']+self.pet.d['kalkan']
        with patch.object(cbs.random,'random',return_value=0):self.c.rival_fire(self.now)
        self.assertEqual(self.pet.d['can']+self.pet.d['kalkan'],total-59850)
        self.assertEqual(self.p.d['gemi']['hitPoints'],hp)
        hit=next(f for n,f in self.sent if n=='AttackHitCommand')
        self.assertEqual((hit['attackerId'],hit['victimId']),(cbs.asset_id(2,2),self.pet.pid))
        self.assertEqual(self.w.last_asset_attacker,(cbs.asset_id(2,2),self.now))

    def test_nearest_target_only_and_cooldown_shared_between_ship_and_pet(self):
        x,y=self.equip('module_ram-ma');self.w.hero=dunya.Mover(x+400,y)
        self.add_pet(x+50,y)
        with patch.object(cbs.random,'random',return_value=0):
            self.c.rival_fire(self.now);self.c.rival_fire(self.now+.01)
        hits=[f for n,f in self.sent if n=='AttackHitCommand']
        self.assertEqual(len(hits),1)
        self.assertEqual(hits[0]['victimId'],self.pet.pid)
        self.assertEqual(hits[0]['attackType']['attackTypeValue'],0)

    def test_inactive_dead_out_of_range_and_shielded_pet_targets_are_ignored(self):
        x,y=self.equip('module_ltm-lr');self.w.hero=dunya.Mover(x+1500,y)
        self.add_pet(x+100,y)
        for mode in ('inactive','dead','range','shield','friendly'):
            with self.subTest(mode=mode):
                self.pet.active=mode!='inactive';self.pet.d.update(yikik=mode=='dead',can=1000000)
                self.pet.mover=dunya.Mover(x+1500 if mode=='range' else x+100,y)
                self.a['deflector']['acik']=mode=='shield'
                self.a['sahip']='oyuncu' if mode=='friendly' else 'rakip'
                self.c.next_shot.clear();self.sent.clear()
                with patch.object(cbs.random,'random',return_value=0):self.c.rival_fire(self.now)
                self.assertEqual(self.sent,[])

    def test_pet_evasion_is_used_without_inheriting_hero_spectrum(self):
        x,y=self.equip('module_ltm-lr');self.w.hero=dunya.Mover(x+1500,y)
        self.add_pet(x+100,y)
        with patch.object(self.pet,'proto',return_value=.5),patch.object(self.p,'mods',return_value={'alinan_lazer':-.8}),patch.object(cbs.random,'random',return_value=.6):
            self.c.rival_fire(self.now)
        miss=next(f for n,f in self.sent if n=='AttackMissedCommand')
        self.assertEqual(miss['targetUserId'],self.pet.pid)
        self.assertFalse(any(n=='AttackHitCommand' for n,f in self.sent))

if __name__=='__main__':unittest.main()
