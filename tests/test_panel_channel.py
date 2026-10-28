"""The panel's in-game shop channel (server/panel_kanali.py).

The panel reads the shop and buys through the game server while the game runs: requests need the per-run key, the list is the
one the client sees and a purchase goes through the same request path as the client's, so its replies also reach the client.
"""
import copy
import json
from pathlib import Path
import sys
import tempfile
import threading
import types
import unittest
import urllib.error
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'server'))
from profil import Profil
from magaza import Magaza
from skylab import Skylab
from muzayede import Muzayede
import muzayede
from unittest import mock
import panel_kanali


class FakeSession:
    """Mirrors game.Session's shop and Skylab routing: on_packet -> Magaza.handle / Skylab.handle -> send."""

    def __init__(self, profile, shop):
        self.profil, self.magaza = profile, shop
        self.skylab = Skylab(profile, lambda *args: None)
        self.skylab.m = shop
        self.sosyal = types.SimpleNamespace(muzayede=Muzayede(profile, lambda *args: None))
        self.sosyal.muzayede.m = shop
        self.packet_lock = threading.Lock()
        self.sent = []

    def send(self, msgs, note=None, quiet=False):
        self.sent.extend(msgs)

    def on_packet(self, name, mid, fields, err):
        if self.magaza.handles(name, fields):
            self.send(self.magaza.handle(name, fields) or [])
        elif name == 'HangarShipChangeShipModelRequest':                   # game.Session routes these outside Magaza.handle
            self.send(self.magaza.change_model(fields)[0])
        elif name == 'HangarShipAutoBuyCpuAmmoRequest':
            self.send(self.magaza.auto_buy_ammo(fields))
        elif name == 'LegacyModule' and fields['message'].startswith('S|CFG|'):
            self.send(self.magaza.switch_config(fields['message'].split('|')[2]))
        elif name in muzayede.REQUESTS:
            self.send(self.sosyal.muzayede.handle(name, fields))
        elif name.startswith('Skylab'):
            self.send(self.skylab.handle(name, fields) or [])


class PanelChannel(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.profile = Profil(path=str(Path(temporary.name) / 'profil.json'))
        with (ROOT / 'server/data/varsayilan/yanitlar.json').open(encoding='utf8') as stream:
            replies = json.load(stream)
        self.session = FakeSession(self.profile, Magaza(self.profile, copy.deepcopy(replies), lambda *args: None))
        self.game = types.SimpleNamespace(CURRENT=self.session)
        port, panel_kanali.PORT = panel_kanali.PORT, 0              # any free port: a running game server may hold the real one
        self.addCleanup(setattr, panel_kanali, 'PORT', port)
        server = panel_kanali.start(self.game, temporary.name, lambda *args: None)
        self.addCleanup(server.server_close)
        self.addCleanup(server.shutdown)
        with open(Path(temporary.name) / 'panel_kanali.json', encoding='utf8') as stream:
            self.channel = json.load(stream)

    def call(self, path, body=None, key=True):
        request = urllib.request.Request('http://127.0.0.1:%d%s' % (self.channel['port'], path),
                                         data=None if body is None else json.dumps(body).encode('utf8'),
                                         headers={'X-Anahtar': self.channel['anahtar'] if key else 'x'})
        try:
            with urllib.request.urlopen(request, timeout=10) as response:
                return response.status, json.load(response)
        except urllib.error.HTTPError as error:
            return error.code, json.load(error)

    def test_requires_key(self):
        self.assertEqual(self.call('/magaza', key=False)[0], 403)

    def test_not_logged_in(self):
        self.game.CURRENT = None
        self.assertEqual(self.call('/magaza')[0], 409)

    def test_shop_list_is_the_clients(self):
        code, shop = self.call('/magaza')
        self.assertEqual(code, 200)
        self.assertEqual(shop['kategoriler'][0], 'ship')                     # the client's tab order (promptList)
        self.assertEqual(shop['kredi'], self.profile.d['pilot']['credits'])
        listed = self.session.magaza.shop_list('laser')[1]['itemList']
        self.assertEqual([it['lootId'] for it in shop['esyalar']['laser']], [it['lootId'] for it in listed])

    def test_buy_goes_through_the_client_path(self):
        loot = 'ammunition_laser_lcb-10'
        currency, unit = self.session.magaza.buy_price(loot)
        self.profile.d['pilot'][currency] = 10 ** 9
        code, out = self.call('/magaza/al', {'lootId': loot, 'category': 'ammunition', 'amount': 1000})
        self.assertEqual(code, 200)
        self.assertTrue(out['tamam'], out)
        self.assertLess(self.profile.d['pilot'][currency], 10 ** 9)
        self.assertIn('ShopItemBuyCommand', [m[0] for m in self.session.sent if isinstance(m, tuple)])   # the client got the reply
        self.assertNotIn('send', vars(self.session))                         # capture removed

    def test_buy_without_money(self):
        loot = next(it['lootId'] for it in self.session.magaza.shop_list('laser')[1]['itemList'] if self.session.magaza.buy_price(it['lootId']))
        currency, unit = self.session.magaza.buy_price(loot)
        self.profile.d['pilot'][currency] = 0
        code, out = self.call('/magaza/al', {'lootId': loot, 'category': 'laser', 'amount': 1})
        self.assertEqual(code, 200)
        self.assertFalse(out['tamam'])
        self.assertEqual(out['hata'], 'not_enough_' + currency)

    def test_hangar_equip_and_unequip(self):
        laser = self.profile.new_item('equipment_weapon_laser_lf-4')
        ship = self.profile.d['aktif_gemi']
        code, hangar = self.call('/hangar')
        self.assertEqual(code, 200)
        self.assertEqual(hangar['gemi'], ship)
        self.assertIn('laser', hangar['yuvalar'])
        self.assertIn(laser, [e['id'] for e in hangar['envanter']])
        code, out = self.call('/hangar/tasi', {'gemi': ship, 'konfig': 2, 'esya': laser, 'yon': 'tak'})
        self.assertTrue(out['tamam'], out)
        self.assertIn(laser, self.profile.config(2).get('laser', []))
        self.assertIn('HangarShipMoveItemsCommand', [m[0] for m in self.session.sent if isinstance(m, tuple)])
        hangar = self.call('/hangar?gemi=' + ship)[1]
        self.assertIn(laser, [e['id'] for e in hangar['konfigler']['2']['laser']['esyalar']])
        self.assertNotIn(laser, [e['id'] for e in hangar['envanter']])
        code, out = self.call('/hangar/tasi', {'gemi': ship, 'konfig': 2, 'esya': laser, 'yon': 'cikar'})
        self.assertTrue(out['tamam'], out)
        self.assertNotIn(laser, self.profile.config(2).get('laser', []))

    def test_skylab_view_and_upgrade(self):
        code, lab = self.call('/skylab')
        self.assertEqual(code, 200)
        self.assertEqual(len(lab['moduller']), 12)
        self.assertEqual(len(lab['depo']), 8)
        self.profile.d['pilot']['credits'] = 0
        out = self.call('/skylab/islem', {'modul': 'BASE_MODULE', 'islem': 'upgrade'})[1]
        self.assertFalse(out['tamam'])
        self.assertEqual(out['hatalar'], ['skylab_message_upgrade_credits'])
        self.profile.d['pilot']['credits'] = 10 ** 9
        for ore in ('1', '2', '3'):
            self.session.skylab.st['depo'][ore] = 10 ** 6
        out = self.call('/skylab/islem', {'modul': 'BASE_MODULE', 'islem': 'upgrade'})[1]
        self.assertTrue(out['tamam'], out)
        self.assertEqual(out['basarilar'], ['skylab_message_upgrade_success'])
        base = next(m for m in self.call('/skylab')[1]['moduller'] if m['id'] == 'BASE_MODULE')
        self.assertIsNotNone(base['kalan'])                                   # upgrade running
        self.assertIn('SkylabUnifiedReceiptCommand', [m[0] for m in self.session.sent if isinstance(m, tuple)])

    def test_drone_equip_and_ship_look(self):
        self.profile.d['pilot']['credits'] = 10 ** 9
        self.assertTrue(self.call('/magaza/al', {'lootId': 'drone_flax', 'category': 'drone', 'amount': 1})[1]['tamam'])
        drone = self.profile.d['dronlar'][-1]['kimlik']
        laser = self.profile.new_item('equipment_weapon_laser_lf-4')
        ship = self.profile.d['aktif_gemi']
        hangar = self.call('/hangar')[1]
        self.assertIn(drone, [d['id'] for d in hangar['dronlar']['1']])
        self.assertIn('drone', next(e for e in hangar['envanter'] if e['id'] == laser)['hedefler'])
        out = self.call('/hangar/tasi', {'gemi': ship, 'konfig': 1, 'esya': laser, 'yon': 'tak', 'hedef': 'drone', 'dron': drone})[1]
        self.assertTrue(out['tamam'], out)
        self.assertIn(laser, self.profile.drone_config(1).get(str(drone), []))
        out = self.call('/hangar/tasi', {'gemi': ship, 'konfig': 1, 'esya': laser, 'yon': 'cikar', 'hedef': 'drone', 'dron': drone})[1]
        self.assertTrue(out['tamam'], out)
        self.assertNotIn(laser, self.profile.drone_config(1).get(str(drone), []))
        look = self.profile.ship()['lootId'] + '_design_test'
        self.profile.ship().setdefault('tasarimlar', []).append(look)
        self.assertIn(look, self.call('/hangar')[1]['tasarimlar'])
        self.assertTrue(self.call('/hangar/tasarim', {'gemi': ship, 'lootId': look})[1]['tamam'])
        self.assertEqual(self.profile.ship_look(), look)
        self.assertFalse(self.call('/hangar/tasarim', {'gemi': ship, 'lootId': 'ship_x_design_y'})[1]['tamam'])

    def test_skylab_robot(self):
        collector = next(m for m in self.call('/skylab')[1]['moduller'] if m['robot'] and m['seviye'] > 0)
        self.profile.d['pilot']['credits'] = 0
        out = self.call('/skylab/robot', {'modul': collector['id'], 'tip': 1})[1]
        self.assertEqual(out, {'tamam': False, 'hatalar': ['skylab_message_upgrade_credits']})
        self.profile.d['pilot']['credits'] = 10 ** 6
        self.assertTrue(self.call('/skylab/robot', {'modul': collector['id'], 'tip': 1})[1]['tamam'])
        after = next(m for m in self.call('/skylab')[1]['moduller'] if m['id'] == collector['id'])
        self.assertEqual(after['robot']['etkin'], collector['robot']['etkin'] + 1)

    def test_equipment_changes_only_in_safe_zone(self):
        laser = self.profile.new_item('equipment_weapon_laser_lf-4')
        ship = self.profile.d['aktif_gemi']
        self.session.world = types.SimpleNamespace(in_station=lambda: False)        # in space
        self.assertFalse(self.call('/hangar')[1]['istasyonda'])
        out = self.call('/hangar/tasi', {'gemi': ship, 'konfig': 1, 'esya': laser, 'yon': 'tak'})[1]
        self.assertEqual(out, {'tamam': False, 'hata': 'istasyon'})
        self.assertNotIn(laser, self.profile.config(1).get('laser', []))
        for islem in ('temizle', 'yukle', 'aktar', 'dron_sat'):
            self.assertEqual(self.call('/hangar/islem', {'islem': islem, 'gemi': ship})[1]['hata'], 'istasyon')
        self.assertEqual(self.call('/hangar/tasarim', {'gemi': ship, 'lootId': self.profile.ship()['lootId']})[1]['hata'], 'istasyon')
        self.assertTrue(self.call('/hangar/islem', {'islem': 'kaydet', 'gemi': ship})[1]['tamam'])      # no equipment change
        self.session.world = types.SimpleNamespace(in_station=lambda: True)
        self.assertTrue(self.call('/hangar/tasi', {'gemi': ship, 'konfig': 1, 'esya': laser, 'yon': 'tak'})[1]['tamam'])

    def test_config_save_clear_load_and_switch(self):
        laser = self.profile.new_item('equipment_weapon_laser_lf-4')
        ship = self.profile.d['aktif_gemi']
        self.call('/hangar/tasi', {'gemi': ship, 'konfig': 2, 'esya': laser, 'yon': 'tak'})
        self.assertTrue(self.call('/hangar/islem', {'islem': 'kaydet', 'gemi': ship})[1]['tamam'])
        self.assertTrue(self.call('/hangar/islem', {'islem': 'temizle', 'gemi': ship, 'konfig': 2})[1]['tamam'])
        self.assertNotIn(laser, self.profile.config(2).get('laser', []))
        self.assertTrue(next(g for g in self.call('/hangar')[1]['gemiler'] if g['id'] == ship)['kayitli'])
        self.assertTrue(self.call('/hangar/islem', {'islem': 'yukle', 'gemi': ship})[1]['tamam'])
        self.assertIn(laser, self.profile.config(2).get('laser', []))
        self.assertTrue(self.call('/hangar/islem', {'islem': 'konfig', 'konfig': 2})[1]['tamam'])
        self.assertEqual(str(self.profile.ship()['aktif_konfig']), '2')

    def test_sell_and_favourite(self):
        laser = self.profile.new_item('equipment_weapon_laser_lf-4')
        item = next(e for e in self.call('/hangar')[1]['envanter'] if e['id'] == laser)
        currency, value = item['satis']
        before = self.profile.d['pilot'][currency]
        self.assertTrue(self.call('/hangar/islem', {'islem': 'sat', 'esyalar': [laser]})[1]['tamam'])
        self.assertNotIn(str(laser), self.profile.d['esyalar'])
        self.assertEqual(self.profile.d['pilot'][currency], before + value)
        ship = self.profile.d['aktif_gemi']
        self.assertTrue(self.call('/hangar/islem', {'islem': 'favori', 'gemi': ship, 'favori': True})[1]['tamam'])
        self.assertTrue(self.profile.ship()['favori'])

    def test_auto_buy_cpu_ammo(self):
        cpu = self.profile.new_item('equipment_extra_cpu_alb-x')
        self.call('/hangar/tasi', {'gemi': self.profile.d['aktif_gemi'], 'konfig': self.profile.aktif_konfig, 'esya': cpu, 'yon': 'tak'})
        self.profile.sync_ekipman()
        entry = next(c for c in self.call('/hangar')[1]['cpular'] if c['lootId'] == 'equipment_extra_cpu_alb-x')
        ammo = entry['secenekler'][-1]
        self.assertTrue(self.call('/hangar/islem', {'islem': 'cpu_cephane', 'esya': cpu, 'cephane': ammo})[1]['tamam'])
        self.assertEqual(self.profile.d['oto_alim_cephane']['equipment_extra_cpu_alb-x'], ammo)

    def test_auction_bid_and_bid_on_all(self):
        self.profile.d['pilot']['credits'] = 10 ** 9
        lots = self.call('/muzayede')[1]['lotlar']
        lot = lots[0]
        self.assertEqual(lot['sonraki'], muzayede.D['en_az_teklif'])
        self.assertFalse(self.call('/muzayede/teklif', {'tur': lot['tur'], 'loot': lot['loot'], 'fiyat': 1})[1]['tamam'])
        self.assertTrue(self.call('/muzayede/teklif', {'tur': lot['tur'], 'loot': lot['loot'], 'fiyat': lot['sonraki']})[1]['tamam'])
        self.assertTrue(next(l for l in self.call('/muzayede')[1]['lotlar'] if l['loot'] == lot['loot'] and l['tur'] == lot['tur'])['onde'])
        out = self.call('/muzayede/hepsi', {'lotlar': [[l['tur'], l['loot']] for l in lots[:4]]})[1]
        self.assertEqual(out['verilen'], 3)                                   # the first lot is already leading
        self.assertEqual(out['tutar'], 3 * muzayede.D['en_az_teklif'])

    def test_auction_auto_bid_and_alarms(self):
        self.profile.d['pilot']['credits'] = 10 ** 9
        mz = self.session.sosyal.muzayede
        lot = self.call('/muzayede')[1]['lotlar'][0]
        key = lot['tur'] + '|' + lot['loot']
        self.assertTrue(self.call('/muzayede/oto', {'tur': lot['tur'], 'loot': lot['loot'], 'azami': 50000})[1]['tamam'])
        self.assertTrue(self.call('/muzayede/alarm', {'tur': lot['tur'], 'loot': lot['loot'], 'gecilince': True, 'dk': 10080})[1]['tamam'])
        msgs = mz.oto()
        self.assertEqual(mz.d['teklifler'][key]['teklif'], muzayede.D['en_az_teklif'])     # auto-bid placed
        self.assertIn('MessageCommand', [m[0] for m in msgs])                               # the end-of-period alarm
        self.assertEqual({o['tip'] for o in mz.d['olaylar']}, {'oto_teklif', 'bitiyor'})
        self.assertFalse([m for m in mz.oto() if m[0] == 'MessageCommand'])                  # the alarm fires once per period
        with mock.patch.object(muzayede, 'rival', lambda *a, **k: (70000, 'Rival', 1)):
            mz.settle()                                                                      # outbid: refund and alarm
            self.assertNotIn(key, mz.d['teklifler'])
            self.assertEqual(mz.d['olaylar'][0]['tip'], 'gecildi')
            mz.oto()                                                                         # 80,000 needed, limit 50,000
            self.assertEqual(mz.d['olaylar'][0]['tip'], 'oto_sinir')
        events = self.call('/muzayede/olaylar?son=%d' % mz.d['olaylar'][1]['no'])[1]['olaylar']
        self.assertEqual([o['tip'] for o in events], ['oto_sinir'])
        self.call('/muzayede/oto', {'tur': lot['tur'], 'loot': lot['loot'], 'azami': 0})
        self.assertNotIn(key, mz.d['otomatik'])

    def test_skylab_rejects_unknown_action(self):
        self.assertEqual(self.call('/skylab/islem', {'modul': 'BASE_MODULE', 'islem': 'x'})[0], 400)


if __name__ == '__main__':
    unittest.main()
