"""P.E.T.-10: satın alma, hangar (donanım, yuva açma, ad), uzayda eşlik, dişliler, yakıt, seviye, hasar ve tamir.

Kayıttaki hesapta P.E.T. yoktu (PetInitializationCommand hasPet false). Biçimler başka oyuncuların P.E.T.'lerinden (kayıttaki
PetActivationCommand, PetStatusCommand) ve istemcinin kodundan (UIPetSystem, PetRequest/PetGearType enum'ları, Pet.Initialize
yuva adları, game.xml P.E.T. gemi türleri):
  giriş     PetInitializationCommand {hasPet, hasFuel, petIsAlive}: P.E.T. penceresinin düğmeleri
  başlat    PetRequest LAUNCH (pencere) / TOGGLE_ACTIVATION (kısayol) -> PetHeroActivationCommand + PetStatusCommand +
            dişli başına PetGearAddCommand + PetGearSelectCommand (+ bulucu dişlilerin hedef listesi)
  durdur    PetRequest DEACTIVATE -> PetDeactivationCommand
  dişli     PetGearActivationRequest {gearTypeToActivate, optParam} -> PetGearSelectCommand
  hareket   MoveCommand (P.E.T. kimliğiyle): gemiyi izler; toplayıcı dişlilerle kutuya/cevhere gider
  savaş     koruma modunda gemi hedefine (ya da gemiye saldıran NPC'ye) seçili cephaneyle ateş eder
  hasar     NPC atışları bazen P.E.T.'e gider; ölünce ShipDestroyedCommand + PetIsDestroyedCommand + tamir düğmesi
            (PetUIRepairButtonCommand); PetRequest REPAIR_DESTROYED_PET -> PetRepairCompleteCommand
  yakıt     etkinken dakika başına harcar (PetFuelUpdateCommand); biterse PetOutOfFuelCommand; HOTKEY_BUY_FUEL 1.000 birim
  seviye    oyuncunun kazandığı EP'nin %5'i: PetExperiencePointsUpdateCommand, PetLevelUpdateCommand
  HEAT      etkinken ısınır (PetHeatUpdateCommand {heatState 0 ısınıyor/1 sabit/2 soğuyor, heatLevel, petHeatAmount(Max)}; istemci:
            UIPetSystem.HeatUpdate); seviye bonusları P.E.T. uzaydayken gemiye (profil.mods <- pet_mods). Durunca seviyenin soğuma
            gecikmesi başlar, bitince soğur; bir alt seviyeye inince o seviyenin gecikmesi. 4. seviyeden HEAT yuvaları etkin.
  G-HR1     Heat Release dişlisi: 4 sn P.E.T. canı harcayıp HEAT'i düşürür (gecikmesiz), çevresine hasar (VisualModifier 107)
Hangar: HangarShipsCommand.petView (rootId dolu = P.E.T. var), HangarShipEquipmentCommand.petConfigs (config başına lasers,
  generators, gears, protocols, heat, visual); HangarShipUnlockSlotRequest {slotset} yuva açar ("heat" dahil);
  HangarShipRenamePetRequest ad değiştirir. Tasarım (pet_designs_*) "visual" yuvasında: uzaydaki görünüm (game.xml türü).
Mağazada G-HP1 (pet_upgrade-g-hp1): P.E.T. seviyesi kadar +10.000 can.
Değerler data/esyalar.json "pet" (wiki, kayıt ve uyarlamalar; kaynak notu orada).
"""
import json, math, os, random, time
import rutbe as RT
import ayar as AY

HERE = os.path.dirname(os.path.abspath(__file__))
ESYA = json.load(open(os.path.join(HERE, 'data', 'esyalar.json'), encoding='utf8'))
SAVAS = json.load(open(os.path.join(HERE, 'data', 'npc.json'), encoding='utf8'))['savas']
PET = ESYA['pet']
GEARS = PET['disliler']
PROTOCOLS = PET['protokoller']
HEAT = PET['isi']
HEAT_ROWS = HEAT['seviyeler']
HEAT_MAX = HEAT_ROWS[-1]['esik']
HEATING, STABLE, COOLING = 0, 1, 2       # PetHeatUpdateCommand.heatState (istemci: " +" beyaz, " =" sarı, " --" mavi)
VM_HEAT_RELEASE = 107                    # VisualModifierCommand.modifier (istemcinin VisualModifier enum'u)
HULL = PET['can_yukseltme']['loot']
DESIGNS = PET['tasarimlar']

# istemcinin PetGearType enum'u
PASSIVE, GUARD, AUTO_LOOT, AUTO_RESOURCE, ENEMY_LOCATOR, RESOURCE_LOCATOR = 1, 2, 4, 5, 6, 7
TRADE_POD, REPAIR_PET, KAMIKAZE, COMBO_REPAIR, COMBO_GUARD = 8, 9, 10, 11, 12
HEAT_RELEASE = 20
WORKING = {PASSIVE, GUARD, AUTO_LOOT, AUTO_RESOURCE, ENEMY_LOCATOR, RESOURCE_LOCATOR, TRADE_POD, REPAIR_PET, KAMIKAZE, COMBO_REPAIR,
           COMBO_GUARD, HEAT_RELEASE}
FIGHTING = {GUARD, KAMIKAZE, COMBO_GUARD}
# istemcinin PetRequest.PetRequestType enum'u
LAUNCH, DEACTIVATE, TOGGLE, HOTKEY_GUARD, REPAIR_DESTROYED, HOTKEY_REPAIR_SHIP, HOTKEY_BUY_FUEL = range(7)
DESTROYED_NONE, DESTROYED_KAMIKAZE = 0, 1
# hangar yuvaları (istemci: Pet.Initialize, HangarAuxiliary.ReturnPetMaxSlotCount) -> takılabilen eşyalar
SLOTS = {'lasers': 'equipment_weapon_laser_', 'generators': 'equipment_generator_shield_', 'gears': 'equipment_petgear_',
         'protocols': 'equipment_aiprotocol_', 'visual': 'pet_designs_'}
ALL_SLOTS = tuple(SLOTS) + ('heat',)     # heat: lazer ya da kalkan jeneratörü (taşıma isteğinin slotSet'i "heat")
NOVA_KEYS = {'can': 'pet_can', 'menzil': 'pet_menzil', 'isi': 'pet_isi', 'yakit': 'pet_yakit'}     # N.O.V.A. yetenekleri (nova.py)
UNIQUE = ('gears', 'protocols')          # aynı dişli/protokol iki kez takılmaz


def mod(name, **f):
    f['_'] = name
    return f


from eski_protokol import legacy  # noqa: E402,F401  (eski metin protokolü: eski_protokol.py)


def gear_type(t):
    return mod('PetGearTypeModule', typeValue=t)


def at_level(info, lv):
    """Dişli/protokol değerleri bir seviyede: listeler (seviye 1-3) o seviyenin değerine iner."""
    return {k: (v[min(max(lv, 1), len(v)) - 1] if isinstance(v, list) else v) for k, v in info.items()}


def has_levels(loot):
    """Mağazada seviyesi seçilen eşya (P.E.T. dişlisi ya da protokolü)."""
    return loot in GEARS or loot in PROTOCOLS


def level_prices(loot):
    """Seviye 1-3 uridyum fiyatları (wiki) ya da None."""
    info = GEARS.get(loot) or PROTOCOLS.get(loot)
    return info.get('fiyat') if info else None


def level_need(lv):
    """Dişli/protokol seviyesi için gereken P.E.T. seviyesi (wiki: 2. seviye 4, 3. seviye 8)."""
    need = PET['esya_seviye_sarti']
    return need[min(max(lv, 1), len(need)) - 1]


def slot_for(loot):
    """Eşyanın P.E.T.'te takılabileceği yuva (lazer, jeneratör, dişli, protokol, tasarım) ya da None."""
    return next((s for s, pre in SLOTS.items() if loot.startswith(pre)), None)


def heat_slot_ok(loot):
    """HEAT yuvasına yalnız lazer ya da kalkan jeneratörü."""
    return slot_for(loot) in ('lasers', 'generators')


def heat_level(points):
    return max(i for i, r in enumerate(HEAT_ROWS) if points >= r['esik'])


def heat_bonus(lv):
    """HEAT seviyesine kadar biriken bonuslar (wiki: seviyelerin bonusları toplanır)."""
    out = {}
    for r in HEAT_ROWS[1:lv + 1]:
        for k, v in r['bonus'].items():
            out[k] = out.get(k, 0) + v
    return out


def px_bonus(loot, lv):
    """LF-PX01 / SG3N-PX01: HEAT seviyesine göre hasar/kalkan bonusu."""
    return HEAT['px01'][lv - 1] if lv >= 1 and loot.endswith('-px01') else 0.0


def new_pet(profil):
    """Satın alınan P.E.T. (seviye 0, 10.000 yakıt, boş iki config)."""
    return {'kimlik': 7001, 'ad': PET['ad'], 'seviye': 0, 'ep': 0, 'can': PET['can'], 'kalkan': 0, 'yakit': PET['baslangic_yakit'],
            'yikik': False, 'disli': GUARD, 'yuva': dict(PET['baslangic_yuva']), 'isi': 0.0, 'can_yukseltme': 0,
            'konfig': {c: {s: [] for s in ALL_SLOTS} for c in ('1', '2')}}


class Pet:
    def __init__(self, profil, log=print):
        self.p, self.log = profil, log
        self.w = None                # uzaydaki dünya (dunya.World); harita değişince yenisi bağlanır
        self.send_raw = None         # dünya yokken (hangar, mağaza) oturuma gönderme
        self.active = False
        self.relaunch = False        # harita değişti/yeniden yüklendi: hazır olunca yeniden çıkar
        self.mover = None
        self.task = None             # ('box' | 'ore', hash): toplayıcı dişlinin hedefi
        self.shooting = None         # ateş edilen NPC
        self.next_shot = self.next_follow = self.next_second = self.next_locate = 0.0
        self.fuel_clock = 0.0        # harcanmamış yakıt (birim)
        self.tick_t = time.time()
        self.locate = {}             # bulucu dişli -> seçilen hedef (NPC gemi türü / cevher türü)
        self.trading = False         # kargo tüccarı seçili: rafineri penceresi uzayda açık
        self.trade_ready = 0.0
        self.fuel_sent, self.next_fuel_msg = 0, 0.0
        self.release_end = 0.0       # G-HR1 (Heat Release) çalışıyorsa bitişi
        self.release_ready = 0.0     # G-HR1 bekleme bitişi
        self.look = None             # istemcinin bildiği görünüm (gemi türü): yalnız değişince PetLevelUpdateCommand
        self.release_wait = False    # bekleme bitince "hazır" iletisi gidecek
        self.heat_sent, self.next_heat_msg = None, 0.0
        self.on_stats = None         # gemi değerleri yeniden (magaza.apply_stats): HEAT bonusu değişince
        profil.pet_mods = self.heat_mods

    # ------------------------------------------------------------ profil
    @property
    def d(self):
        return self.p.d.get('pet')

    @property
    def owned(self):
        return bool(self.d)

    @property
    def pid(self):
        return self.d['kimlik']

    @property
    def alive(self):
        return self.owned and not self.d['yikik']

    def row(self, lv=None):
        return PET['seviyeler'][self.d['seviye'] if lv is None else lv]

    def config(self, cid=None):
        c = self.d['konfig'].setdefault(str(cid or self.p.aktif_konfig), {})
        for s in ALL_SLOTS:
            c.setdefault(s, [])
        return c

    def loadout(self, cid=None):
        """Bir config'teki takılı eşyalar: yuva -> lootId listesi."""
        es = self.p.d['esyalar']
        return {s: [es[str(i)] for i in ids if str(i) in es] for s, ids in self.config(cid).items()}

    def leveled(self, slot):
        """Takılı dişliler/protokoller: [(lootId, seviye 1-3)]."""
        es = self.p.d['esyalar']
        return [(es[str(i)], self.p.item_level(i)) for i in self.config()[slot] if str(i) in es]

    def proto(self, key):
        """Takılı protokollerin değeri + N.O.V.A.'nın P.E.T. yetenekleri (nova.py: can, menzil, HEAT kazancı; yakıt azalır)."""
        v = sum(at_level(PROTOCOLS.get(l, {}), lv).get(key, 0) for l, lv in self.leveled('protocols'))
        nk = NOVA_KEYS.get(key)
        if nk and getattr(self.p, 'nova_mods', None):
            n = self.p.nova_mods().get(nk, 0)
            v += -n if key == 'yakit' else n
        return v

    def installed_gears(self):
        """Takılı dişliler: tür -> (lootId, seviyedeki değerler, seviye)."""
        out = {}
        for l, lv in self.leveled('gears'):
            g = GEARS.get(l)
            if g:
                out.setdefault(g['tur'], (l, at_level(g, lv), lv))
        return out

    def gear(self, t):
        return (self.installed_gears().get(t) or (None, {}, 0))[1]

    def hp_max(self):
        """Temel can + G-HP1 yükseltmeleri (her biri +10.000), AI-HP protokolüyle."""
        base = PET['can'] + PET['can_yukseltme']['adim'] * self.d.get('can_yukseltme', 0)
        return int(base * (1 + self.proto('can')))

    def heat_items(self, slot):
        """HEAT yuvasındaki lazerler/jeneratörler: yalnız HEAT seviyesi yuva_seviyesi'ne (4) ulaştıysa sayılır."""
        if self.heat_lv() < HEAT['yuva_seviyesi']:
            return []
        return [l for l in self.loadout()['heat'] if slot_for(l) == slot]

    def shields(self):
        kj, hl = ESYA['kalkan_jeneratorleri'], self.heat_lv()
        return [(kj[g]['kalkan'] * (1 + px_bonus(g, hl)), kj[g]['emme']) for g in self.loadout()['generators'] + self.heat_items('generators')
                if g in kj]

    def shield_max(self):
        return int(sum(k for k, e in self.shields()) * (1 + self.row()['kalkan'] + self.proto('kalkan')))

    def absorb(self):
        sh = self.shields()
        total = sum(k for k, e in sh)
        return sum(k * e for k, e in sh) / total if total else 0.8

    def lasers(self):
        return [l for l in self.loadout()['lasers'] + self.heat_items('lasers') if l in ESYA['lazerler']]

    def laser_damage(self):
        """Lazerlerin toplam hasarı (LF-PX01 HEAT bonusuyla)."""
        hl = self.heat_lv()
        return sum(ESYA['lazerler'][l]['hasar'] * (1 + px_bonus(l, hl)) for l in self.lasers())

    def speed(self):
        """P.E.T. gemiyi izler: gemiyle aynı hız (kayıt: başka oyuncunun P.E.T.'i 395)."""
        return self.p.d['gemi'].get('speed', 300)

    def design(self):
        """Takılı P.E.T. tasarımı (lootId) ya da None."""
        v = self.loadout()['visual']
        return v[0] if v else None

    def ship_type(self):
        """Görünüm: takılı tasarımın game.xml türü (tools/pet_tasarimlari.py), yoksa seviyeye göre (12 seviye 1-3 … 22 seviye 13-15)."""
        t = DESIGNS.get(self.design() or '')
        if t:
            return t
        lv = self.d['seviye']
        return [t for need, t in PET['gemi_turu'] if lv >= need][-1]

    def fuel_per_min(self):
        rate = self.row()['yakit_dk'] * (1 + self.proto('yakit'))
        g = self.d.get('disli')
        if g == COMBO_GUARD:
            rate *= 1 + self.gear(COMBO_GUARD).get('ek_yakit', 0)
        if g == COMBO_REPAIR:
            rate += self.gear(COMBO_REPAIR).get('ek_yakit_dk', 0)
        return rate * AY.carpan('pet_yakit')                 # panel: P.E.T. yakıtı

    def open_slots(self, slot):
        if slot == 'visual':
            return 1                         # istemci: HangarAuxiliary.ReturnPetMaxSlotCount "visual" sabit
        return max(self.d['yuva'].get(slot, 0), self.row()['yuva'].get(slot, 0))

    def slot_price(self, slot):
        """Bir sonraki yuvanın uridyum fiyatı; en çok yuvaya ulaşıldıysa 0. HEAT yuvalarının ilki de ücretli (wiki 20.000)."""
        n = self.open_slots(slot)
        prices = PET['yuva_fiyatlari'].get(slot, [])
        # panel: hizmet ücretleri (en az 1: 0 "en çok yuva" demek)
        return max(1, AY.fiyat('hizmet_fiyat', prices[n])) if n < min(PET['azami_yuva'].get(slot, 0), len(prices)) else 0

    def gear_list(self):
        """Pencerenin dişli listesi: (tür, seviye, kullanılabilir). Pasif ve koruma her zaman; diğerleri takılıysa."""
        out = [(PASSIVE, 1, True), (GUARD, 1, True)]
        for t, (l, g, lv) in sorted(self.installed_gears().items()):
            out.append((t, lv, t in WORKING and 'yok' not in g))
        return out

    # ------------------------------------------------------------ HEAT
    def cool(self, now=None):
        """Etkin değilken soğuma: seviyenin gecikmesi bitince sogume_sn hızında; bir alt seviyeye inince durur ve o seviyenin
        gecikmesi başlar (wiki). Oyunda olmadan geçen süre de sayılır (isi_t)."""
        d = self.d
        now = time.time() if now is None else now
        t = d.get('isi_t') or now
        if self.active:
            d['isi_t'] = now
            return
        rate, before = HEAT['sogume_sn'], d.get('isi', 0)
        while d.get('isi', 0) > 0 and t < now:
            start = d.get('isi_bekleme') or 0
            if start >= now:
                break
            t = max(t, start)
            lv = heat_level(d['isi'])
            target = max(0.0, HEAT_ROWS[lv]['esik'] - 1e-6) if lv else 0.0
            need = (d['isi'] - target) / rate
            if t + need <= now:
                t += need
                d['isi'] = target
                d['isi_bekleme'] = t + HEAT_ROWS[heat_level(target)]['bekleme_sn']
            else:
                d['isi'] -= (now - t) * rate
                t = now
        d['isi_t'] = now                 # kilitsiz: P.E.T. değerleri kilit altındayken de okunur (profil.lock yeniden girilmez)
        if d.get('isi', 0) != before:
            self.p.dirty = True

    def heat(self):
        if not self.owned:
            return 0.0
        self.cool()
        return self.d.get('isi', 0.0)

    def heat_lv(self):
        return heat_level(self.heat()) if self.owned else 0

    def heat_state(self, now=None):
        now = time.time() if now is None else now
        if self.active:
            return HEATING if self.d.get('isi', 0) < HEAT_MAX else STABLE
        return COOLING if self.d.get('isi', 0) > 0 and now >= (self.d.get('isi_bekleme') or 0) else STABLE

    def heat_mods(self):
        """Gemiye HEAT bonusları (profil.mods): yalnız P.E.T. uzaydayken."""
        if not (self.owned and self.active):
            return {}
        return heat_bonus(self.heat_lv())

    def heat_msg(self, now=None):
        h = self.heat()
        return ('PetHeatUpdateCommand', dict(heatState=self.heat_state(now), petHeatAmountMax=float(HEAT_MAX), heatLevel=heat_level(h),
                                             petHeatAmount=float(round(h, 2))))

    def add_heat(self, amount):
        """HEAT'i değiştirir (sınırlar içinde) -> seviye değişti mi."""
        d = self.d
        old = heat_level(d.get('isi', 0))
        with self.p.lock:
            d['isi'] = min(float(HEAT_MAX), max(0.0, d.get('isi', 0) + amount))
            d['isi_t'] = time.time()
            self.p.dirty = True
        return heat_level(d['isi']) != old

    def stop_heat(self, now):
        """P.E.T. uzaydan çekildi: bulunduğu seviyenin soğuma gecikmesi başlar."""
        with self.p.lock:
            self.d['isi_bekleme'] = now + HEAT_ROWS[heat_level(self.d.get('isi', 0))]['bekleme_sn']
            self.d['isi_t'] = now
            self.p.dirty = True

    def stats_msgs(self):
        """HEAT bonusu değişti: gemi değerleri (can, hasar …) yeniden."""
        return self.on_stats() if self.on_stats else []

    # ------------------------------------------------------------ G-HP1 (can yükseltmesi)
    def hull_price(self):
        """Bir sonraki can yükseltmesinin uridyum fiyatı ya da None (P.E.T. yok, seviyesi kadar yükseltilmiş, en çok 20)."""
        if not self.owned:
            return None
        n, prices = self.d.get('can_yukseltme', 0), PET['can_yukseltme']['fiyatlar']
        return prices[n] if n < min(self.d['seviye'], len(prices)) else None

    def upgrade_hull(self):
        step = PET['can_yukseltme']['adim']
        with self.p.lock:
            self.d['can_yukseltme'] = self.d.get('can_yukseltme', 0) + 1
            self.d['can'] = min(self.hp_max(), self.d['can'] + step)
            self.p.dirty = True
        self.log('   P.E.T. can yükseltmesi %d: azami can %d' % (self.d['can_yukseltme'], self.hp_max()))
        return [self.hp_msg(), self.status_msg()] if self.active else []

    # ------------------------------------------------------------ mesajlar
    def send(self, msgs):
        msgs = [m for m in msgs if m]
        if not msgs:
            return
        if self.w:
            self.w.send(msgs)
        elif self.send_raw:
            self.send_raw(msgs)

    def init_msg(self):
        return ('PetInitializationCommand', {'hasPet': self.owned, 'hasFuel': self.owned and self.d['yakit'] > 0,
                                             'petIsAlive': self.alive})

    def status_msg(self):
        d = self.d
        return ('PetStatusCommand', dict(
            petId=self.pid, petLevel=d['seviye'], petExperiencePoints=d['ep'], petExperiencePointsUntilNextLevel=self.next_xp(),
            petHitPoints=int(d['can']), petHitPointsMax=self.hp_max(), petShieldEnergyNow=int(d['kalkan']),
            petShieldEnergyMax=self.shield_max(), petCurrentFuel=int(d['yakit']), petMaxFuel=PET['azami_yakit'], petSpeed=self.speed(),
            petName=d['ad'], petLootId=''))

    def next_xp(self):
        lv = self.d['seviye']
        rows = PET['seviyeler']
        return rows[lv + 1]['ep'] if lv + 1 < len(rows) else rows[-1]['ep']

    def activation_msg(self, x, y):
        pl = self.p.d['pilot']
        self.look = self.ship_type()
        return ('PetHeroActivationCommand', dict(
            ownerId=self.p.user_id, petId=self.pid, shipType=self.ship_type(), expansionStage=1, petName=self.d['ad'],
            factionId=pl.get('factionId', 1), clanId=0, petLevel=self.d['seviye'], clanTag='', x=int(x), y=int(y), petSpeed=self.speed(),
            minimapStrategyModule=mod('MinimapStrategyModule', minimapStrategy=0)))

    def gear_msgs(self):
        msgs = [('PetGearAddCommand', dict(gearType=gear_type(t), level=lv, amount=0, enabled=ok)) for t, lv, ok in self.gear_list()]
        for t in (ENEMY_LOCATOR, RESOURCE_LOCATOR):
            if t in self.installed_gears():
                msgs.append(('PetLocatorGearInitializationCommand', dict(locatorType=gear_type(t), possibleTargetValues=self.targets(t))))
        return msgs + [self.select_msg()]

    def select_msg(self):
        t = self.d.get('disli', GUARD)
        opt = [self.locate[t]] if t in self.locate else []
        return ('PetGearSelectCommand', dict(gearType=gear_type(t), optionalParams=opt))

    def hp_msg(self):
        return ('PetHitpointsUpdateCommand', dict(hitpointsNow=int(self.d['can']), hitpointsMax=self.hp_max(),
                                                  useRepairGear=self.d.get('disli') == REPAIR_PET))

    def shield_msg(self):
        return ('PetShieldUpdateCommand', dict(petShieldNow=int(self.d['kalkan']), petShieldMax=self.shield_max()))

    def fuel_msg(self):
        return ('PetFuelUpdateCommand', dict(petFuelNow=int(self.d['yakit']), petFuelMax=PET['azami_yakit']))

    def repair_button(self):
        return ('PetUIRepairButtonCommand', dict(enabled=self.owned and self.d['yikik'], repairCosts=self.repair_cost()))

    def repair_cost(self):
        return AY.fiyat('hizmet_fiyat', self.row()['tamir_uridyum']) if self.owned else 0       # panel: hizmet ücretleri

    def login_msgs(self):
        """Harita yüklendikten sonra: yok edilmişse tamir düğmesi; harita değiştiyse etkin P.E.T. yeniden çıkar."""
        if not self.owned:
            return []
        msgs = [self.repair_button()] if self.d['yikik'] else []
        return msgs + [self.heat_msg()]                  # P.E.T. penceresinin HEAT göstergesi (etkin değilken de)

    # ------------------------------------------------------------ hangar
    def view(self):
        """HangarShipsCommand.petView (istemci rootId boş değilse P.E.T. panelini doldurur)."""
        base = dict(petHeatSlotPrice=0, maxGearSlots=0, petGearsSlotPrice=0, rootId='', petProtocolsSlotPrice=0, maxFuel=0, maxLaserSlots=0,
                    petRenamePrice=0, maxHeatSlots=0, expNextLevel=0, shieldGenerators=0, fuel=0, hitPoints=0, petGeneratorsSlotPrice=0,
                    petLasersSlotPrice=0, exp=0, maxHitPoints=0, damageDistribution=0, level=0, maxDamageDistribution=0, maxProtocolSlots=0,
                    lasers=0, maxGeneratorSlots=0, name='', maxLasers=0)
        if not self.owned:
            return dict(base, _='HangarShipPetView')       # alan adı 'name': mod() ile çakışır
        d, lo = self.d, self.loadout()
        base.update(rootId=PET['loot'], name=d['ad'], level=d['seviye'], exp=d['ep'], expNextLevel=self.next_xp(), hitPoints=int(d['can']),
                    maxHitPoints=self.hp_max(), fuel=int(d['yakit']), maxFuel=PET['azami_yakit'], lasers=len(lo['lasers']),
                    maxLasers=self.open_slots('lasers'), shieldGenerators=len(lo['generators']),
                    maxLaserSlots=self.open_slots('lasers'), maxGeneratorSlots=self.open_slots('generators'),
                    maxGearSlots=self.open_slots('gears'), maxProtocolSlots=self.open_slots('protocols'),
                    petLasersSlotPrice=self.slot_price('lasers'), petGeneratorsSlotPrice=self.slot_price('generators'),
                    petGearsSlotPrice=self.slot_price('gears'), petProtocolsSlotPrice=self.slot_price('protocols'),
                    maxHeatSlots=self.open_slots('heat'), petHeatSlotPrice=self.slot_price('heat'))
        return dict(base, _='HangarShipPetView')       # alan adı 'name': mod() ile çakışır

    def config_msgs(self, cur):
        """HangarShipEquipmentCommand.petConfigs: config başına takılı eşya kimlikleri."""
        if not self.owned:
            return []
        out = []
        for cid in ('1', '2'):
            c = self.config(cid)
            out.append(mod('HangarPetEquipmentMsg', setId=int(cid), active=int(cid) == int(cur), laser=list(c['lasers']),
                           generator=list(c['generators']), gear=list(c['gears']), protocol=list(c['protocols']), heat=list(c['heat']),
                           visual=list(c['visual'])))
        return out

    def unlock(self, f):
        """HangarShipUnlockSlotRequest {slotset}: bir yuva daha uridyumla (wiki fiyatı, yuva numarasına göre)."""
        slot = (f.get('slotset') or '').lower()
        reply = lambda res, err=None: ('HangarShipUnlockSlotCommand', dict(
            nextGearsSlotUridium=self.slot_price('gears') if self.owned else 0, nextLasersSlotUridium=self.slot_price('lasers') if self.owned else 0,
            errorMessage=err, nextGeneratorSlotUridium=self.slot_price('generators') if self.owned else 0,
            nextProtocolsSlotUridium=self.slot_price('protocols') if self.owned else 0,
            nextHeatSlotUridium=self.slot_price('heat') if self.owned else 0, resultId=res))
        if not self.owned or slot not in PET['yuva_fiyatlari']:
            self.log('   P.E.T. yuvası açılmadı: %r' % slot)
            return [reply(0)]
        price = self.slot_price(slot)
        u = self.p.d['pilot'].get('uridium', 0)
        if not price or u < price:
            self.log('   P.E.T. yuvası açılmadı: %s (fiyat %d, uridyum %d)' % (slot, price, u))
            return [reply(0)]
        with self.p.lock:
            self.p.d['pilot']['uridium'] = u - price
            self.d['yuva'][slot] = self.open_slots(slot) + 1
            self.p.dirty = True
        RT.money(self.p, 'uridyum', -price, 'buy_SPECIAL')
        self.log('   P.E.T. yuvası açıldı: %s %d (%d U)' % (slot, self.open_slots(slot), price))
        return [reply(1)]

    def rename(self, f):
        name = (f.get('name') or '').strip()[:20]
        ok = self.owned and len(name) >= 3
        if ok:
            with self.p.lock:
                self.d['ad'] = name
                self.p.dirty = True
            self.log('   P.E.T. adı: %s' % name)
        msgs = [('HangarShipRenamePetCommand', dict(errorMessage=None, resultId=1 if ok else 0, newName=name if ok else ''))]
        if ok and self.active:
            msgs.append(self.status_msg())
        return msgs

    # ------------------------------------------------------------ istekler
    def request(self, f):
        """PetRequest: başlat/durdur/kısayollar/tamir/yakıt."""
        kind = f.get('petRequestType')
        if not self.owned:
            return
        lock = self.w.lock if self.w else _NoLock()
        with lock:
            if kind == LAUNCH or (kind == TOGGLE and not self.active):
                self.launch()
            elif kind == DEACTIVATE or kind == TOGGLE:
                self.deactivate()
            elif kind == HOTKEY_GUARD:
                self.select(GUARD)
            elif kind == HOTKEY_REPAIR_SHIP:
                self.select(COMBO_REPAIR if COMBO_REPAIR in self.installed_gears() else REPAIR_PET)
            elif kind == REPAIR_DESTROYED:
                self.repair()
            elif kind == HOTKEY_BUY_FUEL:
                self.buy_fuel()
            else:
                self.log('   P.E.T. isteği bilinmiyor: %s' % kind)

    def gear_request(self, f):
        t = (f.get('gearTypeToActivate') or {}).get('typeValue')
        lock = self.w.lock if self.w else _NoLock()
        with lock:
            self.select(t, f.get('optParam') or 0)

    def launch(self):
        w = self.w
        if self.active or not w or w.hero_dead:
            return
        if self.d['yikik']:
            self.send([self.repair_button(), legacy('0|A|STM|msg_pet_is_dead')])
            return
        if self.d['yakit'] <= 0:
            self.send([legacy('0|A|STM|msg_pet_no_fuel_to_launch'), self.init_msg()])
            return
        now = time.time()
        hx, hy = w.hero_pos(now)
        a = random.uniform(0, 2 * math.pi)
        x, y = hx + math.cos(a) * PET['takip_mesafe'], hy + math.sin(a) * PET['takip_mesafe']
        from dunya import Mover
        self.mover = Mover(int(x), int(y))
        self.cool(now)                           # uzakta geçen sürenin soğuması; uzaydayken soğumaz
        self.release_end = 0.0
        self.active, self.task, self.shooting = True, None, None
        self.tick_t = self.next_second = now
        with self.p.lock:
            self.d['can'] = min(self.d['can'], self.hp_max())
            self.d['kalkan'] = min(self.d['kalkan'], self.shield_max())
            self.p.dirty = True
        if self.d.get('disli') not in {t for t, lv, ok in self.gear_list() if ok} or self.d.get('disli') in (TRADE_POD, HEAT_RELEASE):
            self.d['disli'] = GUARD
        self.trading = False
        self.fuel_sent = int(self.d['yakit'])
        self.heat_sent = int(self.d.get('isi', 0))
        self.send([self.activation_msg(x, y), self.status_msg()] + self.gear_msgs() + [self.heat_msg(now)] + self.stats_msgs())
        self.log('   P.E.T. çıktı: seviye %d, can %d/%d, kalkan %d, yakıt %d, %d lazer, dişli %d' % (
            self.d['seviye'], self.d['can'], self.hp_max(), self.d['kalkan'], self.d['yakit'], len(self.lasers()), self.d['disli']))

    def deactivate(self, notify=True, msg=None):
        if not self.active:
            return
        now = time.time()
        if self.release_end:
            self.end_release(now, notify=False)
        self.active, self.task, self.trading = False, None, False
        self.stop_heat(now)                      # soğuma gecikmesi başlar
        msgs = [('PetLaserAttackStopCommand', {'petId': self.pid})] if self.shooting else []
        self.shooting = None
        if notify:
            # istemci: PetDeactivationCommand birimi yalnız gizler; pencere P.E.T. birimi varken "etkin" görünür (UIPetSystem.RefPet).
            # Birim ShipRemoveCommand ile kalkar; ardından PetInitializationCommand pencereyi yeniler (başlat düğmesi; canlı test).
            msgs += [('PetDeactivationCommand', {'petId': self.pid}), ('ShipRemoveCommand', {'userId': self.pid}), self.init_msg()]
            if msg:
                msgs.append(legacy('0|A|STM|%s' % msg))
        self.send(msgs + [self.heat_msg(now)] + self.stats_msgs())       # HEAT bonusu gemiden kalkar
        self.log('   P.E.T. durdu%s' % (' (%s)' % msg if msg else ''))

    def select(self, t, opt=0):
        if not self.owned:
            return
        ok = {g for g, lv, usable in self.gear_list() if usable}
        if t not in ok:
            self.log('   P.E.T. dişlisi yok/kullanılamaz: %s' % t)
            self.send([self.select_msg()])
            return
        now = time.time()
        if t == TRADE_POD and now < self.trade_ready:
            self.log('   kargo tüccarı beklemede (%d sn)' % (self.trade_ready - now))
            self.send([self.select_msg()])
            return
        if t == HEAT_RELEASE:
            if self.release_end or not (self.active and self.w):
                self.send([self.select_msg()])   # zaten çalışıyor ya da P.E.T. uzayda değil
                return
            why = ('msg_pet_heat-release-gear_cooldown_not_ready' if now < self.release_ready else
                   'msg_pet_heat-release-gear_no_heat' if self.heat() <= 0 else None)
            if why:
                self.log('   Heat Release seçilemedi: %s' % why)
                self.send([self.select_msg(), legacy('0|A|STM|%s' % why)])
                return
        elif self.release_end:
            self.end_release(now)                # başka dişli seçildi: Heat Release erken biter
        old = self.d.get('disli')
        with self.p.lock:
            self.d['disli'] = t
            self.p.dirty = True
        if t in (ENEMY_LOCATOR, RESOURCE_LOCATOR) and opt:
            self.locate[t] = int(opt)
        self.task = None if t not in (AUTO_LOOT, AUTO_RESOURCE) else self.task
        msgs = [self.select_msg()]
        if self.shooting and t not in FIGHTING:
            msgs.append(('PetLaserAttackStopCommand', {'petId': self.pid}))
            self.shooting = None
        self.trading = t == TRADE_POD
        if self.trading:
            msgs.append(('PetTradeWindowShowCommand', {}))
        if t == REPAIR_PET or old == REPAIR_PET:
            msgs.append(self.hp_msg())
        if t == HEAT_RELEASE:
            self.release_end = now + self.gear(HEAT_RELEASE).get('sure_sn', 4)
            msgs.append(self.release_visual(True))
        self.send(msgs)
        self.log('   P.E.T. dişlisi: %s%s' % (t, ' hedef %s' % opt if opt else ''))

    def release_visual(self, on):
        return ('VisualModifierCommand', dict(userId=self.pid, modifier=VM_HEAT_RELEASE, attribute=0, additionalAttribute='', count=0,
                                              activated=on))

    def release_step(self, now):
        """Heat Release saniyesi: HEAT düşer (soğuma gecikmesi yok), P.E.T. canı harcanır, menzildeki uzaylılar hasar alır."""
        g, w, d = self.gear(HEAT_RELEASE), self.w, self.d
        if now >= self.release_end:
            return self.end_release(now, notify=False)                  # süre doldu (4 sn: 4 vuruş)
        changed = self.add_heat(-g.get('isi_sn', 0))
        with self.p.lock:
            d['can'] = max(1, d['can'] - g.get('can_sn', 0))           # dişli P.E.T.'i yok etmez (uyarlama)
            self.p.dirty = True
        px, py = self.pos(now)
        hit = [n for n in list(w.npcs.values()) if n.alive and math.hypot(n.mover.pos(now)[0] - px, n.mover.pos(now)[1] - py) <= g.get('menzil', 0)]
        for n in hit:
            w.hit_npc(n.id, int(g.get('hasar_sn', 0)), 1, attacker=self.pid)
        if hit:
            w.last_combat = now
        msgs = [self.hp_msg(), self.heat_msg(now)] + (self.stats_msgs() if changed else [])
        if d.get('isi', 0) <= 0 or d['can'] <= g.get('can_sn', 0):
            msgs += self.end_release(now, notify=False)                 # HEAT bitti ya da can yetmiyor
        return msgs

    def end_release(self, now, notify=True):
        """Heat Release bitti: görsel kapanır, bekleme başlar, P.E.T. korumaya döner."""
        self.release_end = 0.0
        self.release_ready = now + self.gear(HEAT_RELEASE).get('bekleme_sn', 60)
        self.release_wait = True
        with self.p.lock:
            self.d['disli'] = GUARD
            self.p.dirty = True
        # P.E.T. penceresinde dişli bekleme boyunca gri (Ö1; istemci yalnız pencere açıkken işler: PetGearActivationChangeCommand)
        msgs = [self.release_visual(False), self.select_msg(),
                ('PetGearActivationChangeCommand', dict(gearType=gear_type(HEAT_RELEASE), active=False))]
        if notify:
            self.send(msgs)
        return msgs

    def repair(self):
        """Yok edilmiş P.E.T.'i tamir: seviyeye göre uridyum (wiki: seviye 0-2 ücretsiz)."""
        if not self.d['yikik']:
            return
        cost = self.repair_cost()
        pl = self.p.d['pilot']
        if pl.get('uridium', 0) < cost:
            self.send([legacy('0|A|STM|not_enough_uridium'), self.repair_button()])
            return
        with self.p.lock:
            pl['uridium'] = pl.get('uridium', 0) - cost
            self.d.update(yikik=False, can=self.hp_max(), kalkan=self.shield_max())
            self.p.dirty = True
        RT.money(self.p, 'uridyum', -cost, 'repair_pet')
        msgs = [('PetRepairCompleteCommand', {}), self.init_msg(), self.repair_button()]
        if cost and self.w and self.w.money_msgs:
            msgs += self.w.money_msgs()
        self.send(msgs)
        self.log('   P.E.T. tamir edildi (%d U)' % cost)

    def buy_fuel(self, amount=None):
        """Kısayol: 1.000 birim yakıt (istemci metinleri log_msg_bought_fuel_hotkey*). P.E.T. etkin olmalı. amount: otomatik alım
        CPU'su (FB-X: 10.000; fiyat aynı oranda)."""
        f = dict(PET['yakit_satin'])
        if amount:
            f.update(kredi=f['kredi'] * amount // f['adet'], adet=amount)
        f['kredi'] = AY.fiyat('hizmet_fiyat', f['kredi'])     # panel: hizmet ücretleri
        pl = self.p.d['pilot']
        if not self.active:
            self.send([legacy('0|A|STM|log_msg_bought_fuel_hotkey_inactive')])
        elif self.d['yakit'] + f['adet'] > PET['azami_yakit']:
            self.send([legacy('0|A|STM|log_msg_bought_fuel_hotkey_full')])
        elif pl.get('credits', 0) < f['kredi']:
            self.send([legacy('0|A|STM|not_enough_credits')])
        else:
            with self.p.lock:
                pl['credits'] -= f['kredi']
                self.d['yakit'] += f['adet']
                self.p.dirty = True
            RT.money(self.p, 'kredi', -f['kredi'], 'buy_PETFUEL', qty=f['adet'])
            msgs = [self.fuel_msg(), legacy('0|A|STM|log_msg_bought_fuel_hotkey')]
            if self.w and self.w.money_msgs:
                msgs += self.w.money_msgs()
            self.send(msgs)
            self.log('   P.E.T. yakıtı alındı: +%d (%d kredi)' % (f['adet'], f['kredi']))

    # ------------------------------------------------------------ uzay
    def attach(self, world):
        """Yeni harita dünyası: etkin P.E.T. hazır demetinden sonra yeniden çıkar (gerçek oyunda portaldan birlikte geçer)."""
        was = self.active
        if was:
            self.stop_heat(time.time())          # geçişte soğumaz (gecikme yeniden çıkışa kadar sürer)
            self.release_end = 0.0
        self.w, self.active, self.task, self.shooting = world, False, None, None
        self.relaunch = self.relaunch or was

    def on_ready(self):
        """Harita yüklendi (ReadyRequest): bir önceki haritada etkinse yeniden çıkar."""
        if self.relaunch and self.w:
            self.relaunch = False
            with self.w.lock:
                self.launch()

    def reload(self):
        """Gemi yeniden yüklendi (tamir, gemi değişimi): istemci haritayı temizler; hazır olunca yeniden çıkar."""
        if self.active:
            self.stop_heat(time.time())
            self.release_end = 0.0
            self.active, self.task, self.shooting = False, None, None
            self.relaunch = True

    def pos(self, now):
        return self.mover.pos(now)

    def move(self, x, y, speed, now):
        ms = self.mover.go(x, y, speed, now)
        self.w.send([('MoveCommand', dict(userId=self.pid, x=int(x), y=int(y), timeToTarget=ms))])

    def tick(self, now):
        """Dünya döngüsünden (kilit altında): izleme, toplama, ateş, yakıt, onarım, bulucu."""
        if not self.active or not self.w:
            return
        w = self.w
        dt, self.tick_t = now - self.tick_t, now
        if w.hero_dead or w.jumping:
            return
        self.fuel_clock += self.fuel_per_min() * dt / 60.0
        if self.fuel_clock >= 1:
            used = int(self.fuel_clock)
            self.fuel_clock -= used
            with self.p.lock:
                self.d['yakit'] = max(0, self.d['yakit'] - used)
                self.p.dirty = True
            if self.d['yakit'] <= 0:
                self.send([self.fuel_msg(), ('PetOutOfFuelCommand', {}), self.init_msg()])
                self.deactivate(msg='msg_pet_out_of_fuel')
                return
        if now >= self.next_second:
            self.next_second = now + 1.0
            self.each_second(now)
        if not self.active:
            return
        g = self.d.get('disli')
        if g in (AUTO_LOOT, AUTO_RESOURCE) and self.collect_step(now, g):
            return
        if g in FIGHTING:
            if self.fight(now):
                return                   # hedefin yanında savaşıyor
        elif self.shooting:
            self.stop_shooting()
        self.follow(now)

    def each_second(self, now):
        w, d, msgs = self.w, self.d, []
        if self.release_end:
            msgs += self.release_step(now)
        else:                                    # HEAT: etkinken ısınır, savaşta daha hızlı; AI-AH protokolü artırır
            fighting = self.shooting or now - w.last_combat < HEAT['savas_sn']
            gain = (HEAT['kazanc_dk'] / 60.0 + (HEAT['savas_kazanc_sn'] if fighting else 0)) * (1 + self.proto('isi'))
            if self.add_heat(gain):
                self.log('   P.E.T. HEAT seviyesi %d (%d puan)' % (heat_level(d['isi']), d['isi']))
                msgs += [self.heat_msg(now)] + self.stats_msgs()
                self.heat_sent, self.next_heat_msg = int(d['isi']), now + 5
            elif int(d['isi']) != self.heat_sent and now >= self.next_heat_msg:
                self.heat_sent, self.next_heat_msg = int(d['isi']), now + 5      # gösterge en çok 5 sn'de bir
                msgs.append(self.heat_msg(now))
        if self.release_wait and now >= self.release_ready:
            self.release_wait = False
            msgs += [legacy('0|A|STM|msg_pet_heat-release-gear_cooldown_ready'),
                     ('PetGearActivationChangeCommand', dict(gearType=gear_type(HEAT_RELEASE), active=True))]
        if int(d['yakit']) != self.fuel_sent and now >= self.next_fuel_msg:
            self.fuel_sent, self.next_fuel_msg = int(d['yakit']), now + 10      # yakıt göstergesi en çok 10 sn'de bir
            msgs.append(self.fuel_msg())
        g = d.get('disli')
        if g == REPAIR_PET and d['can'] < self.hp_max():
            with self.p.lock:
                d['can'] = min(self.hp_max(), d['can'] + self.gear(REPAIR_PET).get('can_sn', 0))
                self.p.dirty = True
            msgs.append(self.hp_msg())
        if d['kalkan'] < self.shield_max() and now - w.last_combat >= ESYA['savas_disi_sn']:
            with self.p.lock:
                d['kalkan'] = min(self.shield_max(), d['kalkan'] + max(1, self.shield_max() * ESYA['kalkan_yenilenme_sn']))
                self.p.dirty = True
            msgs.append(self.shield_msg())
        if g == COMBO_REPAIR:
            ship = self.p.d['gemi']
            if ship.get('hitPoints', 0) < ship.get('hitMax', 0) and now - w.last_hurt >= ESYA['savas_disi_sn']:
                hp0 = ship['hitPoints']
                self.p.set_hull(hp=hp0 + self.gear(COMBO_REPAIR).get('can_sn', 0))
                msgs.append(('HitpointInfoCommand', dict(hitpoints=int(ship['hitPoints']), hitpointsMax=ship.get('hitMax', 0),
                                                         nanoHull=ship.get('nanoHull', 0), nanoHullMax=ship.get('maxNanoHull', 0))))
                msgs += w.heal_msgs(hp0)                                  # "+can" sayısı (Ö1)
        if g in (ENEMY_LOCATOR, RESOURCE_LOCATOR) and g in self.locate:
            spot = self.locate_target(g, self.locate[g])
            if spot:
                msgs.append(('PetGearLocatorUpdate', dict(x=int(spot[0]), y=int(spot[1]))))
        self.send(msgs)

    def follow(self, now):
        """Gemiyi izle: geminin gittiği yerin takip_mesafe kadar gerisine (geride kaldıysa daha hızlı)."""
        w = self.w
        if now < self.next_follow:
            return
        hx, hy = w.hero.x1, w.hero.y1
        px, py = self.pos(now)
        a = math.atan2(py - hy, px - hx)
        tx, ty = hx + math.cos(a) * PET['takip_mesafe'], hy + math.sin(a) * PET['takip_mesafe']
        if math.hypot(tx - self.mover.x1, ty - self.mover.y1) < 80 and math.hypot(tx - px, ty - py) < 400:
            return
        hpx, hpy = w.hero_pos(now)
        far = math.hypot(px - hpx, py - hpy) > 700
        self.move(tx, ty, self.speed() * (1.5 if far else 1.0), now)
        self.next_follow = now + 0.5

    def range_bonus(self):
        return 1 + self.proto('menzil')

    def collect_step(self, now, g):
        """Otomatik toplayıcı: menzildeki en yakın kutuya/cevhere git, varınca topla. Çalıştıysa True."""
        w = self.w
        if self.task:
            kind, h = self.task
            target = (w.boxes if kind == 'box' else w.ores).get(h)
            if not target or (kind == 'ore' and target.get('busy')):
                self.task = None
                return False
            if now >= self.mover.t1:
                self.task = None
                if kind == 'box':
                    w.take_box(h, by_pet=True)
                else:
                    target['busy'] = True
                    w.later(ORE_DELAY, lambda: w.finish_harvest(h))
            return True
        rng = self.gear(g).get('menzil', 0) * self.range_bonus()
        hx, hy = w.hero_pos(now)
        if g == AUTO_LOOT:
            full = self.p.cargo_free() < 1
            cands = [(h, b) for h, b in w.boxes.items() if not (full and b['tip'] in ('FROM_SHIP', 'CANDY_CARGO')) and not b.get('anahtarli')]
        else:
            if self.p.cargo_free() < 1:
                return False
            cands = [(h, o) for h, o in w.ores.items() if not o.get('busy')]
        cands = [(math.hypot(o['x'] - hx, o['y'] - hy), h, o) for h, o in cands]
        cands = [c for c in cands if c[0] <= rng]
        if not cands:
            return False
        dist, h, o = min(cands, key=lambda c: c[0])
        self.task = ('box' if g == AUTO_LOOT else 'ore', h)
        self.move(o['x'], o['y'], self.speed() * 1.5, now)
        return True

    def fight(self, now):
        """Koruma: geminin hedefine, yoksa gemiye saldıran en yakın NPC'ye ateş et (seçili cephane, lazer başına 1). P.E.T. hedefin
        yanına gider (gemiden en çok yakin_mesafe uzağa). Savaşıyorsa True (izleme yapılmaz)."""
        w = self.w
        n = w.npcs.get(w.target) if w.attacking else None
        px, py = self.pos(now)
        hx, hy = w.hero_pos(now)
        if not n or not n.alive:
            near = [(math.hypot(x.mover.pos(now)[0] - hx, x.mover.pos(now)[1] - hy), x) for x in w.npcs.values() if x.alive and x.engaged]
            near = [c for c in near if c[0] <= PET['savas_mesafe']]
            n = min(near, key=lambda c: c[0])[1] if near else None
        nx, ny = n.mover.pos(now) if n else (0, 0)
        if not n or math.hypot(nx - hx, ny - hy) > PET['savas_mesafe']:
            if self.shooting:
                self.stop_shooting()
            return False
        lasers = self.lasers()
        if not lasers:
            return False
        dist = math.hypot(nx - px, ny - py)
        if dist > PET['yakin_mesafe'] and now >= self.next_follow:
            a = math.atan2(py - ny, px - nx)          # hedefin P.E.T. tarafındaki bir noktaya
            self.move(nx + math.cos(a) * PET['yakin_mesafe'] * 0.8, ny + math.sin(a) * PET['yakin_mesafe'] * 0.8, self.speed() * 1.2, now)
            self.next_follow = now + 0.5
        if dist > SAVAS['lazer_menzil'] or now < self.next_shot:
            return True
        ammo = self.p.d['secili']['lazer']
        if self.p.use_ammo(ammo, len(lasers)) is None:
            if self.shooting:
                self.stop_shooting()
            return False
        if self.shooting != n.id:
            self.log('   P.E.T. ateş ediyor: %s (%d lazer, %s)' % (n.d['ad'], len(lasers), ammo))
        self.shooting = n.id
        self.next_shot = now + ESYA['lazer_cephane'].get(ammo, {}).get('aralik_sn', SAVAS['lazer_aralik_sn'])
        w.last_combat = now
        w.send(w.ammo_msgs(ammo) + [('AttackLaserRunCommand', dict(attackerId=self.pid, targetId=n.id,
                                                                   laserColor=ESYA['lazer_renkleri']['cephane'].get(ammo, 0),
                                                                   isDiminishedBySkillShield=False, skilledLaser=False, visualType=0))])
        if random.random() < AY.chance('oyuncu_isabet', SAVAS['lazer_isabet'] * (1 + self.proto('isabet'))):      # panel
            base = self.laser_damage()                                   # LF-PX01: HEAT seviyesine göre
            base *= 1 + self.row()['hasar'] + self.proto('lazer') + self.proto('uzayli')
            a = ESYA['lazer_cephane'].get(ammo, {'carpan': 1})
            r = random.uniform(*ESYA['hasar_rastgele'])
            shield = int(base * a.get('kalkan_carpan', 0) * r)
            if shield:
                w.hit_npc(n.id, shield, 1, shield_only=True, attacker=self.pid)
            else:
                w.hit_npc(n.id, int(base * a.get('carpan', 1) * r), 1, attacker=self.pid)
        else:
            w.send([('AttackMissedCommand', dict(attackType=mod('AttackTypeModule', attackTypeValue=1), targetUserId=n.id, skillColorId=0))])
        return True

    def stop_shooting(self):
        self.shooting = None
        self.w.send([('PetLaserAttackStopCommand', {'petId': self.pid})])

    def trade_used(self, now):
        """Kargo tüccarıyla satış yapıldı: dişli bekleme süresine girer (wiki: 300 sn), P.E.T. korumaya döner."""
        self.trade_ready = now + self.gear(TRADE_POD).get('bekleme_sn', 0)
        self.trading = False
        self.select(GUARD)

    def targets(self, g):
        """Bulucu dişlinin seçilebilir hedefleri: haritadaki NPC gemi türleri ya da cevher türleri."""
        w = self.w
        if not w:
            return []
        if g == ENEMY_LOCATOR:
            return sorted({int(n.model) for n in w.npcs.values()})
        return sorted({o['tip'] for o in w.ores.values()})

    def locate_target(self, g, value):
        w = self.w
        now = time.time()
        hx, hy = w.hero_pos(now)
        rng = self.gear(g).get('menzil', 0) * self.range_bonus()
        if g == ENEMY_LOCATOR:
            spots = [n.mover.pos(now) for n in w.npcs.values() if n.alive and int(n.model) == value]
        else:
            spots = [(o['x'], o['y']) for o in w.ores.values() if o['tip'] == value]
        spots = [s for s in spots if math.hypot(s[0] - hx, s[1] - hy) <= rng]
        return min(spots, key=lambda s: math.hypot(s[0] - hx, s[1] - hy)) if spots else None

    def take_shot(self, n, now, force=False):
        """NPC'nin atışı P.E.T.'e mi (yakınsa hedef_alinma olasılığıyla; force: birden çok hedefe ateş eden uzaylı, Mindfire
        Behemoth)? Öyleyse vuruşu uygular, True döner."""
        if not self.active or not self.w:
            return False
        w = self.w
        px, py = self.pos(now)
        nx, ny = n.mover.pos(now)
        if math.hypot(px - nx, py - ny) > w.npc_range(n) or (not force and random.random() >= PET['hedef_alinma']):
            return False
        n.next_shot = now + SAVAS['npc_saldiri_aralik_sn']
        w.last_combat = now
        msgs = [('AttackLaserRunCommand', dict(attackerId=n.id, targetId=self.pid, laserColor=0, isDiminishedBySkillShield=False,
                                               skilledLaser=False, visualType=0))]
        if random.random() >= AY.chance('npc_isabet', SAVAS['npc_isabet']) * (1 - self.proto('kacinma')):        # panel
            msgs.append(('AttackMissedCommand', dict(attackType=mod('AttackTypeModule', attackTypeValue=1), targetUserId=self.pid,
                                                     skillColorId=0)))
            w.send(msgs)
            return True
        dmg = int(n.d['hasar'] * random.uniform(0.7, 1.0) * AY.carpan('npc_hasar'))      # panelin hasar çarpanı
        g = self.d.get('disli')
        if g in (COMBO_GUARD, COMBO_REPAIR) and random.random() < self.gear(g).get('sapma', 0):
            w.send(msgs)
            w.hit_npc(n.id, dmg, 1, attacker=self.pid)          # saptırma: hasar saldırana döner
            return True
        d = self.d
        with self.p.lock:
            to_shield = min(d['kalkan'], int(dmg * self.absorb()))
            d['kalkan'] -= to_shield
            d['can'] = max(0, d['can'] - (dmg - to_shield))
            self.p.dirty = True
        msgs += [('AttackHitCommand', dict(attackType=mod('AttackTypeModule', attackTypeValue=1), attackerId=n.id, victimId=self.pid,
                                           victimHitpoints=int(d['can']), victimShield=int(d['kalkan']), victimNanoHull=0, damage=dmg,
                                           skilled=False, strike=False, cannonType=0)),
                 self.hp_msg(), self.shield_msg()]
        w.send(msgs)
        kk = self.gear(KAMIKAZE)
        if g == KAMIKAZE and d['can'] <= self.hp_max() * kk.get('esik', 0):
            self.kamikaze(now)
        elif d['can'] <= 0:
            self.destroyed(DESTROYED_NONE, n)
        return True

    def kamikaze(self, now):
        """Kamikaze dişlisi: can eşiğin altına inince patlar, yakındaki NPC'lere hasar verir (P.E.T. yok olur)."""
        w, kk = self.w, self.gear(KAMIKAZE)
        px, py = self.pos(now)
        hit = [n for n in list(w.npcs.values()) if n.alive and math.hypot(n.mover.pos(now)[0] - px, n.mover.pos(now)[1] - py) <= kk['menzil']]
        self.destroyed(DESTROYED_KAMIKAZE)
        for n in hit:
            w.hit_npc(n.id, kk['hasar'], 1, attacker=self.pid)
        self.log('   P.E.T. kamikaze: %d NPC vuruldu' % len(hit))

    def destroyed(self, kind, killer=None):
        with self.p.lock:
            self.d.update(yikik=True, can=0, kalkan=0)
            self.p.dirty = True
        self.deactivate(notify=False)
        self.send([('ShipDestroyedCommand', dict(destroyedUserId=self.pid, explosionTypeId=0)), ('ShipRemoveCommand', {'userId': self.pid}),
                   ('PetIsDestroyedCommand', dict(destroyedType=kind)), self.init_msg(), self.repair_button()])
        self.log('   P.E.T. yok edildi%s' % (' (%s)' % killer.d['ad'] if killer else ''))

    def hero_died(self):
        """Gemi yok edildi: P.E.T. de durur (yeniden doğunca elle çıkarılır)."""
        self.relaunch = False
        self.deactivate()

    def gain_xp(self, ep):
        """Oyuncunun kazandığı EP'nin %5'i (wiki). Etkin değilken kazanmaz. Seviye atlayınca görünüm ve yuvalar değişir."""
        if not self.active or ep <= 0:
            return []
        add = int(ep * PET['ep_payi'] * (1 + self.p.mods().get('pet_ep', 0)) * AY.carpan('pet_ep'))     # P-EP booster; panel
        if not add:
            return []
        d = self.d
        with self.p.lock:
            d['ep'] += add
            old = d['seviye']
            while d['seviye'] + 1 < len(PET['seviyeler']) and d['ep'] >= PET['seviyeler'][d['seviye'] + 1]['ep']:
                d['seviye'] += 1
            self.p.dirty = True
        msgs = [('PetExperiencePointsUpdateCommand', dict(currentExperiencePoints=d['ep'], maxExperiencePoints=self.next_xp()))]
        if d['seviye'] > old:
            self.look = self.ship_type()
            msgs += [('PetLevelUpdateCommand', dict(petLevel=d['seviye'], petExperiencePointsUntilNextLevel=self.next_xp(),
                                                    designId=self.ship_type(), expansionStage=1)), self.status_msg()]
            self.log('   P.E.T. seviye atladı: %d' % d['seviye'])
            self.p.ach('pet_level', deger=d['seviye'])
        return msgs

    def refresh(self):
        """Hangarda P.E.T. donanımı değişti: uzaydaysa dişliler, durum ve görünüm (tasarım) yeniden. Görünüm PetLevelUpdateCommand'la
        gidiyor; istemci onu seviye atlama efektiyle ve üstte seviye yazısıyla gösteriyor: yalnız görünüm değişince (2026-10-19,
        kullanıcı bildirimi: hangarda her eşya değişince efekt çıkıyordu)."""
        if not self.active:
            return []
        hp, sh = self.hp_max(), self.shield_max()
        with self.p.lock:
            self.d['can'] = min(self.d['can'], hp)
            self.d['kalkan'] = min(self.d['kalkan'], sh)
        if self.d.get('disli') not in {t for t, lv, ok in self.gear_list() if ok}:
            self.d['disli'] = GUARD
        look = []
        if self.ship_type() != self.look:
            self.look = self.ship_type()
            look = [('PetLevelUpdateCommand', dict(petLevel=self.d['seviye'], petExperiencePointsUntilNextLevel=self.next_xp(),
                                                   designId=self.look, expansionStage=1))]
        return [('PetGearResetCommand', {}), self.status_msg()] + look + self.gear_msgs()


ORE_DELAY = ESYA['cevherler']['toplama_sn']


class _NoLock:
    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False
