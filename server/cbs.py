"""Clan Battle Station (yol haritası Ö5 CBS-1..4; veri data/cbs.json <- tools/cbs.py).

CBS-1 Kurma: X-3..X-7, 4-1..4-5 ve X-BL'deki 23 asteroit (AssetCreateCommand tür 35). Klanlı oyuncu yaklaşınca (600) pencere verisi
(BattleStationBuildingUiInitializationCommand); tıklayınca istemci pencereyi (76) kendisi açar. Modüller sürükle-bırakla 10 yuvaya
(0 Hull, 1 Deflector merkez; 2-9 uydu), her biri 50 sn'de kurulur (aynı anda tek); on modül takılınca Build (5-60 dk). Kurulunca
merkez (36) ve uydular (37), deflector 30 dk kapalı.
CBS-2 Yönetim: Deflector açıkken istasyon dokunulmaz ve süre harcar; kapalıyken süre dolar (saatte 120 dk, prime time 18-21'de 600;
en çok 48 sa); biterse 120 dk zorunlu kapalı; Deactivate 30 dk-8 sa. Boosterlar (onur, EP: her yerde; hasar: istasyonun haritasında)
takılınca %1'den 20 saatte azamiye (%3-10). İstasyonda maden satışı (%10 pahalı), acil onarım (500 U; 20 sn x 7.500), Engineering Bay
ya da yavaş kendiliğinden onarım; yok olmuş modül hangarda uridyumla onarılır. Kurulu istasyonda modül değiştirme 4 dk.
CBS-3 Uzaylı baskınları: prime time'da deflector kapalıyken saatte iki dalga (haritanın seviyesinden 6-12 uzaylı) istasyonu vurur;
silah modülleri menzildeki uzaylılara ateş eder. Merkez yıkılırsa istasyon düşer, modüller yok olmuş (0 can) envantere döner.
CBS-4 Sanal rakip klanlar: boş asteroitlerde zamanla ilerleyen rakip (Progress of leading Clan); rakip önce bitirirse düşman istasyonu
(HOSTILE); deflector'u prime time dışında açık. Rakip modüllerini yıkmak 500-2.600 U, merkezi 5.000 U + 50.000 kredi.
İstemci: istekler Equip/UnequipModule, BuildStation, DeflectorShieldStatusChange, EmergencyRepair, MapAssetActivation, TradeRequest
(istasyonda), HangarShipRepairModule; klan penceresi ClanBattleStationInfo / BattleStationHistoryList; galaksi haritası
StarmapStationCommand. Profilde: cbs {moduller {iid: {loot, seviye, can, kalkan}}, asteroitler {id: …}, gunluk [...], istatistik}.
"""
import datetime, json, math, os, random, time, traceback, types

import ayar as AY
import dunya
import harita as H
import kapi as KAPI
import pve_ortak as PO
from eski_protokol import legacy

HERE = os.path.dirname(os.path.abspath(__file__))
_PATH = os.path.join(HERE, 'data', 'cbs.json')
D = json.load(open(_PATH, encoding='utf8')) if os.path.exists(_PATH) else {}
AST = {a['kimlik']: a for a in D.get('asteroitler', [])}
BY_MAP = {}
for _a in AST.values():
    BY_MAP.setdefault(int(_a['harita']), []).append(_a['kimlik'])
MODS = D.get('moduller', {})
ASSET_BASE = 157000000                 # + asteroit x 100 (asteroit/merkez), + yuva (uydular)
ITEM_BASE = 157500000                  # modül örneklerinin itemId'si
ASTEROID, BATTLESTATION, SATELLITE = 35, 36, 37
HULL, DEFLECTOR = 0, 1                 # merkez yuvaları
SLOTS = 10
OWN, NEUTRAL, HOSTILE = 1, 2, 3        # StarmapStationInfo.StationStatus
DESTRUCTION_BATTLESTATION = 5           # DestructionTypeModule.DestructionCause (ölüm ekranı)
E = dict(UNSPECIFIED=0, NO_CLAN=1, STATION_ALREADY_BUILDING=2, ITEM_HITPOINTS_ZERO=3, ITEM_ALREADY_EQUIPPED_IN_ANOTHER_ASTEROID=4,
         CONCURRENT_EQUIP=5, REPLACE_RIGHT_MISSING=6, ITEM_NOT_OWNED=7, OUT_OF_RANGE=8, EQUIP_OF_SAME_PLAYER_RUNNING=9,
         SATELLITE_ONLY=10, HUB_ONLY=11, ITEM_NOT_IN_STATION=12, MAX_NUMBER_OF_MODULE_TYPE_EXCEEDED=13, DEFLECTOR_ALREADY_ON=14,
         DEFLECTOR_ALREADY_OFF=15, REPAIR_NO_MODULE=16, REPAIR_NO_MONEY=17, REPAIR_ALREADY_RUNNING=18, ITEM_UPGRADE_RUNNING=19)
TRADE_BATTLE_STATION = 4


def mod(_cls, **f):
    f['_'] = _cls
    return f


def asset_id(aid, slot=None):
    return ASSET_BASE + aid * 100 + (slot if slot is not None and slot > DEFLECTOR else 0)


def position(aid):
    a = AST[aid]
    w, h = H.map_size(a['harita'])
    return int(w * a['x_yuzde'] / 100.0), int(h * a['y_yuzde'] / 100.0)


def satellite_pos(aid, slot):
    """Uydu modülünün konumu: merkezin çevresinde (yuva 2-9, 45 derece arayla)."""
    x, y = position(aid)
    a = (slot - 2) * math.pi / 4
    return int(x + math.cos(a) * 260), int(y + math.sin(a) * 180)


def prime_time(now=None):
    t = datetime.datetime.fromtimestamp(time.time() if now is None else now)
    a, b = D.get('prime_time', ['18:00', '21:00'])
    h = t.hour + t.minute / 60.0
    return float(a.split(':')[0]) <= h < float(b.split(':')[0])


def level_value(row, lv):
    return row[max(0, min(len(row) - 1, int(lv)))]


def stm(key, **params):
    """İstemcinin metni (flashres) yer tutucularıyla: 0|A|STM|anahtar|%AD%|değer…"""
    return legacy('0|A|STM|%s%s' % (key, ''.join('|%%%s%%|%s' % (k, v) for k, v in params.items())))


def stamp(t=None):
    return time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time() if t is None else t))


class Cbs:
    REQUESTS = ('EquipModuleRequest', 'UnequipModuleRequest', 'BuildStationRequest', 'DeflectorShieldStatusChangeRequest',
                'EmergencyRepairRequest', 'HangarShipRepairModuleRequest')

    def __init__(self, profil, magaza, log=print):
        self.p, self.m, self.log = profil, magaza, log
        self.world = None
        self.near = None                        # menzildeki asteroit
        self.shown_assets = []                  # bu haritada gönderilen varlıklar
        self.next_raid = {}
        self.raiders = {}                       # uzaylı -> asteroit
        self.next_shot = {}
        self.tick_err = {}                      # asteroit -> hatası bir kez yazıldı
        self.starmap_tpl = None                 # girişin StarmapStationCommand şablonu (değişince yeniden gönderilir)
        self.home = None                        # oturum bağlar: üs haritası

    # ------------------------------------------------------------ profil
    @property
    def st(self):
        d = self.p.d.setdefault('cbs', {})
        for k, v in (('moduller', {}), ('asteroitler', {}), ('gunluk', []), ('istatistik', {}), ('sira', 0)):
            d.setdefault(k, v)
        self.absorb(d)
        return d

    def absorb(self, d):
        """Ödül yolundan depoya düşen modüller (module_* sayaçları) tek tek örneğe çevrilir (can, kalkan, seviye)."""
        store = self.p.d.get('diger_esyalar', {})
        loots = [l for l in list(store) if l in MODS]
        for loot in loots:
            n = int(store.pop(loot, 0))
            for _ in range(n):
                d['sira'] += 1
                iid = ITEM_BASE + d['sira']
                hp = level_value(MODS[loot]['can'], 0)
                d['moduller'][str(iid)] = dict(loot=loot, seviye=0, can=hp, kalkan=int(hp * D['kalkan_orani']))
            self.p.dirty = True

    def ast(self, aid):
        a = self.st['asteroitler'].setdefault(str(aid), {})
        a.setdefault('durum', 'bos')
        a.setdefault('yuvalar', {})
        a.setdefault('deflector', {'acik': False, 'sn': 0.0, 'kapali_bitis': 0.0, 'son': time.time()})
        return a

    def klan(self):
        return self.p.d.get('klan')

    def clan_name(self):
        k = self.klan()
        return k['ad'] if k else ''

    def faction(self):
        k = self.klan()
        return int((k or {}).get('firma') or self.p.d['pilot'].get('factionId', 0))

    def module(self, iid):
        return self.st['moduller'].get(str(iid))

    def where(self, iid):
        """Modülün takılı olduğu (asteroit, yuva) ya da None."""
        for aid, a in self.st['asteroitler'].items():
            for slot, y in a.get('yuvalar', {}).items():
                if str(y.get('iid')) == str(iid):
                    return int(aid), int(slot)
        return None

    def mx(self, m):
        hp = level_value(MODS[m['loot']]['can'], m['seviye'])
        return hp, int(hp * D['kalkan_orani'])

    # ------------------------------------------------------------ komutlar
    def module_cmd(self, iid, aid=-1, slot=-1, now=None):
        now = time.time() if now is None else now
        m = self.module(iid)
        md = MODS[m['loot']]
        mh, ms = self.mx(m)
        y = (self.ast(aid)['yuvalar'].get(str(slot)) if aid > 0 else None) or {}
        left = max(0, int(y.get('kurulum_bitis', 0) - now))
        rep = max(0, int(y.get('onarim_bitis', 0) - now))
        return mod('StationModuleModule', asteroidId=aid, itemId=int(iid), slotId=slot, type=md['tur'], currentHitpoints=int(m['can']),
                   maxHitpoints=mh, currentShield=int(m['kalkan']), maxShield=ms, upgradeLevel=int(m['seviye']),
                   ownerName=self.p.d['pilot'].get('userName', '') if aid > 0 else '', installationSeconds=int(y.get('kurulum_sn', 0)),
                   installationSecondsLeft=left, emergencyRepairSecondsLeft=rep,
                   emergencyRepairSecondsTotal=D['acil_onarim']['sure_sn'] if rep else 0, emergencyRepairCost=D['acil_onarim']['bedel'])

    def available_cmd(self):
        free = [iid for iid in sorted(self.st['moduller'], key=int) if not self.where(iid)]
        return mod('AvailableModulesCommand', modules=[self.module_cmd(i) for i in free])

    def available_msg(self):
        """Pencerenin envanterini yeniler (istemci UiInitialization'daki listeyi yalnız ilk kez alıyor; canlı tur Ö5)."""
        return ('AvailableModulesCommand', {'modules': self.available_cmd()['modules']})

    def equipped(self, aid, now=None):
        a = self.ast(aid)
        return mod('EquippedModulesModule', modules=[self.module_cmd(y['iid'], aid, int(s), now) for s, y in sorted(a['yuvalar'].items(),
                                                                                                                key=lambda kv: int(kv[0]))
                                                     if self.module(y['iid'])])

    def own_progress(self, aid, now=None):
        now = time.time() if now is None else now
        a = self.ast(aid)
        done = sum(1 for y in a['yuvalar'].values() if y.get('kurulum_bitis', 0) <= now)
        return done / float(SLOTS)

    def progress_cmd(self, aid, now=None):
        a = self.ast(aid)
        own = self.own_progress(aid, now)
        r = a.get('rakip')
        best = max(own, a.get('rakip_ilerleme', 0) if r else 0)
        best_name = (self.clan_name() if own >= a.get('rakip_ilerleme', 0) else r) if (own or r) else ''
        return mod('AsteroidProgressCommand', battleStationId=aid, ownProgress=float(own), bestProgress=float(best), ownClanName=self.clan_name(),
                   bestProgressClanName=best_name or '', state=self.equipped(aid, now), buildButtonActive=own >= 1.0 and a['durum'] == 'bos')

    def progress_msg(self, aid, now=None):
        f = dict(self.progress_cmd(aid, now))
        f.pop('_')
        return ('AsteroidProgressCommand', f)

    def status_msg(self, aid, now=None):
        f = dict(self.status_cmd(aid, now))
        f.pop('_')
        return ('BattleStationStatusCommand', f)

    def building_ui(self, aid):
        k = D['kurma_dk']
        return ('BattleStationBuildingUiInitializationCommand', dict(
            mapAssetId=asset_id(aid), battleStationId=aid, battleStationName=AST[aid]['ad'], progress=self.progress_cmd(aid),
            availableModules=self.available_cmd(), buildTimeInMinutesMin=k[0], buildTimeInMinutesMax=k[1], buildTimeInMinutesIncrement=k[2]))

    def booster_pct(self, aid, kind, now=None):
        """Booster modülünün etkisi (%): takılıp kurulduktan sonra %1'den 20 saatte azamiye."""
        now = time.time() if now is None else now
        a = self.ast(aid)
        if a['durum'] != 'kurulu':
            return 0.0
        for slot, y in a['yuvalar'].items():
            m = self.module(y['iid'])
            if not m or MODS[m['loot']].get('booster') != kind or y.get('kurulum_bitis', 0) > now or m['can'] <= 0:
                continue
            top = level_value(MODS[m['loot']]['booster_yuzde'], m['seviye'])
            t = (now - max(y.get('kurulum_bitis', 0), a.get('kurulus', 0))) / (D['booster']['buyume_sa'] * 3600.0)
            return min(top, D['booster']['baslangic'] + (top - D['booster']['baslangic']) * max(0.0, min(1.0, t)))
        return 0.0

    def ratings(self, aid, now=None):
        a = self.ast(aid)
        att = dfn = rep = 0
        for y in a['yuvalar'].values():
            m = self.module(y['iid'])
            if not m:
                continue
            md = MODS[m['loot']]
            dfn += int(m['can'] + m['kalkan'])
            if md.get('silah'):
                att += level_value(md['hasar'], m['seviye'])
            if md.get('onarim_sn'):
                rep += level_value(md['onarim_sn'], m['seviye'])
        return att // 1000, dfn // 1000, rep

    def deflector_rate(self, now=None):
        r = D['deflector_hiz']
        return r['prime_time'] if prime_time(now) else r['normal']

    def status_cmd(self, aid, now=None):
        now = time.time() if now is None else now
        a = self.ast(aid)
        df = a['deflector']
        att, dfn, rep = self.ratings(aid, now)
        return mod('BattleStationStatusCommand', mapAssetId=asset_id(aid), battleStationId=aid, battleStationName=AST[aid]['ad'],
                   deflectorShieldActive=bool(df['acik']), deflectorShieldSeconds=int(df['sn']), deflectorShieldSecondsMax=D['deflector_azami_sn'],
                   attackRating=att, defenceRating=dfn, repairRating=rep, honorBoosterRating=int(round(self.booster_pct(aid, 'onur', now))),
                   experienceBoosterRating=int(round(self.booster_pct(aid, 'ep', now))),
                   damageBoosterRating=int(round(self.booster_pct(aid, 'hasar', now))), deflectorShieldRate=self.deflector_rate(now),
                   repairPrice=D['acil_onarim']['bedel'], equipment=self.equipped(aid, now), isOreTradeAvailable=True)

    def management_ui(self, aid):
        dm = D['deflector_dk']
        a = self.ast(aid)
        return ('BattleStationManagementUiInitializationCommand', dict(
            mapAssetId=asset_id(aid), battleStationId=aid, battleStationName=AST[aid]['ad'], clanName=self.clan_name(),
            faction=mod('FactionModule', faction=self.faction()), state=self.status_cmd(aid), availableModules=self.available_cmd(),
            deflectorShieldMinutesMin=dm[0], deflectorShieldMinutesMax=dm[1], deflectorShieldMinutesIncrement=dm[2],
            deflectorDeactivationPossible=bool(a['deflector']['acik'])))

    def building_state(self, aid, now=None):
        now = time.time() if now is None else now
        a = self.ast(aid)
        return ('BattleStationBuildingStateCommand', dict(mapAssetId=asset_id(aid), battleStationId=aid, battleStationName=AST[aid]['ad'],
                                                          secondsLeft=max(0, int(a.get('kurma_bitis', now) - now)),
                                                          totalSeconds=int(a.get('kurma_sn', 0)), ownerClan=self.clan_name(),
                                                          affiliatedFaction=mod('FactionModule', faction=self.faction())))

    def ui_msgs(self, aid):
        """Yaklaşınca pencerenin verisi (istemci tıklamada kendisi açar): klansız / asteroit / kuruluyor / kurulu."""
        a = self.ast(aid)
        if not self.klan():
            return [('BattleStationNoClanUiInitializationCommand', {'mapAssetId': asset_id(aid)})]
        if a.get('sahip') == 'rakip':
            return []
        if a['durum'] == 'kurma':
            return [self.building_state(aid)]
        if a['durum'] == 'kurulu':
            return [self.management_ui(aid)]
        return [self.building_ui(aid)]

    def error(self, kind):
        return [('BattleStationErrorCommand', {'type': E[kind]})]

    # ------------------------------------------------------------ varlıklar
    def asset_cmd(self, aid_asset, kind, x, y, name, design=1, stage=0, clan=None, faction=0, relation=0):
        return ('AssetCreateCommand', dict(designId=design, clanId=int((clan or {}).get('id', 0)), showBubble=True, userName=name,
                                           assetId=aid_asset, expansionStage=stage, modifier=[], type=mod('AssetTypeModule', typeValue=kind),
                                           detectedByWarnRadar=True, invisible=False, posY=int(y),
                                           clanRelation=mod('ClanRelationModule', type=relation), clanTag=(clan or {}).get('etiket', ''),
                                           factionId=faction, posX=int(x), visibleOnWarnRadar=False))

    def map_assets(self, aid):
        """Asteroidin varlıkları: boşsa asteroit (35); kuruluysa merkez (36) ve uydular (37)."""
        a = self.ast(aid)
        x, y = position(aid)
        if a['durum'] != 'kurulu':
            return [(asset_id(aid), ASTEROID, self.asset_cmd(asset_id(aid), ASTEROID, x, y, AST[aid]['ad']))]
        rival = a.get('sahip') == 'rakip'
        clan = {'id': 9000 + aid, 'etiket': (a.get('rakip') or '')[:3].upper()} if rival else self.klan()
        fac = a.get('rakip_firma', 0) if rival else self.faction()
        rel = 3 if rival else 0
        hull = a['yuvalar'].get(str(HULL))
        hm = (hull if rival else self.module(hull['iid'])) if hull else None       # rakibin yuvasında modülün kendisi
        stage = hm['seviye'] if hm else 0
        out = [(asset_id(aid), BATTLESTATION, self.asset_cmd(asset_id(aid), BATTLESTATION, x, y, a.get('rakip') if rival else self.clan_name(),
                                                             stage=stage, clan=clan, faction=fac, relation=rel))]
        for slot, yv in sorted(a['yuvalar'].items(), key=lambda kv: int(kv[0])):
            s = int(slot)
            if s <= DEFLECTOR:
                continue
            m = self.module(yv['iid']) if not rival else yv
            if not m:
                continue
            sx, sy = satellite_pos(aid, s)
            loot = m['loot']
            dead = m['can'] <= 0
            out.append((asset_id(aid, s), SATELLITE, self.asset_cmd(asset_id(aid, s), SATELLITE, sx, sy, 'wreck' if dead else MODS[loot]['kod'],
                                                                   design=0 if dead else MODS[loot]['tasarim'], stage=m['seviye'],
                                                                   clan=clan, faction=fac, relation=rel)))
        return out

    def remove_assets(self):
        msgs = [('AssetRemoveCommand', {'assetType': mod('AssetTypeModule', typeValue=k), 'uid': i}) for i, k in self.shown_assets]
        self.shown_assets = []
        return msgs

    def show_assets(self, map_id):
        msgs = self.remove_assets()
        for aid in BY_MAP.get(int(map_id), []):
            for i, k, cmd in self.map_assets(aid):
                self.shown_assets.append((i, k))
                msgs.append(cmd)
        return msgs

    def info_cmd(self, aid, slot, m=None):
        """Varlığın can/kalkan çubuğu (AssetInfoCommand)."""
        a = self.ast(aid)
        y = a['yuvalar'].get(str(slot)) or {}
        m = m or (y if a.get('sahip') == 'rakip' else self.module(y.get('iid')))
        if not m:
            return None
        mh = m.get('azami') or level_value(MODS[m['loot']]['can'], m['seviye'])     # rakipte tek oyunculu çarpanla (azami)
        ms = int(mh * D['kalkan_orani'])
        kind = BATTLESTATION if slot <= DEFLECTOR else SATELLITE
        return ('AssetInfoCommand', dict(assetId=asset_id(aid, slot), type=mod('AssetTypeModule', typeValue=kind),
                                         designId=1 if kind == BATTLESTATION else MODS[m['loot']]['tasarim'], expansionStage=int(m['seviye']),
                                         hitpoints=int(m['can']), maxHitpoints=mh, shielded=m['kalkan'] > 0, shieldEnergy=int(m['kalkan']),
                                         maxShieldEnergy=ms))

    # ------------------------------------------------------------ dünya
    def attach(self, world):
        self.world = world
        self.near = None
        world.cbs_trade = self.trade_mult
        world.asset_targets = self                      # rakip istasyonun modülleri seçilir ve vurulur (dunya.asset_laser)
        msgs = self.show_assets(world.map_id)
        return msgs

    def starmap_msgs(self):
        """Yıldız haritasının istasyon durumları değişti (kuruldu, rakip kurdu, yıkıldı): girişteki şablonla yeniden."""
        return self.login_replace('StarmapStationCommand', self.starmap_tpl) if self.starmap_tpl and self.world else []

    def login_replace(self, n, f):
        if n != 'StarmapStationCommand':
            return None
        self.starmap_tpl = f
        f = json.loads(json.dumps(f))
        by_name = {a['ad']: k for k, a in AST.items()}
        for s in f.get('stations', []):
            aid = by_name.get(s.get('asteroidName'))
            if not aid:
                continue
            a = self.ast(aid)
            if a['durum'] in ('kurulu', 'kurma'):
                rival = a.get('sahip') == 'rakip'
                s.update(status=HOSTILE if rival else OWN, clanName=a.get('rakip') if rival else self.clan_name(),
                         owningFaction=mod('FactionModule', faction=a.get('rakip_firma', 0) if rival else self.faction()),
                         lastChangedTimestamp=int(a.get('kurulus', time.time()) * 1000))
        f['currentServerTimestamp'] = int(time.time() * 1000)
        return [('StarmapStationCommand', {k: v for k, v in f.items() if k != '_m'})]

    def tick(self, now):
        msgs = []
        st = self.st
        for aid_s, a in list(st['asteroitler'].items()):
            try:                                        # bir asteroidin hatası ötekileri ve yakınlığı durdurmasın
                msgs += self.tick_asteroid(int(aid_s), a, now)
            except Exception:
                if not self.tick_err.get(aid_s):
                    self.tick_err[aid_s] = True
                    self.log('   CBS: %s asteroidinde hata:\n%s' % (AST.get(int(aid_s), {}).get('ad', aid_s), traceback.format_exc()))
        w = self.world
        if w and not w.hero_dead and BY_MAP.get(int(w.map_id)):
            hx, hy = w.hero_pos(now)
            near = next((aid for aid in BY_MAP[int(w.map_id)] if math.hypot(position(aid)[0] - hx, position(aid)[1] - hy)
                         <= D['menzil']), None)
            if near != self.near:
                if self.near:
                    msgs += [H.asset_available(asset_id(self.near), 'ttip_cbs', False),
                             ('OutOfBattleStationRangeCommand', {'battleStationId': asset_id(self.near)})]
                if near:
                    msgs += [H.asset_available(asset_id(near), 'ttip_cbs', True)] + self.ui_msgs(near)
                    msgs += self.p.hint(27) if getattr(self.p, 'hint', None) else []      # CLAN_BATTLE_STATION ipucu
                self.near = near
            if w:
                msgs += self.raid_tick(now)
                msgs += self.rival_fire(now)
        return msgs

    def tick_asteroid(self, aid, a, now):
        msgs = []
        w = self.world
        here = w is not None and int(w.map_id) == int(AST[aid]['harita'])
        if a.get('sahip') != 'rakip':
            done = [y for y in a['yuvalar'].values()            # kurulumu biten modüller: adımda bir kez yenilenir
                    if y.get('kurulum_sn') and not y.get('kuruldu') and now >= y.get('kurulum_bitis', 0)]
            for y in done:
                y['kuruldu'] = True
                self.p.dirty = True
            if done and here and self.near == aid:
                msgs.append(self.progress_msg(aid, now) if a['durum'] == 'bos' else self.status_msg(aid, now))
            if done and a['durum'] == 'kurulu' and here:
                msgs += self.refresh_assets(aid)
        if a['durum'] == 'kurma' and now >= a.get('kurma_bitis', 0):
            msgs += self.finish_build(aid, now)
        if a['durum'] == 'kurulu' and a.get('sahip') != 'rakip':        # rakibin deflector'ü ve onarımı rival_tick'te
            msgs += self.deflector_tick(aid, a, now)
            msgs += self.repair_tick(aid, a, now)
        msgs += self.rival_tick(aid, a, now)
        return msgs

    def refresh_assets(self, aid):
        msgs = []
        for i, k in [x for x in self.shown_assets if ASSET_BASE + aid * 100 <= x[0] < ASSET_BASE + aid * 100 + 100]:
            msgs.append(('AssetRemoveCommand', {'assetType': mod('AssetTypeModule', typeValue=k), 'uid': i}))
            self.shown_assets.remove((i, k))
        for i, k, cmd in self.map_assets(aid):
            self.shown_assets.append((i, k))
            msgs.append(cmd)
        return msgs

    # ------------------------------------------------------------ istekler
    def in_range(self, aid):
        w = self.world
        if not w or int(w.map_id) != int(AST.get(aid, {}).get('harita', -1)):
            return False
        hx, hy = w.hero_pos()
        x, y = position(aid)
        return math.hypot(x - hx, y - hy) <= D['menzil'] + 100

    def handles(self, name, f):
        if name == 'MapAssetActivationRequest':
            return int(f.get('mapAssetId') or 0) // 100 * 100 - ASSET_BASE in [k * 100 for k in AST]
        return name in self.REQUESTS

    def handle(self, name, f):
        if name == 'MapAssetActivationRequest':
            aid = (int(f.get('mapAssetId') or 0) - ASSET_BASE) // 100
            return self.ui_msgs(aid) if aid in AST and self.in_range(aid) else []
        if name == 'HangarShipRepairModuleRequest':
            return self.hangar_repair(int(f.get('itemId') or 0))
        aid = int(f.get('battleStationId') or 0)
        if aid not in AST:
            return self.error('UNSPECIFIED')
        if not self.klan():
            return self.error('NO_CLAN')
        if not self.in_range(aid):
            return self.error('OUT_OF_RANGE')
        if name == 'EquipModuleRequest':
            return self.equip(aid, int(f.get('itemId') or 0), int(f.get('slotId') or 0), bool(f.get('replace')))
        if name == 'UnequipModuleRequest':
            return self.unequip(aid, int(f.get('itemId') or 0))
        if name == 'BuildStationRequest':
            return self.build(aid, int(f.get('buildTimeInMinutes') or 0))
        if name == 'DeflectorShieldStatusChangeRequest':
            return self.deflector_off(aid, int(f.get('minutes') or 0))
        if name == 'EmergencyRepairRequest':
            return self.emergency(aid, int(f.get('slotId') or 0))
        return []

    def equip(self, aid, iid, slot, replace):
        a = self.ast(aid)
        now = time.time()
        m = self.module(iid)
        if a.get('sahip') == 'rakip':
            return self.error('CONCURRENT_EQUIP')
        if a['durum'] == 'kurma':
            return self.error('STATION_ALREADY_BUILDING')
        if not m:
            return self.error('ITEM_NOT_OWNED')
        if self.where(iid):
            return self.error('ITEM_ALREADY_EQUIPPED_IN_ANOTHER_ASTEROID')
        if m['can'] <= 0:
            return self.error('ITEM_HITPOINTS_ZERO')
        if any(y.get('kurulum_bitis', 0) > now for b in self.st['asteroitler'].values() for y in b.get('yuvalar', {}).values()):
            return self.error('EQUIP_OF_SAME_PLAYER_RUNNING')
        md = MODS[m['loot']]
        if slot < 0 or slot >= SLOTS:
            return self.error('UNSPECIFIED')
        if slot <= DEFLECTOR and (not md['merkez'] or (slot == HULL) != (md['tur'] == 2)):
            return self.error('HUB_ONLY' if not md['merkez'] else 'SATELLITE_ONLY')
        if slot > DEFLECTOR and md['merkez']:
            return self.error('SATELLITE_ONLY')
        same = sum(1 for s, y in a['yuvalar'].items() if int(s) != slot and self.module(y['iid'])
                   and self.module(y['iid'])['loot'] == m['loot'])
        if same >= md['en_cok']:
            return self.error('MAX_NUMBER_OF_MODULE_TYPE_EXCEEDED')
        old = a['yuvalar'].get(str(slot))
        if old and not replace:
            return self.error('CONCURRENT_EQUIP')
        secs = D['degistirme_sn'] if a['durum'] == 'kurulu' else D['kurulum_sn']
        with self.p.lock:
            a['yuvalar'][str(slot)] = {'iid': iid, 'kurulum_bitis': now + secs, 'kurulum_sn': secs}
            self.p.dirty = True
        if old:
            self.note(aid, 'MODULE_REPLACED', oldModuleType=self.module(old['iid'])['loot'] if self.module(old['iid']) else '',
                      oldModuleLevel=0, newModuleType=m['loot'], newModuleLevel=m['seviye'], slot=slot if slot > DEFLECTOR else -1)
        self.log('   CBS: %s %s yuva %d (%d sn)' % (AST[aid]['ad'], m['loot'], slot, secs))
        msgs = [self.progress_msg(aid, now) if a['durum'] == 'bos' else self.status_msg(aid, now), self.available_msg()]
        if a['durum'] != 'bos':
            msgs += self.refresh_assets(aid)
        return msgs

    def unequip(self, aid, iid):
        a = self.ast(aid)
        hit = next((s for s, y in a['yuvalar'].items() if int(y['iid']) == iid), None)
        if hit is None:
            return self.error('ITEM_NOT_IN_STATION')
        with self.p.lock:
            del a['yuvalar'][hit]
            self.p.dirty = True
        m = self.module(iid)
        self.note(aid, 'MODULE_REMOVED', moduleType=m['loot'] if m else '', moduleLevel=m['seviye'] if m else 0,
                  slot=int(hit) if int(hit) > DEFLECTOR else -1)
        if a['durum'] == 'kurulu' and int(hit) == HULL:
            self.destroy(aid, 'hull removed')
            return [self.building_ui(aid), self.available_msg()] + self.refresh_assets(aid)
        msgs = [self.progress_msg(aid) if a['durum'] == 'bos' else self.status_msg(aid), self.available_msg()]
        return msgs + (self.refresh_assets(aid) if a['durum'] != 'bos' else [])

    def build(self, aid, minutes):
        a = self.ast(aid)
        now = time.time()
        if a['durum'] != 'bos' or self.own_progress(aid, now) < 1.0:
            return self.error('STATION_ALREADY_BUILDING')
        k = D['kurma_dk']
        minutes = max(k[0], min(k[1], minutes or k[0]))
        with self.p.lock:
            a.update(durum='kurma', kurma_bitis=now + minutes * 60, kurma_sn=minutes * 60, sahip='oyuncu')
            a.pop('rakip', None)
            a.pop('rakip_ilerleme', None)
            self.p.dirty = True
        self.note(aid, 'BUILD_START', buildSeconds=minutes * 60)
        self.log('   CBS: %s kuruluyor (%d dk)' % (AST[aid]['ad'], minutes))
        return [self.building_state(aid, now)]

    def finish_build(self, aid, now):
        a = self.ast(aid)
        with self.p.lock:
            a.update(durum='kurulu', kurulus=now)
            a['deflector'] = {'acik': False, 'sn': 0.0, 'kapali_bitis': now + D['kurulunca_kapali_dk'] * 60, 'son': now}
            ist = self.st['istatistik']
            ist['tum'] = ist.get('tum', 0) + 1
            ist['en_cok'] = max(ist.get('en_cok', 0), sum(1 for b in self.st['asteroitler'].values() if b.get('durum') == 'kurulu'
                                                       and b.get('sahip') != 'rakip'))
            self.p.dirty = True
        self.note(aid, 'BUILD_FINISHED')
        self.log('   CBS: %s kuruldu' % AST[aid]['ad'])
        msgs = [stm('msg_station_accomplished', STATION=AST[aid]['ad'], CLAN=self.clan_name(),
                    MAP=H.name(AST[aid]['harita']))] + self.starmap_msgs()
        w = self.world
        if w and int(w.map_id) == int(AST[aid]['harita']):
            msgs += self.refresh_assets(aid)
            if self.near == aid:
                msgs.append(self.management_ui(aid))
        return msgs

    def deflector_tick(self, aid, a, now):
        df = a['deflector']
        dt = max(0.0, now - df.get('son', now))
        df['son'] = now
        msgs = []
        if df['acik']:
            df['sn'] = max(0.0, df['sn'] - dt)
            if df['sn'] <= 0:
                df.update(acik=False, kapali_bitis=now + D['deflector_bitince_dk'] * 60)
                self.note(aid, 'DEFLECTOR_OFF')
                msgs.append(KAPI.screen('The deflector shield of your Battle Station at %s is down!' % AST[aid]['ad']))
                msgs += self.near_status(aid, now)
        else:
            df['sn'] = min(D['deflector_azami_sn'], df['sn'] + dt * self.deflector_rate(now) / 60.0)
            if now >= df.get('kapali_bitis', 0) and df['sn'] > 0:
                df['acik'] = True
                self.note(aid, 'DEFLECTOR_ON')
                msgs += self.near_status(aid, now)
        self.p.dirty = True
        return msgs

    def near_status(self, aid, now):
        """Deflector açıldı/kapandı: durum + yönetim verisi (Deactivate düğmesinin kaydırıcısı deflectorDeactivationPossible'dan)."""
        return [self.status_msg(aid, now), self.management_ui(aid)] if self.near == aid else []

    def deflector_off(self, aid, minutes):
        a = self.ast(aid)
        if a['durum'] != 'kurulu':
            return self.error('UNSPECIFIED')
        df = a['deflector']
        if not df['acik']:
            return self.error('DEFLECTOR_ALREADY_OFF')
        dm = D['deflector_dk']
        minutes = max(dm[0], min(dm[1], minutes or dm[0]))
        now = time.time()
        with self.p.lock:
            df.update(acik=False, kapali_bitis=now + minutes * 60, son=now)
            self.p.dirty = True
        self.note(aid, 'DEFLECTOR_OFF', userName=self.p.d['pilot'].get('userName', ''))
        self.log('   CBS: %s deflector %d dk kapalı' % (AST[aid]['ad'], minutes))
        return [self.status_msg(aid, now), self.management_ui(aid)]

    def emergency(self, aid, slot):
        a = self.ast(aid)
        y = a['yuvalar'].get(str(slot))
        m = self.module(y['iid']) if y else None
        if not m or m['can'] <= 0:
            return self.error('REPAIR_NO_MODULE')
        now = time.time()
        if y.get('onarim_bitis', 0) > now:
            return self.error('REPAIR_ALREADY_RUNNING')
        cost = D['acil_onarim']['bedel']
        if self.p.d['pilot'].get('uridium', 0) < cost:
            return self.error('REPAIR_NO_MONEY')
        self.p.gain(uridyum=-cost, neden='battlestation_emergency_repair')
        with self.p.lock:
            y['onarim_bitis'] = now + D['acil_onarim']['sure_sn']
            self.p.dirty = True
        self.note(aid, 'EMERGENCY_REPAIR', moduleType=m['loot'], moduleLevel=m['seviye'], slot=slot if slot > DEFLECTOR else -1)
        return [self.status_msg(aid, now), stm('msg_emergency_repair_started', STATION=AST[aid]['ad'])] + self.m.money_msgs()

    def repair_tick(self, aid, a, now):
        """Acil onarım (7.500/sn), Engineering Bay (bütün modüller) ya da son hasardan 30 sn sonra yavaş onarım; kalkan dolar."""
        rep = 0
        for y in a['yuvalar'].values():
            m = self.module(y['iid'])
            if m and MODS[m['loot']].get('onarim_sn') and m['can'] > 0:
                rep = level_value(MODS[m['loot']]['onarim_sn'], m['seviye'])
        changed = []
        for slot, y in a['yuvalar'].items():
            m = self.module(y['iid'])
            if not m or m['can'] <= 0:
                continue
            mh, ms = self.mx(m)
            heal = 0
            if y.get('onarim_bitis', 0) > now:
                heal += D['acil_onarim']['can_sn']
            if rep:
                heal += rep
            elif now - a.get('son_hasar', 0) > D['pasif_onarim']['gecikme_sn']:
                heal += D['pasif_onarim']['can_sn']
            before = (m['can'], m['kalkan'])
            m['can'] = min(mh, m['can'] + heal)
            if now - a.get('son_hasar', 0) > 10:
                m['kalkan'] = min(ms, m['kalkan'] + ms * 0.02)
            if (m['can'], m['kalkan']) != before:
                changed.append(int(slot))
        w = self.world
        if changed and w and int(w.map_id) == int(AST[aid]['harita']) and int(now) % 5 == 0:
            return [c for c in (self.info_cmd(aid, s) for s in changed) if c]
        return []

    def hangar_repair(self, iid):
        m = self.module(iid)
        if not m:
            return []
        mh, ms = self.mx(m)
        from magaza import stack_msg
        if self.where(iid):
            return [('HangarShipRepairModuleCommand', dict(errorMessage=stack_msg('eqt_error_playerMayNotRepair'), itemId=iid,
                                                            currentHitPoints=int(m['can']), maxHitPoints=mh, resultId=1))]
        cost = max(D['onarim_bedeli']['en_az'], int((mh - m['can']) * D['onarim_bedeli']['can_basina_U']))
        if m['can'] >= mh or self.p.d['pilot'].get('uridium', 0) < cost:
            return [('HangarShipRepairModuleCommand', dict(errorMessage=stack_msg('empty'), itemId=iid, currentHitPoints=int(m['can']),
                                                            maxHitPoints=mh, resultId=1))]
        self.p.gain(uridyum=-cost, neden='repair_module')
        with self.p.lock:
            m['can'], m['kalkan'] = mh, ms
            self.p.dirty = True
        self.log('   CBS: modül onarıldı %s (%d U)' % (m['loot'], cost))
        return [('HangarShipRepairModuleCommand', dict(errorMessage=stack_msg('empty'), itemId=iid, currentHitPoints=mh, maxHitPoints=mh,
                                                        resultId=0))] + self.m.money_msgs()

    # ------------------------------------------------------------ boosterlar ve ticaret
    def mods(self):
        """Profilin bonusları (profil.mods): onur ve EP her yerde, hasar istasyonun haritasında (en güçlü istasyonun)."""
        out = {}
        here = int(self.p.d['konum'].get('mapId', 0))
        for aid_s, a in self.st['asteroitler'].items():
            if a.get('durum') != 'kurulu' or a.get('sahip') == 'rakip':
                continue
            aid = int(aid_s)
            out['onur'] = max(out.get('onur', 0), self.booster_pct(aid, 'onur') / 100.0)
            out['ep'] = max(out.get('ep', 0), self.booster_pct(aid, 'ep') / 100.0)
            if int(AST[aid]['harita']) == here:
                d = self.booster_pct(aid, 'hasar') / 100.0
                out['lazer'] = max(out.get('lazer', 0), d)
                out['roket'] = max(out.get('roket', 0), d)
        return {k: v for k, v in out.items() if v}

    def trade_mult(self):
        """Kendi istasyonunun menzilinde maden satışı (TradeType BATTLE_STATION, fiyat x1,1) -> çarpan ya da None."""
        if self.near and self.ast(self.near)['durum'] == 'kurulu' and self.ast(self.near).get('sahip') != 'rakip':
            return D['maden_carpani']
        return None

    # ------------------------------------------------------------ hasar ve yıkım (baskın ve rakip)
    def damage_module(self, aid, slot, dmg, attacker_name=''):
        """Modüle hasar (kalkan %80 emer) -> mesajlar; can 0: yok olur; merkez (Hull) giderse istasyon düşer."""
        a = self.ast(aid)
        y = a['yuvalar'].get(str(slot))
        rival = a.get('sahip') == 'rakip'
        m = y if rival else (self.module(y['iid']) if y else None)
        if not m or m['can'] <= 0:
            return []
        to_shield = min(m['kalkan'], int(dmg * 0.8))
        m['kalkan'] -= to_shield
        m['can'] = max(0, m['can'] - (dmg - to_shield))
        a['son_hasar'] = time.time()
        self.p.dirty = True
        msgs = [c for c in [self.info_cmd(aid, slot, m)] if c]
        if m['can'] <= 0:
            msgs += self.module_destroyed(aid, slot, attacker_name)
        return msgs

    def module_destroyed(self, aid, slot, by=''):
        a = self.ast(aid)
        rival = a.get('sahip') == 'rakip'
        y = a['yuvalar'].get(str(slot))
        m = y if rival else self.module(y['iid'])
        msgs = []
        self.note(aid, 'MODULE_DESTROYED', moduleType=m['loot'], moduleLevel=m['seviye'], slot=slot if slot > DEFLECTOR else -1,
                  opponentClanName=by)
        if rival:                                       # oyuncu rakibin modülünü yıktı: uridyum
            kind = MODS[m['loot']].get('silah') or 'diger'
            u = D['yikma_odulu']['taban'].get(kind, D['yikma_odulu']['taban']['diger']) + D['yikma_odulu']['seviye_basina'] * m['seviye']
            u = AY.miktar('uridyum', u)                     # panelin uridyum çarpanı
            self.p.gain(uridyum=u, neden='battlestation_destroy_modul')
            msgs += [stm('msg_station_satellite_destruction_reward', AMOUNT=u, MODULE=MODS[m['loot']]['kod'], LEVEL=m['seviye'] + 1,
                         STATION=AST[aid]['ad'])] + self.m.money_msgs()
        elif self.world:                                # oyuncunun modülü yıkıldı: uyarı
            msgs.append(stm('msg_station_module_destroyed', STATION=AST[aid]['ad'], MAP=H.name(AST[aid]['harita']),
                            MODULE=MODS[m['loot']]['kod'], LEVEL=m['seviye'] + 1))
        if slot == HULL:
            msgs += self.destroy(aid, by)
        elif self.world:
            msgs += self.refresh_assets(aid)
        return msgs

    def destroy(self, aid, by=''):
        """İstasyon düştü: modüller (yok olmuş) envantere, asteroit boş."""
        a = self.ast(aid)
        rival = a.get('sahip') == 'rakip'
        msgs = []
        if rival:
            r = D['yikma_odulu']['merkez']
            r = dict(r, uridyum=AY.miktar('uridyum', r['uridyum']), kredi=AY.miktar('kredi', r['kredi']))     # panelin çarpanları
            self.p.gain(uridyum=r['uridyum'], kredi=r['kredi'], neden='battlestation_destroy_station')
            msgs += [stm('msg_station_hub_destruction_reward', AMOUNT=r['uridyum'], STATION=AST[aid]['ad']),
                     stm('msg_station_destroyed_by_clan', DESTROYER=self.clan_name(), LOSER=a.get('rakip', ''), STATION=AST[aid]['ad'],
                         MAP=H.name(AST[aid]['harita']))] + self.m.money_msgs()
        else:
            for y in a['yuvalar'].values():
                m = self.module(y['iid'])
                if m:
                    m['can'], m['kalkan'] = 0, 0
            ist = self.st['istatistik']
            ist['yikilan'] = ist.get('yikilan', 0) + 1
            ist['en_uzun_sn'] = max(ist.get('en_uzun_sn', 0), int(time.time() - a.get('kurulus', time.time())))
            msgs.append(stm('msg_station_destroyed', LOSER=self.clan_name(), STATION=AST[aid]['ad'], MAP=H.name(AST[aid]['harita'])))
        self.note(aid, 'DESTROYED', opponentClanName=by)
        self.log('   CBS: %s istasyonu yıkıldı (%s)' % (AST[aid]['ad'], by or 'oyuncu'))
        with self.p.lock:
            self.st['asteroitler'][str(aid)] = {'durum': 'bos', 'yuvalar': {}, 'rakip_tur': a.get('rakip_tur', 0) + (1 if rival else 0)}
            self.p.dirty = True
        self.ast(aid)
        for i in [i for i, k in self.raiders.items() if k == aid]:
            self.raiders.pop(i, None)
        msgs += self.starmap_msgs()
        if self.world:
            msgs += self.refresh_assets(aid)
        if self.near == aid and not rival:
            msgs += [self.building_ui(aid), self.available_msg()]
        return msgs

    # ------------------------------------------------------------ CBS-3: uzaylı baskınları
    def raid_tick(self, now):
        w = self.world
        msgs = []
        for aid in BY_MAP.get(int(w.map_id), []):
            a = self.ast(aid)
            if a['durum'] != 'kurulu' or a.get('sahip') == 'rakip':
                continue
            open_ = not a['deflector']['acik']
            if open_ and prime_time(now) and now >= self.next_raid.get(aid, 0):
                self.next_raid[aid] = now + D['baskin']['ara_dk'] * 60
                msgs += self.spawn_raid(aid)
            msgs += self.raid_fight(aid, a, now)
        return msgs

    def spawn_raid(self, aid):
        w = self.world
        cls = H.map_class(AST[aid]['harita'])
        kinds = D['baskin']['turler'].get(cls) or ['81']
        x, y = position(aid)
        n = random.randint(*D['baskin']['adet'])
        hp_each, dmg_each = self.raid_power(aid, n, time.time())
        prep = lambda nn: PO.scale_npc(nn, hp=max(1.0, hp_each / max(1, nn.d['hp'] + nn.d['kalkan'])),     # oyuncuya türün hasarı
                                       extra={'istasyon_hasari': max(nn.d['hasar'], int(dmg_each))})
        for _ in range(n):
            a, r = random.uniform(0, 2 * math.pi), random.uniform(900, 1300)
            nx = min(max(int(x + math.cos(a) * r), 300), w.map_w - 300)
            ny = min(max(int(y + math.sin(a) * r), 300), w.map_h - 300)
            npc = w.spawn_npc_at(random.choice(kinds), nx, ny, prep=prep)
            npc.gate = True
            npc.next_think = time.time() + 10 ** 6         # hareketi baskın yönetir (vurulunca oyuncuyla savaşır)
            self.raiders[npc.id] = aid
            tx, ty = x + random.randint(-300, 300), y + random.randint(-200, 200)
            ms = npc.mover.go(tx, ty, max(150, npc.d.get('hiz', 300)), time.time())
            w.send([('MoveCommand', dict(userId=npc.id, x=int(tx), y=int(ty), timeToTarget=ms))])
        self.log('   CBS: %s uzaylı baskını (%d)' % (AST[aid]['ad'], n))
        return [KAPI.screen('Aliens are attacking your Battle Station at %s!' % AST[aid]['ad'], big=True)]

    def raid_power(self, aid, n, now):
        """Baskıncı başına can+kalkan ve atış hasarı istasyona göre (haritanın sıradan uzaylıları 1 milyonluk uyduları çizemiyordu;
        canlı test: baskın 10 sn'de bitti): silahlar baskını yardımsız ~sure_sn'de temizler, o sürede baskın modüllerin can+kalkanının
        ~hasar_orani'nı götürür. Oyuncu da vurursa daha erken biter."""
        B = D['baskin']
        boost = 1 + self.booster_pct(aid, 'hasar', now) / 100.0
        dps = total = 0.0
        for yv in self.ast(aid)['yuvalar'].values():
            m = self.module(yv['iid'])
            if not m or m['can'] <= 0:
                continue
            md = MODS[m['loot']]
            total += m['can'] + m['kalkan']
            if md.get('silah'):
                dps += level_value(md['hasar'], m['seviye']) * boost * md['isabet'] / md['aralik_sn']
        shots = B['sure_sn'] / dunya.SAVAS['npc_saldiri_aralik_sn']
        return dps * B['sure_sn'] / n, total * B['hasar_orani'] / shots / n

    def raid_fight(self, aid, a, now):
        w = self.world
        msgs = []
        x, y = position(aid)
        alive = [w.npcs[i] for i, k in list(self.raiders.items()) if k == aid and i in w.npcs and w.npcs[i].alive]
        for i in [i for i, k in list(self.raiders.items()) if k == aid and i not in w.npcs]:
            self.raiders.pop(i, None)
        # uzaylılar modülleri vurur (oyuncuyla savaşmayanlar)
        targets = [int(s) for s, yv in a['yuvalar'].items() if self.module(yv['iid']) and self.module(yv['iid'])['can'] > 0]
        for n in alive:
            if n.engaged or now < self.next_shot.get(n.id, 0):
                continue
            nx, ny = n.mover.pos(now)
            if math.hypot(nx - x, ny - y) > 700 and math.hypot(n.mover.x1 - x, n.mover.y1 - y) > 700:   # oyuncudan kopan: istasyona döner
                n.next_think = now + 10 ** 6
                tx, ty = x + random.randint(-300, 300), y + random.randint(-200, 200)
                ms = n.mover.go(tx, ty, max(150, n.d.get('hiz', 300)), now)
                w.send([('MoveCommand', dict(userId=n.id, x=int(tx), y=int(ty), timeToTarget=ms))])
                continue
            if math.hypot(nx - x, ny - y) > 700 or not targets:
                continue
            self.next_shot[n.id] = now + dunya.SAVAS['npc_saldiri_aralik_sn']
            sats = [s for s in targets if s > DEFLECTOR]
            slot = random.choice(sats) if sats else HULL
            dmg = int(n.d.get('istasyon_hasari', n.d['hasar']) * random.uniform(0.7, 1.0))
            w.send([('AttackLaserRunCommand', dict(attackerId=n.id, targetId=asset_id(aid, slot), laserColor=0,
                                                   isDiminishedBySkillShield=False, skilledLaser=False, visualType=0))])
            msgs += self.damage_module(aid, slot, dmg, n.d['ad'])
            if self.ast(aid)['durum'] != 'kurulu':
                return msgs
        # silah modülleri menzildeki baskıncılara ateş eder
        dmg_boost = 1 + self.booster_pct(aid, 'hasar', now) / 100.0
        for s, yv in a['yuvalar'].items():
            m = self.module(yv['iid'])
            md = MODS[m['loot']] if m else {}
            if not m or not md.get('silah') or m['can'] <= 0 or yv.get('kurulum_bitis', 0) > now:
                continue
            key = (aid, int(s))
            if now < self.next_shot.get(key, 0):
                continue
            sx, sy = satellite_pos(aid, int(s))
            near = [n for n in alive if n.alive and math.hypot(n.mover.pos(now)[0] - sx, n.mover.pos(now)[1] - sy) <= md['menzil']]
            if not near:
                continue
            self.next_shot[key] = now + md['aralik_sn']
            n = random.choice(near)
            w.send([('AttackLaserRunCommand', dict(attackerId=asset_id(aid, int(s)), targetId=n.id, laserColor=0,
                                                   isDiminishedBySkillShield=False, skilledLaser=False, visualType=0))])
            if random.random() < md['isabet']:
                w.hit_npc(n.id, int(level_value(md['hasar'], m['seviye']) * dmg_boost), 1, attacker=asset_id(aid, int(s)), engage=False)
        return msgs

    # ------------------------------------------------------------ CBS-4: sanal rakip klanlar
    def rival_tick(self, aid, a, now):
        """Boş asteroitte rakip klan (tohumlu): ilerler, önce bitirirse düşman istasyonu kurar."""
        if a['durum'] == 'kurma' or (a['durum'] == 'kurulu' and a.get('sahip') != 'rakip'):
            return []
        msgs = []
        if a['durum'] == 'bos':
            if 'rakip' not in a:
                rnd = random.Random('%s-%s' % (aid, a.get('rakip_tur', 0)))
                if rnd.random() < D['rakip']['olasilik']:
                    hours = rnd.uniform(*D['rakip']['sure_sa'])
                    a.update(rakip=rnd.choice(D['rakip']['klanlar']), rakip_ilerleme=0.0, rakip_hiz=1.0 / (hours * 3600),
                             rakip_firma=rnd.choice([f for f in (1, 2, 3) if f != self.faction()] or [1]), rakip_son=now)
                else:
                    a['rakip'] = None
                self.p.dirty = True
            if a.get('rakip'):
                slow = 0.5 if self.own_progress(aid, now) > 0 else 1.0          # oyuncu da kuruyorsa rakip yavaşlar
                a['rakip_ilerleme'] = min(1.0, a.get('rakip_ilerleme', 0) + (now - a.get('rakip_son', now)) * a['rakip_hiz'] * slow)
                a['rakip_son'] = now
                if a['rakip_ilerleme'] >= 1.0 and self.own_progress(aid, now) < 1.0:
                    msgs += self.rival_build(aid, a, now)
        elif a.get('sahip') == 'rakip':
            df = a.setdefault('deflector', {})
            df['acik'] = not prime_time(now) if D['rakip'].get('deflector_prime_disinda') else False
            msgs += self.rival_repair(aid, a, now)
        return msgs

    def rival_repair(self, aid, a, now):
        """Saldırı kesilince (pasif_onarim.gecikme_sn) rakibin canlı modülleri onarılır, kalkanları dolar; haritadaysa 5 sn'de bir
        can çubukları."""
        dt = min(5.0, max(0.0, now - a.get('onarim_son', now)))
        a['onarim_son'] = now
        po = D['pasif_onarim']
        if not dt or now - a.get('saldiri', 0) < po['gecikme_sn']:
            return []
        changed = []
        for s, y in a['yuvalar'].items():
            mx = y.get('azami') or level_value(MODS[y['loot']]['can'], y['seviye'])
            ms = int(mx * D['kalkan_orani'])
            if y['can'] <= 0 or (y['can'] >= mx and y['kalkan'] >= ms):
                continue
            y['can'] = min(mx, y['can'] + po['can_sn'] * dt)
            y['kalkan'] = min(ms, y['kalkan'] + ms * 0.02 * dt)
            changed.append(int(s))
        if not changed:
            return []
        self.p.dirty = True
        w = self.world
        if not w or int(w.map_id) != int(AST[aid]['harita']) or now < a.get('onarim_bildirim', 0):
            return []
        a['onarim_bildirim'] = now + 5
        return [c for c in (self.info_cmd(aid, s) for s in changed if s != DEFLECTOR) if c]

    def rival_build(self, aid, a, now):
        """Rakip istasyonu: merkez (Hull, Deflector) ve 8 uydu, seviye 0, oyuncunun modüllerinden bağımsız."""
        free = [y['iid'] for y in a['yuvalar'].values() if 'iid' in y]       # oyuncunun kurulmamış modülleri
        rnd = random.Random('%s-b' % aid)
        sats = ['module_ltm-lr', 'module_ltm-mr', 'module_ltm-hr', 'module_ram-la', 'module_ram-ma', 'module_repm-1', 'module_honm-1',
                'module_xpm-1']
        slots = {str(HULL): 'module_hulm-1', str(DEFLECTOR): 'module_defm-1'}
        for s in range(2, SLOTS):
            slots[str(s)] = sats[(s - 2) % len(sats)] if s < 4 else rnd.choice(sats[:5])
        yv = {}
        for s, loot in slots.items():
            hp = int(level_value(MODS[loot]['can'], 0) * D['rakip']['can_carpani'])      # tek oyunculu: tek gemi yıkabilsin
            yv[s] = dict(loot=loot, seviye=0, can=hp, kalkan=int(hp * D['kalkan_orani']), azami=hp)
        with self.p.lock:
            a.update(durum='kurulu', sahip='rakip', yuvalar=yv, kurulus=now, deflector={'acik': True})
            self.p.dirty = True
        self.log('   CBS: rakip %s, %s istasyonunu kurdu (oyuncunun %d modülü envantere)' % (a['rakip'], AST[aid]['ad'], len(free)))
        msgs = [stm('msg_station_built', CLAN=a['rakip'], STATION=AST[aid]['ad'], MAP=H.name(AST[aid]['harita']))] + self.starmap_msgs()
        if self.world and int(self.world.map_id) == int(AST[aid]['harita']):
            msgs += self.refresh_assets(aid)
        return msgs

    def rival_attackable(self, aid):
        a = self.ast(aid)
        return a.get('sahip') == 'rakip' and a['durum'] == 'kurulu' and not (a.get('deflector') or {}).get('acik')

    def hit_asset(self, asset, dmg):
        """Oyuncunun rakip istasyonuna vuruşu (varlık kimliği) -> mesajlar."""
        aid, slot = self.asset_slot(asset)
        if aid is None:
            return []
        return self.asset_attackable(asset) or self.asset_hit(asset, dmg)

    # ------------------------------------------------------------ dünyanın asset_targets arayüzü (dunya.select/laser_start/asset_laser)
    @staticmethod
    def asset_slot(uid):
        uid = int(uid or 0)
        aid = (uid - ASSET_BASE) // 100
        slot = uid - ASSET_BASE - aid * 100
        return (aid, slot) if aid in AST and 0 <= slot < SLOTS and slot != DEFLECTOR else (None, None)

    def asset_pos(self, uid):
        """Bu haritadaki rakip istasyonun canlı modülü (merkez = Hull yuvası) -> konum ya da None."""
        aid, slot = self.asset_slot(uid)
        w = self.world
        if aid is None or not w or int(w.map_id) != int(AST[aid]['harita']):
            return None
        a = self.ast(aid)
        y = a['yuvalar'].get(str(slot)) if a.get('sahip') == 'rakip' and a['durum'] == 'kurulu' else None
        if not y or y['can'] <= 0:
            return None
        return position(aid) if slot == HULL else satellite_pos(aid, slot)

    def asset_select(self, uid):
        aid, slot = self.asset_slot(uid)
        y = self.ast(aid)['yuvalar'][str(slot)]
        mh = y.get('azami') or level_value(MODS[y['loot']]['can'], y['seviye'])
        return [('ShipSelectionCommand', dict(userId=int(uid), shipType=0, shield=int(y['kalkan']), shieldMax=int(mh * D['kalkan_orani']),
                                              hitpoints=int(y['can']), hitpointsMax=int(mh), nanoHull=0, maxNanoHull=0, shieldSkill=False)),
                self.info_cmd(aid, slot, y)]

    def asset_attackable(self, uid):
        """[] vurulabilir; deflector açıksa istemcinin uyarısı."""
        aid, slot = self.asset_slot(uid)
        if aid is not None and self.rival_attackable(aid):
            return []
        return [legacy('0|A|STM|msg_station_not_atackable')]

    def asset_hit(self, uid, dmg):
        aid, slot = self.asset_slot(uid)
        a = self.ast(aid)
        a['saldiri'] = time.time()
        msgs = self.damage_module(aid, slot, dmg, self.clan_name())
        b = self.ast(aid)
        y = b['yuvalar'].get(str(slot)) if b.get('sahip') == 'rakip' else None
        if y:
            msgs.append(('AttackHitAssetCommand', dict(assetId=int(uid), hitpointsNow=int(y['can']),
                                                       hitpointsMax=int(y.get('azami') or level_value(MODS[y['loot']]['can'], y['seviye'])))))
        return msgs

    def rival_fire(self, now):
        """Rakip istasyonun silah uyduları vurulabilirken (deflector kapalı) menzildeki oyuncuya ateş eder; hasar tek oyunculu
        çarpanla (rakip.hasar_carpani). Ölüm ekranında neden BATTLESTATION."""
        w = self.world
        if not w or w.hero_dead or getattr(w, 'jumping', False):
            return []
        hx, hy = w.hero_pos(now)
        for aid in BY_MAP.get(int(w.map_id), []):
            if not self.rival_attackable(aid):
                continue
            a = self.ast(aid)
            for s, y in list(a['yuvalar'].items()):
                md = MODS[y['loot']]
                if not md.get('silah') or y['can'] <= 0 or w.hero_dead:
                    continue
                sx, sy = satellite_pos(aid, int(s))
                key = ('rakip', aid, int(s))
                if math.hypot(sx - hx, sy - hy) > md['menzil'] or now < self.next_shot.get(key, 0):
                    continue
                self.next_shot[key] = now + md['aralik_sn']
                uid = asset_id(aid, int(s))
                w.send([('AttackLaserRunCommand', dict(attackerId=uid, targetId=w.hid, laserColor=0, isDiminishedBySkillShield=False,
                                                       skilledLaser=False, visualType=0))])
                if random.random() < md['isabet']:
                    dmg = int(level_value(md['hasar'], y['seviye']) * D['rakip']['hasar_carpani'])
                    who = types.SimpleNamespace(id=uid, alive=False, d={'ad': '%s [%s]' % (md['kod'], a.get('rakip', ''))})
                    w.send(w.hurt_hero(dmg, killer=who, cause=DESTRUCTION_BATTLESTATION, now=now))
                else:
                    w.send([('AttackMissedCommand', dict(attackType=dunya.attack_type(1), targetUserId=w.hid, skillColorId=0))])
        return []

    # ------------------------------------------------------------ klan sekmesi ve günlük
    def note(self, aid, kind, **values):
        a = AST[aid]
        e = dict(type=kind, date=stamp(), stationId=aid, stationName=a['ad'], mapName=H.name(a['harita']),
                 userName=values.pop('userName', ''), opponentClanName=values.pop('opponentClanName', ''),
                 buildSeconds=int(values.pop('buildSeconds', 0)), values=json.dumps(values) if values else '{}')
        with self.p.lock:
            self.st['gunluk'].insert(0, e)
            del self.st['gunluk'][200:]
            self.p.dirty = True

    def clan_info(self):
        st = self.st
        rows = []
        for aid_s, a in sorted(st['asteroitler'].items(), key=lambda kv: int(kv[0])):
            if a.get('durum') not in ('kurulu', 'kurma') or a.get('sahip') == 'rakip':
                continue
            aid = int(aid_s)
            df = a.get('deflector') or {}
            has_def = any(int(s) == DEFLECTOR for s in a['yuvalar'])
            rows.append(mod('BattleStationOverviewInfoCommand', stationName=AST[aid]['ad'], xpBonus=float(self.booster_pct(aid, 'ep')),
                            timerCounter=max(0, int(a.get('kurma_bitis', 0) - time.time())) if a['durum'] == 'kurma' else 0,
                            deflectorDownTime=max(0, int(df.get('kapali_bitis', 0) - time.time())),
                            damageBonus=float(self.booster_pct(aid, 'hasar')), defStatus=bool(df.get('acik')),
                            hasDeflectorModul=has_def, deflectorIsActive=bool(df.get('acik')), deflectorTime=int(df.get('sn', 0)),
                            allModuleCount=len(a['yuvalar']), mapName=H.name(AST[aid]['harita']), buildCompleted=a['durum'] == 'kurulu',
                            maxAmountOfModule=SLOTS, honourBonus=float(self.booster_pct(aid, 'onur')), stationId=aid))
        ist = st['istatistik']
        longest = max(ist.get('en_uzun_sn', 0), max([int(time.time() - a.get('kurulus', time.time())) for a in st['asteroitler'].values()
                                                     if a.get('durum') == 'kurulu' and a.get('sahip') != 'rakip'] or [0]))
        return ('ClanBattleStationInfoCommand', dict(battleStationOverviewInfoCommands=rows,
                                                     stationOwnedLongestTime=str(int(longest)),     # saniye (istemci biçimler)
                                                     maxStationAtOnce=int(ist.get('en_cok', 0)), destroyedStations=int(ist.get('yikilan', 0)),
                                                     stations=len(rows), allStations=int(ist.get('tum', 0))))

    USER_KINDS = ('BUILD_START', 'DEFLECTOR_ON', 'EMERGENCY_REPAIR', 'MODULE_REPLACED', 'MODULE_REMOVED')

    def history_row(self, e):
        """Günlük satırı istemciye: values'ın her alanı metin (istemci GetLogMessage string'e çevirir: sayı InvalidCastException ile
        listeyi keser - canlı test), seviye 1'den; oyuncunun yaptığı işlerde ad (metinde %USERNAME%)."""
        e = dict(e)
        try:
            v = json.loads(e.get('values') or '{}')
        except ValueError:
            v = {}
        e['values'] = json.dumps({k: str(int(x) + 1) if k.endswith('Level') and isinstance(x, (int, float)) else str(x)
                                  for k, x in v.items()})
        if e['type'] in self.USER_KINDS and not e.get('userName'):
            e['userName'] = self.p.d['pilot'].get('userName', '')
        return mod('BattleStationHistoryInfoCommand', **e)

    def history(self, start):
        g = self.st['gunluk']
        rows = [self.history_row(e) for e in g[start:start + 20]]
        return ('BattleStationHistoryListCommand', {'commandList': rows, 'startIndex': start, 'total': len(g)})

    # ------------------------------------------------------------ GM konsolu
    def gm(self, rows, d):
        """battleStation: buildTime (kurmayı / kurulumları bitir), modules (bir modül seti), accept (yanındaki asteroidi kur),
        deflector (aç/kapa), raid (baskın), rival (rakip istasyonu kur)."""
        what = str(d.get('option') or d.get('name') or (rows[0] if rows else '')).strip().lower()
        msgs = []
        if 'module' in what:
            for loot in MODS:
                n = 8 if MODS[loot]['en_cok'] > 1 else 1
                self.p.add_resource(loot, n)
            self.st
            msgs.append(KAPI.screen('GM: modül seti envantere'))
        aid = self.near
        if aid and ('build' in what or 'accept' in what):
            a = self.ast(aid)
            for y in a['yuvalar'].values():
                y['kurulum_bitis'] = 0
            if a['durum'] == 'kurma' or 'accept' in what:
                a['kurma_bitis'] = 0
                if a['durum'] == 'bos':
                    a.update(durum='kurma', kurma_sn=60)
            msgs.append(KAPI.screen('GM: kurulum bitti'))
        if aid and 'deflector' in what:
            df = self.ast(aid)['deflector']
            df['acik'] = not df.get('acik')
            df['kapali_bitis'] = 0 if df['acik'] else time.time() + 3600
            df['sn'] = max(df.get('sn', 0), 3600) if df['acik'] else df.get('sn', 0)
            msgs += [self.status_msg(aid), self.management_ui(aid)]
        if aid and 'raid' in what:
            msgs += self.spawn_raid(aid)
        if aid and 'rival' in what:
            a = self.ast(aid)
            if a['durum'] in ('kurulu', 'kurma') and a.get('sahip') != 'rakip':
                msgs.append(KAPI.screen('GM: burada kendi istasyonun var'))
            else:
                a.update(rakip=D['rakip']['klanlar'][0], rakip_ilerleme=1.0, rakip_firma=1 if self.faction() != 1 else 2)
                msgs += self.rival_build(aid, a, time.time())
        self.p.dirty = True
        return msgs or [KAPI.screen('GM battleStation: modules | build | accept | deflector | raid | rival')]
