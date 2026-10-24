"""Harita dünyası (bağlantı başına bir dünya): NPC'ler, hareket, yapay zekâ, lazer/roket savaşı, ölüm, ödüller, kargo ve bonus
kutuları. Arkadaş sunucusunda aynı normal haritadaki oyuncuların dünyaları uzaylıları, kutuları ve cevherleri paylaşır (ortak_harita.py).

Mesaj akışları gerçek sunucu kaydından (belgeler/istemci/kayit_analizi.md, "Oyun içi kalıplar"):
  seçme   ShipSelectRequest -> ShipSelectionCommand (vuruşlardan sonra güncellenir)
  lazer   AttackLaserRequest -> her ~1,1 sn AttackLaserRunCommand + AttackHitCommand(attackType 1) | AttackMissedCommand
  roket   AttackRocketRequest -> "0|v|<saldıran>|<hedef>|H|1|0|0" + 4 sn bekleme, ~0,8 sn sonra AttackHitCommand(attackType 0)
  ölüm    AttackHitCommand(hp 0) + ShipDestroyedCommand + ShipDeselectionCommand + ShipRemoveCommand
  ödül    "0|LM|ST|EP|<kazanç>|<toplam>|<seviye>", HON, CRE (+ InventoryItemUpdatedCommand), URI
  kutu    AddBoxCommand(FROM_SHIP) ölüm yerinde (CandyCargo etkinliğinde, Halloween, CANDY_CARGO: aynı kutu, şekerli görünüm; kayıt);
          CollectBoxRequest -> RemoveCollectableCommand(collected) + cevher günlüğü. Etkinliğin 'kargo_yok' uzaylıları düşürmez
  cevher  AddOreCommand (kümeler hâlinde); HarvestRequest -> ~0,5 sn sonra InventoryItemPack + MapEventOreCommand(1) +
          AttributeOreCountUpdateCommand + RemoveCollectableCommand(collected); kargo doluysa MapEventOreCommand(2)
  satış   istasyon rafinerisine yaklaşınca MapAssetActionAvailableCommand; TradeRequest -> OreTradeInfoCommand;
          TradeSellOreRequest -> AttributeOreCountUpdateCommand + "0|LM|ST|CRE|kazanç|toplam" + kredi
  P.E.T.  pet.py (dünya döngüsünden tick; NPC atışları bazen P.E.T.'e; P.E.T. vuruşları ve topladığı kutular burada işlenir)
  kapılar kapi.py (X-1'deki kapı portalları add_gate ile; kapı haritasında dalgalar dünya döngüsünden, kapı NPC'leri yeniden doğmaz)
  oyuncu  ShipDestroyedCommand + KillScreenPostCommand (ölüm ekranı; kayıtta yok, alanlar ve seçenek türleri istemcinin kodundan)
          KillScreenRepairRequest -> ShipInitializationCommand (istasyonda / portalda / yerinde tamir)
Sayısal değerler data/npc.json'dan, tamir fiyatları data/esyalar.json'dan (olum_ekrani).
"""
import json, math, os, random, re, string, threading, time, traceback, weakref

import harita as H
import booster as BOOSTER
import gemi_yetenek as GY
import durum as DURUM
import ekstra as EK
import lazer as LAZER
import savas_esya as SE
import teknoloji as TK
import parcacik as PC
import rutbe as RT
import uzayli as UZ
import etkinlik_harita as ETK  # noqa: E402
import takvim as TKV          # noqa: E402
import ganimet as GN
import ayar as AY
import yukseltme as YK
import ipucu as IP
import ortak_harita as OH

HERE = os.path.dirname(os.path.abspath(__file__))
CFG = json.load(open(os.path.join(HERE, 'data', 'npc.json'), encoding='utf8'))
ESYA = json.load(open(os.path.join(HERE, 'data', 'esyalar.json'), encoding='utf8'))
SAVAS = CFG['savas']
MAP_W, MAP_H = CFG['harita_boyutu']
CREDITS_ITEM, URIDIUM_ITEM = -1908845164, -707736347      # kayıttaki InventoryItemModule.itemId değerleri
LASER_AMMO = 'ammunition_laser_lcb-10'
OLUM = ESYA['olum_ekrani']
# istemcinin KillScreenOptionTypeModule.OptionType enum'u (global-metadata.dat)
REPAIR_BASE, REPAIR_GATE, REPAIR_LOCATION, REPAIR_RAID_GATE = 1, 2, 3, 7
# seçenek -> (ayrıntı metni, ipucu, düğme): istemcinin çeviri anahtarları (flashres)
REPAIR_TEXTS = {REPAIR_BASE: ('desc_killscreen_free_repair_cause_unknown', 'ttip_killscreen_basic_repair', 'btn_killscreen_repair_for_free'),
                REPAIR_GATE: ('desc_killscreen_repair_gate', 'ttip_killscreen_repair_jumpgate', 'btn_killscreen_repair_for_uri'),
                REPAIR_LOCATION: ('desc_killscreen_repair_location', 'ttip_killscreen_repair_location', 'btn_killscreen_repair_for_uri'),
                REPAIR_RAID_GATE: ('desc_killscreen_free_repair_cause_hadesgate', 'ttip_killscreen_repair_hadesgate',
                                   'btn_killscreen_repair_for_free')}
COLLECT_WAIT_SN = 8            # uyarlama: tıklanan kutu, gemi bu kadar saniye içinde varırsa alınır (sunucunun gemisi hızlandırıcılarla geride kalabilir)
HADES_RESPAWN_SN = 30          # Hades'te kapı haritasında yeniden doğma süresi (wiki: canı kalan ölünce 30 sn içinde kapıda ya da X-1'de)
DESTRUCTION_NPC, DESTRUCTION_RADIATION, DESTRUCTION_MISC = 1, 2, 4       # DestructionTypeModule.DestructionCause
# 5-4'ün girişi (wiki: bir Gümüş Booty Key; anahtarın Assembly tarifi 25 Darksilver Coin, assembly.py)
KEY_COST = [('resource_booty-key-silver', 1)]
WORMHOLE_ID = H.GATE_ID_BASE + 990100        # 4-5'teki gizli solucan deliği (Cubikon Mezarlığı'na)
DRONE_LEVELS = ESYA['dron_seviyeleri']
ORE = ESYA['cevherler']
ORE_EVENT_FINISHED, ORE_EVENT_CARGO_FULL = 1, 2       # MapEventOreCommand.EventType (istemci)
TRADE_INACTIVE, TRADE_STATION, TRADE_PET, TRADE_PIRATE = 0, 1, 3, 5     # OreTradeInfoCommand.TradeType (istemci)
PALLADIUM, PIRATE_MARKET = 8, '92'          # Palladium yalnız 5-2'deki korsan tüccarında kapı enerjisine çevrilir


def ore_prices(honor):
    """Rafineri satış fiyatları: taban + onur/bölen, üst sınırlı (wiki; kayıt taban fiyatları veriyor)."""
    out = {}
    k = AY.carpan('cevher_fiyat')                    # panel: cevher satış fiyatı (pencere de bunu gösterir)
    for t, (base, div, cap) in ORE['fiyatlar'].items():
        v = min(cap, base + (int(honor // div) if div else 0))
        out[int(t)] = v if k == 1.0 else min(AY.I32, max(0, int(round(v * k))))
    return out
DRONE_POINTS = ESYA['dron_puanlari']
INVINCIBILITY = 33                             # VisualModifierCommand.modifier (istemcinin VisualModifier enum'u)
STREAK_GAP_SN = 10.0                           # seri öldürme: iki öldürme arası en çok (kill_streak)
STREAKS = [(3, 'epic_msg_killstreak_triplekill'), (6, 'epic_msg_killstreak_unstoppable'), (10, 'epic_msg_killstreak_godlike'),
           (15, 'epic_msg_killstreak_likeaboss')]
FLASHLIGHT = 62                                # el feneri: ekran kararır, geminin baktığı yön aydınlık (FlashLightEffect, etki 90)


def mod(name, **f):
    f['_'] = name
    return f


REPAIR_VOUCHERS = 1              # tamir istasyonunda bir anında onarımın kupon bedeli (uyarlama; kaynak yok)
# CombatStateCommand.combatState (istemcinin CombatStateType'ı; Ö1)
COMBAT_OUT_OF_RANGE, COMBAT_CONTINUES, COMBAT_ESCAPED = 0, 1, 2


def range_exceeded(uid, max_range, kind):
    """Menzil dışı: istemci hedefte menzil efekti gösterir (AttackRangeExceededCommand; type 0 roket, 1 lazer)."""
    return ('AttackRangeExceededCommand', {'uid': uid, 'maxRange': int(max_range), 'type': kind})


# cephane bitince otomatik geçiş sırası (sıradan cephaneler; özel cephaneye kendiliğinden geçilmez)
AUTO_AMMO = ['ammunition_laser_ucb-100', 'ammunition_laser_mcb-50', 'ammunition_laser_mcb-25', 'ammunition_laser_lcb-10']
CARGO_BOXES = ('FROM_SHIP', 'CANDY_CARGO')     # uzaylının kargo kutusu (CANDY_CARGO: Halloween'in CandyCargo'sunda, kayıt)
AUTO_REFINE = (4, 5, 6)       # otomatik arıtmanın ürünleri (laboratuvar tarifleri, bu sırayla): Prometid, Duranium, Promerium


def attack_type(v):
    return mod('AttackTypeModule', attackTypeValue=v)   # 0 roket, 1 lazer (istemcinin AttackType enum'u)


from eski_protokol import legacy, stm  # noqa: E402,F401  (eski metin protokolü: eski_protokol.py)


# başarım "lazer şovu" (LaserTypeUsage 1-6): istemcinin temel lazer cephanesi sırası (uyarlama: LCB-10 … RSB-75)
AMMO_TYPE_IDS = {'ammunition_laser_lcb-10': 1, 'ammunition_laser_mcb-25': 2, 'ammunition_laser_mcb-50': 3, 'ammunition_laser_ucb-100': 4,
                 'ammunition_laser_sab-50': 5, 'ammunition_laser_rsb-75': 6}


def loc(key, **wild):
    """İstemcinin kendi çeviri dosyasından gösterdiği metin: MessageLocalizedWildcardCommand (kayıttaki biçim: anahtar türü 5,
    %AD% yer tutucuları düz metin 0)."""
    return mod('MessageLocalizedWildcardCommand', baseKey=key, baseKeyType=mod('ReplacementTypeModule', typeValue=5),
               wildCardReplacements=[mod('MessageWildcardReplacementModule', wildcard='%%%s%%' % k, replacement=str(v),
                                         replacementType=mod('ReplacementTypeModule', typeValue=0)) for k, v in wild.items()])


class Mover:
    """Doğrusal hareket: başlangıç-bitiş ve süreden anlık konum."""

    def __init__(self, x, y):
        self.x0 = self.x1 = x
        self.y0 = self.y1 = y
        self.t0 = self.t1 = 0.0

    def pos(self, now):
        if now >= self.t1 or self.t1 <= self.t0:
            return self.x1, self.y1
        f = (now - self.t0) / (self.t1 - self.t0)
        return self.x0 + (self.x1 - self.x0) * f, self.y0 + (self.y1 - self.y0) * f

    def go(self, x, y, speed, now, start=None):
        sx, sy = start if start else self.pos(now)
        d = math.hypot(x - sx, y - sy)
        dur = d / max(speed, 1)
        self.x0, self.y0, self.x1, self.y1, self.t0, self.t1 = sx, sy, x, y, now, now + dur
        return int(dur * 1000)


class NPC:
    def __init__(self, uid, tip, x, y, dalga=False):
        self.id, self.tip, self.d = uid, tip, CFG['tipler'][tip]
        k = AY.carpan('npc_can', 'dalga' if dalga else 'harita')     # dalga: kapı ve mod dalgasının uzaylısı
        if k != 1.0 and not self.d.get('dost'):        # panelin can çarpanı: türün paylaşılan sözlüğü değil, kopyası (n.d azami değer)
            self.d = dict(self.d, hp=max(1, int(self.d['hp'] * k)), kalkan=min(AY.I32, int(self.d['kalkan'] * k)))
        self.model = self.d.get('model', tip)      # istemcinin gemi modeli (aynı modeli paylaşan türlerde tür anahtarından farklı)
        self.mover = Mover(x, y)
        self.hp, self.shield = self.d['hp'], self.d['kalkan']
        self.engaged = False
        self.gate = False                   # Galaksi Kapısı uzaylısı: yeniden doğmaz
        self.hunt = False                   # dalga uzaylısı (kapılar, modlar): oyuncunun peşini bırakmaz, kaçıp dolaşmaya gitmez
        self.flee = False                   # oyuncu güvenli bölgeye kaçtı: uzaklaş
        self.invulnerable = None            # işlev: True dönerken hasar almaz (Zeta Devourer: diğer uzaylılar yaşarken; kapi.py)
        self.next_think = time.time() + random.uniform(1, 6)
        self.next_shot = 0.0
        self.alive = True
        # kovalarken oyuncunun çevresinde kendi yeri (açı sapması, uzaklık): aynı yönden gelenler tek noktada üst üste binmesin
        self.spread = random.uniform(-0.8, 0.8)
        self.keep = random.uniform(250, 440)
        self.etki = DURUM.Etkiler()         # durum etkileri: yavaşlatma, dondurma, zehir, zayıf kalkan … (durum.py)
        self.davranis = UZ.of(self.d)       # davranış kancaları ve yetenekler (npc.json, uzayli_yetenekleri.json; uzayli.py)
        self.summoned = False               # çağrılan ya da ölünce doğan: yeniden doğmaz
        self.children = set()               # çağırdıkları (kimlik)
        self.last_hit = 0.0                 # son vurulduğu an (savaş dışı yenilenme)
        self.next_summon = 0.0
        self.next_regen = 0.0
        self.ab = {}                        # yeteneklerin durumu (uzayli.py: beklemeler, eşikler, kaybolma, hız)
        self.attackers = {}                 # saldıran -> son vuruş anı (Battleray'in öfkesi)
        self.foe = None                     # ortak haritada yapay zekâsını işleyen dünya (ortak_harita.Harita.sahipler)

    def speed(self):
        """Hızı: yeteneğin değiştirdiği (Emperor Sibelon 380) ya da türünki; panelin uzaylı hızı çarpanıyla (hareketsizler 0 kalır)."""
        v = self.ab.get('hiz') or self.d['hiz']
        k = AY.carpan('npc_hiz')
        return max(1, int(v * k)) if v > 0 and k != 1.0 else v


def extra_count(spec, chance=1.0):
    """Ek ödülün adedi: sayı, [en az, en çok] ya da {adet, olasilik} (npc.json ek_odul; tools/npc_haritalari.py). chance:
    olasılık çarpanı (PRC-B00/B01 boosterı)."""
    if isinstance(spec, dict):
        if random.random() >= spec.get('olasilik', 1) * chance:
            return 0
        spec = spec.get('adet', 1)
    if isinstance(spec, list):
        return random.randint(int(spec[0]), int(spec[1]))
    return int(spec)


def rand_hash():
    return ''.join(random.choice(string.ascii_lowercase + string.digits) for _ in range(random.randint(4, 6)))


# harita durumunun saklanması: oturumun dünyası (keep_state) haritadan çıkınca uzaylıları, kutuları, cevherleri ve bekleyen
# yeniden doğmaları burada bekler; aynı haritaya bu süre içinde dönülürse kaldığı yerden sürer (portal gidip gelerek kutu ve kapı
# enerjisi toplanamasın). Galaksi Kapısı haritaları saklanmaz (kapi.py kendi durumunu tutar).
ROKET_PAYI = 0.25               # roket beklemesinde istemciye tanınan pay (sn)
WORLD_CACHE = {}
WORLD_CACHE_SN = 600             # uyarlama: 10 dakika
WORLD_CACHE_MAX = 8


RUNNING = weakref.WeakSet()            # döngüsü çalışan dünyalar (sync için)


def sync():
    """Çalışan her dünyanın kilidini bir kez alıp bırakır: süren döngü adımı biter ve adımda biriken mesajlar gönderilmiş olur
    (gönderim toplama). Testler bir durumu bekledikten sonra mesajlara bakmadan önce çağırır."""
    for w in list(RUNNING):
        with w.lock:
            pass


class Olcum:
    """Döngü adımının süresi: son 10 sn'nin ortalaması ve en çoğu (ms), toplam adım ve yavaş adım (> 50 ms) sayısı."""
    YAVAS_MS = 50.0

    def __init__(self, pencere_sn=10.0):
        self.pencere = pencere_sn
        self.adim = 0
        self.yavas = 0
        self.son = []                       # (an, ms)

    def add(self, ms, now=None):
        now = time.time() if now is None else now
        self.adim += 1
        if ms > self.YAVAS_MS:
            self.yavas += 1
        self.son.append((now, ms))
        while self.son and self.son[0][0] < now - self.pencere:
            self.son.pop(0)

    def ozet(self):
        v = [ms for _, ms in self.son]
        return {'adim': self.adim, 'yavas': self.yavas, 'ort_ms': round(sum(v) / len(v), 2) if v else 0.0,
                'en_cok_ms': round(max(v), 2) if v else 0.0}


class World:
    @property
    def invulnerable(self):
        """Test dokunulmazlığı: --dokunulmaz seçeneği ya da panelin ayarı (oyun açıkken de değişir)."""
        return self._invulnerable or AY.get('dokunulmaz')

    @invulnerable.setter
    def invulnerable(self, v):
        self._invulnerable = bool(v)

    def __init__(self, profil, send, log, map_id, station=None, test_near=False, on_jump=None, keep_state=False, paylas=False):
        """paylas: arkadaş sunucusunda normal harita, aynı haritadaki öteki oyuncuların dünyalarıyla ortak (ortak_harita.py)."""
        self.perf = Olcum()                 # döngü adımının süresi (ms): canlı durum ve panel
        self.step_errors = {}               # döngü hatasının son satırı -> en son günlüğe yazıldığı an (step_error)
        self._batch = None                 # döngü adımı sürerken gönderilecekler (adım sonunda tek çerçevede)
        self._loop_ident = None             # döngünün iş parçacığı (defer: oturumun adım içindeki mesajları da sıraya)
        self.cbs_trade = None               # Clan Battle Station'da maden satışı: () -> fiyat çarpanı ya da None (cbs.py)
        self.asset_targets = None           # vurulabilir harita varlıkları (rakip Battle Station'ın modülleri: cbs.py): asset_pos(id)
        #                                     -> (x, y) | None, asset_select(id), asset_attackable(id) -> [] | hata, asset_hit(id, hasar)
        self.p, self.send_raw, self.log = profil, send, log
        self.map_id = str(map_id)
        # 4-4, 4-5, 5-x iki kat (npc.json "boyut"), GG Hades yarım boy (istemcinin scaleFactor'ı)
        self.map_w, self.map_h = (CFG['haritalar'].get(self.map_id) or {}).get('boyut') or H.map_size(self.map_id)
        self.station = station
        self.lock = threading.RLock()
        self.npcs = {}
        self.boxes = {}            # hash -> dict(tip, x, y, icerik, bitis)
        self.ores = {}             # hash -> dict(tip, x, y): haritadaki cevherler
        self.ore_fields = []       # cevher kümelerinin merkezleri
        self.pending = []          # bekleyen yeniden doğmalar [an, tür ('npc', 'bonus', 'ore'), değer]; harita durumuyla saklanır
        self.keep_state = keep_state
        self.assets = []           # (kimlik, x, y, ipucu): istasyonun tıklanabilir nesneleri (HQ, hangar, rafineri)
        self.asset_types = {}      # nesne kimliği -> istemcinin AssetType'ı (görev koşulu VISIT_MAP_ASSET)
        self.near_assets = None    # yakındaki nesneler (None: bir sonraki adımda hepsinin durumu gönderilir)
        self.timers = []           # (zaman, işlev)
        self.collect_wish = None   # (kutu, son an): gemi kutuya varınca alınacak kutu (collect)
        self._next_uid = OH.UID_BASE
        k = self.p.d['konum']
        self.hero = Mover(k['x'], k['y'])
        self.target = None
        self.attacking = False
        self.next_laser = 0.0
        self.ammo_ready = {}           # kendi beklemesi olan cephane (RSB-75, RCB-140: 3 sn) -> yeniden atabileceği an
        self.rocket_ready = 0.0
        self.running = False
        self.hero_dead = False
        self.reload_pending = False   # oyuncu yeniden doğunca istemci haritayı yeniden yükler
        self.test_near = test_near     # test kolaylığı: ilk 4 NPC türünden birer tane oyuncunun yakınında doğar (--yakin-npc)
        self.invulnerable = False      # test kolaylığı: vuruşlar görünür, gövde ve kalkan azalmaz (--dokunulmaz; panelde de)
        self.karanlik = False          # karanlık harita (Trial of Terrors): el feneri etkisi (oturum ayarlar; etkinlik_kapi.DARK_MAPS)
        self.gates = list(H.gates(map_id, self.p.d['pilot'].get('factionId')))   # başka haritaya giden portallar (spacemap-config.xml)
        self.extra_gates = []          # oturumun eklediği portallar (X-1'deki Galaksi Kapıları; kapi.py), girişte bildirilir
        self.kapi = None               # kapı haritasında dalgalar (kapi.Kosu)
        self.low = None                # LoW'un tek kişilik sürümü (low.Low)
        self.labirent = None           # Frozen Labyrinth haritası (labirent.Labirent)
        self.gate_fee = None           # ücretli portal (labirent: Labyrinth Key) -> (geçer mi, mesajlar)
        self.sold = False              # istasyonda cevher satıldı: ilk harekette rafineri penceresi kapanır (on_move)
        self.session_tick = None       # oturumun zamanlı sistemleri (Assembly, Dispatch, Skylab; game.Session.tick)
        self.visible = set()           # istemcinin bildiği NPC'ler (görüş mesafesi; kayıt: ~2.000 birimde gösterilir)
        self.seen_items = set()        # istemcinin bildiği kutu ve cevherler (kayıt: ~1.000 birimde)
        self.next_booster = 0.0        # booster süreleri saniyede bir
        self.radiation_since = None    # harita dışında (radyasyon) ne zamandan beri
        self.ach_next, self.ach_pos, self.ach_dist, self.ach_secs = 0.0, None, 0.0, 0     # başarım sayaçları (ach_tick)
        self.abilities = GY.Motor(self, SAVAS['lazer_menzil'])     # gemi yetenekleri (gemi_yetenek.py)
        self.items = SE.Esyalar(self)                                # mayınlar, CPU'lar, fırlatıcı, özel roketler (savas_esya.py)
        self.tech = TK.Teknoloji(self)                               # teknoloji eşyaları (teknoloji.py)
        self.parcacik = PC.Atis(self)                                # parçacık topları ve Singularity Drive (parcacik.py)
        self.alien = UZ.Yetenekler(self)                             # uzaylı yetenekleri (uzayli.py)
        self.CFG_TYPES = CFG['tipler']
        self.etkinlik = ETK.HaritaEtkinlik(self)                     # takvimin harita etkinlikleri (etkinlik_harita.py)
        self.grant = None                                             # oturum: magaza.reward (uzaylının ek ödülündeki ekipman)
        self.range_warned = None                                      # menzil dışı uyarısı gönderilen hedef (bir kez)
        self.combat_sent = (None, 0.0)                                # son savaş durumu satırı (combat_state)
        self.combat_music = False                                     # savaş müziği çalıyor mu (music_tick)
        self.streak = [0, 0.0, 0]                                     # seri öldürme: sayı, son öldürme, son duyurulan eşik
        self.kill_hooks = []                                          # uzaylı ödülünde (w, npc, x, y) -> mesajlar (Ö3: ek_etkinlikler.py)
        self.free_gate_repair = lambda: False                         # portalda ücretsiz tamir (Fever: fever.py)
        self.cinema = False                                           # sinematik kamera kilitli mi (cinematic)
        self.next_auto, self.auto_wait = 0.0, {}                       # otomatik CPU'lar (auto_tick)
        self.auto_buy = None                                          # oturum: magaza.auto_buy (ALB-X, RB-X)
        self.auto_buy_fail = None                                     # oturum: magaza.auto_buy_fail (para yetmedi metni)
        self.auto_warned = set()                                      # para yetmedi metni gösterilen cephaneler
        self.auto_lab = None                                          # oturum: magaza.auto_lab (NC-AWL/AWR/AWB/AGB)
        self.hero_etki = DURUM.Etkiler()                              # oyuncunun durum etkileri (hız, isabet; profil.mods'a)
        self.p.world_mods = self.hero_etki.mods
        self.ammo_seen = {}                                           # cephane -> son atış (başarım: 60 sn içinde türler)
        self.next_radiation = 0.0
        self.gg_energy = None          # bonus kutusundan kapı enerjisi (kapi.py)
        self.gate_lives = None         # kapıda ölünce kalan can (ölüm ekranının metni)
        self.near_gate = None
        self.gate_peace = False        # portal çevresindeki güvenli bölgede mi (BeaconCommand.inPeaceArea)
        self.entered = time.time()     # haritaya giriş (4-5'te portal DMZ'si bir süre)
        self.station_inside = None     # istasyon bölgesinde mi (BeaconCommand.inStation); None: ilk adımda gönderilir
        self.jumping = False
        self.on_jump = on_jump         # (hedef harita, portal) -> oturum harita değişimini yapar
        self.repairing = False
        self.next_repair = 0.0
        self.last_combat = 0.0         # son atış ya da alınan hasar (onarım robotu savaş dışında çalışır)
        self.next_shield = 0.0
        self.next_form_shield = 0.0    # formasyonun kalkan dolumu/erimesi (form_shield_tick)
        self.next_overdrive = 0.0      # SL-01, Prometheus: 5 sn'de bir ek hasar (lazer.py)
        self.ofke = LAZER.Ofke()       # Asmodeus Fervor
        self.artan = [1.0, 0.0]        # IDB-125: çarpan, son isabet
        self.crit = False              # son laser_damage Odysseus kritiğiydi (vuruş iletisinde strike)
        self.quick_buy = None          # para değişince kısayol çubuğundaki hızlı alım öğelerinin durumu (magaza.py)
        self.map_msgs = None           # haritanın girişteki nesneleri (istasyon, taretler): yeniden yüklemede tekrar gönderilir
        self.on_home = None            # istasyonsuz haritada istasyonda tamir: oturum firmanın ana haritasına götürür
        self.money_msgs = None         # para değişince arayüz güncellemesi (magaza.py)
        self.death_pos = None          # ölüm yeri (yerinde tamir, portalda tamir için en yakın portal)
        self.death_time = 0.0          # ölüm anı (Hades'te kapıda yeniden doğma süresi)
        self.invuln_until = 0.0        # yerinde tamirden sonra saldırı koruması (oyuncu saldırınca kalkar)
        self.drone_msgs = None         # dronlar değişince (seviye atlama) uzaydaki dron dizilimi (magaza.py)
        self.stats_msgs = None         # dron seviyesi değişince kalkan vb. yeniden hesap (magaza.apply_stats)
        self.ayar_surum, self.next_ayar = None, 0.0     # panelin ayar dosyası değişince geminin değerleri yeniden (settings_tick)
        self.ore_pack = None           # cevher sayıları değişince hangar envanteri (magaza.py)
        self.quest_event = None        # görev ilerlemesi: (olay, ...) -> mesajlar (gorev.py)
        self.lab_msgs = None           # yükseltme durumu (LabUpdateItemCommand, magaza.py)
        self.lab_clock = {2: 0.0, 3: 0.0}   # motor (hareket) ve kalkan (savaş) yükseltmesinin harcanmamış saniyeleri
        self.lab_tick = time.time()
        self.quest_list = None         # görev vericiye yaklaşınca görev listesi (gorev.py)
        self.givers = []               # görev vericiler (kimlik, x, y)
        self.near_giver = None         # yakındaki görev verici
        self.pet = None                # oturumun P.E.T.'i (pet.py)
        self.ally = None               # uzaylıların atışını alabilen dost (echoes.py: korunan/eşlik edilen gemi)
        self.portal_cpu = None         # mod kapısı CPU'su (Eternal, Astral, Immunizer; pve_modlari.py)
        self.gate_window = None        # pencereli portal (Voyagers, Trinity, Astral, Echoes): atlamak yerine pencere
        self.last_hurt = 0.0           # gemi son hasar aldığında (C-SR dişlisi hasar almıyorken onarır)
        self.rules = (CFG['haritalar'].get(self.map_id) or {})          # haritanın kuralları (npc.json; mezarlık, solucan deliği …)
        self.next_rules = 0.0
        self.next_drifter = 0.0
        self.wormhole = None           # 4-5'teki gizli solucan deliği: portal ve yer değiştireceği an
        self.boxes_taken = 0           # bu ziyarette alınan bonus kutuları (mezarlıkta değer azalır)
        self.oyuncular = {}            # istemcinin gördüğü öteki oyuncular: kimlik -> görünüm imzası (ortak harita)
        self.gorunum = None            # oturum: (x, y) -> bu kahramanın gemisi öteki oyuncuların istemcisinde (game.Session.gorunum)
        self.secim = None              # seçili öteki oyuncunun son gönderilen ShipSelectionCommand'ı (canı değişince yeniden)
        self.ates = False              # önceki adımda saldırıyor muydu (lazerin bitişi öteki oyunculara: step)
        self.grup_uyesi = lambda uid: False      # oturum: oyuncu bu kahramanın grubunda mı (grup.py; saldırı uyarısı)
        self.olum = None               # oturum: kahraman vuruldu (grup üyelerine bildirim)
        self.ortak = OH.al(self.map_id) if paylas else None     # ortak harita: kilit, uzaylılar, kutular, cevherler, doğmalar
        self.ortak_birakildi = False
        self.durdu = False             # stop bir kez (oturum yeniden bağlanınca girişte de durdurulur, game.Session.devret)
        self.cache_key = self.map_id   # WORLD_CACHE anahtarı (arkadaş sunucusunda oyuncunun kendi kopyası oyuncuya göre; game.start_world)
        if self.ortak:
            o = self.ortak
            self.lock = o.lock
            self.npcs, self.boxes, self.ores, self.pending, self.ore_fields = o.npcs, o.boxes, o.ores, o.pending, o.ore_fields
            if o.etkinlik is None:
                o.etkinlik = self.etkinlik
            self.etkinlik = o.etkinlik             # harita etkinliğinin sayaçları ve patronları herkesin

    @property
    def next_uid(self):
        return self.ortak.next_uid if self.ortak else self._next_uid

    @next_uid.setter
    def next_uid(self, v):
        if self.ortak:
            self.ortak.next_uid = v
        else:
            self._next_uid = v

    # ------------------------------------------------------------ yardımcılar
    @property
    def hid(self):
        return self.p.user_id

    def send(self, msgs):
        if self.ortak is not None and len(self.ortak.uyeler) > 1:
            self.ortak.yansit(self, msgs)     # herkese görünenler (uzaylının hareketi, vuruşlar, patlamalar) öteki oyunculara da
        self.teslim(msgs)

    def teslim(self, msgs):
        """Bu dünyanın istemcisine (görüş süzgeçlerinden geçerek; döngü adımındaysa adım sonunda)."""
        if self.npcs:       # görüş dışındaki NPC'nin hareketi istemciye gitmez (onu tanımıyor)
            msgs = [m for m in msgs if not (m[0] == 'MoveCommand' and m[1]['userId'] in self.npcs and m[1]['userId'] not in self.visible)]
        msgs = [m for m in msgs if self.item_filter(m)]
        if not msgs:
            return
        if self._batch is not None:         # döngü adımında: adım sonunda hepsi birden (gönderim toplama)
            self._batch.extend(msgs)
            return
        try:
            self.send_raw(msgs)
        except OSError:
            self.running = False

    # ------------------------------------------------------------ ortak harita (arkadaş sunucusu; ortak_harita.py)
    def lider(self):
        """Haritanın işlerini (yeniden doğmalar, süresi biten kutular, harita etkinliği) bu dünya mı yürütür."""
        return self.ortak is None or self.ortak.lider is self

    def sahibi(self, n, now):
        """Uzaylının yapay zekâsını ve yeteneklerini bu dünya mı işler (tek oyunculuda hep)."""
        return self.ortak is None or self.ortak.sahibi_mi(self, n, now)

    def bizim(self, n):
        """Uzaylı bu kahramanla mı ilgili (ölünce, atlayınca peşini bıraksın): tek oyunculuda hepsi."""
        return self.ortak is None or n.foe in (None, self)

    def gizli(self, now):
        return self.abilities.cloaked(now) or self.items.cloaked()

    def ulasilir(self, now):
        """Uzaylılar bu kahramana saldırabilir mi (ölü, atlamada, gizli, güvenli bölgede değil)."""
        return not (self.hero_dead or self.jumping or self.gizli(now) or self.in_peace(*self.hero_pos(now)))

    def tanir(self, uid):
        """İstemci bu gemiyi tanıyor mu (kendisi, gördüğü uzaylılar ve oyuncular; 0: çevre)."""
        return uid == 0 or uid == self.hid or uid in self.visible or uid in self.oyuncular

    def imza(self):
        """Gemisinin görünümü: değişince öteki oyuncular gemiyi yeniden kurar (hangarda gemi, tasarım, dronlar, unvan)."""
        pl, g = self.p.d['pilot'], self.p.d['gemi']
        return (g.get('typeId'), pl.get('userName'), pl.get('clanTag'), self.p.d.get('formasyon'), len(self.p.d.get('dronlar') or ()),
                self.p.d.get('uzanti_asamasi'), (self.p.d.get('basarimlar') or {}).get('unvan'))

    def gorunum_msgs(self, now):
        """Öteki oyuncunun istemcisinde bu kahramanın gemisi ve süren hareketi."""
        x, y = self.hero_pos(now)
        msgs = list(self.gorunum(int(x), int(y))) if self.gorunum else []
        m = self.hero
        if m.t1 > now:
            msgs.append(('MoveCommand', dict(userId=self.hid, x=int(m.x1), y=int(m.y1), timeToTarget=int((m.t1 - now) * 1000))))
        return msgs

    def defer(self, msgs):
        """Döngü adımı sürerken döngünün iş parçacığından gelen oturum mesajı (session_tick, kancalar) dünyanınkilerle aynı sırada
        adım sonunda gider -> True; başka zaman False (oturum hemen gönderir)."""
        if self._batch is None or threading.get_ident() != self._loop_ident:
            return False
        self._batch.extend(msgs)
        return True

    def later(self, delay, fn):
        self.timers.append((time.time() + delay, fn))

    def schedule(self, delay, kind, value=None):
        """Yeniden doğma (uzaylı, bonus kutusu, cevher): harita durumuyla birlikte saklanır (WORLD_CACHE)."""
        self.pending.append([time.time() + delay, kind, value])

    def respawn_tick(self, now):
        due = [p for p in self.pending if p[0] <= now]
        if not due:
            return
        self.pending[:] = [p for p in self.pending if p[0] > now]       # yerinde: ortak haritada liste paylaşılıyor
        for _, kind, value in due:
            if kind == 'npc':
                if not str(value).startswith('etk_') or self.etkinlik.active_type(value):     # etkinlik bittiyse doğmaz
                    self.spawn_npc(value)
            elif kind == 'bonus':
                self.spawn_bonus_box()
            elif kind == 'booty':
                self.spawn_booty(value)
            elif kind == 'etk_kutu':
                self.etkinlik.spawn_box(value)
            elif kind == 'ore' and self.ore_fields:
                self.add_ore(value)

    def save_state(self):
        """Haritadan çıkış: durum WORLD_CACHE'e (yalnız oturumun dünyası; kapı haritası değil)."""
        if not self.keep_state or self.kapi:
            return
        with self.lock:
            npcs = [n for n in self.npcs.values() if n.alive and not n.gate]
            for n in npcs:
                n.engaged, n.flee, n.children, n.foe = False, False, set(), None
            WORLD_CACHE[self.cache_key] = dict(an=time.time(), npcs=npcs, boxes=dict(self.boxes), ores=dict(self.ores),
                                            pending=list(self.pending), ore_fields=list(self.ore_fields), next_uid=self.next_uid)
        while len(WORLD_CACHE) > WORLD_CACHE_MAX:
            del WORLD_CACHE[min(WORLD_CACHE, key=lambda k: WORLD_CACHE[k]['an'])]

    def restore_state(self):
        """Saklanmış durum (süresi geçmediyse) -> True: uzaylılar yerinde, kutular ve cevherler aynı, bekleyen doğmalar sürer."""
        c = WORLD_CACHE.pop(self.cache_key, None) if self.keep_state else None
        now = time.time()
        if not c or now - c['an'] > WORLD_CACHE_SN:
            return False
        for n in c['npcs']:
            x, y = n.mover.pos(now)
            n.mover = Mover(int(x), int(y))
            n.next_think, n.next_shot = now + random.uniform(1, 6), 0.0
            self.npcs[n.id] = n
        # kapsayıcılar yerinde doldurulur: ortak haritada öteki dünyalar da aynılarını tutuyor (ortak_harita.py)
        self.boxes.update({h: b for h, b in c['boxes'].items() if not b.get('bitis') or b['bitis'] > now})
        self.ores.update({h: o for h, o in c['ores'].items() if not o.get('busy')})
        self.pending[:], self.ore_fields[:] = c['pending'], c['ore_fields']
        self.next_uid = max(self.next_uid, c['next_uid'])
        self.log('   harita durumu geri geldi (%d sn önce): %d NPC, %d kutu, %d cevher, %d bekleyen doğma' % (
            now - c['an'], len(self.npcs), len(self.boxes), len(self.ores), len(self.pending)))
        return True

    def in_peace(self, x, y):
        """Güvenli bölge: kendi firmasının istasyonunun çevresi ya da harita portallarının çevresi (NPC saldırmaz, doğmaz, oraya dolaşmaz)."""
        s = self.home_station()
        if s and (x - s['posX']) ** 2 + (y - s['posY']) ** 2 <= s['peaceRadius'] ** 2:
            return True
        return self.near_gate_peace(x, y)

    def peace_gates(self):
        """Güvenli bölgesi olan portallar: harita portalları (Galaksi Kapısı ve kapı haritası portalları değil; harita.py). Düşman
        firmanın haritasında ve savaş haritalarında (4-1..4-4) yok; 4-5'te girişten sonra 15 sn (istemcinin DMZ yardımı)."""
        n, fac = H.name(self.map_id), H.company(self.map_id)
        if n in H.NO_DMZ_MAPS or (fac and fac != self.p.d['pilot'].get('factionId')) \
                or time.time() > self.entered + H.DMZ_AFTER_JUMP_SN.get(n, float('inf')):
            return []
        return [g for g in self.gates if not g.get('kapi') and not g.get('gizli')]

    def near_gate_peace(self, x, y):
        return any(math.hypot(g['x'] - x, g['y'] - y) <= H.GATE_PEACE_RADIUS for g in self.peace_gates())

    def home_station(self):
        """Oyuncunun firmasının istasyonu: başka firmanın üssünde (X-1, X-8) güvenli bölge, rafineri, hangar, donanım değiştirme ve
        istasyonda tamir yok; ölünce kendi ana haritasında doğar."""
        s = self.station
        return s if s and s.get('type') == self.p.d['pilot'].get('factionId') else None

    def in_station(self):
        return self.in_peace(*self.hero_pos())

    def reload_ship(self):
        """Hangarda gemi değişti: yeni gemiyle ShipInitializationCommand; istemci haritayı yeniden yükler,
        ReadyRequest gelince NPC'ler ve kutular yeniden bildirilir (yeniden doğmadaki akış)."""
        with self.lock:
            self.stop_repair()
            x, y = self.hero_pos()
            self.p.d['konum'].update(x=int(x), y=int(y))
            self.hero = Mover(int(x), int(y))
            self.target, self.attacking = None, False
            self.reload_pending = True
            if self.pet:
                self.pet.reload()
            self.send(self.reload_msgs())

    def reload_msgs(self):
        """ShipInitializationCommand (refreshMap) istemcide haritayı temizler: gemi + haritanın girişteki nesneleri.
        NPC'ler, kutular ve hazır demeti istemcinin ardından gönderdiği ReadyRequest'te gelir."""
        return [self.p.generate('@gemi')] + (self.map_msgs() if self.map_msgs else [])

    def random_spot(self):
        for _ in range(50):
            x, y = random.uniform(600, self.map_w - 600), random.uniform(600, self.map_h - 600)
            s = self.station
            if (not s or math.hypot(x - s['posX'], y - s['posY']) > s['peaceRadius'] + 700) and \
                    all(math.hypot(g['x'] - x, g['y'] - y) > H.GATE_PEACE_RADIUS + 500 for g in self.gates):
                return int(x), int(y)
        return self.map_w // 2, self.map_h // 2

    def hero_pos(self, now=None):
        return self.hero.pos(now or time.time())

    # ------------------------------------------------------------ doğurma
    def ship_create(self, n):
        x, y = n.mover.pos(time.time())
        return ('ShipCreateCommand', dict(
            userId=n.id, typeId=n.model, expansionStage=1, clanTag='', userName=n.d['ad'], x=int(x), y=int(y), factionId=0, clanId=0,
            dailyRank=0, warnBox=False, clanDiplomacy=mod('ClanRelationModule', type=0), galaxyGatesDone=0, useSystemFont=False, npc=True,
            cloaked=bool(getattr(n, 'gizli', False)), motherShipId=0, positionIndex=0, designSet='', modifier=[],      # Infiltration
            minimapStrategyModule=mod('MinimapStrategyModule', minimapStrategy=0), specialNpcType=''))

    def item_pos(self, h):
        it = self.boxes.get(h) or self.ores.get(h)
        return (it['x'], it['y']) if it else None

    def item_in_view(self, h, hx, hy):
        if h in self.boxes and not self.benim(self.boxes[h]):     # başkasının ganimeti (grup)
            return False
        p = self.item_pos(h)
        lim = SAVAS['kutu_birakma' if h in self.seen_items else 'kutu_gorus']
        return bool(p) and math.hypot(p[0] - hx, p[1] - hy) <= lim

    def item_filter(self, m):
        """Kutu ve cevher görüşü: uzaktakinin eklenmesi gitmez (görüşe girince gönderilir), istemcinin bilmediğinin kaldırılması
        gitmez. Gönderilenler istemcinin bildikleri listesine işlenir."""
        name, f = m[0], m[1]
        if name in ('AddBoxCommand', 'AddOreCommand'):
            hx, hy = self.hero_pos()
            if not self.item_in_view(f['hash'], hx, hy):
                return False
            self.seen_items.add(f['hash'])
        elif name == 'RemoveCollectableCommand':
            if f['hash'] not in self.seen_items:
                return False
            self.seen_items.discard(f['hash'])
        return True

    def item_msg(self, h):
        if h in self.ores:
            return self.ore_msg(h)
        b = self.boxes[h]
        return ('AddBoxCommand', dict(hash=h, boxType=b['tip'], x=b['x'], y=b['y']))

    def in_view(self, n, now, hx=None, hy=None):
        """NPC görüş mesafesinde mi (gösterilmişse bırakma uzaklığına dek görünür kalır)."""
        if hx is None:
            hx, hy = self.hero_pos(now)
        nx, ny = n.mover.pos(now)
        lim = SAVAS['gorus_birakma' if n.id in self.visible else 'gorus_mesafesi'] * self.abilities.view_factor(now)   # Recon
        return math.hypot(nx - hx, ny - hy) <= lim

    def show(self, n, now):
        """NPC'yi istemciye bildir: ShipCreateCommand, hareket ediyorsa kalan hareketi (MoveCommand)."""
        self.visible.add(n.id)
        msgs = [self.ship_create(n)]
        msgs += list((getattr(n, 'gorseller', None) or {}).values())     # kalıcı görseller (Ö4: tahliye bölgesi, Guardian alanı)
        m = n.mover
        if m.t1 > now:
            msgs.append(('MoveCommand', dict(userId=n.id, x=int(m.x1), y=int(m.y1), timeToTarget=int((m.t1 - now) * 1000))))
        return msgs

    def info_request(self, uid):
        """Eski metin protokolü "i|<kimlik>": istemci bilmediği bir varlığı soruyor; kayıttaki gibi yeniden gönderilir."""
        with self.lock:
            n = self.npcs.get(uid)
            if n and n.alive and n.id not in self.visible and self.in_view(n, time.time()):
                self.send(self.show(n, time.time()))
            elif n and n.alive and n.id in self.visible:
                self.send([self.ship_create(n)])

    def visible_msgs(self, now):
        """Görüş mesafesindeki bütün NPC'ler (girişte ve harita yeniden yüklenince)."""
        self.visible.clear()
        hx, hy = self.hero_pos(now)
        return [m for n in self.npcs.values() if self.in_view(n, now, hx, hy) for m in self.show(n, now)]

    def omega_maps(self):
        """Omega AutoTactic'in seçim listeleri için (otopilot.py): bulunulan harita ve harita -> orada çıkan uzaylıların adları
        (npc.json'un harita tabloları; bu haritada şu an yaşayanlar da: etkinlik, kapı dalgası, çağrılan)."""
        T = CFG['tipler']
        with self.lock:
            maps = {k: {T[r['tip']]['ad'] for r in v.get('npc', []) if T.get(r.get('tip'), {}).get('ad')}
                    for k, v in CFG['haritalar'].items() if k.isdigit()}
            maps.setdefault(self.map_id, set()).update(n.d['ad'] for n in self.npcs.values()
                                                       if n.alive and n.d.get('ad') and not getattr(n, 'gizli', False))
        return self.map_id, maps

    def view_tick(self, now):
        """Görüşe giren NPC gösterilir, çıkan kaldırılır (kayıttaki gibi ShipRemoveCommand; hedefse seçim bırakılır)."""
        hx, hy = self.hero_pos(now)
        msgs = []
        for n in list(self.npcs.values()):
            seen = n.id in self.visible
            if self.in_view(n, now, hx, hy):
                if not seen:
                    msgs += self.show(n, now)
            elif seen:
                self.visible.discard(n.id)
                if self.target == n.id:
                    self.target, self.attacking = None, False
                    msgs.append(('ShipDeselectionCommand', {}))
                msgs.append(('ShipRemoveCommand', {'userId': n.id}))
        for h in list(self.boxes) + list(self.ores):          # kutular ve cevherler (~1.000 birim)
            seen = h in self.seen_items
            if self.item_in_view(h, hx, hy):
                if not seen:
                    msgs.append(self.item_msg(h))
            elif seen:
                msgs.append(('RemoveCollectableCommand', {'collected': False, 'hash': h}))
        if self.ortak:
            msgs += self.shared_view(now, hx, hy)
        if msgs:
            self.send(msgs)

    def shared_view(self, now, hx, hy):
        """Ortak harita: başka oyuncunun öldürdüğü ya da çektiği uzaylı, topladığı kutu ve cevher bu istemciden de kalkar; öteki
        oyuncuların gemileri görüşe göre gösterilir (ortak_harita.Harita.gorunurluk)."""
        msgs = []
        for uid in [u for u in self.visible if u not in self.npcs]:
            self.visible.discard(uid)
            if self.target == uid:
                self.target, self.attacking = None, False
                msgs.append(('ShipDeselectionCommand', {}))
            msgs.append(('ShipRemoveCommand', {'userId': uid}))
        msgs += [('RemoveCollectableCommand', {'collected': False, 'hash': h}) for h in list(self.seen_items)
                 if h not in self.boxes and h not in self.ores]
        lim = self.abilities.view_factor(now)
        msgs += self.ortak.gorunurluk(self, now, hx, hy, SAVAS['gorus_mesafesi'] * lim, SAVAS['gorus_birakma'] * lim)
        if self.secim is not None and self.target == self.secim[1]['userId']:     # seçili öteki oyuncu
            w = self.oyuncu(self.target)
            if w is None:                                    # görüşten çıktı (ShipRemoveCommand yukarıda)
                self.target, self.attacking, self.secim = None, False, None
                msgs.append(('ShipDeselectionCommand', {}))
            elif self.oyuncu_secimi(w) != self.secim:        # canı ya da kalkanı değişti (gerçek sunucu da yeniden gönderir)
                self.secim = self.oyuncu_secimi(w)
                msgs.append(self.secim)
        return msgs

    def oyuncu(self, uid):
        """İstemcinin gördüğü öteki oyuncunun dünyası (ortak harita) ya da None."""
        if self.ortak is None or uid not in self.oyuncular:
            return None
        return next((w for w in self.ortak.uyeler if w.hid == uid and w.running), None)

    def oyuncu_secimi(self, w):
        """Öteki oyuncunun seçimi: istemci oyuncuyu kimliğiyle seçer (shipType önemsiz), çubuklar kaydından."""
        g = w.p.d['gemi']
        return ('ShipSelectionCommand', dict(userId=w.hid, shipType=0, shield=int(g.get('shield', 0)), shieldMax=int(g.get('shieldMax', 0)),
                                             hitpoints=int(g.get('hitPoints', 0)), hitpointsMax=int(g.get('hitMax', 0)),
                                             nanoHull=int(g.get('nanoHull', 0)), maxNanoHull=int(g.get('maxNanoHull', 0)),
                                             shieldSkill=False))

    def fixed_spot(self, tip):
        """Türün sabit doğma noktalarından boş olanı (npc.json haritalar.sabit_noktalar; Cubikon'un dört noktası) ya da None."""
        pts = self.rules.get('sabit_noktalar', {}).get(tip)
        if not pts:
            return None
        free = [p for p in pts if not any(n.tip == tip and math.hypot(n.mover.x1 - p[0], n.mover.y1 - p[1]) < 800
                                          for n in self.npcs.values())]
        return tuple(random.choice(free or pts))

    def spawn_npc(self, tip, announce=True):
        self.next_uid += 1
        x, y = self.fixed_spot(tip) or self.random_spot()
        n = NPC(self.next_uid, tip, x, y)
        self.npcs[n.id] = n
        now = time.time()
        if announce and self.in_view(n, now):
            self.send(self.show(n, now))
        return n

    def spawn_npc_at(self, tip, x, y, model=None, prep=None, dalga=False):
        """Belirli noktada NPC (kapı dalgaları). model: türünkinden farklı görünüm (Kronos Evil You: oyuncunun gemisi); prep:
        bildirilmeden önce örneğe uygulanan (modlarda güçlendirme, pve_ortak.scale_npc); dalga: kapı ve mod dalgası (panelin can alt
        ayarı)."""
        self.next_uid += 1
        n = NPC(self.next_uid, tip, int(x), int(y), dalga)
        if model:
            n.model = model
        if prep:
            prep(n)
        self.npcs[n.id] = n
        now = time.time()
        if self.in_view(n, now):
            self.send(self.show(n, now))
        return n

    PORTAL_MARGIN, PORTAL_GAP = 800, 700

    def fit_gate(self, g):
        """Portal harita sınırları içinde ve başka portalın üstünde değil. Üssün yanına yay üzerinde dizilen portallar (etkinlik
        kapıları, labirent, Voyagers/Trinity/arena) üs köşedeyse harita dışına (radyasyon bölgesine) düşüyordu (canlı test H46:
        2-1'de Plutus x=21.681, Voyagers y=-1.806)."""
        m = self.PORTAL_MARGIN
        x = min(max(int(g['x']), m), self.map_w - m)
        y = min(max(int(g['y']), m), self.map_h - m)
        for _ in range(12):
            hit = next((o for o in self.gates if o['gateId'] != g['gateId'] and math.hypot(o['x'] - x, o['y'] - y) < self.PORTAL_GAP), None)
            if not hit:
                break
            # kenara yaslanmışsa kenar boyunca, değilse haritanın ortasına doğru kaydır
            if x in (m, self.map_w - m):
                y = min(max(y + (self.PORTAL_GAP if y < self.map_h // 2 else -self.PORTAL_GAP), m), self.map_h - m)
            elif y in (m, self.map_h - m):
                x = min(max(x + (self.PORTAL_GAP if x < self.map_w // 2 else -self.PORTAL_GAP), m), self.map_w - m)
            else:
                x += self.PORTAL_GAP if x < self.map_w // 2 else -self.PORTAL_GAP
        if (x, y) != (g['x'], g['y']):
            g = dict(g, x=x, y=y)
        return g

    def add_gate(self, g):
        """Sonradan eklenen portal (Galaksi Kapısı, kapıdan çıkış)."""
        if any(x['gateId'] == g['gateId'] for x in self.gates):
            return
        g = self.fit_gate(g)
        self.gates.append(g)
        self.send([H.jumpgate_create(g)])

    def remove_gate(self, gid):
        if not any(x['gateId'] == gid for x in self.gates):
            return
        self.gates = [x for x in self.gates if x['gateId'] != gid]
        if self.near_gate == gid:
            self.near_gate = None
        self.send([('JumpGateRemoveCommand', {'gateId': gid})])

    def drop_box(self, kind, x, y, content, life, sahip=None):
        """sahip: kutu yalnız bu kahramanın (grupta herkese düşen ganimet; öteki oyuncular görmez, toplayamaz)."""
        h = rand_hash()
        while h in self.boxes:
            h = rand_hash()
        self.boxes[h] = dict(tip=kind, x=int(x), y=int(y), icerik=content, bitis=time.time() + life if life else None)
        if sahip is not None:
            self.boxes[h]['sahip'] = sahip
        self.send([('AddBoxCommand', dict(hash=h, boxType=kind, x=int(x), y=int(y)))])
        return h

    def benim(self, b):
        """Kutuyu bu kahraman görür ve toplayabilir mi (sahipsiz ya da kendisinin)."""
        return b.get('sahip') in (None, self.hid)

    def drop_chests(self, sd, x, y, sahip=None):
        """Patron sandıkları: tek oyunculuda bütün hasar oyuncunun, en iyi kademeden en çok adet; uzaylının çevresine dizilir,
        içerik etkinlik kutusu gibi açılınca ('kesin' satırlar; etkinlik_harita.roll)."""
        for k in range(sd['adet']):
            a = 2 * math.pi * k / sd['adet']
            h = self.drop_box(sd['tur'], x + math.cos(a) * 200, y + math.sin(a) * 200, None, sd.get('omur_sn', 600), sahip)
            self.boxes[h]['etk'] = sd

    def spawn_bonus_box(self):
        x, y = self.random_spot()
        table = CFG['bonus_kutu_4x'] if H.name(self.map_id).startswith('4-') else CFG['bonus_kutu']   # boxes.md: 4-X'te zengin kutu
        self.drop_box('BONUS_BOX', x, y, random.choice(table), None)

    def spawn_booty(self, kind):
        """Anahtarlı ganimet kutusu (ganimet.py): rastgele yerde, süresiz; toplanınca yeniden_sn sonra yenisi."""
        if not GN.active(kind):
            return
        x, y = self.random_spot()
        h = self.drop_box(kind, x, y, None, None)
        self.boxes[h]['anahtarli'] = True

    def start(self):
        m = CFG['haritalar'].get(self.map_id)
        if not m:
            self.log('   dünya: harita %s için NPC listesi yok' % self.map_id)
            m = {'npc': [], 'bonus_kutu': 0}     # yine de döngü çalışsın: portallar, onarım, kalkan
        with self.lock:
            joined = bool(self.ortak and self.ortak.uyeler)      # ortak haritada başka oyuncu var: uzaylılar, kutular, cevherler onun
            restored = joined or self.restore_state()
            for g in ([] if restored else m['npc']):
                for _ in range(AY.adet('npc_sayi', g['adet'], 'harita')):
                    self.spawn_npc(g['tip'], announce=False)
            if self.test_near and not joined:
                hx, hy = self.hero_pos()
                picks, seen = [], set()
                for n in self.npcs.values():
                    if n.tip not in seen and len(picks) < 4:
                        picks.append(n); seen.add(n.tip)
                for k, n in enumerate(picks):
                    a = 0.6 + k * 1.6
                    n.mover = Mover(int(hx + math.cos(a) * 550), int(hy + math.sin(a) * 450))
                    n.next_think = time.time() + 600     # saldırıya uğrayana kadar yerinde dursun
                    self.log('   test NPC %d %s konum=(%d,%d), oyuncu=(%d,%d)' % (n.id, n.d['ad'], n.mover.x1, n.mover.y1, hx, hy))
            self.send(self.visible_msgs(time.time()) + self.map_effect_msgs())
            if not restored:
                for _ in range(AY.adet('kutu_bolluk', m.get('bonus_kutu', 0), 'bonus')):
                    self.spawn_bonus_box()
                for kind, n in ([] if self.kapi else GN.spawns(H.name(self.map_id))):
                    for _ in range(AY.adet('kutu_bolluk', n, 'ganimet')):
                        self.spawn_booty(kind)
                self.spawn_ores()
            self.send([self.ore_msg(h) for h in self.ores])
            if restored:                  # saklanan kutular yeniden bildirilir (görüş süzgecinden geçer)
                self.send([('AddBoxCommand', dict(hash=h, boxType=b['tip'], x=b['x'], y=b['y'])) for h, b in self.boxes.items()])
            for g in self.extra_gates:
                self.add_gate(g)
            self.start_rules()
            if joined:                    # harita etkinliğinin göstergesi (lider haritaya girdiğinde yalnız ona gitmişti)
                self.send(self.etkinlik.info_msgs())
            for name, a in (self.map_msgs() if self.map_msgs else []):
                if name == 'AssetCreateCommand' and a['type']['typeValue'] in H.STATION_ASSETS \
                        and a.get('factionId') in (0, None, self.p.d['pilot'].get('factionId')):   # düşman üssününkiler kullanılmaz
                    self.assets.append((a['assetId'], a['posX'], a['posY'], H.STATION_ASSETS[a['type']['typeValue']]))
                    self.asset_types[a['assetId']] = a['type']['typeValue']
                if name == 'AssetCreateCommand' and a['type']['typeValue'] == H.QUEST_GIVER:
                    self.givers.append((a['assetId'], a['posX'], a['posY']))
        self.running = True
        with self.lock:
            if self.ortak:
                self.ortak.katil(self)
            self.check_gates(time.time())     # portalda doğduysa atlama hemen mümkün olsun
        RUNNING.add(self)
        threading.Thread(target=self.loop, daemon=True).start()
        self.log('   dünya: harita %s, %d NPC, %d bonus kutusu, %d cevher' % (self.map_id, len(self.npcs), len(self.boxes), len(self.ores)))

    def stop(self):
        self.running = False
        if self.durdu:
            return
        self.durdu = True
        if self.ortak is None:
            self.save_state()
        elif not self.ortak_birakildi:            # ortak harita: durumu son çıkan saklar (WORLD_CACHE), kapsayıcılar boşalır
            self.ortak_birakildi = True
            if self.ortak.ayril(self):
                self.save_state()
                with self.lock:
                    for c in (self.npcs, self.boxes, self.ores, self.pending, self.ore_fields):
                        c.clear()
            self.ortak.birak()
        if self.hero_etki.d.keys() & {'yavas', 'donuk', 'hizlanma', 'hiz_siniri', 'zayiflik'}:
            self.hero_etki.d.clear()             # haritanın etkileri (mezarlığın yavaşlatması …) kalkar; hız yeni haritaya doğru gider
            if self.stats_msgs:
                self.send(self.stats_msgs())
        if getattr(self.p, 'world_mods', None) == self.hero_etki.mods:
            self.p.world_mods = None

    def cinematic(self, x, y, hold=3.0):
        """Sinematik kamera (Ö2; panelin 'sinematik' ayarı): kamera bir noktaya gider (CameraLockToCoordinatesCommand; istemci o sürede
        kontrolleri kilitler), hold saniye sonra gemiye döner (CameraLockToHeroCommand). Harita değişiminde ve ölümde de çözülür."""
        if not AY.get('sinematik') or self.hero_dead or self.jumping:
            return
        self.cinema = True
        self.send([('CameraLockToCoordinatesCommand', dict(x=int(x), y=int(y), duration=1.0))])
        self.later(hold, self.cinematic_end)

    def cinematic_end(self):
        if self.cinema:
            self.cinema = False
            self.send([('CameraLockToHeroCommand', {})])

    def cleanup_msgs(self):
        """Harita değişiminde bu haritanın NPC'lerini ve kutularını istemciden kaldıran mesajlar."""
        with self.lock:
            cam = [('CameraLockToHeroCommand', {})] if self.cinema else []
            self.cinema = False
            players, self.oyuncular = list(self.oyuncular), {}         # öteki oyuncuların gemileri (ortak harita)
            return cam + ([('ShipRemoveCommand', {'userId': uid}) for uid in players] +
                    [('ShipRemoveCommand', {'userId': uid}) for uid in self.npcs if uid in self.visible] +
                    [('RemoveCollectableCommand', {'collected': False, 'hash': h}) for h in list(self.boxes) + list(self.ores)
                     if h in self.seen_items] +
                    [UZ.asset_remove(aid, UZ.BUFF_CAPSULE) for aid in self.alien.capsules] +
                    (self.low.cleanup_msgs() if self.low else []))

    # ------------------------------------------------------------ harita kuralları (Aşama 4)
    def start_rules(self):
        """Girişte: mezarlıkta gizlenme kalkar ve yavaşlatan hava; 4-5'te gizli solucan deliği."""
        r = self.rules
        if r.get('gizlenme_yok'):
            self.abilities.reveal()
            self.items.reveal()
        if r.get('yavaslatma'):
            self.hero_effect('yavas', 24 * 3600, r['yavaslatma'], source='harita')
        if r.get('solucan_deligi'):
            self.move_wormhole(time.time())

    def move_wormhole(self, now):
        """4-5'teki gizli portal: mini haritada görünmez, belli aralıkla yer değiştirir (wiki)."""
        s = self.rules['solucan_deligi']
        if self.wormhole:
            self.remove_gate(WORMHOLE_ID)
        x, y = self.random_spot()
        g = dict(gateId=WORMHOLE_ID, x=x, y=y, hedef=s['hedef'], designId=1, gizli=True)
        self.wormhole = (g, now + s.get('tasinma_sn', 600))
        self.add_gate(g)
        self.log('   solucan deliği (%d,%d) -> %s' % (x, y, H.name(s['hedef'])))

    def rules_tick(self, now):
        """Saniyede bir: mezarlıkta gizlenme kullanılamaz; solucan deliği yer değiştirir; zaman çizelgeli başıboşlar."""
        if now < self.next_rules:
            return
        self.next_rules = now + 1.0
        if self.rules.get('gizlenme_yok') and (self.abilities.cloaked(now) or self.items.cloaked()):
            self.abilities.reveal()
            self.items.reveal()
        if self.wormhole and now >= self.wormhole[1] and not self.jumping:
            self.move_wormhole(now)
        self.drifter_tick(now)

    @staticmethod
    def slot_time(hm, now):
        """"HH:MM" -> bu saatin en son geçtiği an (bugün ya da dün; yerel saat)."""
        h, m = (int(v) for v in hm.split(':'))
        lt = time.localtime(now)
        t = time.mktime((lt.tm_year, lt.tm_mon, lt.tm_mday, h, m, 0, 0, 0, -1))
        # dün: takvim günü (yaz saati değişen günde 86.400 sn bir saat kaydırırdı); mktime ayın 0. gününü önceki aya taşır
        return time.mktime((lt.tm_year, lt.tm_mon, lt.tm_mday - 1, h, m, 0, 0, 0, -1)) if t > now else t

    def drifter_tick(self, now):
        """Zaman çizelgeli Black Light başıboşları (npc.json haritalar.zamanli; wiki saatleri): saatinden sonra zamanli_sure_sn içinde
        haritada yoksa ve o saatte öldürülmediyse doğar; yeniden doğmaz."""
        if now < self.next_drifter or self.kapi or not self.lider():
            return
        self.next_drifter = now + 5.0
        done = self.p.d.get('zamanli', {})
        for e in self.rules.get('zamanli', []):
            for hm in e['saatler']:
                slot = self.slot_time(hm, now)
                if now >= slot + SAVAS.get('zamanli_sure_sn', 3600):
                    continue
                key = '%s|%s|%d' % (self.map_id, e['tip'], int(slot))
                if key in done or any(n.alive and n.ab.get('zamanli') for n in self.npcs.values() if n.tip == e['tip']):
                    continue
                n = self.spawn_npc(e['tip'])
                n.summoned = True
                n.ab['zamanli'] = key
                self.log('   zaman çizelgeli uzaylı: %s (%s)' % (n.d['ad'], hm))

    def drifter_killed(self, n):
        key = n.ab.get('zamanli')
        if not key:
            return
        now = int(time.time())
        for w in [self] + [w for w in (self.ortak.uyeler if self.ortak else []) if w is not self]:   # ortak harita: lider de bilsin
            with w.p.lock:
                done = w.p.d.setdefault('zamanli', {})
                done[key] = now
                for k in [k for k, t in done.items() if now - t > 2 * 86400]:
                    del done[k]
                w.p.dirty = True

    def pay_key(self):
        """5-4'ün girişi: bir Gümüş Booty Key (KEY_COST) -> ödendi mi."""
        for loot, n in KEY_COST:
            if self.p.resource(loot) >= n:
                self.p.add_resource(loot, -n)
                self.log('   5-4 girişi: %d %s' % (n, loot))
                return True
        return False

    # ------------------------------------------------------------ cevherler
    def spawn_ores(self):
        """Haritanın cevherleri (esyalar.json cevherler.haritalar, harita sınıfına göre) kümeler hâlinde; güvenli bölgelerin dışında."""
        counts = ORE['haritalar'].get(H.map_class(self.map_id))
        if not counts:
            return
        total = sum(counts.values())
        self.ore_fields[:] = [self.random_spot() for _ in range(max(3, total // ORE['kume_basina']))]
        for t, n in counts.items():
            for _ in range(AY.adet('maden_bolluk', n)):              # panel: maden bolluğu
                self.add_ore(int(t), announce=False)
        self.log('   cevher kümeleri: %s' % ' '.join('(%d,%d)' % c for c in self.ore_fields))

    def ore_spot(self):
        for _ in range(30):
            cx, cy = random.choice(self.ore_fields)
            a, r = random.uniform(0, 2 * math.pi), random.uniform(0, ORE['kume_yaricap'])
            x, y = cx + math.cos(a) * r, cy + math.sin(a) * r
            if 300 < x < self.map_w - 300 and 300 < y < self.map_h - 300 and not self.near_zone(x, y, 200):
                return int(x), int(y)
        return self.random_spot()

    def add_ore(self, t, announce=True):
        h = rand_hash()
        while h in self.ores or h in self.boxes:
            h = rand_hash()
        x, y = self.ore_spot()
        self.ores[h] = dict(tip=t, x=x, y=y)
        if announce:
            self.send([self.ore_msg(h)])
        return h

    def ore_msg(self, h):
        o = self.ores[h]
        return ('AddOreCommand', dict(hash=h, oreType=mod('OreTypeModule', typeValue=o['tip']), x=o['x'], y=o['y']))

    def harvest(self, f):
        """HarvestRequest {itemHash}: istemci gemiyi cevhere götürüp gönderir; ~0,5 sn sonra toplanır (kayıt)."""
        with self.lock:
            h = f.get('itemHash')
            o = self.ores.get(h)
            if not o or o.get('busy') or self.hero_dead or self.jumping:
                return
            hx, hy = self.hero_pos()
            if math.hypot(o['x'] - hx, o['y'] - hy) > ORE['toplama_mesafe']:
                self.log('   cevher uzakta: %d birim' % math.hypot(o['x'] - hx, o['y'] - hy))
                return
            pre = self.auto_refine()
            if self.p.cargo_free() < 1:
                self.send(pre + [('MapEventOreCommand', dict(eventType=ORE_EVENT_CARGO_FULL, oreType=mod('OreTypeModule', typeValue=o['tip']),
                                                             hash=h)), legacy('0|A|STM|loadfull')] + self.p.hint(IP.FULL_CARGO))
                self.log('   kargo dolu')
                return
            o['busy'] = True
            self.send(pre + [self.beam_msg()])           # toplama ışını (kayıt: HarvestRequest'ten hemen sonra SLA)
            self.later(ORE['toplama_sn'], lambda: self.finish_harvest(h))

    def finish_harvest(self, h):
        o = self.ores.get(h)
        if not o:
            return
        pre = self.auto_refine()
        if self.p.cargo_free() < 1:
            o['busy'] = False
            self.send(pre + [('MapEventOreCommand', dict(eventType=ORE_EVENT_CARGO_FULL, oreType=mod('OreTypeModule', typeValue=o['tip']),
                                                         hash=h)), legacy('0|A|STM|loadfull')] + self.p.hint(IP.FULL_CARGO))
            return
        del self.ores[h]
        got = max(1, min(AY.miktar('toplama', 1, 'maden'), self.p.cargo_free()))      # panelin toplama çarpanı
        totals = self.p.add_ores({o['tip']: got})
        msgs = pre + ([self.ore_pack([o['tip']])] if self.ore_pack else [])
        msgs += [('MapEventOreCommand', dict(eventType=ORE_EVENT_FINISHED, oreType=mod('OreTypeModule', typeValue=o['tip']), hash='')),
                 ('AttributeOreCountUpdateCommand', {'oreCountList': totals}),
                 ('RemoveCollectableCommand', {'collected': True, 'hash': h})]
        msgs += self.quest('loot', loot=ORE['turler'].get(str(o['tip']), ''), amount=got)
        self.send(msgs + self.auto_refine() + self.p.hint(IP.SELL_RESOURCE))
        self.schedule(random.uniform(*ORE['yeniden_dogma_sn']) * AY.carpan('maden_yenilenme'), 'ore', o['tip'])     # panel

    def auto_refine(self):
        """Ayarlar > Gameplay "Auto-refine raw materials" (autoRefinement; istemcinin ipucu "Only works with a premium pack", tek
        oyunculuda herkes premium): her toplamadan sonra (cevher, kargo kutusu, P.E.T.'in topladıkları), toplamadan önce ve kargo
        doluyken laboratuvar tarifleri yettikçe her şey arıtılır: Prometium + Endurium -> Prometid, Endurium + Terbium -> Duranium,
        Prometid + Duranium + Xenomit -> Promerium ("Raw materials were automatically refined.", auto_ore_update). Ayar hiç
        uygulanmıyordu (H84); 2026-10-18'e dek yalnız kargo dolunca ve Promerium'suz çalışıyordu (kullanıcı bildirimi). -> mesajlar"""
        if not self.p.gameplay('autoRefinement'):
            return []
        recipes = [(t, {int(k): v for k, v in ESYA['laboratuvar']['tarifler'][str(t)].items()}) for t in AUTO_REFINE]
        have = {k: self.p.ore_count(k) for t, r in recipes for k in [t, *r]}
        start, made, more = dict(have), {}, True
        while more:                 # sırayla birer birim: ortak Endurium iki ürüne paylaşılır, yeni Prometid/Duranium Promerium'a girer
            more = False
            for t, r in recipes:
                if all(have[k] >= v for k, v in r.items()):
                    for k, v in r.items():
                        have[k] -= v
                    have[t] += 1
                    made[t] = made.get(t, 0) + 1
                    more = True
        if not made:
            return []
        used = {k: start[k] - have[k] for k in have if have[k] < start[k]}
        gained = {k: have[k] - start[k] for k in have if have[k] > start[k]}
        self.p.remove_ores(used)
        totals = self.p.add_ores(gained)
        self.log('   otomatik arıtma: %s (%s); kargoda boş %d' % (', '.join('%s %d' % (ORE['turler'].get(str(t)), n) for t, n in made.items()),
                                                                 ', '.join('%s %d' % (ORE['turler'].get(str(k)), n) for k, n in used.items()),
                                                                 self.p.cargo_free()))
        msgs = [('AttributeOreCountUpdateCommand', {'oreCountList': totals}), stm('auto_ore_update')]
        if self.ore_pack:
            msgs.append(self.ore_pack(sorted(set(used) | set(gained))))
        for t, n in made.items():
            msgs += self.quest('loot', loot=ORE['turler'].get(str(t), ''), amount=n)
        return msgs

    # ------------------------------------------------------------ istasyon: nesneler ve rafineri
    def at_station(self):
        s = self.home_station()
        hx, hy = self.hero_pos()
        return bool(s) and math.hypot(hx - s['posX'], hy - s['posY']) <= s['peaceRadius']

    def at_trade(self):
        """Ticaret yapılabilir mi: istasyonda ya da tek başına duran Trader'ın (5-2) yanında."""
        if self.at_station():
            return True
        hx, hy = self.hero_pos()
        return any(tip == 'ttip_ore_trade' and math.hypot(x - hx, y - hy) <= H.ASSET_RANGE for a, x, y, tip in self.assets)

    def check_assets(self, now):
        """İstasyon nesnelerine yaklaşma/uzaklaşma: tıklanabilir olur (rafineri -> ticaret penceresi). Görev vericiye yaklaşınca
        QuestGiversAvailableCommand + görev listesi, uzaklaşınca boş liste (kayıt: ~500 birim)."""
        hx, hy = self.hero_pos(now)
        giver = next((g for g in self.givers if math.hypot(g[1] - hx, g[2] - hy) <= H.ASSET_RANGE), None)
        gid = giver[0] if giver else None
        if gid != self.near_giver:
            self.near_giver = gid
            tip = mod('MessageKeyListWildcardCommand', commandList=[mod('MessageKeyListWildcardModule', wildCardReplacements=[],
                      baseKey='ttip_quest_giver_company', baseKeyType=mod('ReplacementTypeModule', typeValue=5), textStyle=0)])
            msgs = [('QuestGiversAvailableCommand', {'questGivers': [mod('QuestGiverModule', questGiverId=1, mapObjectId=gid, toolTip=tip)]
                                                     if gid else []})]
            if gid and self.quest_list:
                msgs.append(self.quest_list())
            self.send(msgs)
        if not self.assets:
            return
        near = {a for a, x, y, tip in self.assets if math.hypot(x - hx, y - hy) <= H.ASSET_RANGE}
        arrived = near - (self.near_assets or set())
        changed = {a for a, x, y, tip in self.assets} if self.near_assets is None else near ^ self.near_assets
        self.near_assets = near
        if changed:
            msgs = [self.asset_msg(a, tip, a in near) for a, x, y, tip in self.assets if a in changed]
            for a in sorted(arrived):                        # görev: "Fly to the following location: Hangar" (Ö1)
                msgs += self.quest('asset', tur=self.asset_types.get(a))
            self.send(msgs)

    def asset_msg(self, a, tip, near):
        """İstasyon nesnesinin ipucu; tamir istasyonunda kupon sayıları (istemcinin ttip_instant_repair / _not_available)."""
        if tip != 'ttip_instant_repair':
            return H.asset_available(a, tip, near)
        v = self.vouchers()
        if v >= REPAIR_VOUCHERS:
            return H.asset_available(a, tip, near, [('%VOUCHERS_PRESENT%', v), ('%REPAIRS_POSSIBLE%', v // REPAIR_VOUCHERS)])
        return H.asset_available(a, 'ttip_instant_repair_not_available', near, [('%VOUCHERS_PRESENT%', v),
                                                                                   ('%VOUCHERS_NEEDED%', REPAIR_VOUCHERS)])

    def instant_repair(self, f):
        """InstantRepairRequest {repairAssetId} (Ö1): istasyondaki tamir istasyonu (AssetType 53/54; istemci AssetClickOpenWindow) onarım
        kuponuyla gövdeyi hemen doldurur (kuponun açıklaması: "a sojourn at a repair station for your ship"). Kupon yetmezse ya da
        gövde tamsa olmaz; ipucu yenilenir."""
        with self.lock:
            now = time.time()
            hx, hy = self.hero_pos(now)
            st = next(((a, x, y, tip) for a, x, y, tip in self.assets if a == f.get('repairAssetId') and tip == 'ttip_instant_repair'), None)
            g = self.p.d['gemi']
            if not st or self.hero_dead or math.hypot(st[1] - hx, st[2] - hy) > H.ASSET_RANGE:
                self.log('   anında onarım yok: tamir istasyonu yakında değil')
                return
            if g.get('hitPoints', 0) >= g.get('hitMax', 0) or self.vouchers() < REPAIR_VOUCHERS:
                self.log('   anında onarım olmadı: %s' % ('gövde tam' if g.get('hitPoints', 0) >= g.get('hitMax', 0) else 'kupon yok'))
                self.send([self.asset_msg(st[0], st[3], True)])
                return
            with self.p.lock:
                self.p.d['kapilar']['kupon'] -= REPAIR_VOUCHERS
                self.p.dirty = True
            hp0 = g.get('hitPoints', 0)
            self.p.set_hull(hp=g.get('hitMax', 0))
            self.send([self.hp_msg()] + self.heal_msgs(hp0) + [legacy('0|A|STM|repair_voucher_used'), self.asset_msg(st[0], st[3], True)])
            self.log('   anında onarım: +%d can (kalan kupon %d)' % (int(g['hitPoints'] - hp0), self.vouchers()))

    def trade_info(self):
        """TradeRequest (rafineriye tıklama) -> OreTradeInfoCommand: istasyondaysa fiyatlar; uzayda P.E.T.'in kargo tüccarı
        seçiliyse P.E.T. ticareti; değilse ticaret etkin değil."""
        pr = ore_prices(self.p.d['pilot'].get('honourPoints', 0))
        pirate = self.at_trade() and self.map_id == PIRATE_MARKET          # 5-2'deki korsan tüccarı: Palladium -> kapı enerjisi
        kind = TRADE_PIRATE if pirate else TRADE_STATION if self.at_trade() else TRADE_PET if self.pet_trade() else TRADE_INACTIVE
        cbs = self.cbs_trade() if self.cbs_trade and not self.at_trade() else None
        if cbs:                                                             # kendi Battle Station'ında (Ö5): %10 pahalı
            kind = 4
            pr = {k: int(v * cbs) for k, v in pr.items()}
        return ('OreTradeInfoCommand', dict(
            prometiumPrice=pr[0], enduriumPrice=pr[1], terbiumPrice=pr[2], prometidPrice=pr[4], duraniumPrice=pr[5],
            promeriumPrice=pr[6], sepromPrice=pr[7], osmiumPrice=ORE['osmium_fiyati'],
            palladiumExchangeRate=ORE['palladium_enerji'] if pirate else -1, type=kind, remainingCharges=0))

    def trade_palladium(self, n):
        """5-2'deki korsan tüccarında Palladium -> kapı enerjisi (15'e 1; artan Palladium kargoda kalır)."""
        rate = ORE['palladium_enerji']
        units = min(n, self.p.ore_count(PALLADIUM)) // rate
        if not (self.at_trade() and self.map_id == PIRATE_MARKET) or units <= 0 or not self.gg_energy:
            self.log('   Palladium değişimi olmadı: %d (5-2 tüccarında mı: %s)' % (n, self.at_trade() and self.map_id == PIRATE_MARKET))
            return
        totals = self.p.remove_ores({PALLADIUM: units * rate})
        msgs = [('AttributeOreCountUpdateCommand', {'oreCountList': totals})] + self.gg_energy(units)
        if self.ore_pack:
            msgs.append(self.ore_pack([PALLADIUM]))
        msgs += self.quest('sell', ore=PALLADIUM, amount=units * rate)
        self.send(msgs)
        self.log('   Palladium x%d -> %d kapı enerjisi' % (units * rate, units))

    def hm7_ready(self):
        return EK.has(self.p, 'her_yerde_satis') and EK.uses(self.p, 'equipment_extra_hmd-07') > 0

    def pet_trade(self):
        return bool(self.pet and self.pet.active and self.pet.trading and time.time() >= self.pet.trade_ready)

    def sell_ore(self, f):
        """TradeSellOreRequest {toSell: {oreType, count}} -> kargo ve kredi (kayıttaki sıra)."""
        m = f.get('toSell') or {}
        t, n = (m.get('oreType') or {}).get('typeValue'), int(m.get('count') or 0)
        if t == PALLADIUM:
            with self.lock:
                self.trade_palladium(n)
            return
        with self.lock:
            price = ore_prices(self.p.d['pilot'].get('honourPoints', 0)).get(t)
            have = self.p.ore_count(t) if t is not None else 0
            cbs = self.cbs_trade() if self.cbs_trade and not self.at_trade() else None
            if cbs and price is not None:                                   # kendi Battle Station'ında (Ö5)
                price = int(price * cbs)
            by_pet = not self.at_trade() and not cbs and self.pet_trade()
            by_hm7 = not self.at_trade() and not by_pet and not cbs and self.hm7_ready()     # HM-7: her yerde, 100 satış
            if not (self.at_trade() or cbs or by_pet or by_hm7) or price is None or n <= 0 or n > have:
                self.log('   satış olmadı: tür %s x%d (elde %d, istasyonda %s)' % (t, n, have, self.at_trade()))
                return
            if by_pet:
                price = int(price * (1 + self.pet.trade_bonus()))     # G-TRA1: +%5/15/30
                self.pet.trade_used(time.time())      # kargo tüccarı bekleme süresine girer
            elif by_hm7:
                self.log('   HM-7 ile satış (kalan %d)' % EK.use(self.p, 'equipment_extra_hmd-07'))
            totals = self.p.remove_ores({t: n})
            kredi = n * price
            msgs = [('AttributeOreCountUpdateCommand', {'oreCountList': totals})]
            msgs += self.reward_msgs(self.p.gain(kredi=kredi, neden=RT.ore_desc(t), adet=n), kredi=kredi)
            if self.ore_pack:
                msgs.append(self.ore_pack([t]))
            msgs += self.quest('sell', ore=t, amount=n)
            self.send(msgs)
            self.sold = self.sold or self.at_trade()
            self.log('   satıldı: %s x%d = %d kredi' % (ORE['turler'].get(str(t), t), n, kredi))

    # ------------------------------------------------------------ portallar
    def check_gates(self, now):
        """Portala yaklaşma/uzaklaşma: BeaconCommand(nearJumpGate) + MapAssetActionAvailableCommand (kayıttaki gibi)."""
        hx, hy = self.hero_pos(now)
        g = next((g for g in self.gates if math.hypot(g['x'] - hx, g['y'] - hy) <= H.JUMP_RADIUS), None)
        gid = g['gateId'] if g else None
        peace = self.near_gate_peace(hx, hy)
        s = self.home_station()
        inside = bool(s) and math.hypot(hx - s['posX'], hy - s['posY']) <= s['peaceRadius']
        if gid == self.near_gate and peace == self.gate_peace and inside == self.station_inside:
            return
        was = None if self.station_inside is None else bool(self.station_inside or self.gate_peace)
        self.gate_peace, self.station_inside = peace, inside    # istasyona giriş/çıkışta da (inStation, inPeaceArea; kayıt)
        msgs = [('BeaconCommand', self.p.beacon(self.home_station(), near_gate=bool(g), pos=(hx, hy), gate_peace=peace,
                                                radiation=self.radiation_since is not None))]
        if (inside or peace) != was:          # donanım değiştirilebilir mi (in_station; kayıt: varınca ve ayrılınca, çiftler hâlinde)
            msgs += [('EquipReadyCommand', {'ready': inside or peace}),
                     legacy('0|n|MSG|3|2|%s|' % ('msg_equip_ready' if inside or peace else 'msg_equip_not_ready'))]
        if gid == self.near_gate:
            self.send(msgs)
            return
        old = next((x for x in self.gates if x['gateId'] == self.near_gate), None)
        if old:
            msgs.append(H.gate_available(old, False))
        if g:
            msgs.append(H.gate_available(g, True))
            msgs += self.p.hint(IP.JUMP_GATES)
        self.near_gate = gid
        self.send(msgs)

    def jump(self, f=None):
        """JumpRequest: yakında portal varsa JumpInitiatedCommand, ~3 sn sonra harita değişimi (oturum yapar)."""
        with self.lock:
            g = next((x for x in self.gates if x['gateId'] == self.near_gate), None)
            if not g or self.jumping or self.hero_dead:
                if not (g or self.jumping or self.hero_dead):
                    self.send([stm('jumpgate_failed_no_gate')])     # "Jump not possible! You're not located close enough to a jump gate."
                return False
            need = 0 if g.get('kapi') else H.level_required(g['hedef'], self.p.d['pilot'].get('factionId'))
            if self.p.d['pilot'].get('level', 1) < need:
                # istemcinin metni: "You need level %! for the jump. Not possible to jump from your level."
                self.send([legacy('0|A|STM|jumplevelfalse|%%!|%d' % need)])
                self.log('   portal %d: %s için seviye %d gerekli' % (g['gateId'], H.name(g['hedef']), need))
                return True
            if g.get('ucret') == 'gumus_anahtar' and not self.pay_key():
                self.send([legacy('0|A|STM|msg_hidden_pirate_map_no_silverkey')])     # "You need a Silver Booty Key to enter 5-4."
                self.log('   portal %d: 5-4 için Gümüş Booty Key yok' % g['gateId'])
                return True
            if g.get('pencere') and self.gate_window:  # pencereli portal: atlamak yerine modun penceresi (pve_modlari.py)
                self.gate_window(g)
                return True
            if g.get('ucretli') and self.gate_fee:     # ücretli portal (Frozen Labyrinth'in köşe portalları: Labyrinth Key)
                ok, fee = self.gate_fee(g)
                if fee:
                    self.send(fee)
                if not ok:
                    return True
            self.abilities.reveal()
            self.jumping, self.attacking, self.target = True, False, None
            for n in self.npcs.values():
                if self.bizim(n):
                    n.engaged = False
            self.send([('JumpInitiatedCommand', {'mapId': g['hedef'], 'gateId': g['gateId']})])
            self.log('   portal %d: %s -> %s atlama başladı' % (g['gateId'], H.name(self.map_id), H.name(g['hedef'])))
            if self.on_jump:
                self.later(H.JUMP_DELAY_SN, lambda: self.on_jump(g['hedef'], g))
            return True

    def resend(self):
        """Harita yeniden yüklendi (ör. yeniden doğma): tüm NPC'leri ve kutuları yeniden bildir; portal/güvenli bölge durumu ve
        saldırı koruması yeniden gönderilir (istemci haritayı temizledi)."""
        with self.lock:
            self.reload_pending = False
            self.near_gate, self.gate_peace, self.station_inside = None, None, None   # bir sonraki check_gates işareti yeniden gönderir
            self.seen_items.clear()                                                    # istemci haritayı temizledi
            self.oyuncular.clear()                                                     # öteki oyuncular (ortak harita) sonraki adımda
            msgs = self.visible_msgs(time.time()) + \
                   [('AddBoxCommand', dict(hash=h, boxType=b['tip'], x=b['x'], y=b['y'])) for h, b in self.boxes.items()] + \
                   [self.ore_msg(h) for h in self.ores] + [H.jumpgate_create(g) for g in self.gates if 'designId' in g] + \
                   self.alien.capsule_msgs() + (self.low.asset_msgs() if self.low else [])
            self.near_assets, self.near_giver = None, None
            left = self.invuln_until - time.time()
            if left > 0:
                msgs.append(self.invuln_msg(True))
                self.later(left, self.end_invuln)
            self.send(msgs + self.map_effect_msgs())
            self.check_gates(time.time())

    def map_effect_msgs(self):
        """Haritanın görsel etkisi: Trial of Terrors haritalarında el feneri (VisualModifierCommand FLASHLIGHT; istemci
        VisualModifierAssemblyHelper -> FlashLightEffect2D: karanlık örtü, ışık konisi geminin yönünde). İstemci etkiyi harita
        değişiminde, yeniden yüklemede ve tamirde siliyor (ParticleEffectComponentSystem.RemoveAllEffects): dünya kurulunca ve
        her yeniden yüklemede yeniden gönderilir. Panelin "karanlik" ayarı kapatır."""
        if not (self.karanlik and AY.get('karanlik')):
            return []
        return [('VisualModifierCommand', dict(userId=self.hid, modifier=FLASHLIGHT, attribute=0, additionalAttribute='', count=0,
                                               activated=True))]

    # ------------------------------------------------------------ istemci istekleri
    def on_move(self, f):
        with self.lock:
            now = time.time()
            ms = self.hero.go(f['targetX'], f['targetY'], self.p.d['gemi'].get('speed', 300), now, start=(f['positionX'], f['positionY']))
            if self.ortak:                 # onu gören oyuncular (ortak harita)
                self.ortak.hareket(self, f['targetX'], f['targetY'], ms)
            if self.sold:                  # kayıt: satıştan sonraki ilk MoveRequest'te 0|UI|W|MIW|ore_trade (pencere küçülür)
                self.sold = False
                self.send([legacy('0|UI|W|MIW|ore_trade')])

    def selection(self, n):
        # dize modelli patronlarda (DREADFYRE_FORTRESS, EMPEROR_KRISTALLON_BOSS_2) shipType istemcinin npcId'si
        stype = int(n.model) if str(n.model).isdigit() else int(n.d.get('npc_kimlik', 0))
        return ('ShipSelectionCommand', dict(userId=n.id, shipType=stype, shield=int(n.shield), shieldMax=n.d['kalkan'],
                                             hitpoints=int(n.hp), hitpointsMax=n.d['hp'], nanoHull=0, maxNanoHull=0, shieldSkill=False))

    def asset_at(self, uid):
        """Vurulabilir harita varlığının konumu (rakip istasyon modülü) ya da None."""
        return self.asset_targets.asset_pos(uid) if self.asset_targets and uid not in self.npcs else None

    def select(self, f):
        with self.lock:
            n = self.npcs.get(f.get('targetId'))
            if n and n.alive:
                self.target = n.id
                self.send([self.selection(n)] + ([] if n.d.get('dost') else self.p.hint(IP.ATTACK)))
            elif self.asset_at(f.get('targetId')):          # istemci varlığı ShipSelectionCommand + AssetInfoCommand ile seçer
                self.target = f.get('targetId')
                self.send(self.asset_targets.asset_select(self.target))
            elif self.oyuncu(f.get('targetId')):            # öteki oyuncu (arkadaş sunucusu): seçilir, canı izlenir (shared_view)
                w = self.oyuncu(f.get('targetId'))
                self.target, self.attacking, self.secim = w.hid, False, self.oyuncu_secimi(w)
                self.send([self.secim])

    def laser_start(self, f):
        with self.lock:
            n = self.npcs.get(f.get('targetId'))
            asset = None if n else self.asset_at(f.get('targetId'))
            if not n and not asset and self.oyuncu(f.get('targetId')):    # oyuncuya saldırı yok (arkadaş sunucusunda PvP yok)
                self.send([legacy('0|A|STM|%s' % ('msg_grp_attack_impossible' if self.grup_uyesi(f.get('targetId'))
                                                  else 'friendlyfire_disabled'))])
                return
            if (not asset and (not n or not n.alive)) or self.hero_dead:
                return
            if asset:                                       # varlık (çift tık: AttackLaserRequest) - deflector açıkken vurulamaz
                err = self.asset_targets.asset_attackable(f.get('targetId'))
                if err:
                    self.send(err)
                    return
            uid = n.id if n else f.get('targetId')
            self.end_invuln(force=True)          # saldırınca yerinde tamirin koruması kalkar
            self.abilities.reveal()              # saldırınca gizlenme biter
            self.items.reveal()                  # gizlenme CPU'su da
            self.target, self.attacking = uid, True
            self.next_laser = max(self.next_laser, time.time())
            self.send([('UIItemAddHighlightCommand', dict(
                soundModule=mod('SoundTriggerModule', playSound=False, soundId=0), itemSource=mod('UiItemSourceModule', itemSource=0),
                highlightType=mod('HighlightTypeModule', type=6), itemId=LASER_AMMO)),
                legacy('0|n|LSH|%d|%d' % (uid, self.hid))])

    def laser_stop(self, notify=True):
        with self.lock:
            was = self.attacking
            self.attacking = False
            if notify:
                self.ates = False            # bitiş aşağıda herkese gidiyor (step yeniden göndermesin)
                msgs = [('AttackAbortLaserCommand', {'uid': self.hid})]
                if was:
                    msgs.append(('UIItemRemoveHighlightCommand', dict(itemId=LASER_AMMO, itemSource=mod('UiItemSourceModule', itemSource=0),
                                                                     highlightType=mod('HighlightTypeModule', type=6))))
                self.send(msgs)

    def rocket(self, f):
        with self.lock:
            now = time.time()
            n = self.npcs.get(f.get('targetId'))
            rocket = self.p.d['secili']['roket']
            special = SE.special(rocket)          # özel roketin kendi beklemesi var (savas_esya.py)
            # bekleme payı: istemci sayacını mesaj gelince başlattığı için bekleme bitmeden hemen önce istek gelebiliyor (canlı deneme:
            # 4 sn beklemede 3,89 sn'de gelen roket sessizce yok sayılıyordu)
            if (not special and now < self.rocket_ready - ROKET_PAYI) or not n or not n.alive or self.hero_dead:
                return
            hx, hy = self.hero_pos(now)
            nx, ny = n.mover.pos(now)
            if math.hypot(nx - hx, ny - hy) > SAVAS['roket_menzil']:
                self.send([range_exceeded(n.id, SAVAS['roket_menzil'], 0)])
                return
            if special:
                self.items.fire_special(rocket, n, now)
                return
            if self.p.use_ammo(rocket, 1) is None:
                alt, msgs = self.ammo_out('roket', rocket, 1)    # otomatik değişim açıksa yeni türle aynı atış
                self.send(msgs)
                if not alt or self.p.use_ammo(alt, 1) is None:
                    return
                rocket = alt
            if rocket != IP.PLT_2021 and self.p.ammo(IP.PLT_2021) > 0:
                h = self.p.hint(IP.EQUIP_YOUR_ROCKETS)            # "PLT-2021'i neden takmadın?" (ipucu bir kez)
                if h:
                    self.send(h)
            self.end_invuln(force=True)
            self.abilities.reveal()
            self.items.reveal()
            self.last_combat = now
            self.stop_repair()
            self.p.ach('shot', silah='ROCKET_LAUNCHER')
            ms = int(SAVAS['roket_bekleme_ms'] * (0.5 if self.p.premium else 1)                  # Premium: "50% shorter rocket reload"
                     * (1 + self.p.mods().get('roket_bekleme', 0))                               # 3D Ring +%25, 3D Dome -%25, Demon -%5
                     * EK.rocket_factor(self.p) * AY.carpan('roket_bekleme'))                          # R0K-T01: yarıya; panel
            ms = self.abilities.rocket_ms(ms, now)                  # Rapid Fire (Tartarus)
            self.rocket_ready = now + ms / 1000
            hit = random.random() < self.rocket_hit(rocket)
            self.send(self.ammo_msgs(rocket) + [legacy('0|v|%d|%d|%s|%d|0|0' % (self.hid, n.id, 'H' if hit else 'M',
                                                                            ESYA['roketler'].get(rocket, {}).get('kimlik', 1))),
                       ('MenuItemCooldownGroupTimerCommand', dict(timerState=mod('TimerStateModule', timerStateValue=2),
                                                                  cooldownType=mod('CooldownTypeModule', typeValue=4), maxTime=ms, time=ms))])
            dmg = int(ESYA['roketler'].get(rocket, {'hasar': 1000})['hasar'] * random.uniform(0.85, 1.0)   # kayıt: R-310 853/991
                      * (1 + self.p.mods().get('roket', 0) + self.p.mods().get('npc', 0)) * (1 + self.p.lab_bonus(1)))
            if self.p.lab_bonus(1):
                self.lab_spend(1)                   # roket yükseltmesi: roket başına 1
            if hit:
                self.later(SAVAS['roket_ucus_sn'], lambda: self.hit_npc(n.id, dmg, 0))
            else:
                self.later(SAVAS['roket_ucus_sn'], lambda: self.send([('AttackMissedCommand', dict(
                    attackType=attack_type(0), targetUserId=n.id, skillColorId=0))]))
            self.later(ms / 1000, lambda: self.send([('MenuItemCooldownGroupTimerCommand', dict(
                timerState=mod('TimerStateModule', timerStateValue=0), cooldownType=mod('CooldownTypeModule', typeValue=4),
                maxTime=ms, time=0))]))

    def rocket_hit(self, rocket):
        """Roketin isabet şansı: taban (npc.json roket_isabet; BDR-1211 %100) x (1 + Heat-Seeking Missiles + DMG-H01 + durum)."""
        if self.tech.full_rocket_hit():
            return 1.0                                      # Precision Targeter
        m = self.p.mods()
        base = ESYA['roketler'].get(rocket, {}).get('isabet', SAVAS['roket_isabet'])
        return AY.chance('oyuncu_isabet', min(1.0, base * max(0.0, 1 + m.get('roket_isabet', 0) + m.get('isabet', 0))))     # panel

    def collect(self, f):
        """CollectBoxRequest {itemHash, boxX/Y, posX/Y}: istemci gemiyi kutuya götürüp gönderir. Mesafe sunucunun bildiği gemi
        konumuyla ölçülür (cevherdeki gibi): istemcinin posX/posY'si gemi değil, tıklanan nesnenin sahnedeki konumu; 3D'de kutunun
        kendisi, 2D'de Y'si hep 0 (2D'de kutular toplanmıyordu, H80). Gemi henüz yoldaysa kutu varınca alınır."""
        with self.lock:
            h = f.get('itemHash')
            if h not in self.boxes or not self.benim(self.boxes[h]) or self.hero_dead or self.jumping:
                return
            if not self.box_near(h):
                self.collect_wish = (h, time.time() + COLLECT_WAIT_SN)
                return
            self.collect_wish = None
            self.take_box(h)

    def beam_msg(self, by_pet=False):
        """Toplama ışını: 0|A|SLA|kip|birim (istemci: SetAttributeAssemblyHelper.AssembleCollectionBeamActive). Işın birimden
        çıkar; kip 0 oyuncunun tıkladığı nesnenin sesini (Hero.LastCollectedSoundId; kayıtta hep 0|oyuncu), 1 toplama ışını sesini
        (beam0, ses 3) çalar. P.E.T. toplarken de 0|gemi gidiyordu: ışın gemiden çıkıyor, son ses (çoğu kez 0 = lazer) çalıyordu."""
        if by_pet and self.pet:
            return legacy('0|A|SLA|1|%d' % self.pet.pid)
        return legacy('0|A|SLA|0|%d' % self.hid)

    def box_near(self, h, now=None):
        b = self.boxes.get(h)
        hx, hy = self.hero_pos(now)
        return bool(b) and math.hypot(b['x'] - hx, b['y'] - hy) <= SAVAS['toplama_mesafe']

    def collect_tick(self, now):
        """İstenen kutu: gemi varınca alınır; süre dolarsa, kutu gittiyse ya da gemi öldüyse istek düşer."""
        h, until = self.collect_wish
        if now > until or h not in self.boxes or self.hero_dead:
            self.collect_wish = None
        elif not self.jumping and self.box_near(h, now):
            self.collect_wish = None
            self.take_box(h)

    def take_box(self, h, by_pet=False):
        """Kutuyu al (oyuncu ya da P.E.T.'in otomatik toplayıcısı): kargo kutusu cevherleri kargoya sığdığı kadar, bonus kutusu
        kredi/uridyum/cephane. P.E.T.'in kurtarma protokolü (AI-S) P.E.T.'in topladığı kutunun içeriğini artırır (istemci "boxes,
        collected by your P.E.T.")."""
        with self.lock:
            b = self.boxes.get(h)
            if not b or not self.benim(b) or (by_pet and b.get('pet_yok')):      # Vortex of Greed kutularını P.E.T. toplayamaz (Ö4)
                return False
            boost = 1 + (self.pet.proto('kutu') if by_pet and self.pet else 0)
            m = self.p.mods()          # pilot yetenekleri: Tractor Beam I/II (kargo/bonus kutusu), Luck (bonus kutusu uridyumu)
            pre = []
            cargo_box = b['tip'] in CARGO_BOXES
            if cargo_box:                                       # önce otomatik arıtma (ayar açıksa): yer açılır
                pre = self.auto_refine()
            if cargo_box and self.p.cargo_free() < 1:
                self.send(pre + [legacy('0|A|STM|loadfull')] + self.p.hint(IP.FULL_CARGO))     # kargo dolu: kutu yerinde kalır
                return False
            if b['tip'] in GN.BOXES and not b.get('etk'):
                return False if by_pet else self.open_booty(h, b)
            del self.boxes[h]
            msgs = pre + [self.beam_msg(by_pet), ('RemoveCollectableCommand', {'collected': True, 'hash': h})]
            if cargo_box:
                ores, free = {}, self.p.cargo_free()
                for k, v in sorted(b['icerik'].items()):
                    take = min(int(v * boost * (1 + m.get('kargo_kutusu', 0))), free)
                    if take > 0:
                        ores[int(k)] = take
                        free -= take
                totals = self.p.add_ores(ores)
                content = [mod('OreCountModule', oreType=mod('OreTypeModule', typeValue=t), count=c) for t, c in sorted(ores.items())]
                msgs += [('LMCollectResourcesCommand', dict(priorityMode=mod('LogMessengerPriorityModule', priorityModeValue=0),
                                                            contentList=content)),
                         ('AttributeOreCountUpdateCommand', {'oreCountList': totals})]
                msgs += self.quest('cargo')
                for t, c in sorted(ores.items()):
                    msgs += self.quest('loot', loot=ORE['turler'].get(str(t), ''), amount=c)
                    RT.note(self.p, 'received_item', ORE['turler'].get(str(t), ''), c)       # seyir defteri
                msgs += self.auto_refine()               # her toplamadan sonra (ayar açıksa)
            elif b.get('al'):                        # kendi toplama işlevi olan kutu (Ö4: Vortex'in Stellar Coin kutuları)
                msgs += b['al'](b) or []
            elif b.get('etk'):                       # etkinlik kutusu (etkinlik_harita.py): içerik açılınca çekilir
                got = ETK.roll(b['etk'])
                for loot, n in got:
                    msgs += self.grant_loot(loot, n)
                if b['etk'].get('yeniden_sn'):
                    self.schedule(random.uniform(*b['etk']['yeniden_sn']) * AY.carpan('kutu_yenilenme'), 'etk_kutu', b['tip'])
                self.log('   etkinlik kutusu %s: %s' % (b['tip'], ', '.join('%s x%d' % x for x in got) or '-'))
            elif b['tip'] == 'BONUS_BOX':
                what, amount = b['icerik']
                seq = self.rules.get('bonus_dizisi')
                if seq:                                  # Cubikon Mezarlığı: ilki 1.000 UCB-100, sonra giderek LCB-10 (wiki)
                    what, amount = seq[min(self.boxes_taken, len(seq) - 1)]
                    self.boxes_taken += 1
                amount = int(amount * boost * (1 + m.get('bonus_kutusu', 0)) * (1 + (m.get('bonus_uridyum', 0) if what == 'uridyum' else 0)))
                amount = AY.miktar({'kredi': 'kredi', 'uridyum': 'uridyum', 'enerji': 'kapi_enerji'}.get(what, 'toplama'), amount, 'kutu')  # panel
                if what == 'kredi':
                    msgs += self.reward_msgs(self.p.gain(kredi=amount, neden='collect_bonusbox'), kredi=amount)
                elif what == 'uridyum':
                    msgs += self.reward_msgs(self.p.gain(uridyum=amount, neden='collect_bonusbox'), uridyum=amount)
                elif what == 'enerji':
                    msgs += self.gg_energy(amount) if self.gg_energy else []      # Galaksi Kapısı üreticisinin ücretsiz enerjisi
                    RT.note(self.p, 'gg_extra_energy_got', count=amount)
                else:
                    RT.note(self.p, 'received_item', what, amount)
                    self.p.add_ammo(what, amount)
                    msgs.append(legacy('0|LM|ST|BAT|%s|%d' % (what, amount)))
                    self.p.ach('box_ammo', silah='LASER' if what.startswith('ammunition_laser_') else 'ROCKET_LAUNCHER', adet=amount)
                self.schedule(random.uniform(30, 60) * AY.carpan('kutu_yenilenme'), 'bonus')
                msgs += self.quest('bonus')
            self.send(msgs)
            if not by_pet:
                self.abilities.reveal()          # kutu toplayınca gizlenme biter
            self.p.ach('box', tip=b['tip'], pet=by_pet)
            if by_pet:
                self.log('   P.E.T. kutu topladı: %s' % b['tip'])
            return True

    def open_booty(self, h, b):
        """Anahtarlı kutu (ganimet.py): anahtar yoksa kutu kalır ve istemcinin metni; yeşil anahtar ayarda otomatik alınabilir.
        Varsa bir anahtar harcanır, içerikten bir ödül mağazanın ödül işleviyle verilir. Kilit tutulurken çağrılır."""
        kind = b['tip']
        box = GN.BOXES[kind]
        key, msgs = box['anahtar'], []
        if self.p.resource(key) < 1 and key == GN.GREEN_KEY:
            if not self.p.gameplay('autoBuyGreenBootyKeys'):           # Ayarlar > Gameplay
                self.send([legacy('0|A|STM|msg_booty-key-green_auto_buy_not_active')])
                return False
            msgs = self.auto_buy(key, 1) if self.auto_buy else []
            if self.p.resource(key) < 1:
                self.send([legacy('0|A|STM|msg_booty-key-green_no_uridium_for_auto_buy')])
                return False
        if self.p.resource(key) < 1:
            self.send([legacy('0|A|STM|%s' % box['yok_mesaji'])])
            return False
        del self.boxes[h]
        self.p.add_resource(key, -1)
        if box.get('defter'):
            RT.note(self.p, box['defter'])                              # seyir defteri: "… booty key used"
        loot, n = GN.pick(self.p, kind)
        msgs += [self.beam_msg(), ('RemoveCollectableCommand', {'collected': True, 'hash': h})]
        if GN.key_line(self.p, kind):
            msgs.append(legacy(GN.key_line(self.p, kind)))
        msgs += self.grant_loot(loot, n)          # para (Prime Astral'ın EP/onuru …) hesaba, gerisi mağazanın ödül işleviyle; panelin çarpanları
        if box.get('yeniden_sn'):                                       # Echo sandığı: patronun düşürdüğü, yeniden doğmaz
            self.schedule(GN.respawn_delay(kind) * AY.carpan('kutu_yenilenme'), 'booty', kind)
        self.send(msgs)
        self.abilities.reveal()
        self.p.ach('box', tip=kind, pet=False)
        self.log('   %s açıldı (%s): %s x%d' % (box['ad'], key, loot, n))
        return True

    # ------------------------------------------------------------ savaş
    def reward_msgs(self, tot, ep=0, onur=0, kredi=0, uridyum=0):
        msgs = []
        if ep:
            msgs.append(legacy('0|LM|ST|EP|%d|%d|%d' % (ep, tot['ep'], tot['seviye'])))
        if tot.get('seviye_atladi'):
            msgs.append(('LevelUpCommand', {'uid': self.hid, 'newLevel': tot['seviye']}))     # seviye atlama efekti
        if onur:
            msgs.append(legacy('0|LM|ST|HON|%d|%d' % (onur, tot['onur'])))
        if kredi:
            msgs += [legacy('0|LM|ST|CRE|%d|%d' % (kredi, tot['kredi'])), self.currency_item('currency_credits', CREDITS_ITEM, tot['kredi'])]
        if uridyum:
            msgs += [legacy('0|LM|ST|URI|%d|%d' % (uridyum, tot['uridyum'])), self.currency_item('currency_uridium', URIDIUM_ITEM, tot['uridyum'])]
        if (kredi or uridyum) and self.quick_buy:
            msgs += self.quick_buy()
        return msgs

    @staticmethod
    def currency_item(loot, item_id, amount):
        return ('InventoryItemUpdatedCommand', {'item': mod('InventoryItemModule', upgradeLevel=0, lootId=loot, amount=amount, itemId=item_id,
                                                            star=0, isNew=False, hangarId=0, extAttributes=[], inventoryItemAttributes=[])})

    def hit_npc(self, uid, dmg, atype, shield_only=False, attacker=None, hull_only=False, split=None, strike=False, cannon=0,
                engage=True):
        """Kahramanın (ya da P.E.T.'in) vuruşu: kalkan hasarın %70'ini emer (kayıttan), kalan HP'ye. SAB-50 gibi cephane yalnız
        kalkanı vurur. split=(kalkana, gövdeye): mayın gibi oranı belli hasar (emme yok). engage=False: vuran oyuncunun değil
        (Clan Battle Station'ın uyduları): uzaylı oyuncuya dönmez."""
        with self.lock:
            n = self.npcs.get(uid)
            if not n or not n.alive or n.d.get('dost'):         # dost gemi (Deep Space Echoes: korunan/eşlik edilen) vurulmaz
                return
            now = time.time()
            immune = (n.invulnerable and n.invulnerable()) or n.etki.invulnerable(now) or self.guarded(n)
            if immune:
                dmg = 0
            k = AY.carpan('oyuncu_hasar')                       # panelin hasar çarpanı (lazer, roket, mayın, top, P.E.T. …)
            if k != 1.0:
                dmg = int(dmg * k)
                if split:
                    split = (split[0] * k, split[1] * k)
            n.last_hit = now
            if getattr(n, 'gizli', False):                          # gizli komando vurulunca görünür (Infiltration: sizma.py)
                n.gizli = False
                self.send([legacy('0|n|INV|%d|0' % n.id)])
            self.alien.attacked(n, attacker, now)
            self.npc_summon(n, now)
            if not attacker and not hull_only:                     # Target Marker; Nidhogg'un aşındırma zaafı (parcacik.py)
                dmg = int(dmg * (1 + n.etki.damage_bonus(now) + self.parcacik.vulnerability(n.id, now)))
            red = getattr(n, 'hasar_azaltma', None)                # Ö4: Dreadfyre Fortress'in Guardian kalkanları (%25'er)
            if red:
                dmg = int(dmg * max(0.0, 1 - red()))
            if shield_only:
                dmg = min(dmg, int(n.shield))
            absorb = SAVAS['npc_kalkan_emme'] * n.etki.shield_factor(now)      # Diminisher: zayıf kalkan
            if not attacker:                                                     # kalkan delme (Moth +%20, Double Arrow +%10, Pincer -%10)
                absorb *= max(0.0, 1 - self.p.mods().get('kalkan_delme', 0))
            if split:                                                            # mayın (savas_esya.py)
                b = 0 if immune else 1 + n.etki.damage_bonus(now)
                to_shield = min(int(n.shield), int(split[0] * b))
                dmg = to_shield + int(split[1] * b)
            else:
                to_shield = dmg if shield_only else 0 if hull_only else min(n.shield, int(round(dmg * absorb)))
            n.shield -= to_shield
            n.hp = max(0, n.hp - (dmg - to_shield))
            floor = getattr(n, 'can_tabani', 0)                    # Ö4: Guardian 1 HP'de "düşer" (evre 1-3)
            if floor and n.hp < floor:
                n.hp = floor
                if getattr(n, 'tabanda', None):
                    n.tabanda(n)
            if dmg > 0 and getattr(n, 'hasar_kancasi', None):      # Ö4: savaşın hasar sayacı (ilerleme ödülleri)
                n.hasar_kancasi(dmg)
            if dmg > 0 and not attacker:
                self.p.ach('damage', adet=dmg, npc=n.d.get('npc_kimlik'))
            self.alien.on_hit(n, dmg, attacker, now)              # can eşiğinde çağırma, kaybolma (uzayli.py)
            if engage and not n.engaged:
                n.engaged = True
                n.next_think = min(n.next_think, time.time())   # saldırıya uğrayan NPC hemen tepki verir
                if self.ortak:
                    n.foe = self                                  # ortak harita: vurana döner
            self.last_shield_hit = to_shield
            msgs = [('AttackHitCommand', dict(attackType=attack_type(atype), attackerId=attacker or self.hid, victimId=n.id,
                                              victimHitpoints=int(n.hp),
                                              victimShield=int(n.shield), victimNanoHull=0, damage=dmg, skilled=atype == 1, strike=strike,
                                              cannonType=cannon))]
            if n.hp <= 0:
                msgs += self.kill(n)
            elif self.target == n.id:
                msgs.append(self.selection(n))
            self.send(msgs)

    @staticmethod
    def respawn_range(n):
        """Yeniden doğma süresi: sıradan uzaylı 12-25 sn; Boss, Uber, Cubikon, Behemoth daha uzun (npc.json yeniden_dogma_ozel);
        panelin yeniden doğma çarpanıyla."""
        o = SAVAS.get('yeniden_dogma_ozel', {})
        if n.tip in o:
            r = o[n.tip]
        elif 'Uber' in n.d['ad'] and 'uber' in o:
            r = o['uber']
        elif n.d['ad'].startswith('..::{') and 'boss' in o:
            r = o['boss']
        else:
            r = SAVAS['yeniden_dogma_sn']
        k = AY.carpan('npc_yenilenme')
        return r if k == 1.0 else [x * k for x in r]

    @staticmethod
    def npc_range(n):
        """NPC'nin ateş menzili: türün kendi değeri; hareketsizler oyuncunun menzilinden uzun (yoksa karşılık veremez)."""
        return n.d.get('menzil') or (SAVAS['npc_menzil_sabit'] if n.d['hiz'] <= 0 else SAVAS['npc_menzil'])

    def grant_loot(self, loot, n, kaynak='kutu'):
        """Kutudan ödül: para EP/onur/kredi/uridyum hesaba (Uridium Bank'a sayılır), gerisi mağazanın ödül işleviyle. kaynak:
        panelin alt ayarı (modların parası 'mod')."""
        cur = {'currency_credits': 'kredi', 'currency_uridium': 'uridyum', 'currency_experience': 'ep', 'currency_honour': 'onur'}
        n = AY.miktar(cur.get(loot, 'toplama'), n, kaynak)                 # panelin çarpanları
        if loot in cur:
            kw = {cur[loot]: n}
            return self.reward_msgs(self.p.gain(neden='collect_bonusbox', **kw), **kw)
        if n <= 0:
            return []
        if self.grant:
            return self.grant(loot, n)
        self.p.add_resource(loot, n)
        return [legacy('0|LM|ST|LOT|%s|%d' % (loot, n))]

    def extra_loot(self, n, specs=None):
        """Ek ödüller (npc.json ek_odul ← aliens.md "Extra destroy rewards"; specs: etkinlik düşmeleri, etkinlik_harita.py): Palladium
        kargoya (sığdığı kadar), ötekiler (Bifenon, Darksilver Coin, Candy Corn …) kaynak deposuna; ganimet günlüğünde görünür."""
        msgs = []
        bm = BOOSTER.mods(self.p)
        boost = 1 + bm.get('ozel_sans', 0)                              # PRC-B00/B01: Hybrid Alloy ve Indoctrine Oil olasılığı
        for loot, spec in (n.d.get('ek_odul', {}) if specs is None else specs).items():
            special = loot in BOOSTER.B.get('ozel_sans_kaynaklar', ())
            cnt = extra_count(spec, (boost if special else 1.0) * AY.carpan('dusme', 'ek'))
            if special and cnt > 0:
                cnt = int(cnt * (1 + bm.get('ozel_miktar', 0)))          # PRM-B01 (PCOMB-B01): miktar x2 (Ö6)
            if loot == 'resource_collectable_agate-splinter' and cnt > 0:
                cnt = int(cnt * (1 + bm.get('agat_miktar', 0)))          # AS-B01: Agate Splinter x2
            if cnt <= 0:
                continue
            if loot.startswith('equipment_'):
                msgs += self.grant(loot, cnt) if self.grant else []      # The Stinger'ın Caucasus lazeri (%0,5)
                continue
            cnt = AY.miktar('toplama', cnt, 'ek')                        # panelin toplama çarpanı
            if loot == 'resource_ore_palladium':
                cnt = min(cnt, self.p.cargo_free())
                if cnt > 0:
                    msgs.append(('AttributeOreCountUpdateCommand', {'oreCountList': self.p.add_ores({8: cnt})}))
                    if self.ore_pack:
                        msgs.append(self.ore_pack([8]))
            elif cnt > 0:
                self.p.add_resource(loot, cnt)
            if cnt > 0:
                msgs.append(legacy('0|LM|ST|LOT|%s|%d' % (loot, cnt)))
                msgs += self.quest('loot', loot=loot, amount=cnt)           # toplama görevleri (Palladium …)
        return msgs

    def cargo_of(self, n):
        """NPC'nin kargo kutusu; X-1 haritalarında yüksek seviyede azalır (npc.json x1_kargo: L7 %50 … L10+ yok)."""
        boost = 1 + self.p.mods().get('kargo', 0)                       # RES-B01 (booster): uzaylı kaynakları
        cargo = {t: AY.miktar('toplama', int(v * boost), 'kargo') for t, v in n.d['kargo'].items()}      # panelin toplama çarpanı
        cargo = {t: v for t, v in cargo.items() if v > 0}
        if H.map_class(self.map_id) == 'X-1' and AY.get('x1_kargo'):          # panel: kapatılabilir
            lv = self.p.d['pilot'].get('level', 1)
            f = next((k for l, k in reversed(SAVAS['x1_kargo']) if lv >= l), 1)
            cargo = {t: int(v * f) for t, v in cargo.items() if int(v * f) > 0}
        return cargo

    def x1_reward(self):
        """Kendi X-1 haritanda yüksek seviyede öldürme ödülü (EP, onur, kredi, uridyum) azalır: seviye 7'den, 15'ten hiç
        (npc.json x1_odul; panelin x1_kargo ayarı kapatır)."""
        if H.map_class(self.map_id) != 'X-1' or H.company(self.map_id) != self.p.d['pilot'].get('factionId') or not AY.get('x1_kargo'):
            return 1
        lv = self.p.d['pilot'].get('level', 1)
        return next((k for l, k in reversed(SAVAS['x1_odul']) if lv >= l), 1)

    @staticmethod
    def aggressive(n):
        """Uzaylı oyuncuyu kendiliğinden kovalar mı: panelin saldırganlık ayarı (0 türün ayarı, 1 hepsi, 2 hiçbiri). Saldırgan
        olmayan da vurulunca karşılık verir."""
        lv = AY.get('npc_saldirganlik')
        return bool(n.d.get('saldirgan')) if not lv else lv == 1

    def remove_npc(self, n):
        """Uzaylı ödülsüz ve patlamadan çekilir (kaçan Infiltration komandosu) -> mesajlar (kilit altında)."""
        n.alive = False
        self.npcs.pop(n.id, None)
        msgs = self.pet.npc_gone(n.id) if self.pet else []
        if self.target == n.id:
            self.target, self.attacking = None, False
            msgs.append(('ShipDeselectionCommand', {}))
        if n.id in self.visible:
            self.visible.discard(n.id)
            msgs.append(('ShipRemoveCommand', {'userId': n.id}))
        return msgs

    def kill(self, n):
        n.alive = False
        del self.npcs[n.id]
        x, y = n.mover.pos(time.time())
        msgs = []
        pet_stop = self.pet.npc_gone(n.id) if self.pet else []     # P.E.T. ona ateş ediyorsa lazeri durur
        if n.d.get('sayilmaz'):                 # sahte Emperor Lordakium: ödülsüz, kutusuz, yeniden doğmaz; patlar
            if n.id in self.visible:
                self.visible.discard(n.id)
                msgs += [('ShipDestroyedCommand', dict(destroyedUserId=n.id, explosionTypeId=0)), ('ShipRemoveCommand', {'userId': n.id})]
            if self.target == n.id:
                self.target, self.attacking = None, False
                msgs.append(('ShipDeselectionCommand', {}))
            return pet_stop + msgs + self.alien.on_kill(n, x, y)
        if n.id in self.visible:
            self.visible.discard(n.id)
            msgs.append(('ShipDestroyedCommand', dict(destroyedUserId=n.id, explosionTypeId=0)))
        if self.target == n.id:
            self.target, self.attacking = None, False
            msgs.append(('ShipDeselectionCommand', {}))
        if msgs and msgs[0][0] == 'ShipDestroyedCommand':
            msgs.append(('ShipRemoveCommand', {'userId': n.id}))
        msgs = pet_stop + msgs
        self.ofke.kill(self.lasers(), time.time())          # Asmodeus Fervor
        pay = self.paydaslar()
        for w in pay:
            w.npc_reward(n, x, y, len(pay), own=w is self)
        for sp in n.davranis.get('olunce_dogur', []):       # ölünce doğanlar (Lordakium sporları …): yeniden doğmazlar
            for k in range(sp.get('adet', 1)):
                a = 2 * math.pi * k / max(1, sp.get('adet', 1))
                c = self.spawn_npc_at(sp['tur'], x + math.cos(a) * 120, y + math.sin(a) * 120)
                self.alien.adopt(n, c)          # kapıda dalganın uzaylısı sayılır
                c.engaged = n.engaged
        if not n.gate and not n.summoned:
            self.schedule(random.uniform(*self.respawn_range(n)), 'npc', n.tip)
        self.drifter_killed(n)
        return msgs + self.alien.on_kill(n, x, y) + self.etkinlik.on_kill(n, x, y, w=self, pay=pay) + \
            (self.labirent.on_kill(n, x, y) if self.labirent else [])

    def paydaslar(self):
        """Uzaylının ödülünü paylaşanlar: öldüren ve ortak haritada grubundan aynı haritada yaşayan üyeler (uzaklık önemsiz;
        grup.py). Tek oyunculuda, kapıda ve grupsuz yalnız öldüren."""
        if self.ortak is None:
            return [self]
        return [self] + [w for w in self.ortak.uyeler if w is not self and w.running and not w.hero_dead and not w.jumping
                         and self.grup_uyesi(w.hid)]

    def kill_reward(self, n):
        """Uzaylının bu kahramana ödülü {ep, onur, kredi, uridyum}: türünki, formasyon ve pilot yetenekleri, X-1 kesintisi, panelin
        çarpanları."""
        o = dict(n.d['odul'])
        k = getattr(n, 'odul_carpani', 1)                          # tek uzaylının çarpanı (Infiltration komandosu: sizma.py)
        if k != 1:
            o = {a: int(v * k) for a, v in o.items()}
        form = self.p.mods()
        o['ep'] = int(o['ep'] * (1 + form.get('ep', 0)))          # Barrage, Bat, 3D X
        o['onur'] = int(o['onur'] * (1 + form.get('onur', 0)))    # Pincer, 3D Veteran; 3D X onuru kaldırır
        o['kredi'] = int(o['kredi'] * (1 + form.get('kredi', 0)))  # Greed (pilot yeteneği)
        if o.get('uridyum') and random.random() < form.get('cift_uridyum', 0):
            o['uridyum'] *= 2                                      # N.O.V.A. Autonomous Extraction (Galaksi Kapılarında; nova.py)
        f = self.x1_reward()
        if f != 1:
            o = {a: int(v * f) for a, v in o.items()}
        for k in ('ep', 'onur', 'kredi', 'uridyum'):
            o[k] = AY.miktar(k, o.get(k, 0), 'npc')                # panelin ödül çarpanları
        return o

    def npc_reward(self, n, x, y, share=1, own=True):
        """Uzaylının ödülü ve ganimeti bu kahramana (kill; grupta her paydaşın dünyası kendisininkini verir). EP, onur, kredi ve
        uridyum paydaşlar arasında bölünür (yukarı yuvarlanır; P.E.T.'in EP'si de); kargo kutusu, sandıklar, ek ödüller ve
        booster herkese tam, grupta kutular sahibinin (yalnız o görür ve toplar). own: öldüren; başarım, seri, dron EP'si, gemi
        yeteneğinin yükü, seyir defteri, kapı puanı ve etkinlik kancaları onun; öteki paydaşlara görev olarak sayılır (grup)."""
        o = self.kill_reward(n)
        if share > 1:
            o = dict(o, **{k: -(-o[k] // share) for k in ('ep', 'onur', 'kredi', 'uridyum')})
        in_rad = self.radiation_since is not None
        sahip = self.hid if share > 1 else None

        def reward():
            if own:
                self.p.ach('kill', avatar='NPC', npc=n.d.get('npc_kimlik'), radyasyon=in_rad, ad=n.d.get('ad'))
                GY.charge(self.p, 'oldurme')                 # Momentum, Stockpile: öldürme başına bir yük
            tot = self.p.gain(ep=o['ep'], onur=o['onur'], kredi=o['kredi'], uridyum=o['uridyum'], neden='bonus_abschussAlien')
            if own:
                RT.note_kill(self.p, n.d.get('npc_kimlik', 0), o['ep'], o['onur'])     # seyir defteri
            points = self.kapi.points(n) if own and n.d.get('puan') and hasattr(self.kapi, 'points') else []    # Plutus'un puanı
            quest = self.quest('kill', npc=n.d.get('npc_kimlik')) if own else \
                self.quest('kill', npc=n.d.get('npc_kimlik'), avatar='NPC', radyasyon=in_rad, ad=n.d.get('ad'), grup=True)
            self.send(self.reward_msgs(tot, ep=o['ep'], onur=o['onur'], kredi=o['kredi'], uridyum=o['uridyum'])
                      + (self.drone_points(n) if own else []) + quest + (self.pet.gain_xp(o['ep']) if self.pet else [])
                      + self.booster_drop(n) + self.extra_loot(n) + points
                      + (self.kill_streak() + self.p.hint(IP.WEALTHY_FAMOUS) + [m for hk in self.kill_hooks for m in hk(self, n, x, y)]
                         if own else []))
            self.log('   %s yok edildi%s: +%d EP, +%d onur, +%d kredi, +%d uridyum (seviye %d)' % (
                n.d['ad'], ' (grup payı 1/%d%s)' % (share, '' if own else ', grup üyesi vurdu') if share > 1 else '',
                o['ep'], o['onur'], o['kredi'], o['uridyum'], tot['seviye']))
        self.later(0.3, reward)
        cargo = {} if ETK.no_cargo(n) else self.cargo_of(n)        # Curcubitor: yalnız sandığı (etkinlik_harita)
        if cargo:
            kind = 'CANDY_CARGO' if TKV.has_type('CandyCargo') else 'FROM_SHIP'
            self.later(SAVAS['kutu_gecikme_sn'], lambda: self.drop_box(kind, x, y, cargo, SAVAS['kutu_omur_sn'], sahip))
        if n.d.get('sandik'):                              # hasara göre sandıklar (Invoke XVI, Mindfire Behemoth; npc.json)
            self.later(SAVAS['kutu_gecikme_sn'], lambda: self.drop_chests(n.d['sandik'], x, y, sahip))

    def lab_spend(self, item, n=1):
        """Yükseltmeden harca: lazer turu, roket, motor/kalkan dakikası. Bitince hız/kalkan eski hâline döner; otomatik laboratuvar
        CPU'su (NC-AWL/AWR/AWB/AGB) takılıysa ve Ayarlar > Gameplay "Automatic weapons upgrade by activating lab CPU" (autoBoost;
        istemcide AutoWeaponsUpgrade) açıksa kargodaki cevherle yeniden yükler (ayara bakılmıyordu, H86)."""
        ore = (self.p.d.get('yukseltmeler', {}).get(str(item)) or [None])[0]
        done = self.p.lab_use(item, n)
        msgs = self.lab_msgs() if self.lab_msgs else []
        if done:
            self.log('   yükseltme bitti: parça %d' % item)
            if item in (2, 3) and self.stats_msgs:
                msgs = self.stats_msgs() + msgs
            auto = [(l, EK.X[l]) for l, parts in EK.props(self.p, 'oto_lab') if item in parts]
            if auto and self.auto_lab and self.p.gameplay('autoBoost'):
                msgs += self.auto_lab(item, ore, bool(auto[0][1].get('en_iyi')))
        self.send([m for m in msgs if m])

    def lab_time(self, now):
        """Motor yükseltmesi hareket ederken, kalkan yükseltmesi savaşta dakika dakika harcanır."""
        dt, self.lab_tick = now - self.lab_tick, now
        if self.p.lab_bonus(2) and self.hero.t1 > now:
            self.lab_clock[2] += dt
        if self.p.lab_bonus(3) and now - self.last_combat < ESYA['savas_disi_sn']:
            self.lab_clock[3] += dt
        for item in (2, 3):
            if self.lab_clock[item] >= ESYA['laboratuvar']['dakika_sn']:
                self.lab_clock[item] -= ESYA['laboratuvar']['dakika_sn']
                self.lab_spend(item)

    def quest(self, kind, **kw):
        """Görev ilerlemesi (oturumun gorev.py'si) -> gönderilecek mesajlar."""
        return self.quest_event(kind, map=int(self.map_id), **kw) if self.quest_event else []

    def drone_points(self, n):
        """Dronlar öldürülen uzaylıdan puan alır; puan gemiye göre (wiki tablosu, güçlü gemide az). Seviye eşiğini geçen dron
        seviye atlar: lazer/kalkan bonusu artar, uzaydaki görünümü değişir."""
        if not self.p.d.get('dronlar'):
            return []
        name = re.sub(r'^[^A-Za-z]+|[^A-Za-z]+$', '', n.d['ad'])      # "-=[ Lordakia ]=-", "..::{ Boss Lordakia }::.."
        for pre in ('Boss ', 'Uber ', 'Über ', 'Uber'):                   # "( UberStreuner )": boşluksuz da
            name = name[len(pre):] if name.startswith(pre) else name
        order = DRONE_POINTS['_gemi_sirasi']
        ship = self.p.ship()['lootId']
        col = order.index(ship) if ship in order else len(order) - 1
        pts = AY.miktar('dron_puan', (DRONE_POINTS.get(name) or [0] * len(order))[col])     # panel: dron deneyimi
        if not pts:
            return []
        up = []
        with self.p.lock:
            for x in self.p.d['dronlar']:
                x['puan'] += pts
                while x['seviye'] < len(DRONE_LEVELS) and x['puan'] >= DRONE_LEVELS[x['seviye']]['puan']:
                    x['seviye'] += 1
                    up.append(x)
            self.p.dirty = True
            if up:
                self.p.sync_ekipman()
        if not up:
            return []
        self.log('   dron seviye atladı: %s' % ', '.join('%s %d' % (x['lootId'][6:], x['seviye']) for x in up))
        return (self.drone_msgs() if self.drone_msgs else []) + (self.stats_msgs() if self.stats_msgs else [])

    # ------------------------------------------------------------ ekipman ve cephane
    def lasers(self):
        return [l for l in self.p.d['ekipman'].get('laser', []) if l in ESYA['lazerler']]

    def laser_levels(self):
        """Gemideki lazerler yükseltme seviyeleriyle [(lootId, seviye)] (yukseltme.py)."""
        lv = self.p.d.get('ekipman_seviye', {}).get('laser', [])
        out = [(l, lv[i] if i < len(lv) else 0) for i, l in enumerate(self.p.d['ekipman'].get('laser', [])) if l in ESYA['lazerler']]
        ship = self.lasers()
        return out if [l for l, v in out] == ship else [(l, 0) for l in ship]      # lasers() başka kaynaktan (test, etkiler)

    def drone_lasers(self):
        return [l for level, loots in self.p.d.get('dron_ekipman', []) for l in loots if l in ESYA['lazerler']]

    def ammo_msgs(self, loot):
        """Cephane sayısı değişti: kısayol çubuğu sayacı + envanter (kayıttaki gibi her atışta)."""
        msgs = [('InventoryItemUpdatedCommand', {'item': mod('InventoryItemModule', upgradeLevel=0, lootId=loot, amount=self.p.ammo(loot),
                                                             itemId=self.p.item_id(loot), star=0, isNew=False, hangarId=0,
                                                             extAttributes=[], inventoryItemAttributes=[])})]
        st = self.p.menu_status(loot)
        if st:
            msgs.insert(0, ('MenuItemStatusCommand', st))
        return msgs

    def laser_damage(self, ammo, target=None, now=None):
        """Toplam lazer hasarı = toplam lazer hasarı x cephane çarpanı x rastgele (kayıt: 65 x 0,76-1,0).
        Lazerlerin özel nitelikleri lazer.py'de (Unstable LF-4 rastgele, Prometheus x3,5, set bonusları, Odysseus kritiği, SL-01 ek hasarı).
        -> (HP+kalkan hasarı, yalnız kalkan hasarı)"""
        now = now or time.time()
        lz = ESYA['lazerler']
        ship = self.lasers()
        base = sum(LAZER.hit(l, target) * YK.factor(l, lv, YK.LASER) for l, lv in self.laser_levels()) \
            * (1 + LAZER.set_bonus(ship) + self.ofke.bonus(ship, now))
        self.crit = bool(ship) and random.random() < LAZER.crit_chance(ship)
        if self.crit:
            base += LAZER.crit_damage(ship)                       # Odysseus kritiği
        extra = LAZER.overdrive(ship)
        if extra and now >= self.next_overdrive:                  # SL-01 +38, Prometheus +200: 5 sn'de bir
            base += extra
            self.next_overdrive = now + LAZER.OVERDRIVE_SN
        mods = self.p.mods()
        dlv = self.p.d.get('dron_ekipman_seviye', [])
        for k, (level, loots) in enumerate(self.p.d.get('dron_ekipman', [])):
            dloot, dup, ilv = dlv[k] if k < len(dlv) else (None, 0, [])
            hits = sum(LAZER.hit(l, target) * YK.factor(l, ilv[j] if j < len(ilv) else 0, YK.LASER)
                       for j, l in enumerate(loots) if l in lz)
            base += (hits * (1 + DRONE_LEVELS[level - 1]['lazer'] + mods.get('dron_lazer', 0))      # Havoc, Cerberus: dron lazerine
                     * YK.factor(dloot, dup, YK.DRONE_DAMAGE))
        base *= ((1 + mods.get('lazer', 0) + mods.get('npc', 0) + mods.get('npc_lazer', 0))       # formasyon, dron tasarımı
                 * (1 + self.p.lab_bonus(0)))                                                   # lazer yükseltmesi
        a = ESYA['lazer_cephane'].get(ammo, {'carpan': 1})
        r = random.uniform(*ESYA['hasar_rastgele'])
        carpan = LAZER.name_match(a.get('hedef_carpan', {}), target) or a.get('carpan', 1)   # SBL-100 x8 Sibelon'a …
        ramp = a.get('artan')
        if ramp:                                                  # IDB-125: x1'den isabet başına +1,25, en çok x6; 3 sn'de sıfırlanır
            carpan = 1.0 if now - self.artan[1] > ramp['sifirlama_sn'] else self.artan[0]
            self.artan = [min(ramp['azami'], carpan + ramp['adim']), now]
        if target is not None and ammo in (target.d.get('cephane_carpani') or {}):          # Ö4: etkinlik uzaylısının cephane bonusu
            carpan = target.d['cephane_carpani'][ammo]
        return int(base * carpan * r), int(base * a.get('kalkan_carpan', 0) * r)

    def laser_range(self):
        """Lazer menzili: SL-01 takılıysa -%25 (lazer.py); Momentum/Stockpile'ın biriken yükü (yük başına +5)."""
        return int(SAVAS['lazer_menzil'] * LAZER.range_factor(self.lasers())) + GY.range_bonus(self.p)

    def other_ammo(self, kind, empty, need):
        """Biten cephanenin yerine eldeki en güçlü sıradan cephane -> lootId (lazer: AUTO_AMMO sırası; roket: hasara göre, özel
        roketler hariç) ya da None."""
        if kind == 'lazer':
            order = AUTO_AMMO + sorted(a for a in self.p.d['cephane'] if a.startswith('ammunition_laser_') and a not in AUTO_AMMO)
        else:
            order = sorted((r for r in ESYA['roketler'] if not SE.special(r)), key=lambda r: -ESYA['roketler'][r].get('hasar', 0))
        return next((a for a in order if a != empty and self.p.ammo(a) >= need), None)

    def ammo_out(self, kind, empty, need):
        """Seçili cephane bitti -> (yeni cephane ya da None, mesajlar). Ayarlar > Gameplay "Change ammo/rocket type automatically"
        (autoChangeAmmo) açıksa eldeki cephaneye geçilir ("chgbat"/"chgrok" metni); değilse ya da başka cephane yoksa istemcinin
        cephane uyarısı: 0|W|<L|R>|0|1 "saldırı iptal, türü değiştir", 0|W|<L|R> "cephane kalmadı, satın al"
        (NetConnectionHelper.OnData -> SetAttributeAssemblyHelper.NoAmmunition; sunucu hiç göndermiyordu, H85)."""
        alt = self.other_ammo(kind, empty, need)
        code = 'L' if kind == 'lazer' else 'R'
        if alt and self.p.gameplay('autoChangeAmmo'):
            self.p.d['secili'][kind] = alt
            self.p.dirty = True
            name = alt.rsplit('_', 1)[-1].upper()
            msgs = [('MenuItemStatusCommand', st) for st in (self.p.menu_status(empty), self.p.menu_status(alt)) if st]
            self.log('   cephane bitti (%s): %s cephanesine geçildi' % (empty, alt))
            return alt, msgs + [stm('chgbat' if code == 'L' else 'chgrok', '%!', name)]
        self.log('   cephane bitti (%s): %s' % (empty, 'elde başka cephane var' if alt else 'hiç yok'))
        return None, [legacy('0|W|%s|0|1' % code) if alt else legacy('0|W|%s' % code)] + ([] if alt else self.p.hint(IP.GET_MORE_AMMO))

    def laser_color(self, ammo):
        """AttackLaserRunCommand.laserColor: istemcinin lazer türü (ışın, ışık ve ses; esyalar.json lazer_renkleri). Geminin bütün
        lazer yuvaları aynı lazerle doluysa o setin rengi (bütün LF-3: x1/x2 mavi, x3 yeşil), yoksa cephaneninki (x4 beyaz …)."""
        lr = ESYA['lazer_renkleri']
        lasers = self.lasers()
        cap = self.p.ship_row().get('laser', 0)
        if lasers and len(lasers) >= cap and len(set(lasers)) == 1 and ammo in lr['tam_set'].get(lasers[0], {}):
            return lr['tam_set'][lasers[0]][ammo]
        return lr['cephane'].get(ammo, 0)

    def asset_laser(self, now):
        """Lazer bir harita varlığına (rakip Battle Station modülü): menzil, cephane, isabet; hasarı varlığın sahibi uygular
        (asset_targets.asset_hit: kalkan, can, yıkılma ve ödül)."""
        uid = self.target
        pos = self.asset_at(uid)
        if not pos or self.asset_targets.asset_attackable(uid):
            self.laser_stop()
            return
        hx, hy = self.hero_pos(now)
        rng = self.laser_range()
        if math.hypot(pos[0] - hx, pos[1] - hy) > rng:
            if self.range_warned != uid:
                self.range_warned = uid
                self.send([range_exceeded(uid, rng, 1)] + self.combat_state(COMBAT_OUT_OF_RANGE, now))
            return
        if self.range_warned == uid:
            self.send(self.combat_state(COMBAT_CONTINUES, now))
        self.range_warned = None
        lasers = self.lasers() + self.drone_lasers()
        ammo = self.p.d['secili']['lazer']
        cooldown = ESYA['lazer_cephane'].get(ammo, {}).get('aralik_sn')
        if cooldown and now < self.ammo_ready.get(ammo, 0):
            return
        if not lasers or self.p.use_ammo(ammo, len(lasers)) is None:
            if not lasers:
                self.send([stm('no_lasers_on_board')])      # "Your ship doesn't have any laser cannons. That's why you can't attack."
                self.laser_stop()
                return
            alt, msgs = self.ammo_out('lazer', ammo, len(lasers))
            self.send(msgs)
            if not alt:
                self.laser_stop()
            return
        self.last_combat = now
        self.stop_repair()
        self.next_laser = now + SAVAS['lazer_aralik_sn']
        if cooldown:
            self.ammo_ready[ammo] = now + cooldown
        self.send(self.ammo_msgs(ammo) + [('AttackLaserRunCommand', dict(attackerId=self.hid, targetId=uid, laserColor=self.laser_color(ammo),
                                                                         isDiminishedBySkillShield=False, skilledLaser=False, visualType=0))])
        self.p.ach('shot', silah='LASER')
        m_ = self.p.mods()
        if random.random() < self.items.aim(AY.chance('oyuncu_isabet', SAVAS['lazer_isabet'] * (1 + m_.get('isabet', 0) + m_.get('lazer_isabet', 0)))):
            dmg, _ = self.laser_damage(ammo)
            self.send(self.asset_targets.asset_hit(uid, dmg))
        else:
            self.send([('AttackMissedCommand', dict(attackType=attack_type(1), targetUserId=uid, skillColorId=0))])
        if not self.asset_at(uid):
            self.laser_stop()

    def hero_laser(self, now):
        if self.target not in self.npcs and self.asset_at(self.target):
            return self.asset_laser(now)
        n = self.npcs.get(self.target)
        if not n or not n.alive:
            self.attacking = False
            return
        hx, hy = self.hero_pos(now)
        nx, ny = n.mover.pos(now)
        rng = self.laser_range()
        if math.hypot(nx - hx, ny - hy) > rng:
            if self.range_warned != n.id:               # istemci menzil efekti çizer (AttackRangeExceededCommandHandler)
                self.range_warned = n.id
                self.send([range_exceeded(n.id, rng, 1)] + self.combat_state(COMBAT_OUT_OF_RANGE, now))
            return
        if self.range_warned == n.id:                   # menzile geri dönüldü: "The battle continues."
            self.send(self.combat_state(COMBAT_CONTINUES, now))
        self.range_warned = None
        lasers = self.lasers() + self.drone_lasers()      # dron lazerleri de ateş eder ve cephane harcar
        ammo = self.p.d['secili']['lazer']
        cooldown = ESYA['lazer_cephane'].get(ammo, {}).get('aralik_sn')
        if cooldown and now < self.ammo_ready.get(ammo, 0):
            return            # bekleme bu cephanenin (wiki: RSB-75 3 sn); başka cephaneye geçilince o hemen atar
        if not lasers or self.p.use_ammo(ammo, len(lasers)) is None:
            if not lasers:
                self.log('   lazer atışı yok: lazer takılı değil')
                self.send([stm('no_lasers_on_board')])      # "Your ship doesn't have any laser cannons. That's why you can't attack."
                self.laser_stop()
                return
            alt, msgs = self.ammo_out('lazer', ammo, len(lasers))
            self.send(msgs)
            if not alt:
                self.laser_stop()
            return                                      # geçildiyse bir sonraki atış yeni cephaneyle
        self.last_combat = now
        self.stop_repair()
        self.next_laser = now + SAVAS['lazer_aralik_sn']
        if cooldown:
            self.ammo_ready[ammo] = now + cooldown
        self.send(self.ammo_msgs(ammo) + [('AttackLaserRunCommand', dict(attackerId=self.hid, targetId=n.id,
                                                                         laserColor=self.laser_color(ammo),
                                                                         isDiminishedBySkillShield=False, skilledLaser=False, visualType=0))])
        self.p.ach('shot', silah='LASER')
        self.ammo_seen[ammo] = now                      # başarım "lazer şovu": 60 sn içinde 6 temel cephane
        recent = [AMMO_TYPE_IDS[a] for a, t in self.ammo_seen.items() if a in AMMO_TYPE_IDS and now - t <= 60]
        self.p.ach('laser_types', items=recent)
        m_ = self.p.mods()
        if random.random() < self.items.aim(AY.chance('oyuncu_isabet', SAVAS['lazer_isabet'] * (1 + m_.get('isabet', 0) + m_.get('lazer_isabet', 0)))):   # + AIM CPU'su, P.E.T. HEAT; panel
            dmg, shield_dmg = self.laser_damage(ammo, n)
            if shield_dmg:
                self.last_shield_hit = 0
                self.hit_npc(n.id, shield_dmg, 1, shield_only=True)
                if self.last_shield_hit:                 # Shield Leech (SAB-50 x2, CBO-100 x1): çekilen kalkan oyuncuya
                    g = self.p.d['gemi']
                    self.p.set_hull(shield=g.get('shield', 0) + self.last_shield_hit)
                    self.send([('AttributeShieldUpdateCommand', {'shieldNow': int(g['shield']), 'shieldMax': g.get('shieldMax', 0)})])
            if dmg:
                self.hit_npc(n.id, dmg, 1, strike=self.crit)
                self.tech.leech(ammo, dmg)               # Energy Leech
            proc = LAZER.slow_proc(self.lasers())        # LF-5 Anchorlock: adede göre şansla yavaşlatma
            if proc and n.alive and random.random() < proc[0]:
                self.npc_effect(n, 'yavas', proc[2], proc[1], source='lf-5-al')
        else:
            self.send([('AttackMissedCommand', dict(attackType=attack_type(1), targetUserId=n.id, skillColorId=0))])
        if self.p.lab_bonus(0):
            self.lab_spend(0)                   # lazer yükseltmesi: tur başına 1
        self.items.auto_weapons(n, now)         # AROL-X, RL-LB1
        if n.alive:
            self.parcacik.auto(n, now)          # RG-SL (slug), AGS-X (GSP)

    def menu_action(self, f):
        """Kısayol çubuğu. İstemcinin gönderdiği actionType öğenin türüne bağlı (istemcinin kodu, ItemMenuActionRequest): tek
        atımlık ve seçim öğeleri 1, aç-kapa ve zamanlayıcı öğeleri (gemi yetenekleri, teknoloji, gizlenme/nişan CPU'ları) 0; öğe
        çubuğunda seçim öğesine tek tıklama 0 (yanıtsız, kayıt)."""
        item = f.get('menuItemId', '')
        act = f.get('actionType')
        with self.lock:
            kind = SE.ammo_kind(item)
            if kind in ('slug', 'gsp'):                 # parçacık topu / Singularity Drive: seçilir ve hedefe ateşlenir
                self.parcacik.menu(item, act)
                return
            if kind:                                    # seçim: lazer, roket (özel roketler dahil), fırlatıcı cephanesi
                if act != 1:
                    return
                old = self.p.d['secili'].get(kind)
                if kind == 'lazer' and self.quickslot_attack(item, old):
                    return
                if item == old or self.p.ammo(item) <= 0:
                    return
                self.p.d['secili'][kind] = item
                self.p.dirty = True
                self.send([('MenuItemStatusCommand', st) for st in (self.p.menu_status(old), self.p.menu_status(item)) if st])
                self.log('   %s cephanesi: %s' % (kind, item))
                if kind == 'lazer' and self.quickslot_on() and not self.attacking:
                    self.quickslot_start()
            elif item.startswith(SE.EMOTE_PREFIX):
                if act == 1:
                    self.emote(item)                # ifade (Ö6)
            elif item.startswith('ability_'):
                self.abilities.activate(item)       # gemi yeteneği (gemi_yetenek.py)
            elif item.startswith('tech_'):
                self.tech.activate(item)            # teknoloji eşyası (teknoloji.py)
            elif self.items.menu(item):
                pass                                # mayın, Smart Bomb, Insta-Shield, EMP, CPU'lar, fırlatıcı (savas_esya.py)
            elif item.startswith('ammunition_ggportal_') and self.portal_cpu:
                self.portal_cpu(item)               # mod kapısı CPU'su (pve_modlari.py)
            elif act == 0:
                pass                                # SELECT: öğe çubuğunda tek tıklama (kayıtta gerçek sunucu yanıt vermiyor)
            elif item == 'equipment_extra_repbot_rep':
                if self.repairing:
                    self.stop_repair()
                else:
                    self.start_repair()
            else:
                self.log('   menü işlemi henüz yok: %s' % item)

    def emote(self, item, now=None):
        """İfade (kısayol çubuğunun special_items'ı): 1 adet düşer, geminin üstünde 5 sn (EmoteActivationCommand; istemci
        EmoteEffect, sprite <ad>_100x100); bütün ifadeler ortak bekleme grubunda (58, 10 sn: uyarlama)."""
        now = now or time.time()
        group = SE.O6['ifadeler']['bekleme_grubu']
        if self.hero_dead or self.p.ammo(item) <= 0 or not self.items.ready(group, now):
            return False
        if self.p.use_ammo(item, 1) is None:
            return False
        st = self.p.menu_status(item)
        self.send([('EmoteActivationCommand', {'userId': self.hid, 'lootId': item})] + ([('MenuItemStatusCommand', st)] if st else [])
                  + [self.items.cooldown(item, now)])
        self.log('   ifade: %s' % item)
        return True

    def quickslot_on(self):
        """Ayarlar > Gameplay "Start and stop attacks using the shortcut bar" (quickslotStopAttack). İstemci ayarı okumuyor, yalnız
        MenuActionRequest gönderiyor (H87). Omega AutoTactic çalışırken uygulanmaz: o da kısayol isteğiyle cephane seçer."""
        return self.p.gameplay('quickslotStopAttack') and (self.p.d.get('otopilot') or {}).get('durum') != 0

    def quickslot_start(self):
        n = self.npcs.get(self.target)
        if n and n.alive and not self.hero_dead:
            self.log('   kısayolla saldırı: %s' % n.d['ad'])
            self.laser_start({'targetId': n.id})

    def quickslot_attack(self, item, old):
        """Seçili lazer cephanesine basıldı: saldırıyorsa durur, hedef seçiliyse saldırı başlar -> işlendi mi."""
        if item != old or not self.quickslot_on():
            return False
        if self.attacking:
            self.log('   kısayolla saldırı durdu')
            self.laser_stop()
        elif self.p.ammo(item) > 0:
            self.quickslot_start()
        return True

    # ------------------------------------------------------------ onarım robotu
    def repair_rate(self):
        rep = next((e for e in self.p.d['ekipman'].get('extra', []) if e in ESYA['onarim_robotlari']), None)
        if not rep:
            return 0
        r = ESYA['onarim_robotlari'][rep]
        boost = (1 + self.p.mods().get('onarim', 0)) * AY.carpan('onarim_hizi')     # REP-B01 (booster); panel
        if self.p.premium:
            boost *= 2                                                              # Premium: "twice as effective repair robots"
        if self.low:
            boost *= self.low.regen(time.time())                                    # LoW: etkin röleler ortada hızlandırır
        if 'tam_onarim_sn' in r:
            return self.p.d['gemi'].get('hitMax', 0) / r['tam_onarim_sn'] * boost
        return r.get('dakikada_hp', 0) / 60.0 * boost

    def repbot_highlight(self):
        return dict(itemId='equipment_extra_repbot_rep', itemSource=mod('UiItemSourceModule', itemSource=0),
                    highlightType=mod('HighlightTypeModule', type=3))

    def start_repair(self):
        g = self.p.d['gemi']
        now = time.time()
        if (not self.repair_rate() or self.hero_dead or g.get('hitPoints', 0) >= g.get('hitMax', 0)
                or now - self.last_combat < ESYA['savas_disi_sn']):
            self.send([('UIItemRemoveHighlightCommand', self.repbot_highlight())])     # kayıttaki başarısız deneme yanıtı
            return
        self.repairing = True
        self.next_repair = now + 1.0
        self.send([('BeaconCommand', self.p.beacon(self.home_station(), near_gate=bool(self.near_gate), pos=self.hero_pos(now), repairing=True,
                                                    gate_peace=self.gate_peace, radiation=self.radiation_since is not None)),
                   ('UIItemAddHighlightCommand', dict(self.repbot_highlight(), soundModule=mod('SoundTriggerModule', playSound=False, soundId=0)))])
        self.log('   onarım robotu çalıştı (%.0f HP/sn)' % self.repair_rate())

    def stop_repair(self):
        if not self.repairing:
            return
        self.repairing = False
        self.send([('BeaconCommand', self.p.beacon(self.home_station(), near_gate=bool(self.near_gate), pos=self.hero_pos(), repairing=False,
                                                    gate_peace=self.gate_peace, radiation=self.radiation_since is not None)),
                   ('UIItemRemoveHighlightCommand', self.repbot_highlight())])

    # ------------------------------------------------------------ durum etkileri (durum.py)
    def npc_effect(self, n, kind, sec, value=1.0, source=None, **extra):
        """Uzaylıya durum etkisi. Donuk ve yavaş: süren hareketi o anda keser (istemci yeni hızla yeniden hesaplasın)."""
        now = time.time()
        e = n.etki.add(kind, sec, value, source, now, **extra)
        if kind in ('donuk', 'yavas') and n.mover.t1 > now:
            x, y = n.mover.pos(now)
            n.mover = Mover(x, y)
            n.next_think = now if kind == 'yavas' else now + sec
            if n.id in self.visible:
                self.send([('MoveCommand', dict(userId=n.id, x=int(x), y=int(y), timeToTarget=0))])
        return e

    # ------------------------------------------------------------ uzaylı davranış kancaları (npc.json "davranis")
    def guarded(self, n):
        """cagrilar_yasarken_dokunulmaz: çağırdıklarından biri yaşarken hasar almaz (Battleray'in Interceptor'ları …)."""
        if not n.davranis.get('cagrilar_yasarken_dokunulmaz'):
            return False
        n.children = {c for c in n.children if c in self.npcs and self.npcs[c].alive}
        return bool(n.children)

    def npc_summon(self, n, now):
        """vurulunca_cagir {tur, adet, en_cok, bekleme_sn}: vurulunca çevresine yardımcı çağırır (Cubikon -> Protegit …)."""
        v = n.davranis.get('vurulunca_cagir')
        if not v or now < n.next_summon:
            return
        n.children = {c for c in n.children if c in self.npcs and self.npcs[c].alive}
        room = v.get('en_cok', v.get('adet', 1)) + (self.alien.extra_summons(n, now) if 'ofke' in n.davranis else 0) - len(n.children)
        if room <= 0:
            return
        n.next_summon = now + v.get('bekleme_sn', 10)
        x, y = n.mover.pos(now)
        for k in range(min(room, v.get('adet', 1))):
            a = random.uniform(0, 2 * math.pi)
            c = self.spawn_npc_at(v['tur'], x + math.cos(a) * 200, y + math.sin(a) * 200)
            self.alien.adopt(n, c)
            c.engaged = True
            n.children.add(c.id)
        self.log('   %s yardım çağırdı: %d %s' % (n.d['ad'], min(room, v.get('adet', 1)), CFG['tipler'][v['tur']]['ad']))

    def npc_regen(self, n, now):
        """yenilenme {can_sn, kalkan_sn, bekleme_sn}: bekleme_sn boyunca vurulmazsa saniyede can/kalkan dolar (Cubikon …)."""
        r = n.davranis['yenilenme']
        if now < n.next_regen or now - n.last_hit < r.get('bekleme_sn', 5):
            return
        n.next_regen = now + 1.0
        hp, sh = n.hp, n.shield
        n.hp = min(n.d['hp'], n.hp + r.get('can_sn', 0))
        n.shield = min(n.d['kalkan'], n.shield + r.get('kalkan_sn', 0))
        if (n.hp, n.shield) != (hp, sh) and self.target == n.id:
            self.send([self.selection(n)])

    def hero_effect(self, kind, sec, value=1.0, source=None):
        """Oyuncuya durum etkisi: hız/isabet profil bonuslarından (profil.mods -> world_mods); hız göstergesi hemen güncellenir."""
        e = self.hero_etki.add(kind, sec, value, source)
        if kind in ('yavas', 'donuk', 'hizlanma', 'hiz_siniri') and self.stats_msgs:
            self.send(self.stats_msgs())
        return e

    def effects_tick(self, now):
        for n in list(self.npcs.values()):
            if not self.sahibi(n, now):
                continue                                  # ortak harita: uzaylının etkilerini sahibi işler
            if n.alive and n.etki.d:
                for dmg in n.etki.poison_due(now):        # zehir (Venom …): gövdeye
                    self.hit_npc(n.id, dmg, 1, hull_only=True)
                n.etki.expired(now)
            if n.alive and 'yenilenme' in n.davranis:
                self.npc_regen(n, now)
        if self.hero_etki.d and self.hero_etki.expired(now) & {'yavas', 'donuk', 'hizlanma', 'hiz_siniri', 'zayiflik'} and self.stats_msgs:
            self.send(self.stats_msgs())                  # yavaşlık/donukluk bitti: hız eski hâline

    # ------------------------------------------------------------ otomatik CPU'lar (ekstra.py)
    def auto_tick(self, now):
        """NC-RRB-X: can eksikse ve savaş dışındaysa onarım robotu kendiliğinden; ALB-X/RB-X/FB-X: eşiğin altında otomatik alım."""
        if now < self.next_auto:
            return
        self.next_auto = now + 1.0
        g = self.p.d['gemi']
        if not self.hero_dead and self.p.cargo_free() < 1:
            # kargo dolu: otomatik arıtma (ayar açıksa) kendiliğinden. Yalnız oyuncu toplarken çalışıyordu; kargo P.E.T.'in
            # toplamasıyla, Palladium'la, kapı ödülüyle, Skylab'dan doldurulunca dolu kalıyor, P.E.T. de toplamayı bırakıyordu
            msgs = self.auto_refine()
            if msgs:
                self.send(msgs)
        if (EK.has(self.p, 'oto_onarim') and not self.repairing and not self.hero_dead and g.get('hitPoints', 0) < g.get('hitMax', 0)
                and now - self.last_combat >= ESYA['savas_disi_sn'] and self.repair_rate()):
            self.start_repair()
        for loot, cfg in EK.props(self.p, 'oto_alim'):
            kind = cfg['tur']
            if now < self.auto_wait.get(kind, 0):
                continue
            if kind == 'yakit':
                if self.pet and self.pet.owned and self.pet.d['yakit'] < cfg['esik']:
                    self.auto_wait[kind] = now + 10
                    self.pet.buy_fuel(cfg['adet'])
                continue
            ammo = EK.attached(self.p, loot) or self.p.d['secili'].get('lazer' if kind == 'lazer' else 'roket')   # hangarda seçilen
            if ammo and self.p.ammo(ammo) < cfg['esik'] and self.auto_buy:
                self.auto_wait[kind] = now + 10                  # para yetmezse 10 sn sonra yeniden dener
                msgs = self.auto_buy(ammo, cfg['adet'])
                if msgs:
                    self.send(msgs)
                    self.auto_warned.discard(ammo)
                    self.log('   otomatik alım (%s): %s x%d' % (loot, ammo, cfg['adet']))
                elif self.auto_buy_fail and ammo not in self.auto_warned:
                    warn = self.auto_buy_fail(ammo, cfg['adet'])     # para yetmedi: istemcinin metni, alım olana dek bir kez
                    if warn:
                        self.auto_warned.add(ammo)
                        self.send(warn)

    def hp_msg(self):
        g = self.p.d['gemi']
        return ('HitpointInfoCommand', dict(hitpoints=int(g['hitPoints']), hitpointsMax=g.get('hitMax', 0),
                                            nanoHull=int(g.get('nanoHull', 0)), nanoHullMax=g.get('maxNanoHull', 0)))

    def heal_msgs(self, hp0=None, sh0=None):
        """İyileşmenin "+miktar" sayısı (Ö1): 0|A|HL|<iyileştiren>|<hedef>|HPT ya da SHD|<yeni değer>|<miktar>. İstemci
        (SetAttributeAssemblyHelper.AssembleHealInfo) hedefin canını/kalkanını yazar ve sayıyı çıkarır (can yeşil, kalkan mavi).
        hp0 / sh0: iyileşmeden önceki değerler; artmadıysa mesaj yok. Kalkanın kendiliğinden dolmasında kullanılmaz."""
        g, out = self.p.d['gemi'], []
        for kind, before, now in (('HPT', hp0, g.get('hitPoints', 0)), ('SHD', sh0, g.get('shield', 0))):
            if before is not None and int(now) > int(before):
                out.append(legacy('0|A|HL|%d|%d|%s|%d|%d' % (self.hid, self.hid, kind, int(now), int(now) - int(before))))
        return out

    def repair_tick(self, now):
        g = self.p.d['gemi']
        if self.hero_dead or now - self.last_combat < ESYA['savas_disi_sn']:
            self.stop_repair()
            return
        if now < self.next_repair:
            return
        self.next_repair = now + 1.0
        hp0 = g.get('hitPoints', 0)
        self.p.set_hull(hp=hp0 + self.repair_rate())
        self.send([('HitpointInfoCommand', dict(hitpoints=int(g['hitPoints']), hitpointsMax=g.get('hitMax', 0),
                                                nanoHull=g.get('nanoHull', 0), nanoHullMax=g.get('maxNanoHull', 0)))]
                  + self.heal_msgs(hp0))
        if getattr(self.kapi, 'key', None) == 'dunya_patronu':
            self.p.ach('wb_heal', adet=g['hitPoints'] - hp0)          # World Boss başarımı (recoverhp)
        if g['hitPoints'] >= g.get('hitMax', 0):
            self.stop_repair()
            self.log('   onarım tamam')

    def music_tick(self, now):
        """Savaş müziği (Ö1): savaş başlayınca CombatMusicCommand 0 (START), savaş dışına çıkınca 1 (END). İstemci Ses ayarlarındaki
        savaş müziği açıksa ve haritada kapalı değilse çalar (MapViewComponentSystem.UpdateMusic)."""
        fight = not self.hero_dead and now - self.last_combat < ESYA['savas_disi_sn']
        if fight != self.combat_music:
            self.combat_music = fight
            g = self.p.d['gemi']
            hurt = not fight and not self.hero_dead and g.get('hitPoints', 0) < g.get('hitMax', 0)
            self.send([('CombatMusicCommand', {'combatEvent': 0 if fight else 1})] + (self.p.hint(IP.SHIP_REPAIR) if hurt else []))

    def shield_tick(self, now):
        """Savaş dışında kalkan dolar (kalkan jeneratörü takılıysa; oran esyalar.json kalkan_yenilenme_sn)."""
        g = self.p.d['gemi']
        k = AY.carpan('kalkan_yenilenme')                   # panel: 0 dolmaz
        if (now < self.next_shield or self.hero_dead or g.get('shield', 0) >= g.get('shieldMax', 0) or k <= 0
                or now - self.last_combat < ESYA['savas_disi_sn']):
            return
        self.next_shield = now + 1.0
        rate = ESYA['kalkan_yenilenme_sn'] * (1 + self.p.mods().get('kalkan_yenilenme', 0)) * k   # SREG-B01 (booster)
        self.p.set_hull(shield=g.get('shield', 0) + max(1, g['shieldMax'] * rate))
        self.send([('AttributeShieldUpdateCommand', {'shieldNow': int(g['shield']), 'shieldMax': g['shieldMax']})])

    def settings_tick(self, now):
        """Panelin ayar dosyası değişti (saniyede bir bakılır): geminin can, kalkan, hız ve kargo değerleri oyun açıkken yeniden
        (magaza.apply_stats; yalnız değişen değer gönderilir). Haritaya girince de bir kez: oyun kapalıyken değişen ayarlar."""
        if now < self.next_ayar or not self.stats_msgs or self.hero_dead:
            return
        self.next_ayar = now + 1.0
        v = AY.surum()
        if v != self.ayar_surum:
            self.ayar_surum = v
            msgs = self.stats_msgs()
            if msgs:
                self.send(msgs)

    def form_shield_tick(self, now):
        """Formasyonun kalkan etkisi, saniyede bir: Diamond %1/sn (en çok 5.000) ve 3D Dome %0,5/sn savaşta da doldurur; Moth ve
        3D Wheel %5/sn eritir (istemci: "drains shields by 5% per second", savaş koşulu yok)."""
        if now < self.next_form_shield:
            return
        self.next_form_shield = now + 1.0
        m = self.p.mods()
        up, down = m.get('kalkan_dolum_sn', 0), m.get('kalkan_erime_sn', 0)
        if self.hero_dead or not (up or down):
            return
        g = self.p.d['gemi']
        mx, sh = g.get('shieldMax', 0), g.get('shield', 0)
        delta = min(mx * up, m.get('kalkan_dolum_azami') or mx * up)
        delta -= mx * down
        new = max(0, min(mx, sh + delta))
        if int(new) != int(sh):
            self.p.set_hull(shield=new)
            self.send([('AttributeShieldUpdateCommand', {'shieldNow': int(g['shield']), 'shieldMax': mx})])

    def npc_shoot(self, n, now):
        if self.pet:
            self.pet.shot_by.discard(n.id)      # yeni salvo öncekinin yerine geçer; P.E.T.'e giderse take_shot yeniden ekler
        if self.ally and self.ally.take_shot(n, now):
            return                              # atış dost gemiye gitti (echoes.py)
        if self.alien.extra_target(n, now):
            if self.pet:
                self.pet.take_shot(n, now, force=True)     # birden çok hedef (Mindfire Behemoth): P.E.T.'e de
                self.pet.shot_by.discard(n.id)             # ardından gemiye: son salvo gemide
        elif self.pet and self.pet.take_shot(n, now):
            return                              # atış P.E.T.'e gitti
        ddol = n.etki.get('atis_bozuk', now)          # Disruptor DDoL: lazer beklemesi 3-5 sn
        n.next_shot = now + (random.uniform(*ddol[0]['aralik']) if ddol else n.d.get('atis_aralik_sn', SAVAS['npc_saldiri_aralik_sn']))
        m = self.p.mods()
        msgs = [('AttackLaserRunCommand', dict(attackerId=n.id, targetId=self.hid, laserColor=0,
                                               isDiminishedBySkillShield=m.get('alinan_lazer', 0) < 0,     # Spectrum
                                               skilledLaser=False, visualType=0))]
        if random.random() < AY.chance('npc_isabet', n.d.get('isabet', SAVAS['npc_isabet'])) * (1 - m.get('kacinma', 0)) * (1 - n.etki.accuracy_loss(now)):
            raw = n.d['hasar'] * random.uniform(0.8, 1.0) * self.alien.laser_factor(n, now)      # kayıt: x0,8-1,0; öfke, DMG kapsülü
            dmg = int(raw * max(0.0, 1 + m.get('alinan_lazer', 0)))                              # Spectrum
            self.hurt_hero(dmg, n, msgs=msgs, now=now)
            if raw - dmg >= 1 and n.alive and GY.effect(self.p, 'lazer_yansit', now):
                self.hit_npc(n.id, int(raw - dmg), 1)  # Spectrum Plus Prismatic Reflecting: azaltılan hasar saldırana
            self.alien.after_shot(n, now, True)        # yavaşlatan atış (uzayli.py)
        else:
            self.last_combat = now
            self.stop_repair()
            msgs.append(('AttackMissedCommand', dict(attackType=attack_type(1), targetUserId=self.hid, skillColorId=0)))
        self.send(msgs)

    def hurt_hero(self, dmg, killer=None, atype=1, msgs=None, now=None, cause=None):
        """Oyuncuya hasar (uzaylının lazeri, roketi, bombası, tekilliği, patlaması): Fortify, Insta-Shield; kalkan jeneratörlerin
        oranıyla emer, nano gövde kalkandan sonra gövdeden önce erir; Anti-AI tabanı; test dokunulmazlığı. -> mesajlar
        (AttackHitCommand; can biterse ölüm ekranı)."""
        now = now or time.time()
        msgs = [] if msgs is None else msgs
        g, m = self.p.d['gemi'], self.p.mods()
        yer = 'dalga' if getattr(killer, 'hunt', False) else 'harita'      # panelin hasar alt ayarı: kapı ve mod dalgası mı
        dmg = int(dmg * max(0.0, 1 + m.get('alinan_hasar', 0)) * AY.carpan('npc_hasar', yer))      # Fortify; panelin hasar çarpanı
        if self.hero_etki.invulnerable(now):
            dmg = 0                                 # Insta-Shield (savas_esya.py)
        if dmg and killer is not None and getattr(killer, 'alive', False):
            back = GY.effect(self.p, 'yansit', now)                   # Berserker Revenge: hasar saldırana döner
            if back:
                self.hit_npc(killer.id, int(dmg * back), 1)
            heal = GY.effect(self.p, 'emme_can', now)                 # Orcus Assimilate: uzaylı hasarı cana döner
            if heal:
                self.p.set_hull(hp=g.get('hitPoints', 0) + dmg * heal)
                dmg = int(dmg * (1 - heal))
        self.last_hurt = self.last_combat = now
        self.stop_repair()
        if dmg > 0:
            self.p.ach('damage_taken', adet=dmg)       # alınan hasar (görev koşulu TAKE_DAMAGE; Galaxy Trek'in Endurance görevi)
            if getattr(self.kapi, 'key', None) == 'dunya_patronu':
                self.p.ach('wb_damage', adet=dmg)      # World Boss başarımı (takedamage)
        sh = g.get('shield', 0)
        to_shield = min(sh, int(dmg * self.p.d.get('kalkan_emme', 0.8)))   # kalkan jeneratörlerinin emme oranı (esyalar.json)
        hull = dmg - to_shield
        stim, sb = 0, self.p.ship_row().get('stim_bariyer')
        if sb and hull > 0 and random.random() < sb['sans']:      # Pusat Plus Stim Barrier: gövde hasarının %10'u alınmaz, cana döner
            stim = int(hull * sb['oran'])
            hull -= stim
            msgs.append(stm('msg_stim_barrier_activated'))
        nano = g.get('nanoHull', 0)
        from_nano = min(nano, hull)                # nano gövde (kapı çekilişi): kalkandan sonra, gövdeden önce erir
        linked = self.pet.link_take(hull - from_nano) if self.pet and not self.invulnerable else 0   # G-HPL1: gövde hasarı P.E.T.'e
        hp = g.get('hitPoints', 0) - (hull - from_nano - linked) + stim
        floor = self.tech.hp_floor(now)             # Anti-AI Emergency Reserves
        if floor:
            hp = max(hp, floor)
        if hp <= 0 and self.abilities.hold_on(now):                      # Tempest Volt Back-up: can 1, 3 sn dokunulmaz
            hp = 1
        if hp <= 0 and self.abilities.last_stand(now):                   # Paladin Last Stand: can dolar
            hp = g.get('hitMax', hp)
        to_shield = int(to_shield * max(0.0, 1 + m.get('kalkan_hasari', 0)))      # Sentinel: kalkan daha az erir
        if not self.invulnerable:
            self.p.set_hull(hp=hp, shield=sh - to_shield)
            with self.p.lock:
                g['nanoHull'] = nano - from_nano
        msgs.append(('AttackHitCommand', dict(attackType=attack_type(atype), attackerId=killer.id if killer else 0, victimId=self.hid,
                                              victimHitpoints=int(g['hitPoints']), victimShield=int(g.get('shield', 0)),
                                              victimNanoHull=int(g.get('nanoHull', 0)), damage=dmg, skilled=False, strike=False,
                                              cannonType=0)))
        if g['hitPoints'] > 0 and self.pet:
            self.pet.ship_hurt(now)                 # G-KK1: geminin canı eşiğin altında
        if g['hitPoints'] <= 0 and not self.hero_dead:
            self.hero_death(msgs, killer, cause=cause)
        return msgs

    # ------------------------------------------------------------ boosterlar
    def booster_tick(self, now):
        """Saniyede bir: uzaylıdan düşen boosterın süresi azalır; süresi biten booster düşer (gösterge + can/kalkan sınırı)."""
        if now < self.next_booster:
            return
        dt = 1.0 if self.next_booster == 0 else now - self.next_booster + 1.0
        self.next_booster = now + 1.0
        gone = BOOSTER.tick(self.p, now, min(dt, 5.0))
        if gone:
            self.send([BOOSTER.update_cmd(self.p, removed=gone)] + (self.stats_msgs() if self.stats_msgs else []))
            self.log('   booster bitti: %s' % ', '.join(gone))

    def booster_drop(self, n):
        """Boss/Uber uzaylıdan booster (wiki: 1-10 saat; çevrimdışı durur)."""
        got = BOOSTER.drop_for(n.d['ad'])
        if not got:
            return []
        loot, hours = got
        BOOSTER.add(self.p, loot, seconds=hours * 3600)
        self.log('   booster bulundu: %s (%d saat)' % (loot, hours))
        shown = max(1, int(round(hours * AY.carpan('booster_sure'))))      # BOOSTER.add süreyi panelin çarpanıyla uzatır
        return ([('BoosterFoundOnMapCommand', {'lootId': loot, 'hours': shown}), BOOSTER.update_cmd(self.p)]
                + (self.stats_msgs() if self.stats_msgs else []))

    # ------------------------------------------------------------ radyasyon
    def radiation_tick(self, now):
        """Harita sınırının dışı radyasyon: BeaconCommand.inRadiationZone, uyarı (istemcinin msg_radiation_warning metni) ve her
        saniye gövdeye azami canın %1'i, %5'e dek artarak (wiki). Ölürse sebep radyasyon."""
        if self.hero_dead:
            self.radiation_since = None
            return
        hx, hy = self.hero_pos(now)
        inside = 0 <= hx <= self.map_w and 0 <= hy <= self.map_h
        if inside and self.kapi and hasattr(self.kapi, 'safe_at'):
            inside = self.kapi.safe_at(hx, hy, now)          # Ö4: Mimesis Mutiny'de koruma alanının dışı radyasyon
        if inside:
            if self.radiation_since is not None:
                self.radiation_since = None
                self.send([self.beacon_msg(now)])
                self.log('   radyasyon bölgesinden çıkıldı')
            return
        if self.radiation_since is None:
            self.radiation_since, self.next_radiation = now, now + 1.0
            self.send([self.beacon_msg(now), ('MessageCommand', dict(
                displayTarget=2, displayStyle=0, messageModule=mod('WildcardMessageModule', message=mod(
                    'MessageKeyListWildcardModule', wildCardReplacements=[], baseKey='msg_radiation_warning',
                    baseKeyType=mod('ReplacementTypeModule', typeValue=5), textStyle=0))))])
            self.log('   radyasyon bölgesi (%d,%d)' % (hx, hy))
            return
        if now < self.next_radiation:
            return
        self.next_radiation += 1.0
        lo, hi = SAVAS['radyasyon_yuzde']
        pct = min(hi, lo * (1 + int((now - self.radiation_since) / SAVAS['radyasyon_artis_sn']))) * AY.carpan('radyasyon')   # panel
        g = self.p.d['gemi']
        self.stop_repair()
        if not self.invulnerable:
            self.p.set_hull(hp=g.get('hitPoints', 0) - int(g.get('hitMax', 0) * pct))
        msgs = [('HitpointInfoCommand', dict(hitpoints=int(g['hitPoints']), hitpointsMax=g.get('hitMax', 0),
                                             nanoHull=int(g.get('nanoHull', 0)), nanoHullMax=g.get('maxNanoHull', 0)))]
        if g['hitPoints'] <= 0:
            self.hero_death(msgs, cause=DESTRUCTION_RADIATION)
            self.radiation_since = None
        self.send(msgs)

    def beacon_msg(self, now):
        return ('BeaconCommand', self.p.beacon(self.home_station(), near_gate=bool(self.near_gate), pos=self.hero_pos(now),
                                               repairing=self.repairing, gate_peace=self.gate_peace,
                                               radiation=self.radiation_since is not None))

    # ------------------------------------------------------------ ölüm ve ölüm ekranı
    def ach_tick(self, now):
        """Başarım sayaçları: kat edilen yol (saniyede bir; ışınlanma sayılmaz) ve oyun süresi (dakikada bir; P.E.T. etkin mi,
        başka firmanın haritası mı, PvP haritası (4-X) mı)."""
        if now < self.ach_next:
            return
        self.ach_next = now + 1.0
        pos = self.hero_pos(now)
        if self.ach_pos and not self.hero_dead and not self.jumping:
            d = math.hypot(pos[0] - self.ach_pos[0], pos[1] - self.ach_pos[1])
            if d < 2000:
                self.ach_dist += d
                if self.ach_dist >= 1:
                    self.p.ach('distance', adet=int(self.ach_dist))
                    self.ach_dist -= int(self.ach_dist)
        self.ach_pos = pos
        self.ach_secs += 1
        if self.ach_secs >= 60 and not self.hero_dead:
            self.ach_secs = 0
            comp = H.company(self.map_id)
            self.p.ach('minute', pet=bool(self.pet and self.pet.active), pvp_harita=H.name(self.map_id).startswith('4-'),
                       dusman_harita=bool(comp and comp != self.p.d['pilot'].get('factionId')))
            if self.abilities.cloaked(now) or self.items.cloaked():
                self.p.ach('cloak_minute')          # başarım PlayerCloaked (dakika)

    def kill_streak(self, now=None):
        """Seri öldürme (Ö2; panelin 'seri_oldurme' ayarı). İstemci "0|n|KSMSG|<anahtar>" ile duyurunun sesini çalar
        (MapEventsAssemblyHelper.AssembleKillstreakMessage: triplekill, unstoppable, godlike, likeaboss -> ses 0x53-0x56); yazısı aynı
        anahtarla ekran iletisi (STM). Eşikler uyarlama (gerçek sunucunun PvP eşikleri bilinmiyor): STREAK_GAP_SN içinde art arda 3, 6,
        10, 15 öldürme; 15'ten sonra her 5'te "Like a boss!". Ölünce seri sıfırlanır."""
        now = time.time() if now is None else now
        st = self.streak
        st[0] = st[0] + 1 if now - st[1] <= STREAK_GAP_SN else 1
        st[1] = now
        if st[0] == 1:
            st[2] = 0
        key = next((k for c, k in STREAKS if st[0] == c), None)
        if key is None and st[0] > STREAKS[-1][0] and (st[0] - STREAKS[-1][0]) % 5 == 0:
            key = STREAKS[-1][1]
        if not key or not AY.get('seri_oldurme'):
            return []
        st[2] = st[0]
        self.log('   seri öldürme: %d (%s)' % (st[0], key))
        return [legacy('0|n|KSMSG|%s' % key), stm(key)]

    def hero_death(self, msgs, killer=None, cause=None, note=None):
        """Oyuncu öldü: patlama + ölüm ekranı (KillScreenPostCommand). Oyuncu ekranda bir tamir seçince doğar (kill_screen_repair)."""
        self.hero_dead = True
        self.streak = [0, 0.0, 0]                                     # seri bozuldu
        self.cinematic_end()                                          # kamera kilidi kalmasın
        self.attacking = False
        self.stop_repair()
        if self.pet:
            self.pet.hero_died()
        self.abilities.on_death()
        self.items.on_death()
        self.tech.on_death()
        self.gate_lives = self.kapi.on_death() if self.kapi else None
        if self.low:
            self.low.on_death()
        x, y = (int(v) for v in self.hero_pos())
        self.hero = Mover(x, y)
        self.death_pos = (x, y)
        self.death_time = time.time()
        if self.raid_gate():
            self.later(HADES_RESPAWN_SN + 0.5, self.raid_expired)
        self.p.d['konum'].update(x=x, y=y)
        for n in self.npcs.values():
            if self.bizim(n):
                n.engaged = False
        msgs.append(('ShipDestroyedCommand', dict(destroyedUserId=self.hid, explosionTypeId=0)))
        msgs.append(('KillScreenPostCommand', dict(
            killerName=killer.d['ad'] if killer else '', killerEpppLink='', playerShipAlias=self.p.ship_look(),
            cause=mod('DestructionTypeModule', cause=cause or (DESTRUCTION_NPC if killer else DESTRUCTION_MISC)),
            options=self.repair_options())))
        self.log('   oyuncu yok edildi (%s): ölüm ekranı' % (killer.d['ad'] if killer else '?'))
        self.p.ach('death', npc=killer.d.get('npc_kimlik') if killer else None,
                   neden={DESTRUCTION_RADIATION: 'RADIATION'}.get(cause, 'NPC' if killer else 'MISC'))
        key = note or ('killed_by_radiation' if cause == DESTRUCTION_RADIATION
                       else 'killed_by_npc_%s' % killer.d.get('npc_kimlik', 0) if killer else None)
        if key:
            RT.note(self.p, key)                        # seyir defteri
        if self.olum:
            self.olum()                                 # grup üyelerine "vuruldu"

    def raid_gate(self):
        """Hades'te canı kalan oyuncu kapı haritasında yeniden doğabilir (ölümden sonra HADES_RESPAWN_SN içinde)."""
        k = self.kapi
        return bool(k and k.key == 'hades' and self.gate_lives and time.time() - self.death_time < HADES_RESPAWN_SN)

    def raid_expired(self):
        if self.hero_dead and self.kapi:
            self.send([('KillScreenUpdateCommand', {'options': self.repair_options()})])     # kapıda doğma seçeneği kalkar

    def vouchers(self):
        """Onarım kuponları (kapıların ürettiği "repair credit"; istemci: ttip_repair-vouchers_count)."""
        return int((self.p.d.get('kapilar') or {}).get('kupon', 0))

    def repair_offers(self):
        """Ölüm ekranındaki seçenekler: tür -> uridyum fiyatı. İstasyonda tamir ücretsiz; portalda tamir haritada portal varsa.
        Onarım kuponu varsa portalda ve yerinde tamir kuponla (ücretsiz; istemci: "Use repair credit")."""
        offers = {REPAIR_BASE: 0}
        if self.kapi and hasattr(self.kapi, 'repair_offers'):
            return self.kapi.repair_offers()      # Ö4: Vortex of Greed'in ücretsiz yerinde doğması (STRIKE_AND_EXIT)
        if self.low:
            return offers                       # LoW: yalnız istasyonda (X-1); X-3'teki portaldan dönüş süresi içinde dönülür
        if self.kapi:
            if self.raid_gate():
                offers[REPAIR_RAID_GATE] = 0    # Hades: kapı haritasında ücretsiz (istemci: ttip_killscreen_repair_hadesgate)
            return offers                       # kapıda: üste ücretsiz tamir (istemci: galaxygates_pvemap_leave_on_kill_p)
        voucher = self.vouchers() > 0
        k = AY.carpan('tamir_ucreti')                                   # panelin tamir ücreti çarpanı
        if self.gates:
            offers[REPAIR_GATE] = 0 if voucher or self.free_gate_repair() else int(round(OLUM['portal_uridyum'] * k))
        offers[REPAIR_LOCATION] = 0 if voucher else int(round(OLUM['yerinde_uridyum'] * k))
        return offers

    def repair_options(self):
        """KillScreenOptionModule listesi. Simge ve ipucunu istemci seçenek türünden kendisi seçer; fiyat, gücün yetip yetmediği,
        ayrıntı metni ve düğme yazısı buradan (istemcinin çeviri anahtarları)."""
        u = self.p.d['pilot'].get('uridium', 0)
        out = []
        vouchers = self.vouchers()
        for kind, price in self.repair_offers().items():
            if kind not in REPAIR_TEXTS:          # koşucunun seçeneği (Ö4): metinleri ondan
                desc, ttip, btn, (akey, aparams) = self.kapi.repair_texts(kind)
                out.append(mod('KillScreenOptionModule', repairType=mod('KillScreenOptionTypeModule', repairTypeValue=kind),
                               price=mod('PriceModule', type=1, amount=price), affordableForPlayer=True, cooldownTime=0,
                               descriptionKey=loc(desc), descriptionKeyAddon=loc(akey, **aparams), toolTipKey=loc(ttip),
                               buttonKey=loc(btn)))
                continue
            desc, ttip, btn = REPAIR_TEXTS[kind]
            count, addon = price, loc('')
            if self.kapi and kind == REPAIR_BASE:
                desc, price = ('desc_killscreen_free_repair_cause_galaxygate_lives' if self.gate_lives
                               else 'desc_killscreen_free_repair_cause_galaxygate'), self.gate_lives or 0
                count = price
            elif kind == REPAIR_RAID_GATE:
                count = self.gate_lives or 0
                addon = loc('desc_killscreen_option_available_countdown_hadesgate',
                            COUNTDOWN=max(0, int(HADES_RESPAWN_SN - (time.time() - self.death_time))))
            elif kind in (REPAIR_GATE, REPAIR_LOCATION) and vouchers:
                desc, btn, count = ('desc_killscreen_repair_voucher_s' if vouchers == 1 else 'desc_killscreen_repair_voucher_p',
                                    'btn_killscreen_repair_voucher', vouchers)
            out.append(mod('KillScreenOptionModule', repairType=mod('KillScreenOptionTypeModule', repairTypeValue=kind),
                           price=mod('PriceModule', type=1, amount=price), affordableForPlayer=u >= price, cooldownTime=0,
                           descriptionKey=loc(desc, COUNT=count), descriptionKeyAddon=addon, toolTipKey=loc(ttip),
                           buttonKey=loc(btn, COUNT=count)))
            if self.kapi and kind == REPAIR_BASE:
                out[-1]['price'] = mod('PriceModule', type=1, amount=0)
                out[-1]['affordableForPlayer'] = True
        return out

    def kill_screen_repair(self, f):
        """KillScreenRepairRequest: seçilen tamir. İstasyonda: tam can (istasyonsuz haritada firmanın ana haritasında);
        portalda: ölüm yerine en yakın portalda tam can; yerinde: canın %10'u ve saldırı koruması."""
        kind = (f.get('selection') or {}).get('repairTypeValue')
        with self.lock:
            if not self.hero_dead:
                return
            price = self.repair_offers().get(kind)
            if price is None or self.p.d['pilot'].get('uridium', 0) < price:
                self.log('   tamir olmadı: seçenek %s, fiyat %s' % (kind, price))
                self.send([('KillScreenUpdateCommand', {'options': self.repair_options()})])
                return
            msgs = []
            if price:
                self.p.gain(uridyum=-price, neden='repair_ship')
                msgs += self.money_msgs() if self.money_msgs else []
            elif kind in (REPAIR_GATE, REPAIR_LOCATION) and self.vouchers() > 0 and not self.kapi:
                with self.p.lock:
                    self.p.d['kapilar']['kupon'] -= 1          # onarım kuponu kullanıldı (istemci: repair_voucher_used)
                    self.p.dirty = True
                self.log('   onarım kuponu kullanıldı (kalan %d)' % self.vouchers())
            g = self.p.d['gemi']
            hp, shield = g.get('hitMax', 1), g.get('shieldMax', 0)
            x, y = self.death_pos or self.hero_pos()
            if kind == REPAIR_BASE and not self.home_station() and self.on_home:
                self.p.set_hull(hp=hp, shield=shield)
                self.hero_dead = False
                self.send(msgs)
                self.log('   istasyonda tamir: firmanın ana haritasında doğuyor')
                self.on_home()                   # harita değişir; bu dünya durur
                return
            if kind not in REPAIR_TEXTS:              # koşucunun seçeneği (Ö4): konumu ondan, ya da henüz değil
                spot = self.kapi.repair(kind) if self.kapi and hasattr(self.kapi, 'repair') else None
                if not spot:
                    self.send([('KillScreenUpdateCommand', {'options': self.repair_options()})])
                    return
                x, y = spot
            elif kind == REPAIR_BASE and self.home_station():
                x, y = self.station['posX'], self.station['posY']
            elif kind == REPAIR_RAID_GATE:
                x, y = self.map_w // 2, self.map_h // 2         # Hades: kapı haritasının ortasında, tam canla; dalga sürer
                self.kapi.revive()
            elif kind == REPAIR_GATE:
                gate = min(self.peace_gates() or self.gates, key=lambda gt: math.hypot(gt['x'] - x, gt['y'] - y))
                x, y = gate['x'], gate['y']
            elif kind == REPAIR_LOCATION:
                hp, shield = max(1, int(hp * AY.get('yerinde_can') / 100.0)), 0             # panel (oyunun değeri %10, 10 sn)
                self.invuln_until = time.time() + AY.get('yerinde_koruma')
            self.p.set_hull(hp=hp, shield=shield)
            self.p.d['konum'].update(x=int(x), y=int(y))
            self.hero = Mover(int(x), int(y))
            self.hero_dead = False
            self.death_pos = None
            self.target, self.attacking = None, False
            self.reload_pending = True
            if self.pet:
                self.pet.reload()
            self.send(msgs + self.reload_msgs())
            self.log('   tamir (%s, %d U): (%d,%d) konumunda %d HP ile doğdu' % (
                {REPAIR_BASE: 'istasyonda', REPAIR_GATE: 'portalda', REPAIR_LOCATION: 'yerinde'}.get(kind, 'koşunun seçeneği %s' % kind),
                price, x, y, hp))

    def invuln_msg(self, on):
        return ('VisualModifierCommand', dict(userId=self.hid, modifier=INVINCIBILITY, attribute=0, additionalAttribute='',
                                              count=1 if on else 0, activated=on))

    def end_invuln(self, force=False):
        """Yerinde tamirin saldırı koruması biter (süre doldu ya da oyuncu saldırdı)."""
        if self.invuln_until and (force or time.time() >= self.invuln_until - 0.05):
            self.invuln_until = 0.0
            self.send([self.invuln_msg(False)])
            self.log('   saldırı koruması bitti')

    def near_zone(self, x, y, margin):
        """Güvenli bölgenin (istasyon, portallar) margin kadar genişletilmiş hâlinin içinde mi."""
        s = self.station
        if s and math.hypot(x - s['posX'], y - s['posY']) <= s['peaceRadius'] + margin:
            return True
        return any(math.hypot(g['x'] - x, g['y'] - y) <= H.GATE_PEACE_RADIUS + margin for g in self.gates)

    def spot_away(self, hx, hy):
        """Güvenli bölgelerden ve oyuncudan uzak bir dolaşma noktası."""
        best = None
        for _ in range(20):
            x, y = self.random_spot()
            if math.hypot(x - hx, y - hy) > 3000:
                return x, y
            best = best or (x, y)
        return best

    def disengage(self, n, now, flee=True):
        """Peşini bırak. flee: bir sonraki düşüncede güvenli bölgeden ve oyuncudan uzaklaşır (dalga uzaylısı kaçmaz, yerinde bekler)."""
        if n.engaged and not self.hero_dead:
            self.send(self.combat_state(COMBAT_ESCAPED, now))        # "You escaped the attack."
        n.engaged = False
        n.flee = flee
        n.next_think = now

    def combat_state(self, state, now):
        """Savaş durumu satırı (Ö1): CombatStateCommand {combatState}; istemci (AttackUpdateCombatState) günlüğe yazar: 0 "Out of
        range", 1 "The battle continues.", 2 "You escaped the attack.". Aynı durum 5 sn içinde tekrarlanmaz (birden çok uzaylı)."""
        last, t = self.combat_sent
        if state == last and now - t < 5.0:
            return []
        self.combat_sent = (state, now)
        return [('CombatStateCommand', {'combatState': state})]

    def think(self, n, now):
        """NPC yapay zekâsı: dolaş; saldırıya uğrayan ya da saldırgan türse oyuncuyu kovala ve ateş et."""
        if n.d.get('dost'):
            return                              # dost gemiyi modu yönetir (echoes.py)
        if getattr(n, 'pasif', False):
            n.engaged = False                   # ateş etmeyen uzaylı (Infiltration komandosu: sizma.py)
        hx, hy = self.hero_pos(now)
        nx, ny = n.mover.pos(now)
        dist = math.hypot(hx - nx, hy - ny)
        hero_safe = (self.in_peace(hx, hy) or self.hero_dead or self.jumping or self.abilities.cloaked(now)
                     or self.items.cloaked())                      # gizlenme CPU'su
        # dalga uzaylısı (kapı, mod): uzaklık ve saldırganlık ayarından bağımsız hep oyuncunun peşinde. Önceden 2.500 birimden uzak
        # kalınca ya da oyuncu ölüp dirilince/gizlenince peşini bırakıp oyuncudan 3.000+ birim uzağa dolaşmaya gidiyor, kapıda kalan
        # uzaylılar bulunamıyordu (kullanıcı bildirimi, 2026-10-22: Delta Gate dalga III)
        hunt = n.hunt and not getattr(n, 'pasif', False)
        if hunt and not n.engaged and not hero_safe and now >= n.next_think:
            n.engaged = True                    # oyuncu yine ulaşılabilir (dirildi, gizlenme bitti, EMP geçti …)
        if (self.aggressive(n) and not getattr(n, 'pasif', False) and not hero_safe
                and dist < n.d.get('fark_mesafe', SAVAS['npc_fark_mesafe']) * AY.carpan('npc_fark')
                and not self.in_peace(nx, ny)
                and not n.engaged):
            n.engaged = True
            n.next_think = min(n.next_think, now)      # hemen kovalamaya başla (--yakin-npc ile dondurulmuş olsa da)
            self.log('   %s saldırıyor (mesafe %d)' % (n.d['ad'], dist))
        if n.engaged and (hero_safe or (dist > 2500 and not hunt)):
            self.disengage(n, now, flee=not hunt)   # oyuncu güvenli bölgeye kaçtı: peşini bırak ve uzaklaş (portalın önünde beklemez)
        if n.etki.frozen(now):
            return                              # donuk: kıpırdamaz, ateş etmez (durum.py)
        if n.engaged:
            if dist > 450 and now >= n.next_think and n.speed() > 0:
                a = math.atan2(ny - hy, nx - hx) + n.spread
                # harita içinde: oyuncu kenarda ya da sınırın dışındayken (radyasyon) uzaylı haritadan çıkmasın
                tx = min(max(hx + math.cos(a) * n.keep, 300), self.map_w - 300)
                ty = min(max(hy + math.sin(a) * n.keep, 300), self.map_h - 300)
                if not hunt and self.near_zone(tx, ty, 0):
                    self.disengage(n, now)          # güvenli bölgeye girmez
                    return
                if not (hunt and self.in_peace(tx, ty)):     # dalga uzaylısı güvenli bölgenin kenarında bekler
                    ms = n.mover.go(tx, ty, n.speed() * n.etki.speed_factor(now), now)
                    self.send([('MoveCommand', dict(userId=n.id, x=int(tx), y=int(ty), timeToTarget=ms))])
                n.next_think = now + 1.0
            if dist <= self.npc_range(n) and now >= n.next_shot and n.d['hasar'] > 0 and now >= self.invuln_until:
                if n.next_shot == 0.0:
                    self.send([legacy('0|n|LSH|%d|%d' % (self.hid, n.id))])
                self.npc_shoot(n, now)
            return
        if hunt:
            return                              # dalga uzaylısı dolaşmaz: oyuncu yine ulaşılabilir olunca peşine düşer
        if now >= n.next_think and n.speed() <= 0:
            n.next_think = now + 3600          # hareketsiz (Cubikon, Mindfire Behemoth)
        elif now >= n.next_think:
            r = random.uniform(300, 1200)
            a = random.uniform(0, 2 * math.pi)
            tx = min(max(nx + math.cos(a) * r, 300), self.map_w - 300)
            ty = min(max(ny + math.sin(a) * r, 300), self.map_h - 300)
            leaving = n.flee or self.near_zone(nx, ny, 500)
            if leaving or self.near_zone(tx, ty, 500):
                tx, ty = self.spot_away(hx, hy)     # güvenli bölgenin içinden/kenarından uzaklaş, oyuncudan uzağa
            n.flee = False
            ms = n.mover.go(tx, ty, n.speed() * (1.0 if leaving else 0.6) * n.etki.speed_factor(now), now)
            self.send([('MoveCommand', dict(userId=n.id, x=int(tx), y=int(ty), timeToTarget=ms))])
            n.next_think = now + ms / 1000 + random.uniform(2, 6)

    def loop(self):
        self._loop_ident = threading.get_ident()
        while self.running:
            time.sleep(0.1)
            with self.lock:
                if not self.running:
                    break                      # durduruldu (harita değişimi) ama döngü kilidi bekliyordu: bir adım daha işlemesin
                t0 = time.perf_counter()
                self._batch = []
                try:
                    self.step(time.time())
                except Exception:               # iş parçacığı ölmesin (uzaylılar ve zamanlayıcılar dururdu); sonraki adım yeniden dener
                    self.step_error('adım')
                finally:
                    batch, self._batch = self._batch, None
                if batch:                       # kilit altında: oturumun sonraki mesajlarından önce, aynı sırayla
                    try:
                        self.send_raw(batch)
                    except OSError:
                        self.running = False
                    except Exception:
                        self.step_error('gönderim')
                self.perf.add((time.perf_counter() - t0) * 1000.0)

    def step_error(self, what):
        """Döngüdeki hatanın yığın izi günlüğe; aynı hata (son satırı) en çok 60 sn'de bir yazılır."""
        tb = traceback.format_exc()
        key, now = tb.strip().splitlines()[-1], time.time()
        if now - self.step_errors.get(key, 0) >= 60:
            self.step_errors[key] = now
            self.log('   dünya %s hatası (%s):\n%s' % (what, H.name(self.map_id), tb))

    def step(self, now):
        """Döngünün bir adımı (0,1 sn; dünya kilidi altında): zamanlayıcılar, görüş, uzaylılar, kutular … Ölçüm aracı
        (tools/performans.py) iş parçacığı olmadan çağırır."""
        due = [t for t in self.timers if t[0] <= now]
        self.timers = [t for t in self.timers if t[0] > now]
        for _, fn in due:
            try:                               # biri hata verirse aynı adımdaki öteki zamanlayıcılar kaybolmasın
                fn()
            except Exception:
                self.step_error('zamanlayıcı')
        if self.collect_wish:
            self.collect_tick(now)
        if not self.jumping:
            self.check_gates(now)
            self.check_assets(now)
            self.view_tick(now)
            self.radiation_tick(now)
        lider = self.lider()                   # ortak haritada haritanın işleri liderde (ortak_harita.py)
        self.booster_tick(now)
        if lider:
            self.respawn_tick(now)
        self.auto_tick(now)
        self.effects_tick(now)
        self.abilities.tick(now)
        self.items.tick(now)
        self.tech.tick(now)
        self.parcacik.tick(now)
        self.alien.tick(now)
        if lider:
            self.etkinlik.tick(now)
        self.rules_tick(now)
        self.ach_tick(now)
        if self.repairing:
            self.repair_tick(now)
        self.shield_tick(now)
        self.settings_tick(now)
        self.music_tick(now)
        self.form_shield_tick(now)
        self.lab_time(now)
        if self.attacking and not self.hero_dead and not self.jumping and now >= self.next_laser:
            self.hero_laser(now)
        if self.ates and not self.attacking and self.ortak:
            # lazer bitti (hedef öldü ya da başkası öldürdü, görüşten çıktı, oyuncu atladı …): istemci AttackLaserRunCommand'da
            # saldıranın hedefini kurup gemiyi ona döndürür, AttackAbortLaserCommand gelmezse öteki oyuncuların ekranında gemi
            # hedefe dönük kalıyor, burnu dönmüyor ve motor efekti çıkmıyordu (ortak_harita.YANSIYAN)
            self.ortak.yansit(self, [('AttackAbortLaserCommand', {'uid': self.hid})])
        self.ates = self.attacking
        if self.pet:
            self.pet.tick(now)
        if self.kapi:
            self.kapi.tick(now)
        if self.low:
            self.low.tick(now)
        if self.labirent:
            self.labirent.tick(now)
        if self.session_tick:
            self.session_tick(now)
        for n in list(self.npcs.values()):
            if self.sahibi(n, now):            # ortak haritada uzaylının sahibi olan dünya (savaştığı ya da en yakın oyuncu)
                self.think(n, now)
        for h, b in list(self.boxes.items()) if lider else ():
            if b['bitis'] and now > b['bitis']:
                del self.boxes[h]
                self.send([('RemoveCollectableCommand', {'collected': False, 'hash': h})])
