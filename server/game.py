"""Yerel oyun sunucusu (TCP 8081): DarkOrbit Unity istemcisinin libcom protokolü.

Kullanım: python -I game.py <log_klasörü> [--yakin-npc] [--reklamsiz] [--dokunulmaz] [--kontrol] [--profil=<yol>] [--ayarlar=<yol>]
                                         [--durdur=<dosya>]
  Normalde yönetim paneli başlatır (server/panel/): kayıt yuvasının profili, oyun ayarları ve durdurma dosyası onun verdiği.
  --ayarlar=<yol>: oyun ayarları (ayar.py; varsayılan save/ayarlar.json): çarpanlar, etkinlik seçimi, müzayede rakipleri,
  reklamsız/dokunulmaz/yakın NPC (seçeneklerin panel karşılıkları). Dosya değişince oyun açıkken yeniden okunur.
  --durdur=<dosya>: dosya belirince profil kaydedilir ve sunucu kapanır (panelin "Sunucuyu durdur"u).
  --reklamsiz: girişte kendiliğinden açılan tanıtım pencereleri (günlük bonus, ipuçları, Season Pass) de gönderilmez.
  Gerçek parayla alışveriş pencereleri (Helix Blitz kampanyası, paket teklifi) ve Command Center'ın kendiliğinden açılması
  her zaman kapalıdır; Command Center menüden açılabilir.
  --yakin-npc: test kolaylığı, ilk 4 NPC türünden birer tane oyuncunun hemen yakınında doğar.
  --dokunulmaz: test kolaylığı, uzaylıların atışları görünür ama gemi can ve kalkan kaybetmez (ör. kapıları ölmeden denemek).
  --kontrol: canlı test kontrol kanalı (kontrol.py, 127.0.0.1:8099): mesaj izi, istek enjeksiyonu, komut gönderme, durum.
  --profil=<yol>: etkin kayıt yuvası (yollar.py) yerine başka bir profil (panel yuvanınkini verir; canlı testler kopyayla çalışır).
Çerçeve: istemci -> sunucu ilk paket 4 bayt, sonrakiler 3 bayt BE uzunluk; sunucu -> istemci 3 bayt BE uzunluk.
Mesajlar protocol.py ile kodlanır/çözülür (tablo: istemcinin kendi read() kodu, server/data/protocol_read.json).

Giriş akışı (gerçek sunucunun kaydından, bkz. belgeler/istemci/kayit_analizi.md):
  LoginRequest  -> data/giris.json "giris" demeti
  ReadyRequest  -> "hazir" demeti (ilk ReadyRequest'te)
  Demetlerdeki "@…" işaretleri profilden (save/profil.json) ya da harita verisinden (data/haritalar.json) üretilir.
  Salt okunur istekler kayıttaki yanıtlarla karşılanır (data/yanitlar.json); ayar/pencere/hareket istekleri profile yazılır.
  Harita yüklenince dünya simülasyonu başlar (dunya.py): NPC'ler, savaş, ödüller, kutular.
  Mağaza ve hangar istekleri (satın alma, ekipman takıp çıkarma) magaza.py'de, profil üzerinde işlenir.
  P.E.T. (pet.py): PetRequest, PetGearActivationRequest; uzaydaki davranışı dünya döngüsünde, harita değişince yeniden çıkar.
  Galaksi Kapıları (kapi.py): GalaxyGateBuilder* istekleri; X-1'deki kapı portalları ve kapı haritasındaki dalgalar dünyaya bağlanır.
Şablon dosyaları kayit/sablon_cikar.py ile üretilir; yoksa yalnızca profilden en küçük giriş (gemi + LoginResponse) gönderilir.
"""
import os, sys, socket, threading, time, json, math

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import protocol as P       # noqa: E402
import yollar as YOL       # noqa: E402
from profil import Profil  # noqa: E402
from dunya import World    # noqa: E402
from magaza import Magaza  # noqa: E402
from gorev import Gorevler  # noqa: E402
import dunya               # noqa: E402
import kapi as KAPI        # noqa: E402
import etkinlik_kapi as EKP  # noqa: E402
import labirent as LAB      # noqa: E402
import pve_modlari as PVM   # noqa: E402
import low as LOW          # noqa: E402
import assembly as ASM     # noqa: E402
import dispatch as DSP     # noqa: E402
import skylab as SKY       # noqa: E402
import banka as BANK       # noqa: E402
import ganimet as GN       # noqa: E402
import gemi_modul as GM    # noqa: E402
import takvim as TK        # noqa: E402
import traceback           # noqa: E402
import sezon as SZN        # noqa: E402
import savas_bileti as SBL  # noqa: E402
import gunluk_odul as GOD  # noqa: E402
import basarim as BSM      # noqa: E402
from gunluk import Gunluk  # noqa: E402
from yetenek import Yetenekler  # noqa: E402
from basarim import Basarimlar  # noqa: E402
import harita as H
import savas_esya as SE    # noqa: E402
import rutbe as RT         # noqa: E402
import yeni_sistemler as YS  # noqa: E402
import sohbet as SH        # noqa: E402
import sosyal as SO        # noqa: E402
import kontrol as KT       # noqa: E402
import ayar as AY          # noqa: E402
import siralama as SR      # noqa: E402
import gm_konsol as GMK    # noqa: E402
import ipucu as IP         # noqa: E402
import odeme as OD         # noqa: E402
import etkinlik_harita as ETH  # noqa: E402
import canli_durum as CD   # noqa: E402
import ek_etkinlikler as EKE  # noqa: E402
import cbs as CBS
import dukkanlar as DK
import profil as PF
import envanter as INV
from eski_protokol import legacy, parse as legacy_parse  # noqa: E402         # noqa: E402

ARGS = [a for a in sys.argv[1:] if not a.startswith('--')]
LOG_DIR = ARGS[0] if ARGS else '.'
DATA = os.path.join(HERE, 'data')
lock = threading.Lock()


def log(text):
    with lock:
        with open(os.path.join(LOG_DIR, 'gs.log'), 'a', encoding='utf8') as fh:
            fh.write(time.strftime('%H:%M:%S ') + text + '\n')


def encode(msgs):
    """Mesajları çerçeveler; kodlanamayan mesaj (255'i aşan liste, bilinmeyen alan …) adıyla günlüğe yazılıp atlanır, ötekiler gider."""
    out = []
    for n, f in msgs:
        try:
            out.append(P.frame(P.encode_message(n, f)))
        except Exception as e:
            log('   kodlanamadı, gönderilmedi: %s: %r' % (n, e))
    return b''.join(out)


def save_profile():
    """Profil kaydı; hata (dosya kilitli, disk) günlüğe yazılır, oturumu ve harita değişimini düşürmez; bir sonraki kayıtta yeniden denenir."""
    try:
        PROFIL.save()
    except Exception as e:
        log('   profil kaydedilemedi: %r' % e)


def _load(name, default):
    p = YOL.sablon(name) if name in YOL.SABLONLAR else os.path.join(DATA, name)     # şablon: kendi kaydın, yoksa paylaşılabilir kopya
    return json.load(open(p, encoding='utf8')) if p and os.path.exists(p) else default


class Sablonlar:
    """Kayıttan çıkarılmış giriş demetleri, harita dünyası ve istek yanıtları (kendi kaydın yoksa data/varsayilan/'daki paylaşılabilir
    kopya; yollar.sablon)."""

    def __init__(self):
        self.giris = _load('giris.json', {})
        self.haritalar = _load('haritalar.json', {})
        self.yanitlar = _load('yanitlar.json', {})
        self.uretilen = {}

    def map_world(self, map_id):
        """Haritanın dünya mesajları {'giris', 'hazir'}: kayıttaysa kayıttan; değilse üretilir (istasyonlu haritalarda kayıttaki
        2-1 istasyonu taşınır, harita.map_world) ve portallar istemcinin spacemap-config.xml'inden."""
        rec = self.haritalar.get(str(map_id))
        if rec is not None:
            return rec
        if str(map_id) not in self.uretilen:
            self.uretilen[str(map_id)] = H.map_world(map_id, self.haritalar.get('5'))
        return self.uretilen[str(map_id)]

    def station(self, map_id):
        """Haritanın istasyonu (tamir, doğma, hangar): süs istasyonları (5-2'nin korsan istasyonu) sayılmaz."""
        for m in self.map_world(map_id).get('hazir', []):
            if m['_m'] == 'SpaceStationCommand' and m.get('type') not in H.DECOR_STATION_TYPES:
                return m
        return None

    def batch(self, kind, profil):
        """'giris' ya da 'hazir' demetini [(ad, alanlar)] olarak üretir."""
        if not self.giris:
            if kind == 'giris':
                return [profil.generate('@gemi'), profil.generate('@giris_yaniti')]
            return []
        map_id = profil.d['konum']['mapId']
        out = []
        for m in self.giris.get(kind, []):
            mk = m['_m']
            if mk in ('@harita_giris', '@harita_hazir'):
                out += self.world_msgs(map_id, 'giris' if mk == '@harita_giris' else 'hazir')
            elif kind == 'hazir' and (mk == 'EquipReadyCommand' or m.get('message', '').startswith('0|n|MSG|3|2|msg_equip_')):
                continue               # kayıtta her yerde true; dünya istasyon bölgesine girip çıktıkça gönderir (dunya.check_gates)
            elif mk.startswith('@'):
                g = profil.generate(mk, self.station(map_id))
                if g:
                    out.append(g)
            else:
                out.append((mk, profil.patch_template(mk, m)))
        return out

    def world_msgs(self, map_id, kind):
        """Harita dünyası: kayıtta gezilen haritalar için kayıttaki mesajlar, diğerleri için istemcinin portal verisinden."""
        return [(w['_m'], {k: v for k, v in w.items() if k != '_m'}) for w in self.map_world(map_id).get(kind, [])]

    def asset_removes(self, map_id):
        """Harita değişiminde eski haritanın istasyon/taret nesnelerini kaldır (kayıttaki AssetRemoveCommand gibi)."""
        return [('AssetRemoveCommand', {'assetType': w['type'], 'uid': w['assetId']}) for w in
                self.map_world(map_id).get('giris', []) if w['_m'] == 'AssetCreateCommand']

    def yanit(self, name, fields):
        """Salt okunur isteğe kayıttaki yanıtı bulur: tam eşleşme, yoksa yalnız sayfalama/haber alanları farklı olan kayıt.
        Tür, modül, sıralama gibi alanlar farklıysa yanıt yok (eskiden başka türün listesi gidiyordu: Hall of Fame, Skylab modülü)."""
        entries = self.yanitlar.get(name)
        if not entries:
            return None
        def diff(e):
            return {k for k, v in fields.items() if k != '_' and e['istek'].get(k) != v}
        best = min(entries, key=lambda e: len(diff(e)))
        if diff(best) - LOOSE_FIELDS:
            return None
        return [(m['_m'], m) for m in best['yanit']]


LOOSE_FIELDS = {'startIndex', 'page', 'start', 'newsInfo'}       # yanıtın türünü değiştirmeyen istek alanları
# gerçek sunucunun da yanıt vermediği istekler (kayıt): günlüğe "yanıtsız" diye düşmesin
SILENT = {'TrackVariableRequest',
          'CommandCenterNewsClickedRequest', 'PerformanceTrackingSendInfoRequest',
          'ProActionBarOpenStateChangeRequest', 'QuestGiverWindowClosedRequest', 'CommandCenterUpdateDontShowRequest',
          'EggTriggerRequest'}
# günlüğe hiç yazılmayan istekler. EggTriggerRequest: istemcinin "harita dışına 6100 birim çıkıldı" sürprizi
# (ChangePositionSyncGameObjectPos.Run); 2D'de geminin y'si ters eksende tutulduğu için gemi haritanın alt yarısındayken
# saniyede bir gelir (kullanıcının 2D oturumunda 10 dakikada 103 kez; H82). Sunucuda karşılığı yok.
UNLOGGED = ('MoveRequest', 'KeepAlive', 'AttackRocketRequest', 'EggTriggerRequest')
SOHBET = None                # yerel sohbet sunucusu (sohbet.py; main başlatır, port 7771)
KONTROL = '--kontrol' in sys.argv        # canlı test kontrol kanalı (kontrol.py): mesaj izi ve enjeksiyon
CURRENT = None               # son bağlanan istemcinin oturumu (kontrol kanalı bunu yönetir)
PROFIL_YOLU = next((a.split('=', 1)[1] for a in sys.argv if a.startswith('--profil=')), None)
DURDUR = next((a.split('=', 1)[1] for a in sys.argv if a.startswith('--durdur=')), None)    # panel: belirince kaydet ve çık
LOGOUT_SN = 19.2             # kayıt: çıkış düğmesinden 19,2 sn sonra 0|l, bağlantı kapanır

SABLON = Sablonlar()
PROFIL = Profil(SABLON.giris.get('tohum'), **({'path': PROFIL_YOLU} if PROFIL_YOLU else {}))
H.PLAYER_FACTION = PROFIL.d['pilot'].get('factionId')     # 5-X'te yalnız kendi firmasının portalları
KAPI.register_npcs(dunya.CFG['tipler'])     # kapı uzaylıları NPC türleri olarak
EKP.register_npcs(dunya.CFG['tipler'])      # etkinlik kapılarınınkiler (etkinlik_kapi.py)
dunya.CFG['tipler'].update(PVM.AR.D['turler'])  # Aşama 8'in modlarının uzaylıları (data/pve_modlari.json)
for _mid, _rows in PVM.AR.D.get('harita_ek', {}).items():          # X-7'nin Blighted Kristallon'ları (Hybrid Alloy)
    if not _mid.startswith('_') and _mid in dunya.CFG['haritalar']:
        _have = {g['tip'] for g in dunya.CFG['haritalar'][_mid]['npc']}
        dunya.CFG['haritalar'][_mid]['npc'] += [{'tip': t, 'adet': n} for t, n in _rows if t not in _have]


# Season Pass, Battle Pass ve günlük ödül pencerelerinin kayıttaki giriş mesajları -> profilden üretilenler
PASS_LOGIN = dict({n: 'sezon' for n in ('SeasonPassStatusCommand', 'SeasonPassMissionInfoCommand', 'SeasonPointsInfoCommand',
                                        'SeasonPassRewardInfoCommand')},
                  **{n: 'bilet' for n in ('BattlePassInfoCommand', 'BattlePassKeyExchangeInfoCommand', 'BattlePassWindowSettingsModule')},
                  **{n: 'odul' for n in ('MonthlyDeluxeInfoCommand', 'MiniClientRewardInfoCommand', 'EventUnityClientRewardQuestCommand')})
GOD_REQUESTS = ('MiniClientRewardClaimRequest', 'MonthlyDeluxeClaimRequest', 'ClaimUnityClientRewardRequest')
# --reklamsiz: girişte kendiliğinden açılan kampanya/tanıtım pencerelerini gönderme
POPUP_MSGS = {'DisplayOfferCommand', 'HintWindowAddComand', 'HintWindowListInitCommand', 'DailyLoginRewardDayCommand',
              'MiniClientRewardInfoCommand', 'MonthlyDeluxeInfoCommand', 'CommandCenterDontShowInfoCommand', 'SeasonPassStatusCommand',
              'SeasonPassMissionInfoCommand', 'SeasonPassRewardInfoCommand'}
NO_POPUPS = '--reklamsiz' in sys.argv
# her zaman: gerçek parayla alışveriş pencereleri (tek oyunculuda işe yaramaz)
#   EventPaymentActorCommand: "%400 Helix Blitz" uridyum kampanyası; DisplayOfferCommand: paket teklifi penceresi
PAYMENT_POPUPS = {'EventPaymentActorCommand', 'DisplayOfferCommand'}


def no_popups(msgs):
    """Girişte kendiliğinden açılan pencereleri ayıklar. Command Center: istemci CommandCenterDontShowInfoCommand.inspected
    false gelirse pencereyi açar (CommandCenterDontShowInfoCommandHandler); hep true gönderilir, menüden açılabilir kalır."""
    drop = PAYMENT_POPUPS | (POPUP_MSGS if NO_POPUPS or AY.get('reklamsiz') else set())      # seçenek ya da panelin ayarı
    out = []
    for n, f in msgs:
        if n in drop and n != 'CommandCenterDontShowInfoCommand':
            continue
        if n == 'CommandCenterDontShowInfoCommand':
            f = dict(f, inspected=True)
        out.append((n, f))
    return out


def login_batch(kind, first=True):
    """first=False: harita değişimi (portal, istasyonda tamir). Girişte kendiliğinden açılan pencereler (günlük bonus, ipuçları,
    Season Pass) yalnız girişte gelir; arayüz harita değişiminde kalır, veriyi yeniden göndermek pencereleri yeniden açıyordu."""
    msgs = no_popups(SABLON.batch(kind, PROFIL))
    if not first:
        msgs = [(n, f) for n, f in msgs if n not in POPUP_MSGS or n == 'CommandCenterDontShowInfoCommand']
    return msgs


HOME_MAP = {1: 1, 2: 5, 3: 9}     # firma -> ana harita (X-1)
NAME_MIN, NAME_MAX, STATUS_MAX = 3, 20, 200    # pilot adı ve durum yazısı (uyarlama: istemci sınır göndermiyor)


def achievement_groups(now=None):
    """Başarımların etkin grupları: takvimin etkinlikleri ve bu sezonun Season Pass grubu (SEASONPASS_Qn; sezon.py)."""
    sp = SZN.achievement_group(now)
    return TK.achievement_groups(now) | ({sp} if sp else set())

WORLD_REQUESTS = {'ShipSelectRequest': 'select', 'AttackLaserRequest': 'laser_start', 'AttackRocketRequest': 'rocket',
                  'CollectBoxRequest': 'collect', 'MenuActionRequest': 'menu_action', 'HarvestRequest': 'harvest',
                  'TradeSellOreRequest': 'sell_ore', 'InstantRepairRequest': 'instant_repair'}


class Session:
    """Bir istemci bağlantısı: giriş akışı, dünya, harita değişimi. Dünya döngüsü de buraya yazdığı için gönderme kilitli."""

    def __init__(self, c, addr):
        global CURRENT
        CURRENT = self
        self.c, self.addr = c, addr
        self.send_lock = threading.Lock()
        self.packet_lock = threading.Lock()      # istemcinin paketleri ve kontrol kanalının enjekte ettikleri sırayla işlenir
        self.play_start = time.time()            # oynama süresi (play_time)
        self.state_lock = threading.RLock()
        self.map_pending = False     # ShipInitializationCommand gönderildi; harita yüklenince (ReadyRequest) hazır demeti + dünya
        self.ready_n = 0             # karşılanan ReadyRequest sayısı (1: ilk giriş; sonrakiler harita yüklenişleri)
        self.world = None
        self.magaza = Magaza(PROFIL, SABLON.yanitlar, log)
        self.gorev = Gorevler(PROFIL, log)
        self.gorev.grant = self.quest_reward
        self.gorev.send = lambda m: self.send(m, 'görev süresi')
        self.magaza.quest = self.gorev.event                        # toplama görevleri: rafineride üretilen cevher
        self.gunluk = Gunluk(PROFIL, self.magaza, log)      # günlük giriş takvimi
        PROFIL.daily_fields = self.gunluk.fields
        self.pet = self.magaza.pet
        self.pet.send_raw = lambda m: self.send(m, quiet=True)
        self.kapilar = KAPI.Kapilar(PROFIL, log)
        self.kapilar.m = self.magaza
        self.magaza.kapilar = self.kapilar      # ödüllerdeki ücretsiz kapı enerjisi
        self.ekapilar = EKP.EtkinlikKapilari(PROFIL, log)                    # etkinlik kapıları (Gauntlet of Plutus, Vortex …)
        self.ekapilar.m = self.magaza
        self.pve = PVM.PveModlari(PROFIL, self.magaza, self.ekapilar, log)    # Aşama 8: sonsuz ve rogue-lite PvE modları
        self.pve.send = lambda m: self.send(m, 'mod')
        self.pve.change_map = self.change_map
        PROFIL.mode_mods = lambda: self.pve.ebl.mods(PROFIL.d['konum']['mapId']) if self.pve.ebl else {}
        self.yeni = YS.YeniSistemler(PROFIL, self.magaza, log)     # Aşama 9: N.O.V.A., Armory Unlock, QFC/Hyperforge, otomatik pilot
        self.magaza.yeni = self.yeni
        PROFIL.nova_mods = lambda: self.yeni.mods(PROFIL.d['konum']['mapId'])
        PROFIL.captain_energy = self.yeni.nova.hud
        self.sosyal = SO.Sosyal(PROFIL, self.magaza, log, SOHBET)   # Aşama 10: sohbet, posta, klan, müzayede, gemi ışınlama
        self.sosyal.send = lambda m, note: self.send(m, note)
        self.sosyal.reload = lambda: self.world and self.world.reload_ship()
        self.social_next = 0.0
        self.yetenek = Yetenekler(PROFIL, self.magaza, self.kapilar, log)    # pilot yetenek ağacı (log diskleri kapı sayacında)
        self.assembly = ASM.Assembly(PROFIL, log)                            # Assembly (tarifler, üretim)
        self.assembly.m = self.magaza
        self.assembly.send = lambda m: self.send(m, 'Assembly')
        self.dispatch = DSP.Dispatch(PROFIL, self.kapilar, log)             # Dispatch (toplayıcı ve kapı gönderimi)
        self.dispatch.m = self.magaza
        self.skylab = SKY.Skylab(PROFIL, log)                                # Skylab (üretim, yükseltme, taşıma)
        self.skylab.m = self.magaza
        self.skylab.send = lambda m: self.send(m, 'Skylab')
        self.skylab.quest = lambda **kw: self.gorev.event('skylab', **kw)        # görev koşulu UPDATE_SKYLAB_TO_LEVEL (Ö1)
        self.moduller = GM.Moduller(PROFIL, log)                             # kararsız modüller (Restabilize)
        self.moduller.m = self.magaza
        self.sezon = SZN.Sezon(PROFIL, log)                                  # Season Pass (sezon.py)
        self.bilet = SBL.SavasBileti(PROFIL, log)                            # Battle Pass ve anahtar değişimi (savas_bileti.py)
        self.odul = GOD.GunlukOdul(PROFIL, log)                              # Mini Client, Monthly Deluxe, Unity ödülü (gunluk_odul.py)
        for _o, _note in ((self.sezon, 'Season Pass'), (self.bilet, 'Battle Pass'), (self.odul, 'günlük ödül')):
            _o.m = self.magaza
            _o.send = (lambda note: lambda m: self.send(m, note))(_note)
        self.magaza.biletler = (self.sezon, self.bilet, self.odul)
        self.bilet.objective = lambda: self.sezon.event('objective')     # Season Pass 700023-700025 (etkinlikte 15 Battle Pass görevi)
        self.magaza.quest = self.quest_event                        # toplama görevleri: rafineride üretilen cevher
        self.bank_sent = None         # istemcinin son gördüğü Uridium Bank birikimi
        self.cal_sent, self.cal_next = None, 0.0                            # takvim: son bildirilen etkin etkinlikler
        self.win_sent = {}                                                  # etkinlik pencerelerinin son bildirilen görünürlüğü
        BSM.set_events(achievement_groups())
        self.bank_next = 0.0
        self.basarim = Basarimlar(PROFIL, log)                               # başarımlar ve unvanlar
        self.basarim.send = lambda m: self.send(m, 'başarım')
        PROFIL.ach = self.ach_event
        self.kapilar.world = lambda: self.world
        self.kapilar.info_tpl = next((m for e in SABLON.yanitlar.get('GalaxyGateBuilderInfoRequest', []) for m in e['yanit']
                                      if m['_m'] == 'GalaxyGateBuilderInfoCommand'), None)
        self.logout_timer = None      # çıkış geri sayımı (UIButtonTriggerRequest logout)
        self.gm = GMK.Konsol(self, log)   # GM konsolu (panelde açıksa)
        self.ipucu = IP.Ipuclari(PROFIL, log)   # yeni başlayan ipuçları (bir kez; panelin 'ipuclari' ayarı)
        self.pencereler = OD.Pencereler()      # son açılan pencereler: ödeme düğmesinin ürünü (odeme.py)
        self.ek = EKE.EkEtkinlikler(PROFIL, self.magaza, self.ekapilar, log)   # Ö3'ün etkinlikleri (Chromin Rush …)
        if self.ek.fiesta:
            self.ek.fiesta.change_map = self.change_map
            self.pve.extra_windows['fiesta'] = self.ek.fiesta.portal_window
        self.cbs = CBS.Cbs(PROFIL, self.magaza, log)                     # Clan Battle Station (Ö5)
        self.ek.add(self.cbs)
        self.sosyal.klan.cbs = self.cbs
        PROFIL.cbs_mods = self.cbs.mods
        self.dukkan = DK.Dukkanlar(PROFIL, self.magaza, log)              # Ö7: uridyumla çalışan dükkân pencereleri
        self.ek.add(self.dukkan)
        PF.WINDOW_HOOKS['returnee_login'] = self.dukkan.returnee_active
        PF.WINDOW_HOOKS['diminish_quests'] = self.ek.acil.menu_visible     # Urgent Missions: yalnız görev varken (acil_gorevler.py)
        for kind, s in (('vortex', self.ek.vortex), ('dunya_patronu', self.ek.patron), ('mimesis', self.ek.mimesis)):   # Ö4
            s.change_map = self.change_map
            self.pve.extra_windows[kind] = s.portal_window
        self.ek.send = lambda m: self.send(m, 'etkinlik')
        self.ek.unvan.base_title = lambda: self.basarim.title_msgs()
        self.ek_next = 0.0
        PROFIL.hint = self.ipucu.show
        self.secrets = set()         # LoginRequest'teki oturum anahtarı: eski metin protokolü de taşır ("S|CFG|2|<kullanıcı>|<anahtar>")
        self.magaza.rescue_depot()   # görünmez depoya düşmüş ödüller (dron tasarımı, P.E.T. protokolü, Season Pass rezervi) yerine

    # ------------------------------------------------------------ çıkış
    def logout_start(self):
        """Çıkış düğmesi: istemci kendi geri sayımını gösterir; kayıttaki gibi ~19 sn sonra 0|l ve bağlantı kapanır. Göndermezsek
        istemci süre bitince bağlantıyı koparıp yeniden giriş yapıyordu (günlük 13:11)."""
        self.logout_cancel()
        t = threading.Timer(LOGOUT_SN, self.logout_done)
        t.daemon = True
        self.logout_timer = t
        t.start()
        log('   çıkış: %.1f sn sonra' % LOGOUT_SN)

    def logout_cancel(self):
        if self.logout_timer:
            self.logout_timer.cancel()
            self.logout_timer = None
            log('   çıkış iptal')

    def logout_done(self):
        self.logout_timer = None
        save_profile()
        try:
            self.send([legacy('0|l')], 'çıkış')
            self.c.shutdown(socket.SHUT_RDWR)
        except OSError:
            pass

    def ach_event(self, kind, **kw):
        """Oyun olayları: rütbe sayaçları (rutbe.py), Pass görevleri ve başarımlar (basarim.py)."""
        RT.event(PROFIL, kind, **kw)
        if kind != 'map':                         # harita ziyareti görev olayından gelir (çift sayılmasın)
            self.pass_event(kind, **kw)
            msgs = self.ek.event(kind, kw)        # Ö3'ün etkinlik görevleri (Galaxy Trek)
            if msgs:
                self.send(msgs, 'etkinlik görevi')
        if kind == 'death':                       # "ölmeden" görevleri başarısız (gorev.py)
            failed = self.gorev.broken('death')
            if failed:
                self.send(failed, 'görev başarısız')
        if kind == 'level':                       # seviye atlandı: yeni özelliğin davet ipucu (ipucu.py)
            hint = self.ipucu.level(kw.get('deger', 1))
            if hint:
                self.send(hint, 'ipucu: seviye')
        return self.basarim.event(kind, **kw)

    def event_tips(self, now=None):
        """Süren harita etkinliklerinin açıklaması dönemde bir kez (ipucu.py; NormalTipsCommand mesaj kutusu)."""
        per = lambda k: (TK.period(k, now) or (0,))[0]
        msgs = self.ipucu.event_tips(ETH.specs(now), per)
        if msgs:
            self.send(msgs, 'etkinlik bildirimi')

    def quest_event(self, kind, **kw):
        """Dünyanın görev olayları: görevler ve Pass görevleri (öldürme Pass'lere başarım olayından gider)."""
        if kind in ('cargo', 'loot', 'sell', 'bonus', 'map'):
            self.pass_event(kind, **kw)
            msgs = self.ek.event(kind, kw)
            if msgs:
                self.send(msgs, 'etkinlik görevi')
        return self.gorev.event(kind, **kw)

    def quest_state_events(self):
        """Durum koşulları (Ö1): görev kabul edilince şimdiki durum bir kez değerlendirilir (çubuktaki eşya, Skylab modüllerinin
        seviyeleri), yoksa koşul ancak bir sonraki değişiklikte ilerlerdi."""
        tpl = next((m for m in SABLON.giris.get('hazir', []) if m['_m'] == 'MenuInitializationCommand'), None)
        msgs = self.gorev.event('slot_bar', **PROFIL.slot_bar_state(tpl['slotBars'] if tpl else []))
        for key, lv in self.skylab.levels().items():
            msgs += self.gorev.event('skylab', modul=key, seviye=lv)
        return msgs

    def pass_event(self, kind, **kw):
        """Season Pass, Battle Pass ve Unity ödülü görevleri (her biri iletisini kendisi gönderir)."""
        mid = PROFIL.d['konum'].get('mapId')
        for o in (self.sezon, self.bilet, self.odul):
            o.map_id = mid
            try:
                o.event(kind, **kw)
            except Exception:
                log('   Pass olayı hatası (%s %s):\n%s' % (kind, kw, traceback.format_exc()))

    def hint_msgs(self, n, f):
        """İpucu pencereleri: oyuncunun kapattıkları (HintWindowClosedRequest, profilde ipuclari_kapali) girişte yeniden açılmaz,
        ipucu arşivinin listesine eklenir (canlı deneme 2026-10-17: "New Employee Orientation" her girişte açılıyordu)."""
        closed = PROFIL.d.get('ipuclari_kapali', [])
        if n == 'HintWindowAddComand':
            return [] if (f.get('window') or {}).get('content') in closed else [(n, f)]
        have = [w.get('content') for w in f.get('windows', [])]
        return [(n, dict(f, windows=list(f.get('windows', [])) + [{'_': 'HintWindowModule', 'content': c} for c in closed
                                                                  if c not in have]))]

    def play_time(self):
        """Bağlı kalınan süre profilde (oynama_sn): pilot kartının "Player activity: … hours" satırı (canlı test H28)."""
        now = time.time()
        start = getattr(self, 'play_start', None) or now
        self.play_start = now
        with PROFIL.lock:
            PROFIL.d['oynama_sn'] = PROFIL.d.get('oynama_sn', 0) + max(0, now - start)

    def rename(self, name):
        """Pilot adını değiştir (tek oyunculu: ücretsiz; adı yalnız oyuncu kullanıyor). Yeni ad harita değişiminde gemide görünür
        (istemcinin NameChangeCommand işleyicisi yok). Geçersiz ad: InternalPilotBioUpdateResultsCommand success=False."""
        name = str(name or '').strip()
        ok = NAME_MIN <= len(name) <= NAME_MAX and '|' not in name and name.isprintable()
        if ok:
            with PROFIL.lock:
                PROFIL.d['pilot']['userName'] = name
                PROFIL.dirty = True
            log('   pilot adı: %s' % name)
        else:
            log('   pilot adı değişmedi: %r' % name)
        return ('InternalPilotBioUpdateResultsCommand', {'success': ok, 'baseStackCommand': None})

    def pilot_bio(self, resp):
        """InternalPilotBioRequest: kayıttaki profil kartı + oyuncunun kaydettiği bilgiler (InternalPilotBioUpdateRequest)."""
        bio = PROFIL.d.get('pilot_bio', {})
        self.play_time()
        k = PROFIL.d.get('klan') or {}                                  # tek kişilik klan (klan.py)
        rank = {'rank': PROFIL.d['pilot'].get('dailyRank', 1),            # pilot kartındaki rütbe (sayı)
                'playTime': int(PROFIL.d.get('oynama_sn', 0) // 3600),     # saat
                'userName': PROFIL.d['pilot'].get('userName', ''),          # kayıttaki ad değil, profilinki
                'userId': PROFIL.user_id, 'registrationDate': PROFIL.d.get('olusturma', '') + '.0',    # kayıttaki hesabınki değil
                'ranking': 1,                                               # Hall of Fame'de tek oyuncu (rutbe.hof_top)
                'clanName': k.get('ad', ''), 'clanRank': k.get('sira', 0) if k else 0, 'clanMemberCount': 1 if k else 0}
        return [(n, dict(f, **{k: v for k, v in dict(bio, **rank).items() if k in f})) if n == 'InternalPilotBioUserProfileCommand'
                else (n, f) for n, f in resp]

    def send(self, msgs, note=None, quiet=False):
        msgs = INV.client_filter(msgs)                # istemcinin envanter dizinini kıran eşya güncellemeleri (H134)
        w = getattr(self, 'world', None)
        if w is not None and w.defer(msgs):           # dünyanın döngü adımında: dünyanın mesajlarıyla aynı sırada adım sonunda
            if note and not quiet:
                log('-> %s (%d mesaj, adım sonunda)' % (note, len(msgs)))
            elif not quiet:
                for n, f in msgs:
                    log('-> %s %s' % (n, P.fmt(f, 160)))
            return
        data = encode(msgs)
        with self.send_lock:
            self.c.sendall(data)
            if KONTROL:
                for n, f in msgs:
                    KT.IZ.add('->', n, f)
        if quiet:
            return
        if note:
            log('-> %s (%d mesaj, %d bayt)' % (note, len(msgs), len(data)))
        else:
            for n, f in msgs:
                log('-> %s %s' % (n, P.fmt(f, 160)))

    def start_world(self):
        map_id = PROFIL.d['konum']['mapId']
        self.world = World(PROFIL, lambda m: self.send(m, quiet=True), log, map_id, SABLON.station(map_id), keep_state=True,
                           test_near='--yakin-npc' in sys.argv or AY.get('yakin_npc'), on_jump=self.change_map)
        self.world.invulnerable = '--dokunulmaz' in sys.argv
        self.world.karanlik = int(map_id) in EKP.DARK_MAPS           # Trial of Terrors: el feneri
        self.world.quick_buy = self.magaza.quick_buy_msgs
        self.world.auto_buy = self.magaza.auto_buy                  # otomatik alım CPU'ları (ekstra.py)
        self.world.auto_buy_fail = self.magaza.auto_buy_fail
        self.world.auto_lab = self.magaza.auto_lab                  # otomatik laboratuvar CPU'ları
        self.world.money_msgs = self.magaza.money_msgs
        self.world.drone_msgs = self.magaza.drone_msgs
        self.world.quest_event = self.quest_event
        self.world.lab_msgs = lambda: [self.magaza.lab_cmd()]
        self.world.quest_list = self.gorev.list_cmd
        self.world.stats_msgs = self.magaza.apply_stats
        self.world.ore_pack = self.magaza.ore_pack
        self.world.map_msgs = lambda: SABLON.world_msgs(map_id, 'giris')
        self.world.on_home = self.respawn_home
        self.world.session_tick = self.tick                        # Assembly, Dispatch, Skylab zamanlayıcıları
        self.world.grant = self.magaza.reward                       # uzaylının ek ödülündeki ekipman (The Stinger: Caucasus)
        self.world.pet = self.pet
        self.pet.attach(self.world)
        self.world.gg_energy = self.kapilar.bonus_energy
        LAB.expire_keys(PROFIL)                                     # Frozen Labyrinth bittiyse anahtarlar silinir
        self.world.extra_gates = (self.kapilar.home_portals(map_id, SABLON.station(map_id)) +     # X-1'de hazırlanan kapılar
                                  self.ekapilar.entry_portals(map_id, SABLON.station(map_id)) +  # etkinlik kapıları
                                  LAB.portals(map_id, self.kapilar.home()) +                    # labirentin bölge portalları
                                  self.pve.portals(map_id, SABLON.station(map_id)) +              # modların kapıları (Aşama 8)
                                  self.ek.portals(map_id, SABLON.station(map_id)))                # Ö3: Fiesta Gate
        self.world.start()
        if int(map_id) in KAPI.BY_MAP:
            with self.world.lock:
                self.world.kapi = KAPI.Kosu(self.kapilar, self.world, KAPI.BY_MAP[int(map_id)])
        elif int(map_id) in EKP.BY_MAP:
            with self.world.lock:
                self.world.kapi = EKP.Kosu(self.ekapilar, self.world, EKP.BY_MAP[int(map_id)])
        elif int(map_id) in LAB.MAPS:
            with self.world.lock:
                self.world.labirent = LAB.Labirent(self.world)        # Frozen Labyrinth (labirent.py)
        with self.world.lock:
            self.pve.attach(self.world)                               # mod haritasıysa koşusu; CPU ve pencereli portallar
            self.yeni.attach(self.world)                              # N.O.V.A. (istasyonda mı), otomatik pilot (lazer menzili)
            self.sosyal.attach(self.world)                            # gemi ışınlama (istasyon, savaş, geri sayım)
            ek_msgs = self.ek.attach(self.world)                      # Ö3/Ö4'ün etkinlikleri: öldürme kancaları, harita koşuları
        if ek_msgs:
            self.world.send(ek_msgs)                                  # (önce yok sayılıyordu: Vortex'ten çıkınca HUD açık kalıyordu)
        if int(map_id) == LOW.MAP:
            with self.world.lock:
                self.world.low = LOW.Low(self.world)              # LoW (tek kişilik sürüm, low.py)
        msgs = self.quest_event('map', map=int(map_id))
        comp = H.company(map_id)
        if (comp and comp != PROFIL.d['pilot'].get('factionId')) or H.name(map_id).startswith('4-'):
            msgs += self.ipucu.show(IP.PVP_WARNING)   # başka firmanın haritası ya da 4-X: PvP uyarısı (bir kez)
        if msgs:
            self.send(msgs, 'görev: harita')
        PROFIL.ach('map', map=int(map_id))       # başarım: haritaları keşfet

    # ------------------------------------------------------------ görevler
    def quest_map(self, map_id):
        """Görevlerin işaretleri için haritanın görev vericisi ve rafinerisi."""
        g = self.gorev
        g.map_id, g.giver, g.trade = int(map_id), None, None
        for n, a in SABLON.world_msgs(map_id, 'giris'):
            if n == 'AssetCreateCommand' and a['type']['typeValue'] == H.QUEST_GIVER:
                g.giver = (a['assetId'], a['posX'], a['posY'])
            if n == 'AssetCreateCommand' and H.STATION_ASSETS.get(a['type']['typeValue']) == 'ttip_ore_trade':
                g.trade = (a['posX'], a['posY'])

    def with_quests(self, msgs):
        """Giriş demetindeki kayıtlı görev mesajları yerine profilin görevleri; kayıttaki Assembly tarif listesi, Dispatch yuvaları
        ve Uridium Bank birikimi yerine profilinkiler."""
        self.quest_map(PROFIL.d['konum']['mapId'])
        out, done, asm, passes = [], False, False, set()
        present = {n for n, f in msgs}
        for n, f in msgs:
            if n == 'DispatchSlotInfoCommand':
                out.append(self.dispatch.slot_info())
                continue
            if n == 'EventUpdateCommand':             # takvimin etkinlikleri (takvim.py)
                out.append(TK.event_cmd())
                continue
            if n in ('NpcEventInfoCommand', 'NpcEventBossInfoCommand'):    # kayıttaki Halloween göstergesi: harita etkinliği gönderir
                continue
            if n == 'DailyLoginRewardDayCommand' and self.gunluk.claimed_today():
                continue                              # bugünün ödülü alındı: takvim girişte açılmaz (menüden: DailyLoginRewardDayRequest)
            if n in ('HintWindowAddComand', 'HintWindowListInitCommand'):
                out += self.hint_msgs(n, f)           # kapatılan ipuçları yeniden açılmaz, arşive geçer
                continue
            rep = self.sosyal.login_replace(n, f)     # sohbet adresi yerel sunucuya, okunmamış posta (Aşama 10)
            if rep is not None:
                out += rep
                continue
            rep = self.yeni.login_replace(n)          # N.O.V.A. kadrosu, Evocation Chip, QFC listesi (Aşama 9): profilden
            if rep is not None:
                out += rep
                continue
            rep = self.pve.login_replace(n)           # modların göstergeleri (Eternal Black Light, Astral Ascension): profilden
            if rep is not None:
                out += rep
                continue
            rep = self.ek.login_replace(n, f)         # Ö3'ün etkinlikleri (ek_etkinlikler.py)
            if rep is not None:
                out += rep
                continue
            group = PASS_LOGIN.get(n)                 # Season Pass, Battle Pass, günlük ödüller: profilden (kayıttaki yerine)
            if group:
                if group not in passes:               # demette kalanlar (harita değişiminde ve --reklamsiz'da pencereler çıkar)
                    passes.add(group)
                    out += [m for m in {'sezon': self.sezon, 'bilet': self.bilet, 'odul': self.odul}[group].login_msgs()
                            if m[0] in present or PASS_LOGIN.get(m[0]) != group]
                continue
            code = str(f.get('message', '')).split('|')[2:3] if n == 'LegacyModule' else []
            if code and code[0] in GN.CODES:          # ganimet anahtarlarının HUD sayaçları (kayıtta hepsi 0; ganimet.py)
                out.append((n, dict(f, message=GN.key_line(PROFIL, GN.CODES[code[0]]))))
                continue
            if n == 'UnstableModulesListCommand':
                out.append(GM.list_cmd(PROFIL))
                continue
            if n == 'ShipUpgradeModuleUpdateCommand' and f.get('uid') == PROFIL.user_id:
                out.append(self.magaza.module_update())
                continue
            if n == 'UridiumBankInfoCommand':
                out.append(BANK.info_cmd(PROFIL))
                self.bank_sent = BANK.value(PROFIL)
                continue
            if n in ('QuestInitializationCommand', 'QuestListCommand'):
                if not done:
                    out += self.gorev.login_msgs()
                    done = True
                continue
            if n == 'AssemblyRecipeContentModule':
                if not asm:
                    out.append(self.assembly.content())
                    asm = True
                continue
            out.append((n, f))
        return out

    def tick(self, now):
        """Dünya döngüsünden (saniyede birkaç kez): zamanlı sistemler (Assembly üretimleri, Skylab yükseltme ve taşımaları, Uridium
        Bank birikimi, takvim)."""
        if now >= self.cal_next:
            self.cal_next = now + 30.0
            self.sezon.tick(now)                      # Season Pass: gün, hafta, sezon değişimi
            cur = TK.active(now)
            if cur != self.cal_sent:
                items = PROFIL.event_window_items()
                if self.cal_sent is not None:
                    log('   takvim: %s' % ', '.join(sorted(cur)) or '-')
                    changed = [(n, f) for n, f in items if self.win_sent.get(f['itemId']) != f['visible']]
                    self.send([TK.event_cmd(now)] + changed, quiet=True)      # menü öğesi (canlıda doğrulanacak: Ö1)
                    self.event_tips(now)
                self.win_sent = {f['itemId']: f['visible'] for n, f in items}
                self.cal_sent = cur
                BSM.set_events(achievement_groups(now))
        self.gorev.tick(now)                          # süreli görevler
        if now >= self.ek_next:
            self.ek_next = now + 1.0
            msgs = self.ek.tick(now)                  # Ö3'ün etkinlikleri: dönem sonları, zamanlı olaylar
            if msgs:
                self.send(msgs, 'etkinlik: zaman')
        if now >= self.social_next:
            self.social_next = now + 5.0
            msgs = self.sosyal.tick(now)              # müzayede: biten dönemlerde kazanılan eşyalar
            if msgs:
                self.send(msgs, 'müzayede: dönem sonu')
        self.assembly.tick(now)
        self.skylab.tick(now)
        if now >= self.bank_next:
            self.bank_next = now + 5.0
            if self.bank_sent is not None and BANK.value(PROFIL) != self.bank_sent:
                self.bank_sent = BANK.value(PROFIL)
                self.send([BANK.info_cmd(PROFIL)], quiet=True)

    def quest_reward(self, loot, n):
        cur = {'currency_credits': 'kredi', 'currency_uridium': 'uridyum', 'currency_experience': 'ep', 'currency_honour': 'onur'}
        if loot in cur:
            n = AY.miktar(cur[loot], n)                    # panelin ödül çarpanları
            tot = PROFIL.gain(neden='quest_won', **{cur[loot]: n})
            return self.world.reward_msgs(tot, **{cur[loot]: n}) if self.world else []
        return self.magaza.prize(loot, n)                  # eşya ödülü: panelin mod/görev ödülü çarpanı

    def respawn_home(self):
        """İstasyonsuz haritada istasyonda tamir: firmanın ana haritasında (X-1) istasyonda doğ (gerçek oyundaki gibi)."""
        dest = HOME_MAP.get(PROFIL.d['pilot'].get('factionId'), 5)
        st = SABLON.station(dest)
        self.change_map(dest, None, pos=(st['posX'], st['posY']) if st else None)

    def revive_on_login(self):
        """Gemi yok edilmişken oyundan çıkılmışsa: istasyonda ücretsiz tamir (gerçek oyunda çıkıştan sonra portalda ve yerinde tamir
        seçenekleri kalkar, istemcinin ttip_killscreen_logout_1 metni)."""
        g = PROFIL.d['gemi']
        if g.get('hitPoints', 1) > 0:
            return
        k = PROFIL.d['konum']
        st = SABLON.station(k['mapId'])
        if not st:
            k['mapId'] = HOME_MAP.get(PROFIL.d['pilot'].get('factionId'), 5)
            st = SABLON.station(k['mapId'])
        if st:
            k.update(x=st['posX'], y=st['posY'])
        k.pop('portalda', None)
        PROFIL.set_hull(hp=g.get('hitMax', 1), shield=g.get('shieldMax', 0))
        log('   gemi yok edilmiş hâlde çıkılmıştı: %s istasyonunda tamir edildi' % H.name(k['mapId']))

    def change_map(self, dest, gate, pos=None):
        """Portal atlaması (kayıttaki akış): eski haritayı temizle, JumpToServerCommand + yeni haritanın giriş demeti.
        pos verilirse oraya iner (yeniden doğma); verilmezse hedefteki geri dönüş portalının yanına."""
        if gate:
            PROFIL.ach('jump')                   # başarım: portal atlamaları
        if gate and gate.get('etkinlik_kapisi'):
            self.ekapilar.enter(gate['kapi'])    # etkinlik kapısının girişi: kapı kurulur (canlar, dalga sırası, süre)
        self.pve.on_jump(gate)                   # Astral'ın çıkışı: oyuncunun donanımı geri
        with self.state_lock:
            old = PROFIL.d['konum']['mapId']
            msgs = SABLON.asset_removes(old)
            if self.world:
                msgs = self.world.cleanup_msgs() + msgs
                self.world.stop()
                self.world = None
            self.pet.attach(None)        # etkinse yeni haritada yeniden çıkar
            if pos == 'istasyon':                        # atlama CPU'su: hedefin istasyonuna (yoksa portalın yanına)
                st = SABLON.station(dest)
                pos = (st['posX'], st['posY']) if st else None
            pos = pos or (gate or {}).get('varis')      # kapı portalları: kapı haritasının ortasına / X-1'de kapının yanına
            x, y = pos or H.arrival(old, dest)
            PROFIL.d['konum'].update(mapId=dest, x=x, y=y, portalda=pos is None)
            PROFIL.dirty = True
            save_profile()
            self.send(msgs + [('JumpToServerCommand', {})], quiet=True)
            self.map_pending = True      # giriş demetinden önce: istemcinin ReadyRequest'i hemen gelse de kaçmaz
            RT.daily_rank(PROFIL)        # gün değiştiyse rütbe (istemci yalnız ShipInitializationCommand'dan okur)
            self.send(self.with_quests(login_batch('giris', first=False)),
                      'harita değişimi: %s -> %s, giriş demeti' % (H.name(old), H.name(dest)))
            PROFIL.d['konum'].pop('portalda', None)

    def on_packet(self, name, mid, f, err):
        if name == 'LoginRequest':
            P.secrets_of(f, self.secrets)
        if name not in UNLOGGED:
            log('<- %s(%s) %s%s' % (name, mid, P.fmt(P.redact(f, self.secrets), 300), ' [HATA %s]' % err if err else ''))
        w = self.world
        if name == 'VersionRequest':
            self.send([('VersionCommand', {'version': f['version'], 'equal': True})])
        elif name == 'LoginRequest':
            self.revive_on_login()
            RT.daily_rank(PROFIL)                     # günlük rütbe (ShipInitializationCommand.dailyRank)
            self.send(self.with_quests(login_batch('giris')), 'giriş demeti')
            self.map_pending = True
        elif name == 'ReadyRequest' and (self.map_pending or (w and w.reload_pending)):
            with self.state_lock:      # dünyaya kilit dışında dokun (harita değişimi dünya iş parçacığından bu kilidi alır)
                self.map_pending = False
                start = self.world is None
                self.ready_n += 1
            # Restabilize sekmesinin listesi: kayıtta girişten sonra ve envanter değişince ayrıca geliyor, giriş demetlerinde yok;
            # yalnız demetteki kaydın yerine konduğu için hiç gitmiyordu, sekme "No Items" diyordu (canlı test H69)
            unstable = [GM.list_cmd(PROFIL)]
            self.send(login_batch('hazir') + self.magaza.login_msgs() + self.pet.login_msgs() + self.basarim.title_msgs()
                      + self.yeni.login_msgs() + unstable + self.ek.login_msgs(), 'hazır demeti')
            if start:
                self.start_world()
                self.basarim.sync()              # seviye, P.E.T. seviyesi, takılı eşyalar (önceden ulaşılanlar da sayılır)
                self.pass_event('login')         # "oyuna gir" görevleri (Unity ödülü; kayıt: girişten hemen sonra biter)
                self.pass_event('level', deger=PROFIL.d['pilot'].get('level', 1))
                self.event_tips()                # süren etkinliğin açıklaması (dönemde bir kez)
            else:
                self.world.resend()
            if self.ready_n > 1:                 # harita yüklendi (portal, ışınlama, yeniden doğma): istemci menüyü yeniden kuruyor
                self.ek.on_ready()               # (Urgent Missions'ın simgesi, acil_gorevler.py)
            self.pet.on_ready()
        elif name == 'KeepAlive':
            self.send([('StayinAlive', {})], quiet=True)
        elif name == 'MoveRequest':
            log('<- MoveRequest konum=(%d,%d) hedef=(%d,%d)' % (f['positionX'], f['positionY'], f['targetX'], f['targetY']))
            PROFIL.apply(name, f)
            if w:
                w.on_move(f)
            # yanıt yok: gerçek sunucu oyuncunun kendi hareketine MoveCommand göndermiyor (kayıt: 876 isteğe 0). Gönderilen
            # MoveCommand istemcinin "hedefe varınca" işini (cevhere varınca HarvestRequest) kesiyordu.
        elif name == 'AttackAbortLaserRequest' and w:
            w.laser_stop()
        elif name == 'JumpRequest':
            if not (w and w.jump(f)):
                log('   atlama yok: yakında portal değil')
        elif name == 'QuestAcceptRequest':
            if w and not w.near_giver:
                # görev ancak görev vericinin (Mission Control) yanında alınır; istemcinin metni "Fly to Mission Control to see if
                # there are any missions for you."
                log('   görev alınamadı: görev vericiden uzakta (%s)' % f.get('questId'))
                self.send([legacy('0|A|STM|msg_maybe_quest_at_nyx'), self.gorev.list_cmd()], 'görev: uzak')
            else:
                self.send(self.gorev.accept(f.get('questId')) + self.quest_state_events(), 'görev: kabul')
        elif name == 'QuestCancelRequest':
            self.send(self.gorev.cancel(f.get('questId')), 'görev: iptal')
        elif name == 'QuestInfoRequest':
            self.send(self.gorev.info(f.get('questId')), quiet=True)
        elif name == 'QuestPrivilegeRequest':
            self.send([('QuestPrivilegeCommand', {'questId': f.get('questId', 0)})], quiet=True)
        elif name in ('QuestSettingsRequest', 'QuestListRequest'):
            if name == 'QuestSettingsRequest':
                PROFIL.apply(name, f)                 # görev penceresinin süzgeci profilde kalsın
            self.send([self.gorev.list_cmd()], quiet=True)
        elif name == 'QuestGiverApproachedRequest':
            msgs = self.gorev.event('giver') if w and w.near_giver == f.get('questGiverId') else []
            self.send(msgs or [self.gorev.list_cmd()], 'görev verici')
        elif name == 'TradeRequest' and w:
            self.send([w.trade_info()], 'rafineri: fiyatlar')
        elif name == 'KillScreenRepairRequest' and w:
            w.kill_screen_repair(f)
        elif name == 'AchievementListRequest':
            self.send(self.basarim.request(f), 'başarımlar')
        elif name == 'SkillTreeListRequest':
            self.send([self.yetenek.list_cmd()], 'yetenek ağacı')
        elif name == 'ConvertResearchPointsRequest':
            self.send(self.yetenek.convert(), 'yetenek ağacı: pilot puanı')
        elif name == 'UpLevelSkillTreeRequest':
            self.send(self.yetenek.up_level(f), 'yetenek ağacı: seviye')
        elif name == 'ResetSkillTreeRequest':
            self.send(self.yetenek.reset(), 'yetenek ağacı: sıfırlama')
        elif name == 'DailyLoginRewardDayRequest':
            self.send([self.gunluk.info_cmd()], 'günlük giriş: bilgi')
        elif name == 'DailyLoginClaimTodayRequest':
            self.send(self.gunluk.claim(), 'günlük giriş: ödül')
        elif name == 'GalaxyGateBuilderInfoRequest':
            self.send([self.kapilar.info_cmd()], 'kapı üreticisi: bilgi')
        elif name == 'GalaxyGateBuilderGetGatePartsRequest':
            self.send([self.kapilar.parts_cmd(f)], quiet=True)
        elif name == 'GalaxyGateBuilderMultiEnergyRequest':
            self.send(self.kapilar.spin(f), 'kapı üreticisi: çekiliş')
        elif name == 'GalaxyGateBuilderSetupGateRequest':
            self.send(self.kapilar.setup(f), 'kapı üreticisi: hazırlık')
        elif name == 'GalaxyGateBuilderBuyLifeRequest':
            self.send(self.kapilar.buy_life(f), 'kapı üreticisi: can')
        elif name == 'GalaxyGateBuilderSaveSpinAmountRequest':
            self.kapilar.save_spin(f)
        elif name == 'PetRequest':
            self.pet.request(f)
        elif name == 'PetGearActivationRequest':
            self.pet.gear_request(f)
        elif name == 'MapAssetActivationRequest':
            if self.cbs.handles(name, f):                # Clan Battle Station asteroidi/istasyonu (Ö5): pencere verisi
                self.send(self.cbs.handle(name, f), 'CBS: pencere')
            # portal için ardından JumpRequest gelir
        elif name == 'HangarShipActivateShipRequest':
            # oyundaki gibi yalnız istasyonda; gemi değişince istemci yeni gemiyle haritayı yeniden yükler (yeniden doğma gibi)
            msgs, changed = self.magaza.activate(f, in_station=w.in_station() if w else True)
            self.send(msgs, 'hangar: gemi etkinleştirme')
            if changed and w:
                w.reload_ship()
        elif name == 'HangarShipChangeShipModelRequest':
            msgs, reload = self.magaza.change_model(f)
            self.send(msgs, 'hangar: tasarım')
            if reload and w:
                w.reload_ship()      # yeni görünümle ShipInitializationCommand (istemci haritayı yeniden yükler)
        elif name == 'LegacyModule':                  # eski metin protokolü (eski_protokol.py)
            key, parts = legacy_parse(f)
            if key == 'S|CFG' and len(parts) > 2:
                msgs = self.magaza.switch_config(parts[2])
                if msgs:
                    self.send(msgs, 'config geçişi')
            elif key == 'i' and len(parts) > 1 and parts[1].isdigit():
                if w:                                 # istemci bilmediği bir kimliği soruyor (kayıt: gerçek sunucu yeniden gönderir)
                    w.info_request(int(parts[1]))
            elif key == 'JCPU' and SE.has_ajp(PROFIL):  # gelişmiş atlama CPU'su (AJP-01): uzay haritasının atlama paneli
                if len(parts) > 1 and parts[1] == 'GET':
                    self.send([SE.jcpu_list(PROFIL), SE.vouchers_msg(PROFIL)], 'gelişmiş atlama listesi')
                elif w:
                    with w.lock:
                        w.items.jcpu(parts)
            elif key == 'XCP' and len(parts) > 1 and parts[1].isdigit() and w:
                with w.lock:                          # 5-2 tüccarında Palladium -> kapı enerjisi: istemci "XCP|<adet>" gönderiyor
                    w.trade_palladium(int(parts[1]))  # (canlı deneme 2026-10-17; TradeSellOreRequest gelmiyor)
            elif key in ('LF', 'JCPU'):
                pass                                  # her girişte LF|c, JCPU|GET; gerçek sunucu da yanıt vermiyor (kayıt)
            else:
                log('   yanıtsız: LegacyModule %s' % key)
        elif name == 'UIButtonTriggerRequest':
            item = f.get('itemId')
            self.pencereler.opened(item)
            if item == 'logout':
                self.logout_start()
            else:                                     # pencere açıldı bildirimi (sosyal.py): gemi ışınlama penceresi
                resp = self.sosyal.window(item) + self.ek.window(item)       # Ö3: Pursuit of Prestige penceresi …
                if resp:
                    self.send(resp, 'pencere: %s' % item)
        elif name == 'HangarShipAutoBuyCpuAmmoRequest':   # hangarda otomatik alım CPU'suna cephane seçimi
            self.send(self.magaza.auto_buy_ammo(f), 'otomatik alım cephanesi')
        elif name == 'HallOfFameTopRequest':
            self.send(RT.hof_top(PROFIL, f), 'Hall of Fame: %s' % f.get('type'))
        elif name == 'HallOfFamePagesRequest':
            self.send(RT.hof_pages(PROFIL, f), 'Hall of Fame sayfası')
        elif name == 'HallOfFameDataListRequest':
            self.send(RT.hof_events(PROFIL, f), 'Hall of Fame etkinlikleri')
        elif name == 'LogbookDataListRequest':
            self.send(RT.logbook(PROFIL, f), 'seyir defteri')
        elif name == 'BalanceInfoListRequest':
            self.send(RT.balance(PROFIL, f), 'hesap geçmişi')
        elif name == 'LogoutCancelRequest':
            self.logout_cancel()
        elif name == 'HintWindowClosedRequest':      # gerçek sunucu yanıt vermiyor (kayıt); kapatılan ipucu bir daha açılmasın
            c = (f.get('closedWindow') or {}).get('content')
            if c is not None and not f.get('wasOpenedFromArchive'):
                with PROFIL.lock:
                    lst = PROFIL.d.setdefault('ipuclari_kapali', [])
                    if c not in lst:
                        lst.append(c)
                        PROFIL.dirty = True
        elif name == 'InternalPilotBioRequest':
            self.send(self.pilot_bio(SABLON.yanit(name, f) or []), 'pilot kartı')
        elif name == 'InternalPilotBioUpdateRequest':
            with PROFIL.lock:
                old = PROFIL.d.get('pilot_bio', {})
                PROFIL.d['pilot_bio'] = dict({k: v for k, v in f.items() if k not in ('_', 'userId')},
                                             **({'statusMessage': old['statusMessage']} if 'statusMessage' in old else {}))
                PROFIL.dirty = True
            self.send([('InternalPilotBioUpdateResultsCommand', {'success': True, 'baseStackCommand': None})], 'pilot kartı: kayıt')
        elif name == 'InternalPilotBioUpdateStatusRequest':          # pilot kartındaki durum yazısı (Ö1; UIPilotSheetSystem)
            with PROFIL.lock:
                PROFIL.d.setdefault('pilot_bio', {})['statusMessage'] = str(f.get('statusMessage') or '')[:STATUS_MAX]
                PROFIL.dirty = True
            self.send([('InternalPilotBioUpdateResultsCommand', {'success': True, 'baseStackCommand': None})], 'pilot kartı: durum')
        elif name == 'InternalPilotBioUpdateUserNameRequest':        # profil düzenlemede ad değiştirme (Ö1; UIEditProfileSystem)
            self.send([self.rename(f.get('userName'))], 'pilot kartı: ad')
        elif name == 'GroupInvitationBlockToggleRequest':
            with PROFIL.lock:                         # kayıt: her istekte açılıp kapanır
                PROFIL.d['davet_engeli'] = not PROFIL.d.get('davet_engeli', False)
                PROFIL.dirty = True
            self.send([('InvitationBlockModule', {'active': PROFIL.d['davet_engeli']})], 'grup daveti engeli')
        elif name in SILENT:
            pass
        elif name.startswith(('Assembly', 'Disassembly', 'Dispatch', 'Skylab')):
            sysm = self.assembly if name.startswith(('Assembly', 'Disassembly')) else self.dispatch if name.startswith('Dispatch') \
                else self.skylab
            resp = sysm.handle(name, f)
            if resp is None:
                log('   yanıtsız: %s' % name)
            elif resp:
                self.send(resp, '%s: %s' % (name.split('Request')[0], name))
        elif name.startswith(('SeasonPass', 'BattlePass')) or name in GOD_REQUESTS:
            sysm = self.sezon if name.startswith('SeasonPass') else self.bilet if name.startswith('BattlePass') else self.odul
            resp = sysm.handle(name, f)
            if resp is None:
                log('   yanıtsız: %s' % name)
            elif resp:
                self.send(resp, name.split('Request')[0])
        elif name.startswith('UnstableModule') or name == 'RerollWindowSettingsRequest':
            resp = self.moduller.handle(name, f)
            if resp:
                self.send(resp, 'Restabilize: %s' % name)
        elif name == 'RankRewardRequest' and SR.reward(f) is not None:     # sıralama ödül tabloları (Ö1; siralama.py)
            self.send(SR.reward(f), 'sıralama ödülleri')
        elif name in GMK.REQUESTS:                                          # GM konsolu (Ö2; gm_konsol.py)
            self.send(self.gm.handle(name, f), 'GM konsolu: %s' % (f.get('name') or name))
        elif name == 'EvoucherHistoryListRequest':                          # kupon penceresinin geçmişi: yerelde kod çözümü yok (Ö1)
            self.send([('EvoucherHistoryListCommand', {'list': []})], 'kupon geçmişi')
        elif name == 'UridiumBankClaimRequest':
            before = PROFIL.d['pilot'].get('uridium', 0)
            self.send(BANK.claim(PROFIL, self.magaza.money_msgs, log), 'Uridium Bank')
            self.bank_sent = BANK.value(PROFIL)
            if PROFIL.d['pilot'].get('uridium', 0) > before:
                self.pass_event('recharge')                # tek oyunculu: Unity ödülünün "yükleme" görevi (gerçek oyunda ödeme)
        elif self.magaza.handles(name, f):
            resp = self.magaza.handle(name, f)
            if resp is None:
                resp = SABLON.yanit(name, f)
            if resp:
                self.send(resp, 'mağaza/hangar: %s' % name)
            if w and name == 'HangarShipMoveItemsRequest' and w.repairing and not w.repair_rate():
                w.stop_repair()          # onarım robotu çıkarıldı
            if name == 'HangarShipMoveItemsRequest':
                PROFIL.ach('sync')       # başarım: takılı eşyalar (Champion/Beacon tasarımı)
        elif name == 'SlotBarConfigSetRequest':
            tpl = next((m for m in SABLON.giris.get('hazir', []) if m['_m'] == 'MenuInitializationCommand'), None)
            if tpl and PROFIL.slot_bar_set(f, tpl['slotBars']):
                self.send([('MenuInitializationCommand', PROFIL.patch_template('MenuInitializationCommand', tpl))]
                          + self.gorev.event('slot_bar', **PROFIL.slot_bar_state(tpl['slotBars'])), 'kısayol çubuğu')
        elif name in PVM.REQUESTS:
            self.send(self.pve.handle(name, f), 'mod: %s' % name)      # Aşama 8'in modları (pve_modlari.py)
        elif name in SO.REQUESTS:
            resp = self.sosyal.handle(name, f, time.time())             # Aşama 10: sosyal bölüm (sosyal.py)
            if resp:
                self.send(resp, 'sosyal: %s' % name)
        elif name in YS.REQUESTS:
            resp = self.yeni.handle(name, f)                           # Aşama 9'un sistemleri (yeni_sistemler.py)
            if resp:
                self.send(resp, 'yeni sistem: %s' % name)
        elif self.ek.handles(name):
            resp = self.ek.handle(name, f)                             # Ö3'ün etkinlikleri (ek_etkinlikler.py)
            if resp:
                self.send(resp, 'etkinlik: %s' % name)
        elif name in WORLD_REQUESTS and w:
            getattr(w, WORLD_REQUESTS[name])(f)
        elif PROFIL.apply(name, f):
            log('   profile yazıldı: %s' % name)
            if name == 'UIWindowUpdateRequest':
                if f.get('maximized'):
                    self.pencereler.opened(f.get('itemId'))
                resp = self.ek.window_update(f)        # pencere açıldı/kapandı (UIButtonTriggerRequest göndermeyenler)
                if resp:
                    self.send(resp, 'pencere: %s' % f.get('itemId'))
        else:
            resp = no_popups(SABLON.yanit(name, f) or [])
            if resp:
                self.send(resp, 'kayıtlı yanıt: %s' % name)
            elif name != 'ReadyRequest':
                log('   yanıtsız: %s' % name)

    def run(self):
        log('connect %s' % (self.addr,))
        fr = P.Framer(client_side=True)
        last_save = time.time()
        try:
            while True:
                d = self.c.recv(65536)
                if not d:
                    break
                for pkt in fr.feed(d):
                    mid, name, f, left, err = P.decode_message(pkt)
                    if KONTROL:
                        KT.IZ.add('<-', name, f)
                    with self.packet_lock:
                        try:                      # bir isteğin hatası oturumu düşürmesin: yığın izi günlüğe, istemci bağlı kalır
                            self.on_packet(name, mid, f, err)
                        except ConnectionError:
                            raise
                        except Exception:
                            log('   istek hatası (%s):\n%s' % (name, traceback.format_exc()))
                    if time.time() - last_save > 10:
                        last_save = time.time()
                        self.play_time()
                        save_profile()
        except ConnectionError as e:
            log('   bağlantı kapandı: %r' % e)
        except Exception:
            log('error\n%s' % traceback.format_exc())
        if self.world:
            self.world.stop()
        self.play_time()
        save_profile()
        log('disconnect %s' % (self.addr,))
        global CURRENT
        if CURRENT is self:
            CURRENT = None

    def payment_click(self):
        """İstemcinin ödeme düğmesi (odeme.Dinleyici: 127.0.0.1:443'e bağlandı): mağaza Extras'ta açılır, ürün ekranda yazılır."""
        msg = self.pencereler.offline()
        if msg:                                       # kupon kodu ya da resim yükleme: mağaza açılmaz
            log('   443: ödeme dışı istek -> %s' % msg)
            with self.packet_lock:
                self.send([KAPI.screen(msg)], '443: ekran metni')
            return
        item = self.pencereler.guess()
        log('   ödeme düğmesi -> mağaza (son pencere: %s)' % (item or '-'))
        with self.packet_lock:
            self.send(OD.redirect(self.magaza, item), 'ödeme düğmesi: mağaza')

    def inject(self, name, f):
        """Kontrol kanalı: istemci göndermiş gibi bir istek (izde '<=')."""
        KT.IZ.add('<=', name, f)
        log('<= (kontrol) %s' % name)
        with self.packet_lock:
            self.on_packet(name, -1, f, None)


def handle(c, addr):
    Session(c, addr).run()


def autosave():
    """Profil 10 sn'de bir diske (değiştiyse). Oturum yalnız istemciden paket gelince kaydediyordu: boşta yapılan son değişiklik
    (pencere kapatma, kontrol kanalı, NPC ödülü) sunucu penceresi kapatılırsa kayboluyordu (canlı test H57).
    --durdur=<dosya> (panel): dosya belirince oynama süresi ve profil kaydedilir, sunucu kapanır (zorla kapatmada son 10 sn gitmesin)."""
    last = time.time()
    while True:
        time.sleep(0.5 if DURDUR else 10)
        if DURDUR and os.path.exists(DURDUR):
            stop_gracefully()
        if time.time() - last < 10:
            continue
        last = time.time()
        save_profile()                    # dosya kilitliyse bir sonraki turda


def stop_gracefully():
    """Panelin durdurma isteği: oturumun oynama süresi ve profil kaydedilir, süreç çıkar."""
    try:
        if CURRENT is not None:
            CURRENT.play_time()
        PROFIL.save(force=True)
        log('panel: durdurma isteği, profil kaydedildi, sunucu kapanıyor')
    except Exception as e:
        log('panel: durdururken kayıt hatası %r' % e)
    try:
        os.remove(DURDUR)
    except OSError:
        pass
    os._exit(0)


def main():
    global SOHBET
    P.uyari = log
    AY.configure()              # oyun ayarları (panel): --ayarlar=<yol> ya da save/ayarlar.json; değişince kendiliğinden okunur
    log('ayarlar: %s | %s' % (AY._state['yol'], ', '.join('%s %s' % x for x in AY.summary()) or 'varsayılan'))
    SOHBET = SH.Sohbet(log)
    SOHBET.start()                # yerel sohbet (7771); istemci girişteki ChatParamCommand ile buraya bağlanır
    threading.Thread(target=autosave, daemon=True).start()
    CD.start(sys.modules[__name__], LOG_DIR, log)     # panelin canlı durum sayfası (<günlükler>/canli_durum.json)
    if KONTROL:
        KT.Kontrol(sys.modules[__name__]).start()
        SOHBET.iz = KT.sohbet_iz          # sohbet çerçeveleri de izde ("Sohbet:<tür>")
    OD.Dinleyici(lambda: CURRENT and CURRENT.payment_click(), log).start()     # ödeme düğmeleri -> mağaza (127.0.0.1:443)
    s = socket.socket(); s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind(('127.0.0.1', 8081)); s.listen(5)
    log('gs listening 8081 | profil: %s %s harita %s | şablon: %s%s' % (
        PROFIL.d['pilot'].get('userName'), PROFIL.d['gemi'].get('typeId'), PROFIL.d['konum']['mapId'],
        SABLON.giris.get('kaynak', 'yok'), ' | profil dosyası: %s' % PROFIL.path if PROFIL_YOLU else ''))
    while True:
        c, addr = s.accept()
        threading.Thread(target=handle, args=(c, addr), daemon=True).start()


if __name__ == '__main__':
    main()
