"""Sosyal bölümün oturum düzeyi (yol haritası Aşama 10): sohbet (sohbet.py; sunucusu oyun sürecinde, game.py başlatır), posta,
notlar, rehber ve kara liste (posta.py), tek kişilik klan (klan.py), yerel müzayede (muzayede.py), gemi ışınlama (isinlama.py).

Oturum bağları: istekler (REQUESTS, handle), girişteki kayıtlı mesajların yerine profildekiler (login_replace: sohbet adresi,
okunmamış posta sayısı), zamanlı işler (tick: müzayede dönem sonları), ChatAuthenticateUserRequest (sohbete giriş ve odalar).
Pencere düğmesi bildirimi (UIButtonTriggerRequest) yalnız "açıldı" der (istemci kodu: UIMainCenterNewSystem.SendButtonTriggerRequest
açılış animasyonunun sonunda); sunucudan pencere açan bir komutun işleyicisi yok. Pencerenin açık/kapalı durumu, konumu ve boyutu
UIWindowUpdateRequest ile gelir (kapatınca maximized=false) ve profilde saklanır (profil.apply): kapatılan pencere sonraki girişte
açılmaz (canlı deneme 2026-10-17).
"""
import isinlama as IS
import klan as KL
import muzayede as MZ
import posta as PS

REQUESTS = PS.REQUESTS | KL.REQUESTS | MZ.REQUESTS | IS.REQUESTS | {'ChatAuthenticateUserRequest'}
CHAT_HOST = '127.0.0.1:%d'


class Sosyal:
    def __init__(self, profil, magaza, log=print, sohbet=None):
        self.p, self.log, self.m = profil, log, magaza
        self.sohbet = sohbet
        self.posta = PS.Posta(profil, log)
        self.klan = KL.Klan(profil, log)
        self.muzayede = MZ.Muzayede(profil, log)
        self.isinlama = IS.Isinlama(profil, log)
        for x in (self.posta, self.klan, self.muzayede, self.isinlama):
            x.m = magaza
        self.muzayede.posta = self.posta
        self.klan.on_change = self.clan_changed
        self.world = None
        self.send = None                   # oturumun gönderme işlevi (geri sayımla biten ışınlama)
        self.reload = None                 # gemi değişince haritayı yeniden yükletme (dunya.reload_ship)
        self.ep = None                     # sohbet uç kimliği (ChatAuthenticateUserRequest)
        self.welcomed = False
        self.last_window = (None, 0.0)     # son pencere bildirimi (istemci açılışta iki kez gönderiyor)

    def attach(self, world):
        self.world = world

    # -------------------------------------------------------- istekler
    def handle(self, name, f, now):
        if name == 'ChatAuthenticateUserRequest':
            self.chat_login(f.get('endpointId', ''), f.get('language'))
            return []
        if name in PS.REQUESTS:
            return self.posta.handle(name, f)
        if name in KL.REQUESTS:
            return self.klan.handle(name, f)
        if name in MZ.REQUESTS:
            return self.muzayede.handle(name, f, now)
        if name in IS.REQUESTS:
            return self.isinlama.warp(f, self.world, now, self.warp_done)
        return []

    def window(self, item, now=None):
        """UIButtonTriggerRequest: açılan pencereye göre yanıt (ışınlama penceresi). İstemci açılışta bildirimi iki kez gönderiyor,
        gerçek sunucu bir kez yanıtlıyor (kayıt); ikincisi yanıtsız (canlı deneme 2026-10-17: ret metni iki kez çıkıyordu)."""
        import time as _t
        now = _t.time() if now is None else now
        last, at = self.last_window
        self.last_window = (item, now)
        if item == last and now - at < 1.0:
            return []
        if item == 'ship_warp':
            return self.isinlama.window(self.world)
        return []

    def warp_done(self, msgs, changed):
        if self.send:
            self.send(msgs, 'gemi ışınlama')
        if changed and self.reload:
            self.reload()

    def tick(self, now):
        return self.muzayede.settle(now)

    # -------------------------------------------------------- giriş
    def login_replace(self, name, f):
        """Giriş demetindeki kayıtlı mesajın yerine (yoksa None): sohbet adresi yerel sunucuya, okunmamış posta profilden."""
        if name == 'ChatParamCommand':
            port = self.sohbet.port if self.sohbet else 7771
            return [(name, {'moduleList': [dict(m, param1=(CHAT_HOST % port) if m.get('param0') == 'chat_ip' else
                                                ('http://127.0.0.1/crossdomain.xml' if m.get('param0') == 'chat_cross_ip'
                                                 else m.get('param1', '')))
                                           for m in f.get('moduleList', [])]})]
        if name == 'UserMessageNewCommand':
            return [(name, {'userMessageInfoCommand': None, 'unreadCount': self.posta.unread()})]
        return None

    # -------------------------------------------------------- sohbet
    def chat_user(self):
        pl = self.p.d['pilot']
        return {'userId': pl.get('userName', ''), 'id': str(self.p.user_id), 'globalId': str(self.p.user_id), 'role': 'chatter',
                'clanTag': pl.get('clanTag', ''), 'factionId': str(pl.get('factionId', 0)), 'instanceId': '1'}

    def rooms(self):
        fac = self.p.d['pilot'].get('factionId', 0)
        return [('global', 'global', 'yerel'), ('faction', 'faction', str(fac))] + self.klan.rooms()

    def chat_login(self, ep, lang):
        if not self.sohbet:
            self.log('   sohbet sunucusu yok')
            return False
        self.ep = ep
        ok = self.sohbet.authenticate(ep, self.chat_user(), self.rooms(), lang)
        if ok and not self.welcomed:                  # harita değişiminde istemci yeniden bağlanabilir: duyuru oturumda bir kez
            self.welcomed = True
            pl = self.p.d['pilot']
            self.sohbet.duyuru('%s, yerel sunucuya hoş geldin. Burada sohbet, posta, klan ve müzayede tek oyunculudur.'
                               % pl.get('userName', ''))
        return ok

    def clan_changed(self):
        if self.sohbet:
            self.sohbet.update_user(clanTag=self.p.d['pilot'].get('clanTag', ''))
            self.sohbet.update_rooms(self.klan.rooms())

    def duyuru(self, text, room='global'):
        return self.sohbet.duyuru(text, room) if self.sohbet else 0
