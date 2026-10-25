"""Zone visual cleanup must not depend on a still-living primary target."""
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'server'))
from profil import Profil
from dunya import World

class DriveVisualLifecycle(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
  self.p=Profil(path=str(Path(self.tmp.name)/'profile.json'))
  self.sent=[]
  self.w=World(self.p,lambda msgs:self.sent.extend(msgs),lambda *a:None,'1')
  self.a=self.w.parcacik
 def zone(self,target=42,end=8,vm=152):
  z=dict(x=5000,y=5000,bitis=end,sonraki=0,hasar=100,hedef=target,vm=vm,alan=600)
  self.a.zones.append(z);return z
 def inactive(self):
  return [f for name,f in self.sent if name=='VisualModifierCommand' and not f['activated']]
 def test_expired_zone_cleans_up_even_when_target_already_removed(self):
  self.zone();self.a.tick(8)
  self.assertEqual([(f['userId'],f['modifier']) for f in self.inactive()],[(42,152)])
  self.assertEqual(self.a.zones,[])
  self.a.tick(9);self.assertEqual(len(self.inactive()),1)
 def test_removed_primary_does_not_end_area_damage_early(self):
  z=self.zone();self.a.tick(3)
  self.assertEqual(self.a.zones,[z]);self.assertEqual(self.inactive(),[])
  self.assertEqual(z['sonraki'],4)
 def test_world_stop_cleans_all_active_zones_and_is_idempotent(self):
  self.zone();self.zone(target=43,vm=156)
  self.w.stop();self.w.stop()
  self.assertEqual(self.a.zones,[])
  self.assertEqual(sorted((f['userId'],f['modifier']) for f in self.inactive()),[(42,152),(43,156)])
 def test_hero_death_cancels_visuals_and_future_area_damage(self):
  self.zone();msgs=[]
  self.w.hero_death(msgs)
  self.assertEqual(self.a.zones,[])
  self.assertEqual([(f['userId'],f['modifier']) for f in self.inactive()],[(42,152)])
  self.a.tick(4);self.assertEqual(len(self.inactive()),1)
 def test_damage_callback_death_stops_remaining_active_zone_hits(self):
  self.zone();self.zone(target=43)
  hits=[]
  def hit(uid,*args):
   hits.append(uid)
   if not self.w.hero_dead:self.w.hero_death([])
  with patch.object(self.a,'others',return_value=[SimpleNamespace(id=1),SimpleNamespace(id=2)]), \
       patch.object(self.w,'hit_npc',side_effect=hit),patch('parcacik.random.random',return_value=0):
   self.a.tick(3)
  self.assertEqual(hits,[1],'A hit callback killed the hero; all remaining zone damage must stop')
  self.assertEqual(self.a.zones,[])
  self.assertEqual(sorted(f['userId'] for f in self.inactive()),[42,43])
 def test_two_expired_aftershocks_survive_damage_callback_death(self):
  self.zone().update(artci=25,artci_alan=600)
  self.zone(target=43).update(artci=25,artci_alan=600)
  hits=[]
  def hit(uid,*args):
   hits.append(uid)
   if not self.w.hero_dead:self.w.hero_death([])
  with patch.object(self.a,'others',return_value=[SimpleNamespace(id=1),SimpleNamespace(id=2)]), \
       patch.object(self.w,'hit_npc',side_effect=hit):
   try:self.a.tick(8)
   except ValueError as error:self.fail('Zone snapshot was not invalidated after hero death: '+str(error))
  self.assertEqual(hits,[1])
  self.assertEqual(self.a.zones,[])
  self.assertEqual(sorted(f['userId'] for f in self.inactive()),[42,43])
 def test_aftershock_damage_callback_world_stop_cancels_remaining_hits(self):
  self.zone().update(artci=25,artci_alan=600)
  self.zone(target=43).update(artci=25,artci_alan=600)
  hits=[]
  def hit(uid,*args):
   hits.append(uid);self.w.stop()
  with patch.object(self.a,'others',return_value=[SimpleNamespace(id=1),SimpleNamespace(id=2)]), \
       patch.object(self.w,'hit_npc',side_effect=hit):
   try:self.a.tick(8)
   except ValueError as error:self.fail('Zone snapshot was not invalidated after world stop: '+str(error))
  self.assertFalse(self.w.hero_dead)
  self.assertEqual(hits,[1])
  self.assertEqual(self.a.zones,[])
  self.assertEqual(sorted(f['userId'] for f in self.inactive()),[42,43])
 def test_uncancelled_aftershock_still_damages_every_target(self):
  self.zone().update(artci=25,artci_alan=600)
  hits=[]
  with patch.object(self.a,'others',return_value=[SimpleNamespace(id=1),SimpleNamespace(id=2)]), \
       patch.object(self.w,'hit_npc',side_effect=lambda uid,*args:hits.append(uid)):
   self.a.tick(8)
  self.assertEqual(hits,[1,2])
  self.assertEqual(self.a.zones,[])
  self.assertEqual([f['userId'] for f in self.inactive()],[42])

if __name__=='__main__':unittest.main()
