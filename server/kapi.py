"""Galaksi Kapıları (üreticideki hepsi: Alpha, Beta, Gamma, Delta, Epsilon, Zeta, Kappa, Lambda, Kronos, Hades, Kuiper): kapı
üreticisi (enerji, parçalar, çarpan), hazırlık, X-1'deki kapı portalı, kapı haritasında dalgalar, canlar ve tamamlama ödülleri.

Kayıttaki akış (oturum başında ve üretici penceresinde):
  GalaxyGateBuilderInfoRequest      -> GalaxyGateBuilderInfoCommand (kapılar, parça sayısı, can, çarpan, enerji fiyatı 100, uridyum
                                       "money", ücretsiz enerji "samples")
  GalaxyGateBuilderGetGatePartsRequest {gateId} -> GalaxyGateBuilderGetGatePartsCommand (toplanan parça kimlikleri)
  GalaxyGateBuilderMultiEnergyRequest {spinAmount, useMultiplier, gateId} -> GalaxyGateBuilderMultiEnergyCommand (sonuçlar:
                                       GalaxyGateBuilderLootItemModule {type, item_id, amount, spins}: kayıtta ORE 4/13 ve HITPOINTS 1/11000)
Kayıtta olmayanlar istemcinin koduna ve metinlerine göre (GalaxyGateComponentSystem, UIGalaxyGatesSystem, galaxygates_* metinleri):
  GalaxyGateBuilderSetupGateRequest -> GalaxyGateBuilderSetupGateCommand {livesLeft, lifePrice}; kapı X-1'de üssün yanında belirir
  GalaxyGateBuilderBuyLifeRequest   -> GalaxyGateBuilderBuyLifeCommand (can fiyatı her alımda iki katı, wiki)
  kapı haritasında GalaxyGateBuilderGateWaveUpdateCommand (alt dalga sayacı), GateLifeLostCommand (ölüm), GateCompleteCommand (bitiş)
  ekran mesajları MessageCommand ile (istemci: MessageCommandHandler; BIG = büyük bildirim + günlük, NORMAL = üstteki kısa mesaj).
  Kayıtta kapı oynanmadığı için gerçek sunucunun metinleri bilinmiyor: istemcinin kendi metinleri (atk_wave_started,
  log_galaxygate_wave_name, log_msg_gg_completed_*) ve data/kapilar.json "mesajlar" (geri sayım, dalga bitti …). İstemcinin
  geri sayım komutları (EpicFightMessageCommand, CountdownStatusCommand) bu sürümde boş işleyicili, kullanılamıyor.
Kurulu kapı (2026-10-19, kullanıcı bildirimi: kurulu kapıda enerji "Tanımlanamayan bir hata" veriyordu): istemci enerji düğmesini
kapının durumundan bağımsız açık tutuyor, yanıtta yalnız 0 / uridyum yetmiyor / "unclassified_error" var (ParseProduceResponse);
kurulu kapıya çekiliş de kabul edilir: her parça kopyadır (çarpan), öteki ödüller olağan. Kurulu kapının durumu (state FINISHED)
Prepare jump'ı açar ve istemci onu aldığı her bilgide "Kapı ALPHA inşaatı bitti" bildirimini açar (UIGalaxyGatesSystem.RefProgress);
bildirim bir kez çıksın diye istemcide aynı bilgi varken pencerenin isteği yanıtsız kalır (info_request). Kapı hazırlanınca
(PREPARE JUMP, portalı X-1'de) durum IN_PROGRESS gönderilir.
Kapı haritası: ana dalgalar, her biri alt dalgalar ("gruplar"; alt dalga temizlenince sonraki). Alt dalganın uzaylıları
oyuncunun çevresinde bir halkada doğar, bir an durup her biri kendi yönünden gelir. Ana dalgadan sonra ortada iki portal açılır
(resmî kapı rehberi): solundaki sonraki dalgaya (aynı haritaya; girince geri sayımla başlar), sağındaki eve. Eve dönülürse
ilerleme saklanır. Vurulunca üste tamir olunur, can 1 azalır; can kalmazsa kapı (parçalarıyla) kaybolur. Değerler
data/kapilar.json (tools/kapilar.py).
Kapıya özgü kurallar:
  Alpha, Beta, Gamma (ABG): üreticide ortak çekiliş; parça seçilen kapıdan bağımsız üçünden birine düşer (öteki ödüller olağan).
  Zeta (3 harita) ve Kuiper (5 harita): haritanın son dalgasından sonra soldaki portal sonraki haritaya götürür; X-1'deki kapı
  portalı kaldığın dalganın haritasına götürür.
  Zeta Devourer ("kalici"): dalganın başında gelir, diğer uzaylılar yaşadıkça hasar almaz (wiki), dalga o ölünce biter.
  Kronos: üreticide çekiliş yok; parçaları diğer kapıları tamamlayınca gelir (her tamamlamada 1, cumartesi 2; kapı başına en çok
  wiki'deki sayı: Alpha 4, Beta 3, Gamma 1, Delta 1, Epsilon 4, Zeta 1, Kappa 2, Lambda 5 = 21). Üretici penceresinde kapı başına
  ilerleme (GalaxyGateBuilderMultiGateProgressModule). "Evil Clone Of Your Ship" oyuncunun kendi görünümüyle gelir.
  Hades: istemcide yarım boy harita (maps-config.xml scaleFactor 0.5); grup kapısıydı, burada tek oyunculu (botlar gelince grup).
"""
import json, math, os, random, time
import rutbe as RT
import ayar as AY

HERE = os.path.dirname(os.path.abspath(__file__))
K = json.load(open(os.path.join(HERE, 'data', 'kapilar.json'), encoding='utf8'))
KAPI = K['kapilar']
BY_ID = {v['kimlik']: k for k, v in KAPI.items()}
BY_MAP = {m: k for k, v in KAPI.items() for m in v['haritalar']}
SIZES = {int(m): tuple(s) for v in KAPI.values() for m, s in v['boyutlar'].items()}     # standart boydan farklı kapı haritaları
KRONOS_PARTS = next((v['parca'] for v in KAPI.values() if 'kaynaklar' in v), 0)
# istemcinin enum'ları (GalaxyGateBuilder*)
IN_PROGRESS, FINISHED = 0, 1
ERR_NONE, ERR_MONEY, ERR_OTHER = 0, 1, 2
BATTERY, ROCKET, MINE, ORE, VOUCHER, PART, HITPOINTS, LOGFILE = 1, 2, 3, 4, 5, 6, 7, 8
CAT_AMMO, CAT_RES, CAT_VOUCHER, CAT_PART, CAT_SPECIAL, CAT_LOG = 1, 2, 3, 4, 5, 6
XENOMIT, XENOMIT_ITEM = 3, 4              # sunucunun cevher türü; istemcinin üretici kimliği (kayıt: ORE 4)
PORTAL_BASE = 150900000                   # kapı portallarının kimliği: + kapı kimliği (X-1), + 50 + kimlik (kapıdan çıkış),
NEXT_PORTAL = 100                         # + 100 + kimlik (çok haritalı kapıda sonraki harita)
HOME_MAP = {1: 1, 2: 5, 3: 9}
ABG = ('alpha', 'beta', 'gamma')        # üreticide ortak çekiliş: parça üçünden birine düşer (Kapilar.draw)
MAP_W, MAP_H = 21000, 13100


def mod(name, **f):
    f['_'] = name
    return f


DISPLAY_BOTH, STYLE_BIG, STYLE_NORMAL = 2, 0, 1       # MessageCommand.DisplayTarget / DisplayStyle (istemci)


def screen(text, big=False, **wild):
    """Ekran mesajı: "key:anahtar" istemcinin çeviri metni (%AD% yer tutucuları wild'dan), değilse düz metin."""
    if text.startswith('key:'):
        key, kind = text[4:], 5
        reps = [mod('MessageWildcardReplacementModule', wildcard='%%%s%%' % k, replacement=str(v),
                    replacementType=mod('ReplacementTypeModule', typeValue=0)) for k, v in wild.items()]
    else:
        key, kind, reps = text, 0, []
    return ('MessageCommand', dict(displayTarget=DISPLAY_BOTH, displayStyle=STYLE_BIG if big else STYLE_NORMAL,
                                   messageModule=mod('WildcardMessageModule', message=mod(
                                       'MessageKeyListWildcardModule', wildCardReplacements=reps, baseKey=key,
                                       baseKeyType=mod('ReplacementTypeModule', typeValue=kind), textStyle=0))))


from eski_protokol import legacy, loot_kind, stm  # noqa: E402,F401  (eski metin protokolü: eski_protokol.py)


def npc_type(key, wave, i):
    """Kapı uzaylısının NPC türü (dunya.CFG tipler'e eklenir): dalgadaki sırasıyla (aynı uzaylı bir dalgada birkaç kez olabilir)."""
    return 'gg_%s_%d_%d' % (key, wave, i)


def register_npcs(tipler):
    """Kapı uzaylılarını NPC türleri olarak ekler: ad, görünüm (istemcinin gemi türü), hız ve npcId kapilar.json'dan; kapıya özgü
    davranış (Kronos'un roketleri, Kappa Annihilator'ın kapalı fırlatıcısı: uzayli.of) varsa."""
    for key, g in KAPI.items():
        for n, w in enumerate(g['dalgalar']):
            for i, a in enumerate(w['uzaylilar']):
                tipler[npc_type(key, n, i)] = dict(
                    ad=a['gorunen_ad'], model=a['tur'], hp=a['hp'], kalkan=a['kalkan'], hasar=a['hasar'], hiz=a['hiz'],
                    saldirgan=True, odul=dict(a['odul']), kargo=dict(a['kargo']), npc_kimlik=a['npc_kimlik'], kapi=key)
                if a.get('davranis'):
                    tipler[npc_type(key, n, i)]['davranis'] = dict(a['davranis'])


def spread(cx, cy, count, map_w, map_h):
    """Grubun doğma noktaları: merkez çevresinde sayıyla genişleyen alanda, aralarında en az grup_aralik birim (kalabalık grup tek
    noktada üst üste doğmasın)."""
    rad = K['grup_yaricap'][0] + K['grup_yaricap'][1] * math.sqrt(count)
    spots = []
    for _ in range(count):
        for _try in range(20):
            x = min(max(cx + random.uniform(-rad, rad), 300), map_w - 300)
            y = min(max(cy + random.uniform(-rad, rad), 300), map_h - 300)
            if all(math.hypot(x - px, y - py) >= K['grup_aralik'] for px, py in spots):
                break
        spots.append((x, y))
    return spots


def ring(hx, hy, groups, map_w, map_h):
    """Kapı dalgasının doğma halkası: oyuncunun çevresinde eşit aralıklı, her türün uzaylıları halka boyunca dağılmış (kullanıcı
    bildirimi 2026-10-24: alt dalga tek noktada üst üste doğuyordu). Halkaya sığmayanlar (aralık en az grup_aralik) dışta ikinci
    halkada; halkanın merkezi haritaya sığacak biçimde oyuncuya en yakın nokta. groups: [(anahtar, adet)] -> [(anahtar, x, y)]."""
    order = [key for _, key in sorted(((j + 0.5) / n, key) for key, n in groups for j in range(n))]
    rings, r, left = [], random.uniform(*K['dogma_uzaklik']), len(order)
    while left > 0:
        n = min(left, max(1, int(2 * math.pi * r / K['grup_aralik'])))
        rings.append((r, n))
        left -= n
        r += 2 * K['grup_aralik']
    edge = 300 + rings[-1][0] if rings else 0
    cx = min(max(hx, edge), map_w - edge) if map_w > 2 * edge else map_w / 2
    cy = min(max(hy, edge), map_h - edge) if map_h > 2 * edge else map_h / 2
    out, base = [], random.uniform(0, 2 * math.pi)
    for r, n in rings:
        for j in range(n):
            a = base + 2 * math.pi * (j + random.uniform(-0.2, 0.2)) / n
            x = min(max(cx + math.cos(a) * r, 300), map_w - 300)
            y = min(max(cy + math.sin(a) * r, 300), map_h - 300)
            out.append((order[len(out)], x, y))
    return out


def center(map_id):
    w, h = SIZES.get(int(map_id), (MAP_W, MAP_H))
    return w // 2, h // 2


def sub_waves(g, n):
    """İlk n ana dalganın alt dalga sayısı: istemcinin dalga sayacının birimi (GetGateTotalWaves: Alpha 40 … Hades 12; Hades'in
    aşaması bundan, dörtte bir). Kalıcı uzaylı (Zeta Devourer) kendi alt dalgası (istemci Zeta 46)."""
    return sum(len(w['gruplar']) + any(a.get('kalici') for a in w['uzaylilar']) for w in g['dalgalar'][:n])


def wave_map(g, n):
    """n. dalganın haritası (bitmiş kapıda son dalganınki)."""
    waves = g['dalgalar']
    return waves[min(n, len(waves) - 1)]['harita']


def pace(name):
    """Dalga beklemesi (giriş, alt dalga arası, mola; saniye): panelin 'dalga_bekleme' çarpanıyla (etkinlik kapıları da)."""
    return int(round(K[name] * AY.carpan('dalga_bekleme')))


def fresh(g, old=None):
    out = {'parcalar': [], 'hazir': False, 'dalga': 0, 'can': g['can'], 'alinan_can': 0, 'tamam': (old or {}).get('tamam', 0)}
    if 'kaynaklar' in g:
        out['kaynak'] = {}                # Kronos: hangi kapıdan kaç parça geldi
    return out


# ------------------------------------------------------------ süreli kapı bonusları
def bonus_period(now=None):
    """Bonus dönemi -> (sıra, bitiş zamanı): panelin kapi_bonus_saat'i, yerel gece yarısına hizalı."""
    now = time.time() if now is None else now
    span = max(1, int(AY.get('kapi_bonus_saat'))) * 3600
    off = time.localtime(now).tm_gmtoff or 0
    idx = int((now + off) // span)
    return idx, (idx + 1) * span - off


def bonus_amount(n):
    """Panelin çarpanı (miktarlı ödüller; tek eşya bir tane): kesin, pencerede görünen verilenle aynı."""
    m = AY.carpan('kapi_bonus_carpan')
    return n if n <= 1 or m == 1.0 else max(1, int(round(n * m)))


def bonus_selection(now=None):
    """Bu dönemin bonuslu kapıları -> {kapı: (lootId, adet)}; dönem içinde sabit (dönemin sırasıyla tohumlanmış seçim)."""
    B = K.get('bonus') or {}
    n = int(AY.get('kapi_bonus_adet'))
    gates = [k for k in B.get('kapilar', []) if k in KAPI]
    pool = B.get('oduller', [])
    if n <= 0 or not gates or not pool:
        return {}
    idx, _ = bonus_period(now)
    rng = random.Random('kapi-bonus-%d-%d' % (int(AY.get('kapi_bonus_saat')), idx))
    pick = rng.sample(gates, min(n, len(gates)))
    loots = rng.sample(pool, len(pick)) if len(pool) >= len(pick) else [rng.choice(pool) for _ in pick]
    return {k: (l, bonus_amount(a)) for k, (l, a) in zip(pick, loots)}


def ammo_type(loot):
    """Cephane sonucunun türü. Roket ve mayın LootItemModule'le gider (istemci ParseOutputList: tür 2/3, item_id 3 -> PLT-2021,
    11 -> ACM-01; AmmoOutputVo.ToStr: log_entry_rocket, log_entry_mine_s/p); lazer cephanesi pille."""
    return ROCKET if loot.startswith('ammunition_rocket_') else MINE if loot.startswith('ammunition_mine_') else BATTERY


def weights():
    """Çekiliş ağırlıkları (kayıttaki olasılıklar); panelin 'kapi_parca' çarpanı parçanınkini değiştirir."""
    f = AY.carpan('kapi_parca')
    return [[c, w * (f if c == CAT_PART else 1)] for c, w in K['olasilik']]


def percentages():
    """Penceredeki yüzdeler (toplam 100, en büyük kalan yöntemiyle)."""
    wts = weights()
    tot = sum(w for c, w in wts) or 1
    raw = [(c, 100.0 * w / tot) for c, w in wts]
    out = {c: int(v) for c, v in raw}
    for c, v in sorted(raw, key=lambda cv: cv[1] - int(cv[1]), reverse=True)[:100 - sum(out.values())]:
        out[c] += 1
    return out


# kapı ganimeti -> istemcinin lootId'si (günlük ödüller de aynı adla saklar)
LOOT_IDS = {'abr': 'resource_collectable_axion-beam-regulator', 'schism': 'resource_collectable_schism', 'yesil_anahtar': 'resource_booty-key'}


class Kapilar:
    """Oturumun kapı üreticisi (profil: kapilar) ve kapı haritasındaki koşu."""

    def __init__(self, profil, log=print):
        self.p, self.log = profil, log
        self.m = None                 # mağaza (eşya/para mesajları)
        self.world = lambda: None     # oturumun güncel dünyası
        self.info_tpl = None          # kayıttaki GalaxyGateBuilderInfoCommand (diğer kapılar olduğu gibi)
        self.sent = None              # oturumda istemcinin elindeki kapı bilgisi (info_request)

    # ------------------------------------------------------------ profil
    @property
    def d(self):
        """Profildeki kapı bölümü (yoksa kurulur). Kilitsiz: profil kilidi yeniden girilemez, çağıranlar kilit içinde kullanır."""
        d = self.p.d.get('kapilar')
        if d is None:
            d = self.p.d['kapilar'] = {'enerji': 0, 'carpan': 0, 'cekilis': 1, 'log_disk': 0, 'kupon': 0, 'kapilar': {}}
        if 'ganimet' in d:                       # eski profil: kapı ganimeti ayrı tutuluyordu -> diger_esyalar (lootId)
            diger = self.p.d.setdefault('diger_esyalar', {})
            for k, n in d.pop('ganimet').items():
                diger[LOOT_IDS.get(k, k)] = diger.get(LOOT_IDS.get(k, k), 0) + n
        for k, g in KAPI.items():
            if k not in d['kapilar']:
                d['kapilar'][k] = fresh(g)
            elif 'kaynaklar' in g:
                d['kapilar'][k].setdefault('kaynak', {})
        return d

    def gate(self, key):
        return self.d['kapilar'][key]

    def built(self, key):
        return len(self.gate(key)['parcalar']) >= KAPI[key]['parca']

    def state(self, key):
        """Penceredeki durum: kurulu ve henüz hazırlanmamışsa FINISHED (istemci "Prepare jump"u açar, "inşaatı bitti" bildirimini
        gösterir); hazırlanmış kapı IN_PROGRESS (portalı X-1'de, bildirim her açılışta çıkmasın)."""
        return FINISHED if self.built(key) and not self.gate(key)['hazir'] else IN_PROGRESS

    def energy_price(self):
        """Enerji fiyatı: Premium -%5 (tek oyunculuda herkes premium; galaxy_gates.md), hafta sonu -%15; indirimler toplanır (wiki:
        en düşük 55 = 100 - 25 - 5 - 15)."""
        import takvim as TK
        sale = TK.is_active('kapi_hafta_sonu')    # cumartesi-pazar (takvim.py)
        f = (1 - K.get('premium_indirim', 0) - (K['hafta_sonu_indirim'] if sale else 0)) * AY.carpan('kapi_fiyat')     # panel
        return int(round(K['enerji_fiyati'] * f)), sale

    def life_price(self, key):
        G = self.gate(key)
        if not G['hazir']:
            return -1
        pr = K['can_fiyatlari']
        return int(round(pr[G['alinan_can']] * AY.carpan('kapi_fiyat'))) if G['alinan_can'] < len(pr) else -1     # panel

    def money(self):
        return self.p.d['pilot'].get('uridium', 0)

    # ------------------------------------------------------------ süreli bonuslar
    def bonus_taken(self, now=None):
        """Bu dönemde bonusu alınan kapılar (dönem değişince sıfırlanır). Profil: kapilar.bonus {donem, alinan}."""
        idx, _ = bonus_period(now)
        with self.p.lock:
            b = self.d.setdefault('bonus', {})
            if b.get('donem') != idx:
                b.clear()
                b.update(donem=idx, alinan=[])
                self.p.dirty = True
            return b['alinan']

    def bonus_modules(self, key, now=None):
        """Kapının bonusu (GalaxyGateBuilderBonusGGRewardModule; kayıttaki kalıntılar yerine sunucunun seçimi) ya da []."""
        now = time.time() if now is None else now
        sel = bonus_selection(now)
        if key not in sel:
            return []
        loot, n = sel[key]
        return [mod('GalaxyGateBuilderBonusGGRewardModule', claimed=key in self.bonus_taken(now),
                    countdown=max(0, int(bonus_period(now)[1] - now)), lootId=loot, amount=n)]

    def claim_bonus(self, key, now=None):
        """Kapı tamamlandı: dönemin bonusu bu kapıdaysa ve alınmadıysa verilir -> (mesajlar, (lootId, adet) | None)."""
        sel, taken = bonus_selection(now), self.bonus_taken(now)
        if key not in sel or key in taken:
            return [], None
        loot, n = sel[key]
        with self.p.lock:                              # bonus_taken kilidi kendisi alıyor (kilit yeniden girilemez)
            taken.append(key)
            self.p.dirty = True
        self.log('   %s: kapı bonusu %s x%d' % (KAPI[key]['ad'], loot, n))
        return (self.m.reward(loot, n) if self.m else []), (loot, n)

    # ------------------------------------------------------------ üretici penceresi
    def gate_module(self, tpl, key):
        G, g = self.gate(key), KAPI[key]
        out = dict(tpl)
        if out.get('probabilityModules') and AY.carpan('kapi_parca') != 1.0:       # panel: kapı parçası şansı (yüzdeler)
            pct = percentages()
            out['probabilityModules'] = [dict(m, percentage=pct.get(m.get('category'), m.get('percentage', 0)))
                                         for m in out['probabilityModules']]
        out.update(currPart=len(G['parcalar']), currWave=sub_waves(g, G['dalga']), state=self.state(key),
                   livesLeft=G['can'] if G['hazir'] else -1, lifePrice=self.life_price(key), multiplier=self.d['carpan'], mode=key,
                   id=g['kimlik'], bonusGGRewardModules=self.bonus_modules(key))
        if 'kaynaklar' in g:
            # Kronos: kayıttaki gibi kapı başına ilerleme (ad istemcinin gösterdiği "Alpha", "Beta" …)
            # sözlük: mod()'un ilk bağımsız değişkeni de "name"
            out['multiGateProgressModules'] = [{'_': 'GalaxyGateBuilderMultiGateProgressModule', 'total': n,
                                                'current': G['kaynak'].get(k, 0), 'name': KAPI[k]['ad'].replace(' Gate', '')}
                                               for k, n in g['kaynaklar'].items()]
            out['probabilityModules'] = []
        return out

    def info_cmd(self):
        """GalaxyGateBuilderInfoCommand: kayıttaki şablon (kapı sırası ve olasılık modülleri), değerler profilden; bonusRewardsDay:
        Pazar GG Double Rewards (takvim.py gg_cift_odul)."""
        import takvim as TK
        price, sale = self.energy_price()
        t = json.loads(json.dumps(self.info_tpl or {'gates': [], 'spinAmounts': K['cekilis_adetleri'], 'bonusRewardsDay': False,
                                                    'galaxyGateDay': False}))
        t.pop('_m', None)
        gates = []
        have = set()
        for m in t.get('gates', []):
            key = BY_ID.get(m.get('id'))
            gates.append(self.gate_module(m, key) if key else m)
            have.add(key)
        for key in KAPI:
            if key not in have:
                gates.append(self.gate_module(mod('GalaxyGateBuilderGateModule', bonusGGRewardModules=[], currWave=0, mode=key, currPart=0,
                                                  boosts=[], state=0, probabilityModules=[], lifePrice=-1, id=0, multiplier=0,
                                                  multiGateProgressModules=[], livesLeft=-1), key))
        t.update(gates=gates, samples=self.d['enerji'], money=self.money(), energy_cost=price, spinOnSale=sale,
                 spinamount_selected=self.d['cekilis'], spinAmounts=K['cekilis_adetleri'], bonusRewardsDay=TK.is_active('gg_cift_odul'))
        return ('GalaxyGateBuilderInfoCommand', t)

    def info_request(self):
        """GalaxyGateBuilderInfoRequest: istemci pencereyi her açışta sorar. Kurulu kapının FINISHED'ı Prepare jump'ı açtığı gibi her
        bilgide "ALPHA gate completed" bildirimini de yeniden açıyordu, Cancel'dan sonra da (UIGalaxyGatesSystem.RefProgress; Cancel bir
        şey göndermiyor; kullanıcı, canlı tur 2). İstemcide aynı kapı bilgisi varken yanıt yok: pencere elindekiyle açılıyor (Prepare
        jump etkin, bildirim yok); o arada yalnız uridyum değiştiyse pencere eskisini gösterir."""
        cmd = self.info_cmd()
        seen = self.seen(cmd[1])
        if seen == self.sent and any(g.get('state') == FINISHED for g in cmd[1]['gates']):
            return []
        self.sent = seen
        return [cmd]

    @staticmethod
    def seen(t):
        """Karşılaştırılan bölüm: kapılar ve enerji; bonus ödülün geri sayımı her saniye azaldığından dışarıda."""
        gates = [dict(g, bonusGGRewardModules=[{k: v for k, v in m.items() if k != 'countdown'} for m in g.get('bonusGGRewardModules', [])])
                 for g in t['gates']]
        return json.dumps([gates, t['samples']], sort_keys=True)

    def part_ids(self, key):
        return sorted(self.gate(key)['parcalar'])

    def parts_cmd(self, f):
        key = BY_ID.get(f.get('gateId'))
        return ('GalaxyGateBuilderGetGatePartsCommand', dict(gateId=f.get('gateId', 0), gatePartIds=self.part_ids(key) if key else [],
                                                              errorCode=ERR_NONE if key else ERR_OTHER))

    def save_spin(self, f):
        n = f.get('spinAmount')
        if n in K['cekilis_adetleri']:
            with self.p.lock:
                self.d['cekilis'] = n
                self.p.dirty = True
        return []

    # ------------------------------------------------------------ çekiliş
    def spin(self, f):
        """GalaxyGateBuilderMultiEnergyRequest: enerji başına bir çekiliş; önce ücretsiz enerji, sonra uridyum."""
        gid, n = f.get('gateId'), int(f.get('spinAmount') or 0)
        key = BY_ID.get(gid)
        reply = lambda err, items=(), extra=None: [('GalaxyGateBuilderMultiEnergyCommand', dict(
            gatePartIds=self.part_ids(key) if key else [], items=list(items), spinamount_selected=n, errorCode=err, money=self.money(),
            multiplier=self.d['carpan'], gateMode=key or '', samples=self.d['enerji']))] + (extra or [])
        if not key or n <= 0 or KAPI[key].get('uretilmez'):
            self.log('   kapı üreticisi: çekiliş yok (kapı %s, %d)' % (gid, n))     # Kronos: parçaları diğer kapılardan
            return reply(ERR_OTHER)
        group = ABG if key in ABG else (key,)    # Alpha/Beta/Gamma: parça üçünden birine (draw)
        was_built = {k: self.built(k) for k in group}   # kurulu kapıda da çekiliş: parçalar kopya (çarpan), öteki ödüller olağan
        price, sale = self.energy_price()
        free = min(n, self.d['enerji'])
        cost = (n - free) * price
        if self.money() < cost:
            self.log('   kapı üreticisi: uridyum yetmiyor (%d U)' % cost)
            return reply(ERR_MONEY)
        results, grants = [], {}
        used = 0
        for _ in range(n):
            if any(not was_built[k] and self.built(k) for k in group):
                break                          # kapı bu çekilişlerde kuruldu: kalan enerji harcanmaz
            used += 1
            results += self.draw(key, f.get('useMultiplier'), grants)
        free = min(used, self.d['enerji'])
        cost = (used - free) * price
        with self.p.lock:
            self.d['enerji'] -= free
            self.p.d['pilot']['uridium'] = self.money() - cost
            self.p.dirty = True
        RT.money(self.p, 'uridyum', -cost, 'buy_SPECIAL', qty=used - free)
        msgs = self.give(grants)
        if self.m:
            msgs = self.m.money_msgs() + msgs
        items = self.merge(results)
        self.log('   kapı üreticisi %s: %d çekiliş (%d ücretsiz, %d U), parça %s, çarpan %d: %s' % (
            key, used, free, cost, ', '.join('%s %d/%d' % (k, len(self.gate(k)['parcalar']), KAPI[k]['parca']) for k in group), self.d['carpan'],
            ', '.join('%s %s' % (k, v) for k, v in sorted(grants.items()))))
        for k in group:
            if not was_built[k] and self.built(k):
                self.log('   %s kapısı kuruldu' % KAPI[k]['ad'])
        self.sent = self.seen(self.info_cmd()[1])      # yanıt parçaları, enerjiyi ve kurulmayı (bildirimiyle) istemciye taşıyor
        return reply(ERR_NONE, items, msgs)

    def draw(self, key, use_mult, grants):
        """Bir çekiliş -> sonuç kayıtları. Kopya parça çarpan olur (en çok 5 = x6; 5'e ulaşınca bir sonraki ödülde kendiliğinden
        kullanılır). Çarpanla parça çıkarsa çarpan kadar farklı eksik parça; eksik kalmadıysa artanı cephane (istemci SSS
        galaxygates_multiplier_multilpier_on_parts_p: "you'll win new parts for the gate")."""
        d, G, g = self.d, self.gate(key), KAPI[key]
        wts = weights()
        r, cat = random.uniform(0, sum(w for c, w in wts)), CAT_AMMO
        for c, w in wts:          # kayıttaki olasılıklar: cephane 67, kaynak 12, kupon 3, parça 13, özel 4, log 1
            r -= w
            if r < 0:
                cat = c
                break
        if cat == CAT_PART and key in ABG:
            # Alpha, Beta ve Gamma üreticide ortak: parça seçilen kapıdan bağımsız üçünden birine, o kapının ilerlemesine (resmî ABG
            # üreticisi; kullanıcı bildirimi 2026-10-24: her kapı kendi çekilişinden parça alıyordu). Kurulu kapıya düşen parça kopya (çarpan)
            key = random.choice(ABG)
            G, g = self.gate(key), KAPI[key]
        if cat == CAT_PART and d['carpan'] and (use_mult or d['carpan'] >= K['azami_carpan']):
            mult = d['carpan'] + 1
            missing = [i for i in range(1, g['parca'] + 1) if i not in G['parcalar']]
            new = random.sample(missing, min(mult, len(missing)))
            with self.p.lock:
                d['carpan'] = 0
                G['parcalar'] += new
                self.p.dirty = True
            have = len(G['parcalar']) - len(new)
            out = [dict(type=PART, part_id=pid, duplicate=False, current=have + i + 1, gate_id=g['kimlik'], mult=mult)
                   for i, pid in enumerate(new)]
            left = mult - len(new)
            if left:                                       # gerekenden fazlası cephane
                loot, iid, amount = random.choice(K['cephane'])
                grants[loot] = grants.get(loot, 0) + amount * left
                out.append(dict(type=ammo_type(loot), item_id=iid, amount=amount * left, mult=left))
            return out
        if cat == CAT_PART:
            pid = random.randint(1, g['parca'])
            missing = [i for i in range(1, g['parca'] + 1) if i not in G['parcalar']]
            if pid in G['parcalar'] and missing and random.random() < AY.get('kopya_eksige') / 100.0:     # panel (oyunun %50'si)
                pid = random.choice(missing)
            dup = pid in G['parcalar']
            with self.p.lock:
                if dup:
                    d['carpan'] = min(K['azami_carpan'], d['carpan'] + 1)
                else:
                    G['parcalar'].append(pid)
                self.p.dirty = True
            return [dict(type=PART, part_id=pid, duplicate=dup, current=len(G['parcalar']), gate_id=g['kimlik'])]
        mult = 1
        if d['carpan'] and (use_mult or d['carpan'] >= K['azami_carpan']):
            mult, d['carpan'] = d['carpan'] + 1, 0
        if cat == CAT_AMMO:
            loot, iid, amount = random.choice(K['cephane'])
            grants[loot] = grants.get(loot, 0) + amount * mult
            return [dict(type=ammo_type(loot), item_id=iid, amount=amount * mult, mult=mult)]
        if cat == CAT_RES:
            amount = random.randint(*K['xenomit']) * mult
            grants['xenomit'] = grants.get('xenomit', 0) + amount
            return [dict(type=ORE, item_id=XENOMIT_ITEM, amount=amount, mult=mult)]
        if cat == CAT_VOUCHER:
            grants['kupon'] = grants.get('kupon', 0) + mult
            return [dict(type=VOUCHER, item_id=1, amount=mult, mult=mult)]
        if cat == CAT_SPECIAL:
            amount = random.randint(*K['nano_govde']) // 1000 * 1000 * mult
            grants['nano'] = grants.get('nano', 0) + amount
            return [dict(type=HITPOINTS, item_id=1, amount=amount, mult=mult)]
        grants['log_disk'] = grants.get('log_disk', 0) + mult
        return [dict(type=LOGFILE, item_id=1, amount=mult, mult=mult)]

    def merge(self, results):
        """Sonuçları istemcinin günlük satırlarına çevirir: aynı ödüller toplanır (spins), parçalar tek tek."""
        now = int(time.time() * 1000)
        out, loot = [], {}
        for r in results:
            if r['type'] == PART:
                key = BY_ID[r['gate_id']]
                # son parçada FINISHED: istemci "Prepare jump" düğmesini kapı durumundan açar (canlı test: IN_PROGRESS gidince düğme
                # pencere yeniden açılana dek kapalı kaldı)
                done = r['current'] >= KAPI[key]['parca'] and not self.gate(key)['hazir']
                out.append(mod('GalaxyGateBuilderPartItemModule', type=PART, date=now, livesLeft=-1, gate_id=r['gate_id'],
                               state=FINISHED if done else IN_PROGRESS, multiplier_used=r.get('mult', 1) - 1, current=r['current'],
                               part_id=r['part_id'],
                               duplicate=r['duplicate'], lifePrice=-1))
                continue
            k = (r['type'], r['item_id'], r['mult'])
            if k not in loot:
                # istemci (GalaxyGateComponentSystem.ParseOutputList) cephaneyi BatteryItemModule'e dönüştürür: LootItemModule
                # gönderilince dönüşüm boş kalıp NullReferenceException veriyordu (canlı test). Diğerleri LootItemModule (kayıt).
                cls = 'GalaxyGateBuilderBatteryItemModule' if r['type'] == BATTERY else 'GalaxyGateBuilderLootItemModule'
                loot[k] = mod(cls, type=r['type'], date=now, multiplier_used=r['mult'] - 1, item_id=r['item_id'],
                              spins=0, multiplier_amount=r['mult'] if r['mult'] > 1 else 0, amount=0)
                if r['type'] == BATTERY:
                    loot[k]['defaultOutput'] = False
                out.append(loot[k])
            loot[k]['spins'] += 1
            loot[k]['amount'] += r['amount']
        return out

    def give(self, grants, note=True):
        """Ödülleri profile ekler -> arayüz mesajları (cephane sayaçları, envanter, kargo, nano gövde)."""
        msgs, p = [], self.p
        for loot, n in sorted(grants.items()):
            if loot.startswith('ammunition_'):
                total = p.add_ammo(loot, n)
                if self.m:
                    iid = self.m.item_id(loot)
                    st = p.menu_status(loot)
                    msgs += ([('MenuItemStatusCommand', st)] if st else []) + [self.m.inv_item(iid, loot, total),
                                                                              self.m.pack([self.m.hangar_item(iid, loot, total)])]
                if note:
                    msgs.append(legacy('0|LM|ST|%s|%s|%d' % (loot_kind(loot), loot, n)))
        n = grants.get('xenomit', 0)                                  # Xenomit kargoda yer kaplamaz (profil.CARGO_ORES)
        if n > 0:
            totals = p.add_ores({XENOMIT: n})
            msgs.append(('AttributeOreCountUpdateCommand', {'oreCountList': totals}))
            if self.m:
                msgs.append(self.m.ore_pack([XENOMIT]))
            w = self.world()
            if w:
                msgs += w.quest('loot', loot='resource_ore_xenomit', amount=n)      # toplama görevleri (Alien Ore)
        with p.lock:
            self.d['kupon'] += grants.get('kupon', 0)
            self.d['log_disk'] += grants.get('log_disk', 0)
            self.d['enerji'] += grants.get('enerji', 0)           # Kronos: 250 ücretsiz enerji (wiki "Energy")
            p.dirty = True
        for k, n in (grants.get('ganimet') or {}).items():          # ABR, Schism, yeşil anahtar: kaynak deposuna (profil)
            p.add_resource(LOOT_IDS.get(k, k), n)
        if grants.get('nano'):
            gm = p.d['gemi']
            with p.lock:
                gm['nanoHull'] = min(gm.get('maxNanoHull', 0), int(gm.get('nanoHull', 0)) + grants['nano'])
            msgs.append(('HitpointInfoCommand', dict(hitpoints=int(gm.get('hitPoints', 0)), hitpointsMax=gm.get('hitMax', 0),
                                                     nanoHull=int(gm['nanoHull']), nanoHullMax=gm.get('maxNanoHull', 0))))
        return msgs

    # ------------------------------------------------------------ hazırlık, can, portal
    def setup(self, f):
        """GalaxyGateBuilderSetupGateRequest: kurulu kapı X-1'de üssün yanında belirir (wiki: "PREPARE JUMP")."""
        gid = f.get('gateId')
        key = BY_ID.get(gid)
        if not key or not self.built(key):
            self.log('   kapı hazırlanamadı: %s' % gid)
            return [('GalaxyGateBuilderSetupGateCommand', dict(livesLeft=-1, lifePrice=-1, id=gid or 0, errorCode=1))]
        G = self.gate(key)
        with self.p.lock:
            if not G['hazir']:
                G.update(hazir=True, dalga=0, can=AY.adet('kapi_can', KAPI[key]['can']), alinan_can=0)     # panel: kapı canı
            self.p.dirty = True
        w = self.world()
        if w and w.map_id == str(self.home()) and not any(x['gateId'] == PORTAL_BASE + KAPI[key]['kimlik'] for x in w.gates):
            w.add_gate(self.home_portal(key, w.station))
        self.log('   %s kapısı hazır: %d can' % (KAPI[key]['ad'], G['can']))
        return [('GalaxyGateBuilderSetupGateCommand', dict(livesLeft=G['can'], lifePrice=self.life_price(key), id=gid, errorCode=0))]

    def buy_life(self, f):
        gid = f.get('gateId')
        key = BY_ID.get(gid)
        price = self.life_price(key) if key else -1
        err = ERR_OTHER if price < 0 else ERR_MONEY if self.money() < price else ERR_NONE
        if not err:
            with self.p.lock:
                self.p.d['pilot']['uridium'] = self.money() - price
                G = self.gate(key)
                G['can'] += 1
                G['alinan_can'] += 1
                self.p.dirty = True
            RT.money(self.p, 'uridyum', -price, 'buy_SPECIAL')
            self.log('   %s kapısına can alındı (%d U), can %d' % (KAPI[key]['ad'], price, G['can']))
        G = self.gate(key) if key else {'can': -1}
        msgs = [('GalaxyGateBuilderBuyLifeCommand', dict(samples=self.d['enerji'], multiplier=self.d['carpan'], gateId=gid or 0, errorCode=err,
                                                         lifePrice=self.life_price(key) if key else -1, money=self.money(),
                                                         gateMode=key or '', livesLeft=G['can']))]
        return (self.m.money_msgs() if self.m and not err else []) + msgs

    def home(self):
        return HOME_MAP.get(self.p.d['pilot'].get('factionId'), 5)

    def home_portal(self, key, station):
        """X-1'deki kapı portalı: üssün yanında, harita ortasına doğru (kapılar yan yana; beşerli halkalar). Kaldığın dalganın
        haritasına götürür (Zeta, Kuiper)."""
        g, G = KAPI[key], self.gate(key)
        cx, cy = MAP_W // 2, MAP_H // 2
        sx, sy = (station['posX'], station['posY']) if station else (cx, cy)
        ring, slot = divmod(list(KAPI).index(key), 5)
        a = math.atan2(cy - sy, cx - sx) + (-0.45, 0, 0.45, 0.9, -0.9)[slot]
        dist = K['portal_uzaklik'] + ring * 1400
        x, y = int(sx + math.cos(a) * dist), int(sy + math.sin(a) * dist)
        dest = wave_map(g, G['dalga'])
        return dict(gateId=PORTAL_BASE + g['kimlik'], x=x, y=y, hedef=dest, designId=g['portal'], kapi=key, varis=center(dest))

    def home_portals(self, map_id, station):
        if int(map_id) != self.home():
            return []
        return [self.home_portal(k, station) for k in KAPI if self.gate(k)['hazir']]

    def exit_portal(self, key, map_id, side=False):
        """Kapıdan eve dönüş: haritanın ortasında (sonraki dalganın portalı açıkken onun sağında)."""
        x, y = center(map_id)
        return dict(gateId=PORTAL_BASE + 50 + KAPI[key]['kimlik'], x=x + 700 if side else x, y=y, hedef=self.home(), designId=1,
                    kapi=key, cikis=True)

    def next_portal(self, key, map_id, dest):
        """Sonraki dalgaya (aynı haritaya; Zeta ve Kuiper'de haritanın son dalgasından sonra sonraki haritaya): ortanın solunda,
        kapının portal tasarımıyla."""
        g = KAPI[key]
        x, y = center(map_id)
        return dict(gateId=PORTAL_BASE + NEXT_PORTAL + g['kimlik'], x=x - 700, y=y, hedef=dest, designId=g['portal'], kapi=key,
                    varis=center(dest))

    def kronos_part(self, key):
        """Kapı tamamlandı: Kronos parçası (her tamamlamada 1, Kronos günü 2; kapı başına en çok wiki'deki sayı) -> (gelen, toplam)."""
        kr = next((k for k, g in KAPI.items() if key in g.get('kaynaklar', {})), None)
        if not kr:
            return None
        g, G = KAPI[kr], self.gate(kr)
        import takvim as TK
        n = 2 if TK.is_active('kronos_gunu') else 1     # cumartesi (takvim.py)
        with self.p.lock:
            have = G['kaynak'].get(key, 0)
            got = min(n, g['kaynaklar'][key] - have)
            if got > 0:
                G['kaynak'][key] = have + got
                G['parcalar'] = list(range(1, sum(G['kaynak'].values()) + 1))
                self.p.dirty = True
        if got <= 0:
            return None
        self.log('   Kronos parçası: %s +%d (%d/%d)' % (KAPI[key]['ad'], got, len(G['parcalar']), g['parca']))
        return got, len(G['parcalar'])

    def finish(self, key, reward_msgs=None, dispatch=False):
        """Kapı tamamlandı (kapı haritasında son dalga ya da Dispatch'in kapı gönderimi): ödüller (wiki; şanslı ödüller olasılığıyla),
        Kronos parçası, kapı sıfırlanır (ödüldeki parça yeni kapının ilk parçası). reward_msgs: dünyanın ödül mesajları (yoksa para
        güncellemesi). dispatch: görevler saymaz, N.O.V.A. bonusu yok (darkorbitwiki dispatch-gate: "boosters don't apply and missions
        don't count"; başarım sayılır). Pazar GG Double Rewards (takvim.py gg_cift_odul; Dispatch'te değil): EP, onur, Xenomit, log
        diski, kupon, Assembly kaynakları ve şanslı ödüllerin olasılığı iki kat -> (mesajlar, {yeni, kronos, sans})."""
        import takvim as TK
        import ganimet as GN
        g, R = KAPI[key], KAPI[key]['odul']
        x2 = 1 if dispatch or not TK.is_active('gg_cift_odul') else 2
        rm = reward_msgs or (lambda tot, **kw: self.m.money_msgs() if self.m else [])
        self.p.ach('gate', tur='%s_GATE' % key.upper(), dispatch=dispatch)      # istemcinin GalaxyGateType'ı (STREUNER_GATE …)
        with self.p.lock:
            self.p.d['gemi']['galaxyGatesDone'] = self.p.d['gemi'].get('galaxyGatesDone', 0) + 1    # ShipInitializationCommand
        ep = int(R['ep'] * x2 * (1 + (0 if dispatch else self.p.mods().get('kapi_ep', 0))))    # N.O.V.A. Field Intelligence (nova.py)
        ep, onur, uri = AY.miktar('ep', ep, 'kapi'), AY.miktar('onur', R['onur'] * x2, 'kapi'), AY.miktar('uridyum', R['uridyum'], 'kapi')   # panel
        tot = self.p.gain(ep=ep, onur=onur, uridyum=uri, neden='galaxy_gate_done')
        msgs = rm(tot, ep=ep, onur=onur, uridyum=uri)
        q = lambda v: AY.miktar('mod_odul', v, 'kapi')      # panel: kapı/mod ödülü çarpanı
        grants = {k: q(v) for k, v in R['cephane'].items()}
        grants.update(xenomit=q(R['xenomit'] * x2), kupon=q(R['kupon'] * x2), log_disk=q(R['log_disk'] * x2), enerji=q(R['enerji']),
                      ganimet={k: q(v * x2) for k, v in (R['ganimet'] or {}).items()})
        if key in K.get('schism', {}) and 'AllGatesSchism' in TK.ALWAYS:       # Schism'li kapılar (giriş bayrağı; wiki aralığı)
            grants['ganimet']['schism'] = q(random.randint(*K['schism'][key]))
        msgs += self.give(grants)
        got = []
        owned = {x['lootId'] for x in self.p.d['gemiler'].values()}
        for s in [s for s in R['sans'] if random.random() < AY.chance('dusme', s['olasilik'] * x2, 'kapi')]:
            loot = random.choice(s['secenekler']) if s['esya'] == 'tasarim_secimi' else s['esya']
            got.append(loot)
            if loot in owned and s.get('yoksa_uridyum'):                # Kuiper: tasarım zaten varsa 10.000 uridyum (wiki)
                u = AY.miktar('uridyum', s['yoksa_uridyum'], 'kapi')
                tot = self.p.gain(uridyum=u, neden='galaxy_gate_done')
                msgs += rm(tot, uridyum=u)
            elif self.m:
                msgs += self.m.prize(loot, s['adet'], 'kapi')
        for loot, n, chance in TK.gate_rewards(key):          # etkinliğin kapı ödülü (Empyrian / Prosperous Fragment, Lucent Key)
            if random.random() < AY.chance('dusme', chance, 'kapi') and self.m:
                msgs += self.m.prize(loot, n, 'kapi')
                got.append(loot)
        for s in [] if dispatch else TK.gate_choices(key):    # GG Special Rewards Weekend, LF-4 günü: olasılıkla paketten biri
            rows = [r for r in s['secim'] if not (s.get('yinelenmez') and GN.owned(self.p, r[0]))]   # gemi ya da tasarım
            if rows and random.random() < AY.chance('dusme', s['olasilik'], 'kapi') and self.m:
                loot, n = random.choice(rows)
                msgs += self.m.prize(loot, n, 'kapi')
                got.append(loot)
        for pk in TK.gate_packages(key):                      # ödülün paket adı (Prosperous'un 88.888 kredisi): başarım
            self.p.ach('package', paket=pk)
        with self.p.lock:
            new = fresh(g, self.gate(key))
            new['tamam'] += 1
            new['parcalar'] = random.sample(range(1, g['parca'] + 1), min(R['parca'], g['parca']))
            self.d['kapilar'][key] = new
            self.p.dirty = True
        kr = self.kronos_part(key)
        bm, bonus = self.claim_bonus(key)              # süreli kapı bonusu (pencerede "Bonus reward")
        msgs += bm
        self.log('   %s kapısı tamamlandı: +%d EP, +%d onur, +%d U, %s%s' % (
            g['ad'], R['ep'], R['onur'], R['uridyum'], grants, ', şanslı: %s' % got if got else ''))
        return msgs, dict(yeni=new, kronos=kr, sans=got, bonus=bonus, para=dict(ep=ep, onur=onur, uridyum=uri))

    def dispatch_complete(self, key):
        """Dispatch'in kapı gönderimi bitti: tamamlama ödülleri ve ganimet iletisi (DispatchLootMessageCommand)."""
        msgs, info = self.finish(key, dispatch=True)
        P = info['para']                                   # verilen (panelin çarpanlarıyla), iletide de o
        loots = [mod('LootModule', lootId=l, amount=n, modifier='') for l, n in
                 (('currency_experience', P['ep']), ('currency_honour', P['onur']), ('currency_uridium', P['uridyum'])) if n]
        return msgs + [('DispatchLootMessageCommand', dict(messageType=1, loots=loots))]

    def bonus_energy(self, n):
        with self.p.lock:
            self.d['enerji'] += n
            self.p.dirty = True
        return [legacy('0|A|STM|log_msg_gather_extra-energy_s_collected' if n == 1 else
                       '0|A|STM|log_msg_gather_extra-energy_p_collected|%%COUNT%%|%d' % n)]


class Kosu:
    """Kapı haritasında dalgalar (dünya döngüsünden, kilit altında). phase: intro/break (geri sayım), next (alt dalgalar arası),
    fight, move (dalga bitti: sonraki dalganın ve evin portalı açık), done, void (kapı yok ya da başka haritada), dead."""
    cleared = 0                      # bu ana dalgada temizlenen alt dalgalar (istemcinin sayacı alt dalga sayar)

    def __init__(self, kapilar, world, key):
        self.k, self.w, self.key = kapilar, world, key
        self.g = KAPI[key]
        self.map = int(world.map_id)
        G = kapilar.gate(key)
        self.npcs = set()            # bu dalganın uzaylıları
        self.keep = set()            # kalıcı uzaylılar (Zeta Devourer): alt dalgalardan bağımsız
        self.sub = 0
        self.counted = None          # son gönderilen geri sayım saniyesi
        self.left = None             # son bildirilen kalan uzaylı sayısı
        self.exposed = False         # kalıcı uzaylının korumasının kalktığı bildirildi
        self.boss = ''               # kalıcı uzaylının adı (mesajlar)
        now = time.time()
        if not G['hazir'] or G['can'] <= 0:
            self.phase, self.t = 'void', now          # kapı yok: yalnız çıkış portalı
            world.add_gate(kapilar.exit_portal(key, self.map))
        elif wave_map(self.g, G['dalga']) != self.map:
            # başka haritanın dalgası (ör. eski haritaya dönüldü): o haritanın portalı ve eve dönüş
            self.phase, self.t = 'void', now
            world.add_gate(kapilar.next_portal(key, self.map, wave_map(self.g, G['dalga'])))
            world.add_gate(kapilar.exit_portal(key, self.map, side=True))
        else:
            self.phase, self.t = 'intro', now + pace('giris_bekleme_sn')
            world.send(self.say('devam' if G['dalga'] else 'giris'))
        world.log('   %s kapısı: dalga %d/%d, can %d (%s)' % (self.g['ad'], G['dalga'] + 1, len(self.g['dalgalar']), G['can'], self.phase))

    def wave(self):
        G = self.k.gate(self.key)
        return self.g['dalgalar'][min(G['dalga'], len(self.g['dalgalar']) - 1)]

    def say(self, event, wild=None, **extra):
        """data/kapilar.json "mesajlar"daki olay -> ekran mesajları (büyük ve/veya kısa; wild: "key:" metnin öteki yer tutucuları);
        giriş ve devamda kalan can istemcinin metniyle (lifes_left "%! lives left")."""
        G = self.k.gate(self.key)
        waves = self.g['dalgalar']
        n = min(G['dalga'], len(waves) - 1)
        vals = dict(kapi=self.g['ad'].replace(' Gate', ''), dalga=n + 1, toplam=len(waves), can=G['can'], anahtar=self.key,
                    gruplar=len(waves[n]['gruplar']))
        vals.update(extra)
        m = self.messages().get(event, {})
        out = []
        for kind in ('buyuk', 'kisa'):
            if kind in m:
                text = m[kind].format(**vals)
                out.append(screen(text, big=kind == 'buyuk', NAME=self.g['ad'], WAVE='%d/%d' % (vals['dalga'], vals['toplam']),
                                  **(wild or {})))
        if event in ('giris', 'devam'):
            out.append(stm('lifes_left', '%!', vals['can']))
        return out

    def messages(self):
        """Ekran mesajları (etkinlik kapıları kendi metinlerini üstüne koyar)."""
        return K['mesajlar']

    def wave_msgs(self):
        return [self.wave_msg()]

    def sub_msgs(self):
        """Alt dalga temizlendi: pencerenin dalga sayacı (etkinlik kapıları göndermez)."""
        return [self.wave_msg()]

    def wave_count(self):
        return len(self.g['dalgalar'])

    def countdown(self, now):
        """Dalgadan önce geri sayım (kapilar.json geri_sayim saniyelerinde)."""
        left = int(math.ceil(self.t - now))
        if left in K['geri_sayim'] and left != self.counted:
            self.counted = left
            self.w.send(self.say('geri_sayim', sn=left))

    def wave_msg(self):
        """Dalga sayacı alt dalga biriminde (istemci "Wave: {0} / {1}", toplam GetGateTotalWaves; Hades'te aşama bundan)."""
        G = self.k.gate(self.key)
        return ('GalaxyGateBuilderGateWaveUpdateCommand', dict(gateId=self.g['kimlik'],
                                                               currWave=sub_waves(self.g, G['dalga']) + self.cleared))

    def tick(self, now):
        w, G = self.w, self.k.gate(self.key)
        if w.hero_dead or w.jumping or self.phase in ('void', 'done', 'dead', 'move'):
            return
        if self.phase == 'fight':
            alive = sum(1 for i in self.npcs - self.keep if i in w.npcs)
            if alive:
                if alive <= 3 and alive != self.left:
                    self.left = alive
                    w.send(self.say('kalan', kalan=alive))
                return
            self.cleared = self.sub + 1
            if self.sub + 1 < len(self.wave()['gruplar']):
                self.sub += 1
                self.phase, self.t = 'next', now + pace('alt_dalga_bekleme_sn')
                w.send(self.sub_msgs() + self.say('grup_bitti', grup=self.sub, sn=pace('alt_dalga_bekleme_sn')))
                return
            boss = [w.npcs[i] for i in self.keep if i in w.npcs]
            if boss:
                if not self.exposed:              # diğerleri bitti: kalıcı uzaylı artık hasar alır
                    self.exposed = True
                    w.send(self.sub_msgs() + self.say('koruma_bitti', ad=self.boss))
                return
            self.wave_done(now)
            return
        if now < self.t:
            if self.phase in ('intro', 'break'):
                self.countdown(now)
            return
        if self.phase in ('intro', 'break'):
            self.sub, self.counted, self.exposed, self.cleared = 0, None, False, 0
            self.npcs.clear()
            self.keep.clear()
            w.remove_gate(self.k.exit_portal(self.key, self.map)['gateId'])
            msgs = self.wave_msgs() + [legacy('0|A|STM|atk_wave_started|%%COUNT%%|%d' % (G['dalga'] + 1))] + self.say('dalga_basladi')
            if G['dalga'] == self.wave_count() - 1:
                msgs += self.say('son_dalga')
            w.send(msgs)
            w.log('   %s kapısı: dalga %s başladı' % (self.g['ad'], self.wave()['ad']))
        self.spawn()
        if self.phase == 'fight' and G['dalga'] == self.wave_count() - 1 and self.sub == 0 and not getattr(self, 'filmed', False):
            self.filmed = True                                       # son dalga: kamera patrona (Ö2 sinematik giriş)
            boss = next((w.npcs[i] for i in list(self.keep) + list(self.npcs) if i in w.npcs), None)
            if boss:
                w.cinematic(*boss.mover.pos(time.time()))
        self.left = None
        self.phase = 'fight'

    def spawn(self):
        """Alt dalga: "gruplar"daki [uzaylı, adet] kümeleri oyuncunun çevresinde bir halkada (ring); halka_bekleme_sn durur, sonra
        her biri kendi yönünden oyuncunun peşine düşer (hepsi saldırgan). Kalıcı uzaylı (Zeta Devourer) diğerleri yaşadıkça hasar
        almaz; "oyuncu" görünümlü uzaylı (Kronos Evil You) oyuncunun gemisiyle gelir."""
        w, G = self.w, self.k.gate(self.key)
        wave = self.wave()
        counts = []
        for i, count in wave['gruplar'][self.sub]:
            a = wave['uzaylilar'][i]
            if a['ad'] == 'Evil Iris':
                # Kronos: oyuncunun Iris dronu kadar Evil Iris (wikiwiki.jp Kronos Gate; dronu yoksa wiki'nin 8'i)
                iris = sum(1 for d in self.k.p.d.get('dronlar', []) if d.get('lootId') == 'drone_iris')
                count = min(iris, count) if iris else count
            if not a.get('kalici'):
                count = AY.adet('dalga_npc', count)            # panel: dalgalardaki uzaylı sayısı (koruyan patron bir tane)
            counts.append((i, count))
        hold = time.time() + pace('halka_bekleme_sn')
        for i, x, y in ring(*w.hero_pos(), counts, w.map_w, w.map_h):
            a = wave['uzaylilar'][i]
            model = self.k.p.ship_look() if a['tur'] == 'oyuncu' else None
            n = w.spawn_npc_at(npc_type(self.key, G['dalga'], i), x, y, model=model, dalga=True)
            n.gate, n.hunt = True, True
            n.next_think = hold                  # halkada bekler; sonra peşine düşer (dunya.think: hunt)
            self.npcs.add(n.id)
            if a.get('kalici'):
                self.keep.add(n.id)
                n.invulnerable = lambda: any(j in self.w.npcs for j in self.npcs - self.keep)
                self.boss = a['ad']
                w.send(self.say('koruma', ad=a['ad']))

    def wave_done(self, now):
        G = self.k.gate(self.key)
        label = self.wave()['ad']
        with self.k.p.lock:
            G['dalga'] += 1
            self.k.p.dirty = True
        self.cleared = 0
        self.npcs.clear()
        self.keep.clear()
        if G['dalga'] >= len(self.g['dalgalar']):
            self.complete()
            return
        # ortada iki portal: solundaki sonraki dalgaya (çok haritalı kapıda sonraki haritaya), sağındaki eve; sonraki dalga oyuncu
        # portala girince başlar (resmî kapı rehberi; kullanıcı bildirimi 2026-10-24: yalnız eve dönüş portalı açılıyor, dalga mola
        # bitince kendiliğinden başlıyordu)
        nxt = wave_map(self.g, G['dalga'])
        self.w.add_gate(self.k.next_portal(self.key, self.map, nxt))
        self.w.add_gate(self.k.exit_portal(self.key, self.map, side=True))
        self.w.send([self.wave_msg()] + self.say('sonraki_harita' if nxt != self.map else 'sonraki_dalga', dalga=G['dalga']))
        self.phase = 'move'                 # mesajlardan sonra (aşamayı bekleyen mesajları da görsün)
        self.w.log('   %s kapısı: dalga %s bitti; portallar açık (sonraki %s)' % (self.g['ad'], label, nxt))

    def complete(self):
        """Son dalga: ödüller (Kapilar.finish), çıkış portalı, ekran mesajları."""
        k, w = self.k, self.w
        msgs, info = k.finish(self.key, w.reward_msgs)
        w.add_gate(k.exit_portal(self.key, self.map))
        msgs += [('GalaxyGateBuilderGateCompleteCommand', dict(gateId=self.g['kimlik'], currPart=len(info['yeni']['parcalar'])))]
        msgs += self.say('dalga_bitti', dalga=len(self.g['dalgalar']), sn=0)[:1] + self.say('tamam')
        if info['kronos']:
            got, total = info['kronos']
            msgs += self.say('kronos_parca', sk='s' if got == 1 else 'p', wild=dict(COUNT=got))
            if total >= KRONOS_PARTS:                    # son parça: istemcinin "Kronos Gate erected."
                msgs.append(screen('key:log_msg_gg_build_complete_kronos'))
        w.send(msgs)
        self.phase = 'done'

    def on_death(self):
        """Oyuncu kapıda vuruldu: can 1 azalır; kalmazsa kapı parçalarıyla kaybolur. -> kalan can."""
        if self.phase in ('void', 'done'):
            return None
        k, G = self.k, self.k.gate(self.key)
        with k.p.lock:
            if not AY.get('sonsuz_can'):                    # panel: kapıda can harcanmaz
                G['can'] = max(0, G['can'] - 1)
            left = G['can']
            if left <= 0:
                k.d['kapilar'][self.key] = fresh(self.g, G)
            k.p.dirty = True
        self.w.send([('GalaxyGateBuilderGateLifeLostCommand', dict(gateId=self.g['kimlik'], livesLeft=left))])
        self.w.log('   %s kapısında can kaybedildi: kalan %d%s' % (self.g['ad'], left, ' (kapı kayboldu)' if left <= 0 else ''))
        self.before_death = self.phase
        self.phase = 'void' if left <= 0 else 'dead'      # üste tamirle harita değişir; kapıya yeniden girilince dalga baştan
        return left

    def revive(self):
        """Hades: kapı haritasında yeniden doğuldu; dalga kaldığı yerden sürer."""
        if self.phase == 'dead':
            self.phase = getattr(self, 'before_death', 'fight')
            self.w.log('   %s kapısında yeniden doğuldu: %s' % (self.g['ad'], self.phase))
