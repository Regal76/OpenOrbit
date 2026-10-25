"""RSB-75/RCB-140 shots return to the previously selected laser ammo; manual choice stays possible."""
import sys,tempfile,time,unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'server'))
import cbs,dunya
from profil import Profil

class ReloadingLaserSelection(unittest.TestCase):
    def setUp(self):
        tmp=tempfile.TemporaryDirectory();self.addCleanup(tmp.cleanup)
        self.p=Profil(path=str(Path(tmp.name)/'pilot.json'))
        self.p.d['ekipman']['laser']=['equipment_weapon_laser_lf-3']
        self.p.d['dron_ekipman']=[]
        self.sent=[];self.w=dunya.World(self.p,self.sent.extend,lambda *_:None,4)
        self.c=cbs.Cbs(self.p,None,lambda *_:None)
        self.a=self.c.ast(2)
        self.a.update(durum='kurulu',sahip='rakip',yuvalar={'0':dict(loot='module_hulm-1',seviye=0,can=5850000,kalkan=4680000)},deflector={'acik':False})
        self.c.attach(self.w)
        self.x,self.y=cbs.position(2);self.w.hero=dunya.Mover(self.x+100,self.y)
        n=dunya.NPC(91001,'46',self.x,self.y);self.w.npcs[n.id]=n
        self.npc=n
        self.old='ammunition_laser_lcb-10';self.p.d['cephane'][self.old]=100

    def select(self,ammo):
        self.p.d['secili']['lazer']=self.old
        self.p.d['cephane'][ammo]=100
        self.w.menu_action(dict(menuItemId=ammo,actionType=0,sourceType=0))

    def test_npc_and_station_shots_return_to_previous_ammo(self):
        for i,(target,ammo) in enumerate((target,ammo) for target in (self.npc.id,cbs.asset_id(2))
                                        for ammo in ('ammunition_laser_rsb-75','ammunition_laser_rcb-140')):
            with self.subTest(target=target,ammo=ammo):
                self.select(ammo);self.w.target=target;self.w.attacking=True
                self.w.ammo_ready.clear();self.sent.clear();now=time.time()+i*10
                with patch.object(dunya.random,'random',return_value=1):
                    self.w.hero_laser(now)
                self.assertEqual(self.p.ammo(ammo),99)
                self.assertEqual(self.p.d['secili']['lazer'],self.old)
                self.assertEqual(self.p.ammo(self.old),100)

    def test_manual_laser_choice_during_rsb_reload_remains_possible(self):
        rsb='ammunition_laser_rsb-75';self.select(rsb)
        self.w.target=self.npc.id;self.w.attacking=True
        with patch.object(dunya.random,'random',return_value=1):self.w.hero_laser(time.time())
        self.w.menu_action(dict(menuItemId=self.old,actionType=0,sourceType=0))
        self.assertEqual(self.p.d['secili']['lazer'],self.old)
        self.assertTrue(self.w.attacking)

if __name__=='__main__':unittest.main()
