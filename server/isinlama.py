"""Gemi ışınlama penceresi (yol haritası Aşama 10; istemcinin ShipWarp* mesajları): başka bir gemiyi bulunduğun yere getirip
etkin gemi yapar (hangara gitmeden gemi değiştirme).

  UIButtonTriggerRequest 'ship_warp'  -> ShipWarpWindowCommand {jumpVoucherCount, uridium, isNearSpacestation, ships}; başka favori
                                         gemi yoksa kayıttaki gibi "msg_swnoactiveships" + ShipWarpNotAllowedCommand
  ShipWarpRequest {shipId}             -> geri sayım ("msg_swcountdown_p", %SECONDS%), sonra gemi değişir: ShipWarpCompletedCommand
                                         {currentShipLootId} ve istemci haritayı yeni gemiyle yeniden yükler (hangardaki değişim gibi)
Ücret (istemcinin metinleri): istasyonda ücretsiz ("desc_shipwarp_costs_spacestation"); dışarıda bir atlama kuponu
(resource_jumpvoucher, AJP-01'inkiyle aynı) ya da kupon yoksa uridyum. Savaşta ("msg_swnotallowed_fight"), Galaksi Kapısı ve etkinlik
haritalarında, Cubikon Mezarlığı ve LoW'da ("msg_swnotallowed_map") ışınlanılmaz; geri sayımda saldırıya uğrarsa ışınlama iptal
("msg_swblocked", ShipWarpCanceledCommand).
Uyarlamalar (kaynak vermediği için): uridyum fiyatı (AJP-01'in kuponsuz atlaması gibi 1.000 U), geri sayım 5 sn.
"""
import harita as H
from eski_protokol import legacy, stm

KUPON = 'resource_jumpvoucher'
URIDYUM = 1000
GERI_SAYIM = 5
REQUESTS = {'ShipWarpRequest'}


def mod(_cls, **f):
    f['_'] = _cls
    return f


class Isinlama:
    def __init__(self, profil, log=print):
        self.p, self.log = profil, log
        self.m = None
        self.busy = None                  # süren ışınlama: (shipId, ödeme)

    def allowed_map(self, map_id):
        return map_id in H.NAMES and map_id not in H.SPECIAL

    def ships(self):
        """Işınlanabilecek gemiler: etkin olmayan favoriler (istemcinin penceresi: "You can only Warp ships that are marked as your
        favorites!"; favori hangarda HangarShipFavouriteRequest)."""
        act = str(self.p.d['aktif_gemi'])
        return [sid for sid in sorted(self.p.d['gemiler'], key=int) if sid != act and self.p.d['gemiler'][sid].get('favori')]

    def window(self, w):
        """Pencere açıldı (UIButtonTriggerRequest 'ship_warp')."""
        sids = self.ships()
        if not sids:
            return [legacy('0|A|STM|msg_swnoactiveships'), ('ShipWarpNotAllowedCommand', {})]
        home = self.p.d['konum'].get('mapId', 1)
        near = bool(w and w.in_station())
        pay = 0 if near else URIDYUM
        ships = []
        for sid in sids:
            s = self.p.ship(sid)
            ships.append(mod('ShipWarpModule', shipId=int(sid), typeId=s['lootId'], shipDesignName=s.get('tasarim') or '',
                             uridiumPrice=pay, voucherPrice=0 if near else 1, hangarId=int(sid), hangarName='', mapId=home))
        return [('ShipWarpWindowCommand', {'jumpVoucherCount': self.p.resource(KUPON), 'uridium': int(self.p.d['pilot'].get('uridium', 0)),
                                           'isNearSpacestation': near, 'ships': ships})]

    def refuse(self, key):
        self.log('   ışınlama yok: %s' % key)
        return [stm(key), ('ShipWarpNotAllowedCommand', {})]

    def warp(self, f, w, now, done):
        """ShipWarpRequest. done(mesajlar, gemi_değişti): geri sayım bitince oturumun çağırdığı tamamlama (w.later)."""
        sid = str(f.get('shipId'))
        if sid not in self.ships():
            return self.refuse('msg_swnoactiveships')
        if self.busy:
            return []
        if not w or not self.allowed_map(self.p.d['konum'].get('mapId', 0)):
            return self.refuse('msg_swnotallowed_map')
        import magaza as MG
        if now - w.last_combat < MG.ESYA['savas_disi_sn']:
            return self.refuse('msg_swnotallowed_fight')
        if w.in_station():
            pay = {}
        elif self.p.resource(KUPON):
            pay = {KUPON: 1}
        else:
            pay = {'currency_uridium': URIDYUM}
        import envanter as INV
        if INV.missing(self.p, pay):
            return [stm('ttip_currency_missing', '%CURRENCY%', 'Uridium'), ('ShipWarpNotAllowedCommand', {})]
        self.busy = (sid, pay, now)
        self.log('   ışınlama başladı: shipId %s (%s)' % (sid, pay or 'ücretsiz'))
        w.later(GERI_SAYIM, lambda: done(*self.finish(w)))
        return [('ShipWarpWindowCloseCommand', {}), stm('msg_swstarted'),
                stm('msg_swcountdown_p', '%SECONDS%', GERI_SAYIM)]

    def finish(self, w):
        """Geri sayım bitti -> (mesajlar, gemi değişti mi)."""
        sid, pay, t0 = self.busy
        self.busy = None
        import magaza as MG
        if w.last_combat > t0:
            self.log('   ışınlama iptal: saldırı')
            return [stm('msg_swblocked'), ('ShipWarpCanceledCommand', {})], False
        import envanter as INV
        if INV.spend(self.p, pay, 'balance_ship_warp_completed') is None:
            return [stm('ttip_currency_missing', '%CURRENCY%', 'Uridium'), ('ShipWarpCanceledCommand', {})], False
        _, changed = self.m.activate({'shipId': sid}, in_station=True)
        if not changed:
            return [('ShipWarpCanceledCommand', {})], False
        import rutbe as RT
        RT.note(self.p, 'history_ship_warp_completed', self.p.ship()['lootId'])
        msgs = [('ShipWarpCompletedCommand', {'currentShipLootId': self.p.ship()['lootId']})]
        msgs += INV.update_msgs(self.m, self.p, list(pay)) if pay else []
        return msgs + [self.m.ships_cmd()], True
