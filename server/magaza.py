"""Mağaza ve hangar: cephane/ekipman satın alma ve hangarda ekipman takıp çıkarma (kayıttaki ve istemcideki akışlar).

Satın alma (kayıt: LCB-10 ve MCB-25 alımları, belgeler/istemci/kayit_analizi.md):
  ShopItemBuyRequest {lootId, category, amount, …} ->
    [hızlı alım öğelerinin durumu] + 0|A|C|kredi|uridyum + para birimi envanteri + cephane sayacı (MenuItemStatusCommand)
    + InventoryItemUpdatedCommand + InventoryItemPack + 0|LM|ST|BAT|lootId|adet + ShopItemBuyCommand(resultId 1)
    + kategorinin güncel ShopItemListCommand'i (maxAmount = paranın yettiği adet, yetmiyorsa -1)
  Fiyat: price × adet, yukarı yuvarlanır (kayıt: 0,5 U'luk MCB-25'ten 1 adet -> 1 U).
  Ekipman alımında eşya envantere girer (hangarId 0). Gemide boş yuva varsa ShopItemBuyCommand allowAutoEquip=1 ve
  hintEquipTo="hint_equip_to_ship" taşır; istemci "Envantere / Otomatik donat" sorar ve onayda aşağıdaki takma isteğini
  gönderir (istemci kodu: UIShopSystem.SendHangarShipMoveItemsRequest).
Tek oyunculu: gerçek parayla satılan ("Payment") eşyalar uridyumla satılır (fiyatlar esyalar.json odeme_fiyatlari).
  Paketlerin içeriği odeme_paketleri tablosundan verilir (gemi paketleri dahil); içeriği sunucuda olmayan eşya listede gösterilmez.
  Paketin verilemeyen parçaları (sahip olunan gemi, P.E.T., formasyon; dronlar boş yer kadar) atlanır, gerisi verilir, ekranda
  "Already owned, not given: …" (package_fit); hepsi zaten varsa alım olmaz. Fiyat değişmez.
Hızlı alım: kısayol çubuğundaki buy_<lootId> (MenuActionRequest actionType 0); adet öğenin sayacı (lazer 1000, roket 100).
Hangar:
  HangarShipEquipmentRequest -> HangarShipEquipmentCommand (iki config'in eşya kimlikleri profilden)
  HangarListRequest          -> HangarShipsCommand (envanter: ekipman örnekleri, cephane, cevher)
  HangarShipDetailRequest    -> HangarShipDetailCommand (lazer sayısı, cephane, jeneratörler, hız)
  HangarShipMoveItemsRequest {items, source, destination, configId} (istemci: UINewHangarSystem.SendMoveItemRequest;
    hedef/kaynak "ship" | "inventory", yuvayı eşyanın türü belirler) -> HangarShipMoveItemsCommand(result 1)
    + eşyaların hangarId güncellemesi + HangarShipEquipmentCommand; etkin config değiştiyse hız/kalkan/görünüm.
Dronlar (kayıttaki hesapta dron yoktu; biçimler istemcinin kodundan):
  Mağaza "drone" kategorisi: Flax (kredi), Iris (uridyum); fiyat her dronla artar (esyalar.json dronlar), en çok 8.
  Formasyonlar mağazadan alınır; kısayol çubuğunun drone_formations kategorisinde görünür olur. Çubuktan seçilince
  (MenuActionRequest drone_formation_*) DroneFormationChangeCommand + uzaydaki dron dizilimi + bonuslar (hız, kalkan, can).
  Uzayda: "0|n|d|<kullanıcı>|<formasyon>|" + dron başına "tür|seviye|tasarım|görünüm" (istemci: MapEventsAssemblyHelper.
    AssembleSetDrones; tür 1 Flax, 2 Iris, 3 Apis, 4 Zeus; seviye 1-6).
  Hangar: HangarShipsCommand.drones (HangarShipDroneView) ve HangarShipEquipmentCommand.droneConfigs (config başına dron listesi,
    takılı eşyalar SingleDroneEquipmentMsg.defaults). Dronlara yalnız lazer ve kalkan jeneratörü takılır (Flax 1, Iris 2 yuva);
    istemci hedef/kaynak "drone" + droneId gönderir (yuva kümesi "default"; istemci: UINewHangarSystem.ReturnDroneId).
Dron tasarımları (mağaza "customization"; Havoc ve Hercules esyalar.json ek_magaza): dron başına bir "design" (bonuslu,
  istemcide DroneDesignType) ve bir "visual" (görünüm, DroneCustomizationType) yuvası; tüm config'lerde aynı. Uzayda dron
  dizgisinin tasarım/görünüm alanları istemcinin game.xml tasarım kimlikleri (esyalar.json dron_tasarimlari).
P.E.T. (pet.py): mağazada pet_pet10 (bir tane), dişliler (petgear) ve protokoller (protocol) envantere girer; hangarda
  P.E.T. yuvaları (lasers, generators, gears, protocols) config başına; yuva açma ve ad değiştirme pet.py'de.
Katalog ve fiyatlar kayıttaki ShopItemListCommand'lerden (data/yanitlar.json); ekipman değerleri data/esyalar.json.
"""
import json, math, os, time
import booster as BOOSTER   # noqa: E402
import pet as PETM
import ekstra as EK
import rutbe as RT
import teknoloji as TK
import yukseltme as YK
import gemi_modul as GM
import ganimet as GN
import qfc as QF
import parcacik as PC
import rezonator as RZ
import ayar as AY
import ipucu as IP
import sezon as SZ

HERE = os.path.dirname(os.path.abspath(__file__))
ESYA = json.load(open(os.path.join(HERE, 'data', 'esyalar.json'), encoding='utf8'))
FIYAT = json.load(open(os.path.join(HERE, 'data', 'fiyatlar.json'), encoding='utf8'))['fiyatlar']    # market dengesi (tools/market_dengesi.py)
CONFIG_COOLDOWN_SN = 5          # config geçişleri arası (kayıtta 2,4 sn sonraki reddedildi; süre uyarlama)

CURRENCY = {'virtual': 'credits', 'real': 'uridium'}
SLOTS = (('equipment_weapon_laser_', 'laser'), ('equipment_weapon_rocketlauncher_', 'rocket'),
         ('equipment_generator_', 'generators'), ('equipment_extra_', 'extra'), ('equipment_shipupgrade_', 'upgrades'),
         ('equipment_core_', 'QuantumFluidCore'),       # Quantum Fluid Core: geminin özel yuvaları (qfc.py)
         ('equipment_weapon_cannon_', 'cannon'), ('equipment_cannon_shield_', 'cannonShield'),      # parçacık topu, kırıcı
         ('equipment_weapon_drive_', 'drive'), ('equipment_lens_', 'lens'))                        # Singularity Drive, mercek
# hangar panelleri: istemci gemi için "ship" gönderir; yuva adları da kabul edilir
PANELS = {'ship': None, 'laser': 'laser', 'lasers': 'laser', 'generator': 'generators', 'generators': 'generators',
          'extra': 'extra', 'extras': 'extra', 'rocket': 'rocket', 'rockets': 'rocket', 'rocketlauncher': 'rocket',
          'upgrades': 'upgrades', 'upgrade': 'upgrades', 'ship_upgrades': 'upgrades', 'shipupgrade': 'upgrades'}
INVENTORY = ('inventory', '')
DEFAULT_SLOTS = {'laser': 15, 'generators': 15, 'extra': 3, 'rocket': 1, 'upgrades': 3, 'QuantumFluidCore': 2, 'cannon': 3,
                 'cannonShield': 6, 'drive': 0, 'lens': 0}
EQUIP_SLOTS = ('laser', 'generators', 'extra', 'rocket', 'upgrades', 'QuantumFluidCore', 'cannon', 'cannonShield', 'drive', 'lens')
MODULE_TYPE_IDS = {'DAMAGE': 1, 'HP': 2, 'SHIELD': 3, 'SPECIAL': 4}       # ShipUpgradeModuleUpdateCommand.moduleTypeIds (uyarlama)
ORES = {int(t): loot for t, loot in ESYA['cevherler']['turler'].items()}     # OreType -> eşya (hangar envanteri)
DRONES = ESYA['dronlar']
FORMS = ESYA['formasyonlar']
LEVELS = ESYA['dron_seviyeleri']
DRONE_ITEMS = ('equipment_weapon_laser_', 'equipment_generator_shield_')     # dronlara yalnız lazer ve kalkan jeneratörü (wiki)
LAB = ESYA['laboratuvar']
DESIGNS = ESYA['dron_tasarimlari']
DESIGN_TYPES = {'design': 'net.bigpoint.darkorbit.asset.drone.design.DroneDesignType',
                'visual': 'net.bigpoint.darkorbit.asset.drone.design.DroneCustomizationType'}
PET_LOOT = ESYA['pet']['loot']
PACK_MAX = 255             # bayt sayaçlı liste (InventoryItemPack.items): en çok bu kadar eşya
NEW_RESOURCES = ('resource_collectable_evocation-chip', 'resource_collectable_calling-chip',          # N.O.V.A. (nova.py)
                 'resource_collectable_luminaflux-alloy', 'resource_collectable_armory-token',       # Hyperforge (qfc.py), Armory
                 'resource_collectable_armory-token-mega', 'resource_collectable_optigrad-chip',       # Restabilize (parcacik.py)
                 'resource_collectable_horizon-shard', 'resource_collectable_containment-node',       # sürücü alt nitelikleri
                 'resource_collectable_pulse-core', 'resource_ignishard-l01', 'resource_beacon-crystal')
PASS_ITEMS = ('resource_season-pass-point', 'resource_gold-pass', 'resource_ext-gold-pass', 'resource_battle-pass',
              'resource_monthly-deluxe')
EVENT_ITEMS = ('resource_collectable_voyagers-oath-token', 'resource_voyagers-vip-badge',      # Voyagers (pve_modlari.py)
               'resource_ftl-key', 'resource_collectable_galaxy-coupon', 'resource_lottery-capsule')   # Ö3 etkinlik paraları (market dengesi)


def mod(name, **f):
    f['_'] = name
    return f


from eski_protokol import legacy  # noqa: E402,F401  (eski metin protokolü: eski_protokol.py)


def keyed(key, **wild):
    """İstemcinin yerelleştirme anahtarıyla hata metni (MessageKeyListWildcardCommand)."""
    reps = [mod('MessageWildcardReplacementModule', wildcard='%' + k + '%', replacement=v,
                replacementType=mod('ReplacementTypeModule', typeValue=5 if v.startswith('ttip_') else 0)) for k, v in wild.items()]
    return mod('MessageKeyListWildcardCommand', commandList=[
        mod('MessageKeyListWildcardModule', wildCardReplacements=reps, baseKey=key,
            baseKeyType=mod('ReplacementTypeModule', typeValue=5), textStyle=0)])


BASEKEY = json.load(open(os.path.join(HERE, 'data', 'mesaj_anahtarlari.json'), encoding='utf8'))['anahtarlar']


# metindeki yer tutucular (istemcinin ArgKey enum'u): ad "_X_" ise metinde %X%, değilse adın kendisi (XXX, YYY, DATETIME)
ARG_KEYS = {'_COOLDOWN_': 0, '_BOOSTERNAME_': 1, '_module_': 2, '_level_': 3, '_date_': 4, '_userlevel_': 5, '_maxMessages_': 6,
            '_notesLimit_': 7, '_MINIMUM_BID_': 8, '_NAME_': 9, '_AMOUNT_': 10, '_CURRENCY_': 11, 'XXX': 12, 'YYY': 13,
            'DATETIME': 14, '_MAX_BID_': 15}


def res(key):
    """Yer tutucu değerinin istemcide yerelleştirilmesi (ShowCallBackText.ReturnTipByType: ':' ile bölünür, ikinci parça 'res' ise
    son parça GetTextById ile çevrilir). "res:<anahtar>" çalışmıyordu (canlı test H36: yer tutucu ham kalıyordu)."""
    return ':res:' + key


def stack_msg(key, **args):
    """Yanıt komutlarındaki hata/başarı metni (ShopItemBuyCommand, HangarShipMoveItemsCommand, HangarShipActivateShipCommand).
    İstemci BaseStackCommand bekler; başka sınıf InvalidCastException verip bağlantıyı koparır (canlı test).
    type 0 + enumBaseKey: istemci BaseKey enum adını yerelleştirme anahtarı olarak kullanır (stringBasekey ise ham metin olur).
    args: yer tutucuların değerleri (ArgStackCommand; istemci ShowCallBackText.ReturnTipString): ör. XXX='Komutan',
    _MINIMUM_BID_='10,000'. res(<anahtar>) değeri istemcide çevrilir. Verilmezse metinde "XXX" gibi ham yer tutucu kalıyordu
    (canlı deneme 2026-10-17: "A new rank was created: XXX.")."""
    lst = [mod('ArgStackCommand', type=0, value2=None, key=ARG_KEYS[k], value=str(v)) for k, v in args.items()]
    if key in RES_YERINE:
        # istemcinin yüklemediği kaynaktaki anahtar: ham metin "XXX" + XXX'in yerelleştirilmiş değeri (type 1; ReturnTipString
        # yer tutucuları sondan başa çevirir: önce XXX, sonra metnin kendi yer tutucuları)
        alias, extra = RES_YERINE[key]
        lst = [mod('ArgStackCommand', type=0, value2=None, key=ARG_KEYS[k], value=str(v)) for k, v in extra.items()] + lst
        lst.append(mod('ArgStackCommand', type=0, value2=None, key=ARG_KEYS['XXX'], value=res(alias)))
        return mod('BaseStackCommand', type=1, enumBaseKey=0, stringBasekey='XXX', argsList=lst)
    return mod('BaseStackCommand', type=0, enumBaseKey=BASEKEY[key], stringBasekey='', argsList=lst)


# BaseKey adı istemcide metin bulamayanlar -> yüklenen kaynaktaki eşdeğeri (ve yer tutucuları). İstemci "resource_items_old"
# kaynağını yüklüyor ama paketteki dosya "resource_item_old" (LocalizationManager): o dosyadaki anahtarlar (drone_have_max)
# hiç bulunmuyor, hata penceresi boş açılıyordu (canlı test 2026-10-18). clan_errmsg_desc_to_long hiçbir kaynakta yok.
RES_YERINE = {'drone_have_max': ('items_drone_have_max', {}),
              'special_generic_hint': ('items_special_generic_hint', {}),
              'clan_errmsg_desc_to_long': ('clan_errmsg_to_long', {'_NAME_': res('label_description')})}


# Assembly tariflerinde malzeme olan kaynaklar (mağazada satılanlar: Prismatic Socket, Nano Case …; assembly.py)
ASSEMBLY_PARTS = {l for r in json.load(open(os.path.join(HERE, 'data', 'tarifler.json'), encoding='utf8'))['tarifler'].values()
                  for l in r['parcalar'] if l.startswith('resource_')}
STAT_TABLES = (('lazerler', 'hasar'), ('kalkan_jeneratorleri', 'kalkan'), ('hiz_jeneratorleri', 'hiz'))
PAY_CURRENCY = {'currency_uridium': ('uridium', 'URI'), 'currency_credits': ('credits', 'CRE'), 'currency_experience': ('ep', 'EP'),
                'currency_honour': ('honourPoints', 'HON')}
PRIZE_CURRENCY = {'currency_uridium': 'uridyum', 'currency_credits': 'kredi', 'currency_experience': 'ep', 'currency_honour': 'onur'}


def design_base(loot):
    """Gemi tasarımı -> ait olduğu gemi (ship_goliath_design_amber -> ship_goliath); tasarım değilse None."""
    return loot.split('_design_')[0] if loot.startswith('ship_') and '_design_' in loot else None


def slot_of(loot):
    return next((s for p, s in SLOTS if loot.startswith(p)), None)


def loose_item(loot):
    """Gemi yuvası olmayan, envantere örnek olarak giren eşya: dron ve P.E.T. tasarımı, P.E.T. dişlisi ve protokolü (hangarda takılır)."""
    return loot in DESIGNS or loot in PETM.DESIGNS or PETM.slot_for(loot) in ('gears', 'protocols')


def hidden(loot):
    """Depoda (diger_esyalar) envanterde görünmeyen ve hiçbir sistemin okumadığı eşya mı. Kaynaklar (resource_) görünür; gemisi yokken
    gelen gemi tasarımı (pending_designs) ve CBS modülü (cbs.absorb) bilerek bekler. Ödül böyle bir eşyaya düşerse kaybolmuş sayılır
    (2026-10-22: Season Pass'in dron tasarımları, rezervleri ve Assembly'nin P.E.T. protokolleri böyle kayboluyordu)."""
    return not loot.startswith(('resource_', 'module_')) and not design_base(loot)


def pet_only(loot):
    """P.E.T.'e özel lazer/jeneratör (LF-P01, SG3N-P01 …; esyalar.json yalniz_pet)."""
    return bool(ESYA['lazerler'].get(loot, ESYA['kalkan_jeneratorleri'].get(loot, {})).get('yalniz_pet'))


ITEM_TYPE = 'net.bigpoint.darkorbit.asset.item.ItemType'
# istemcinin eşya sınıfları (istemci_esyalari.json 'sinif' kısa ad -> tam ad; istemcinin metin sabitlerinden)
CLASS_PATHS = {c.split('.')[-1]: 'net.bigpoint.darkorbit.asset.' + c for c in (
    'cannonshield.CannonShieldType', 'weapon.CannonType', 'weapon.DriveType', 'lens.LensType', 'quantum.QuantumFluidCoreType',
    'shipupgrade.ShipUpgradeType', 'extra.ExtraType', 'extra.ModuleType', 'extra.UpgradeType', 'module.StationModuleType',
    'drone.DroneType', 'drone.formation.DroneFormationType', 'drone.design.DroneCustomizationType', 'drone.design.DroneDesignType',
    'pet.PetType', 'pet.design.PetCustomizationType', 'item.HardwareType', 'item.SynthesisResourceType', 'captain.CaptainType')}
CLIENT_CLASS = {k: v['sinif'] for k, v in json.load(open(os.path.join(HERE, 'data', 'istemci_esyalari.json'), encoding='utf8'))[
    'esyalar'].items() if v.get('sinif') in CLASS_PATHS}


def loot_type(loot):
    """Hangar envanterinin lootType'ı: tasarımlar, esyalar.json loot_turleri (kayıtla doğrulanmış önekler), yoksa istemcinin kendi
    sınıfı. İstemci hangar envanterini sınıfa göre ayırıyor: genel ItemType giden toplar, sürücüler, mercekler, kırıcılar, QFC'ler
    ve gemi modülleri envanterde hiç görünmüyordu, hangarda takılamıyordu (canlı test H68)."""
    if loot in DESIGNS:
        return DESIGN_TYPES[DESIGNS[loot]['yuva']]
    t = next((t for p, t in sorted(ESYA['loot_turleri'].items(), key=lambda x: -len(x[0])) if loot.startswith(p)), ITEM_TYPE)
    if t == ITEM_TYPE and loot in CLIENT_CLASS:
        return CLASS_PATHS[CLIENT_CLASS[loot]]
    return t


def copy(x):
    return json.loads(json.dumps(x))


class Magaza:
    def __init__(self, profil, yanitlar, log=print):
        self.p, self.log = profil, log
        self.kapilar = None      # Galaksi Kapıları (ödüldeki ücretsiz enerji; oturum bağlar)
        self.quest = None        # görev olayları (oturum: gorev.event; rafine edilen cevher toplama görevlerine sayılır)
        self.biletler = None     # (Season Pass, Battle Pass, günlük ödüller): oturum bağlar; pass eşyaları onlara gider
        self.yeni = None         # Aşama 9'un sistemleri (yeni_sistemler.py): N.O.V.A. ve QFC ödülleri onlara gider
        self.chromin = None      # Chromin Rush (chromin.py; oturum bağlar): Chromin girişi sınırla
        self.hitac = None        # Hitac Word Puzzle (hitac_piyango.py; oturum bağlar): kutudaki harf
        self.lists, self.catalog = {}, {}
        self.payment = {}        # tek oyunculu: gerçek parayla satılan ("Payment") eşya -> uridyum fiyatı
        self.extra_entry = {}    # ek_magaza satırı (takvim / bir_kez: Ö7 dükkânlarının paketleri)
        self.credit = {}         # market dengesi: kredili "Payment" ürünü -> kredi fiyatı (data/fiyatlar.json)
        self.shop_gate = None    # (satır, lootId) -> şimdi satılır mı (dukkanlar.py: etkinlik, kampanya, bir kez, seviye)
        self.on_bought = []      # alımdan sonra (lootId, adet) -> mesajlar (dukkanlar.py: VIP, Pre-BF, Mileage sayaçları)
        fiyat = ESYA['odeme_fiyatlari']
        for e in yanitlar.get('ShopItemListRequest', []):
            for m in e['yanit']:
                if m['_m'] == 'ShopItemListCommand':
                    self.lists.setdefault(m['category'], m)
                    for it in m['itemList']:
                        self.catalog.setdefault(it['lootId'], it)
                        if it.get('cost') == 'Payment' or it.get('isPaymentItem'):
                            self.payment.setdefault(it['lootId'], fiyat['ozel'].get(it['lootId'], fiyat.get(m['category'], fiyat['varsayilan'])))
        for cat, extra in ESYA['ek_magaza'].items():     # kayıtta olmayan, tek oyunculuda başka yoldan alınamayan eşyalar
            lst = self.lists.get(cat) if not cat.startswith('_') else None
            for x in (extra if lst else []):
                self.extra_entry[x['lootId']] = x
                tpl = self.catalog.get(x['sablon'])
                if tpl and x['lootId'] not in self.catalog:
                    it = dict(copy(tpl), lootId=x['lootId'], price=[float(x['uridyum'])], currency='real', isPaymentItem=0,
                              cost='{:,} U.'.format(x['uridyum']))
                    lst['itemList'].append(it)
                    self.catalog[x['lootId']] = it
        self.apply_prices()
        first = lambda req, name: next((m for e in yanitlar.get(req, []) for m in e['yanit'] if m['_m'] == name), None)
        self.equip_tpl = first('HangarShipEquipmentRequest', 'HangarShipEquipmentCommand')
        self.ships_tpl = first('HangarListRequest', 'HangarShipsCommand')
        self.detail_tpl = first('HangarShipDetailRequest', 'HangarShipDetailCommand')
        self.item_tpl, self.tpl_ids = None, {}
        for pack in (self.ships_tpl or {}).get('items', []):
            for it in pack.get('items', []):
                self.item_tpl = self.item_tpl or it
                self.tpl_ids.setdefault(it['lootId'], it['itemid'])
        self.sent_lists = set()          # bu oturumda istemciye gönderilen mağaza kategorileri
        self.featured = None             # (kategori, lootId, bitiş): ödeme düğmesinin ürünü listenin başında (odeme.py)
        self.pet = PETM.Pet(profil, log)  # oturum kendi P.E.T.'ini bağlar (uzaydaki davranış dünyayla)
        self.pet.on_stats = self.apply_stats       # HEAT bonusu değişince gemi değerleri
        for loot, n in list(profil.d.get('diger_esyalar', {}).items()):
            if loot.startswith('pet_designs_'):       # Aşama 6 öncesi depoda saklanan P.E.T. tasarımları -> envanter
                for _ in range(n):
                    profil.new_item(loot)
                profil.add_resource(loot, -n)

    def apply_prices(self):
        """Market dengesinin fiyatları (data/fiyatlar.json <- tools/market_dengesi.py): Payment ürünlerinin ve ek mağazanın
        fiyatı tek ölçekle; içeriği kredi sınıfı olanlar kredili."""
        for loot, r in FIYAT.items():
            it = self.catalog.get(loot)
            if r['para'] == 'C':
                self.payment.pop(loot, None)
                if it is not None and (it.get('cost') == 'Payment' or it.get('isPaymentItem')):
                    self.credit[loot] = r['fiyat']
                elif it is not None:
                    it.update(price=[float(r['fiyat'])], currency='virtual', cost='{:,} C.'.format(r['fiyat']))
            elif loot in self.payment:
                self.payment[loot] = r['fiyat']
            elif it is not None and loot in self.extra_entry:
                it.update(price=[float(r['fiyat'])], currency='real', cost='{:,} U.'.format(r['fiyat']))

    @property
    def hangar_id(self):
        return self.p.ship()['hangarId']

    @property
    def ship_id(self):
        return int(self.p.d['aktif_gemi'])

    # ------------------------------------------------------------ yardımcılar
    def handles(self, name, f):
        if name == 'MenuActionRequest':
            mid = f.get('menuItemId', '')
            return (mid.startswith('buy_') and f.get('actionType') == 0) or mid in FORMS
        return name in ('ShopItemListRequest', 'ShopItemBuyRequest', 'HangarShipEquipmentRequest', 'HangarListRequest',
                        'HangarShipDetailRequest', 'HangarShipMoveItemsRequest', 'LabRefinementRequest', 'LabUpdateItemRequest',
                        'LabUpdateRequest', 'HangarShipUnlockSlotRequest', 'HangarShipRenamePetRequest', 'HangarShipSellItemRequest',
                        'HangarShipSellDroneRequest', 'HangarShipFavouriteRequest', 'HangarShipClearConfigRequest',
                        'HangarShipSaveConfigRequest', 'HangarShipLoadConfigRequest', 'HangarShipImportConfigRequest')

    def ship_sid(self, ship_id):
        """İstekteki shipId profilde yoksa etkin gemi."""
        return str(ship_id) if str(ship_id) in self.p.d['gemiler'] else self.p.d['aktif_gemi']

    def handle(self, name, f):
        """İsteğe yanıt mesajları; None ise kayıtlı yanıta bırakılır."""
        if name == 'ShopItemListRequest':
            m = self.shop_list(f.get('category', ''))
            if m:
                self.sent_lists.add(f.get('category', ''))
            return [m] if m else None
        if name == 'HangarShipSellItemRequest':
            return self.sell(f)
        if name == 'HangarShipSellDroneRequest':
            return self.sell_drone(f)
        if name == 'ShopItemBuyRequest':
            return self.buy(f.get('lootId', ''), f.get('amount', 1), f.get('category', ''), f.get('buyCategory', ''),
                            pet_name=f.get('petName') or '', level=f.get('level') or 1)
        if name == 'MenuActionRequest':
            if f['menuItemId'] in FORMS:
                return self.change_formation(f['menuItemId'])
            return self.quick_buy(f['menuItemId'][4:])
        if name == 'HangarShipEquipmentRequest':
            return [self.equipment_cmd(self.ship_sid(f.get('shipId')))] if self.equip_tpl else None
        if name == 'HangarListRequest':
            if not self.ships_tpl:
                return None
            # istemcinin hangar gemi ızgarası mağazanın gemi listesini kullanır; liste gelmeden hangar açılırsa
            # HangerListCallBack NullReferenceException verir (canlı test). Kayıtta mağaza hep önce açılmıştı.
            pre = []
            if 'ship' not in self.sent_lists and self.shop_list('ship'):
                pre.append(self.shop_list('ship'))
                self.sent_lists.add('ship')
            return pre + [self.ships_cmd()]
        if name == 'HangarShipDetailRequest':
            return [self.detail_cmd(self.ship_sid(f.get('shipId')))] if self.detail_tpl else None
        if name == 'HangarShipMoveItemsRequest':
            return self.move(f)
        if name == 'HangarShipFavouriteRequest':
            return self.favourite(f)
        if name == 'HangarShipClearConfigRequest':
            return self.clear_config(f)
        if name == 'HangarShipSaveConfigRequest':
            return self.save_config(f)
        if name == 'HangarShipLoadConfigRequest':
            return self.load_config(f)
        if name == 'HangarShipImportConfigRequest':
            return self.import_config(f)
        if name == 'LabRefinementRequest':
            return self.refine(f)
        if name == 'LabUpdateItemRequest':
            return self.upgrade(f)
        if name == 'LabUpdateRequest':
            return [self.lab_cmd()]
        if name == 'HangarShipUnlockSlotRequest':
            return self.pet.unlock(f) + self.money_msgs()
        if name == 'HangarShipRenamePetRequest':
            return self.pet.rename(f)
        return None

    # ------------------------------------------------------------ rafine etme ve yükseltmeler
    def lab_cmd(self):
        return ('LabUpdateItemCommand', {'itemsUpdatedInfo': self.p.lab_items()})

    def refine(self, f):
        """LabRefinementRequest {toProduce: {oreType, count}}: tarif kadar hammadde düşer, ürün eklenir (istemcinin game.xml tarifleri)."""
        m = f.get('toProduce') or {}
        t, n = (m.get('oreType') or {}).get('typeValue'), int(m.get('count') or 0)
        recipe = LAB['tarifler'].get(str(t))
        if not recipe or n <= 0:
            return []
        need = {int(k): v * n for k, v in recipe.items()}
        short = [k for k, v in need.items() if self.p.ore_count(k) < v]
        if short:
            self.log('   rafine olmadı: %s x%d (eksik %s)' % (ORES.get(t), n, ', '.join(ORES.get(k, str(k)) for k in short)))
            return [('AttributeOreCountUpdateCommand', {'oreCountList': self.p.d['madenler']})]
        self.p.remove_ores(need)
        totals = self.p.add_ores({t: n})
        self.log('   rafine: %s x%d (%s)' % (ORES.get(t), n, ', '.join('%s %d' % (ORES.get(k), v) for k, v in need.items())))
        msgs = [('AttributeOreCountUpdateCommand', {'oreCountList': totals}), self.ore_pack(sorted(need) + [t])]
        return msgs + (self.quest('loot', loot=ORES.get(t), amount=n) if self.quest else [])

    def upgrade(self, f):
        """LabUpdateItemRequest {itemToUpdate, updateWith {oreType, count}}: cevher parçaya yüklenir. Aynı cevher eklenir, başka cevher
        öncekini siler (istemci: lab_alert). Hız ve kalkan hemen değişir."""
        item = (f.get('itemToUpdate') or {}).get('itemValue')
        m = f.get('updateWith') or {}
        t, n = (m.get('oreType') or {}).get('typeValue'), int(m.get('count') or 0)
        if str(item) not in LAB['bonuslar'] or str(t) not in LAB['bonuslar'][str(item)] or n <= 0 or self.p.ore_count(t) < n:
            self.log('   yükseltme olmadı: parça %s, cevher %s x%d (elde %d)' % (item, t, n, self.p.ore_count(t) if t is not None else 0))
            return [self.lab_cmd()]
        totals = self.p.remove_ores({t: n})
        with self.p.lock:
            ups = self.p.d.setdefault('yukseltmeler', {})
            old = ups.get(str(item))
            ups[str(item)] = [t, (old[1] if old and old[0] == t else 0) + n]
            self.p.dirty = True
        key = ('lab_upgrade_laser', 'lab_upgrade_rocket', 'lab_upgrade_speed', 'lab_upgrade_shield')[item]
        self.log('   yükseltme: parça %d <- %s x%d (toplam %d)' % (item, ORES.get(t), n, ups[str(item)][1]))
        return ([('AttributeOreCountUpdateCommand', {'oreCountList': totals}), self.ore_pack([t]), self.lab_cmd()] + self.apply_stats()
                + [legacy('0|A|STM|%s' % key)])

    def item_id(self, loot):
        return self.p.d['esya_kimlik'].get(loot) or self.tpl_ids.get(loot) or self.p.item_id(loot)

    def capacity(self, slot, sid=None):
        if slot == 'upgrades':                                       # gemi modülü yuvası: istemcinin gemi verisi (gemi_modul.py)
            return GM.slots(self.p.ship(sid)['lootId'])
        if slot == 'QuantumFluidCore':                               # QFC yuvası: istemcinin gemi verisi (qfc.py)
            return QF.slots(self.p.ship(sid)['lootId'])
        if slot in PC.SLOTS:                                         # top, kırıcı, sürücü, mercek: istemcinin gemi verisi
            return PC.slots(self.p.ship(sid)['lootId'], slot)
        ship = ESYA['gemiler'].get(self.p.ship(sid)['lootId'], {})
        bonus = EK.slot_bonus(self.p, sid) if slot == 'extra' else 0      # yuva CPU'su (SL-01..04): config'te en büyüğü
        if slot == 'extra' and self.equip_tpl and 'extra' not in ship:
            return self.equip_tpl.get('extrasSlotsSize1', DEFAULT_SLOTS['extra']) + bonus
        return ship.get(slot, DEFAULT_SLOTS[slot]) + bonus

    def inv_item(self, iid, loot, amount, hangar=0):
        lv = YK.item_level(self.p, iid) if str(iid) in self.p.d['esyalar'] else 0     # yükseltme seviyesi (yukseltme.py)
        return ('InventoryItemUpdatedCommand', {'item': mod('InventoryItemModule', upgradeLevel=lv, lootId=loot, amount=amount, itemId=iid,
                                                            star=(PC.state(self.p, iid) or {}).get('yildiz', 0), isNew=False,
                                                            hangarId=hangar, extAttributes=[], inventoryItemAttributes=[])})

    def hangar_item(self, iid, loot, count, hangar=0, level=None):
        it = copy(self.item_tpl) if self.item_tpl else mod(
            'HangarShipEquipmentInventoryItem', moduleRepairCosts=0, modifiers='', star=0, UpgradeLevel=[], charges=-1, setBonusAmt=0,
            setBonusInfo=[], attachedAmmo='', extAttributes=[], setBonusActiveConfig1=False, setBonusActiveConfig2=False,
            currentHitPoints=1, maxHitPoints=0, asteroidId=-1, level=0, setBonus=False, modifier='', isUnstableShipUpgrade=False, ships='')
        it.update(itemid=iid, lootId=loot, itemCount=count, hangarId=hangar, lootType=loot_type(loot))
        if GM.unstable(loot) and str(iid) in self.p.d['esyalar']:
            it['isUnstableShipUpgrade'] = True                          # kararsız modül (gemi_modul.py)
            it['ships'] = GM.ship_ids(GM.state(self.p, iid)['gemiler'])   # ipucu: "+%5 hasar için Goliath, …"
            it['modifiers'] = GM.modifiers_str(self.p, iid)
        if PC.is_item(loot) and str(iid) in self.p.d['esyalar']:
            it.update(PC.hangar_fields(self.p, iid, loot))              # top: temel hasar, nitelikler, yıldız, UL'nin gemisi
        elif RZ.is_item(loot) and str(iid) in self.p.d['esyalar']:
            it['modifiers'] = RZ.modifiers_str(self.p, iid)             # Xeno Resonator'ın nitelikleri (Ö6)
        if EK.attached(self.p, loot):
            it['attachedAmmo'] = EK.attached(self.p, loot)      # otomatik alım CPU'sunun seçili cephanesi
        if PETM.has_levels(loot):
            # P.E.T. dişlisi/protokolü: istemci 1. seviyeyi "Level: 0" gösterir (canlı test)
            it['level'] = (level if level is not None else self.p.item_level(iid)) - 1
        elif YK.max_level(loot) and str(iid) in self.p.d['esyalar']:
            it['level'] = YK.item_level(self.p, iid)               # yükseltme seviyesi (0 = istemcide 1)
        return it

    def pack(self, items):
        return ('InventoryItemPack', {'items': items})

    def ore_pack(self, types):
        """Cevher sayısı değişince hangar envanterindeki cevher eşyaları (kayıt: toplamada InventoryItemPack, itemCount yeni sayı)."""
        return self.pack([self.hangar_item(self.item_id(ORES[t]), ORES[t], self.p.ore_count(t)) for t in types if t in ORES])

    # ------------------------------------------------------------ mağaza
    def drone_slots(self, loot):
        """Bu türden kaç dron daha alınabilir: Flax/Iris birlikte en çok dron_azami (8); Apis ve Zeus birer tane, sınırın dışında
        (wiki: en çok 10)."""
        ds = self.p.d['dronlar']
        if DRONES[loot].get('tek'):
            return 0 if any(x['lootId'] == loot for x in ds) else 1
        return max(0, ESYA['dron_azami'] - sum(1 for x in ds if not DRONES[x['lootId']].get('tek')))

    def drone_room(self, loot):
        return self.drone_slots(loot) > 0

    def package_fit(self, grants, owned):
        """Paket içeriğinden şimdi verilebilenler: sahip olunan gemi, P.E.T. ve formasyon atlanır, dronlar boş yer kadar verilir
        -> (verilecekler, [(lootId, atlanan adet, hata anahtarı)])."""
        fit, skipped, taken = [], [], 0             # taken: bu pakette sayılan Flax/Iris (ortak sınır)
        for g, n in grants:
            if g.startswith('ship_') and not design_base(g) and g in owned:
                skipped.append((g, 1, 'items_shop_error_ship_contains_ship'))
            elif g == PET_LOOT and self.pet.owned:
                skipped.append((g, 1, 'eqt_error_generic'))
            elif g in FORMS and (g == 'drone_formation_default' or g in self.p.d['formasyonlar']):
                skipped.append((g, 1, 'items_drone_formation_already_in_use'))
            elif g in DRONES:
                tek = DRONES[g].get('tek')
                k = max(0, min(n, self.drone_slots(g) - (0 if tek else taken)))
                taken += 0 if tek else k
                if k:
                    fit.append((g, k))
                if k < n:
                    skipped.append((g, n - k, 'drone_have_max'))
            else:
                fit.append((g, n))
        return fit, skipped

    @staticmethod
    def skipped_msg(skipped):
        """Paketten verilemeyenlerin ekran mesajı (ör. "Already owned, not given: P.E.T., 8x Iris")."""
        import kapi as KAPI
        name = lambda g: 'P.E.T.' if g == PET_LOOT else g.rsplit('_', 1)[-1].title()
        return KAPI.screen('Already owned, not given: ' + ', '.join(('%dx %s' % (n, name(g))) if n > 1 else name(g)
                                                                  for g, n, key in skipped))

    def drone_price(self, loot):
        """Flax/Iris: aynı türden kaçıncı dron olduğuna göre (wiki: Flax 100.000 C'den ikiye katlanır, Iris 15.000 U'dan artar)."""
        info = DRONES[loot]
        n = sum(1 for x in self.p.d['dronlar'] if x['lootId'] == loot)
        return info['para'], info['fiyatlar'][min(n, len(info['fiyatlar']) - 1)]

    def price(self, loot, level=1):
        """-> (para birimi alanı, birim fiyat) ya da None (kayıtta olmayan eşya). "Payment" eşyalar uridyumla.
        P.E.T. dişli/protokolleri seviyeye göre (wiki fiyatları, uridyum)."""
        if loot in DRONES:
            return self.drone_price(loot)
        if loot == PETM.HULL:                        # G-HP1: kaçıncı yükseltme olduğuna göre (P.E.T. seviyesi kadar)
            u = self.pet.hull_price()
            return ('uridium', u) if u else None
        prices = PETM.level_prices(loot)
        if prices and loot in self.catalog:
            return 'uridium', prices[min(max(int(level), 1), len(prices)) - 1]
        if loot in self.payment:
            return 'uridium', self.payment[loot]
        if loot in self.credit:
            return 'credits', self.credit[loot]
        it = self.catalog.get(loot)
        if not it or it.get('cost') == 'Payment' or it.get('currency') not in CURRENCY or not it.get('price') or it['price'][0] < 0:
            return None          # 0 fiyat geçerli: Phoenix mağazada 0 C
        return CURRENCY[it['currency']], it['price'][0]

    def buy_price(self, loot, level=1):
        """Satın alma fiyatı: price() x panelin mağaza fiyatı çarpanı (satış ve geri dönüşüm değerleri price()'tan, çarpansız)."""
        pr = self.price(loot, level)
        k = AY.carpan('magaza_fiyat')
        return pr if not pr or k == 1.0 else (pr[0], pr[1] * k)

    def gate_ok(self, loot):
        return self.shop_gate(self.extra_entry.get(loot), loot) if self.shop_gate else True

    def shop_list(self, category):
        t = self.lists.get(category)
        if not t:
            return None
        t = copy(t)
        t['currentShipLootId'] = self.p.ship()['lootId']
        if self.pet.owned:              # P.E.T. bir tane olur
            t['itemList'] = [it for it in t['itemList'] if it['lootId'] != PET_LOOT]
        # sunucuda karşılığı olmayanlar (Assembly parçaları, anahtarlar, içeriği tanımlanmamış paketler …) gösterilmez
        t['itemList'] = [it for it in t['itemList'] if self.contents(it['lootId'], 1) is not None and self.gate_ok(it['lootId'])]
        for it in t['itemList']:
            if (self.extra_entry.get(it['lootId']) or {}).get('bir_kez'):
                it['maxAmount'] = 1                          # Ö7 paketleri: etkinlikte bir kez
        t['itemList'] = [it for it in t['itemList'] if it['lootId'] != PETM.HULL or self.pet.hull_price()]
        for it in t['itemList']:
            if it['lootId'] == PETM.HULL:
                u = self.pet.hull_price()
                it.update(price=[float(u)], cost='{:,} U.'.format(u))
        for it in t['itemList']:
            if it['lootId'] in self.payment:
                u = self.payment[it['lootId']]
                it.update(price=[float(u)], currency='real', cost='{:,} U.'.format(u), isPaymentItem=0, elite=1)
            elif it['lootId'] in self.credit:
                c = self.credit[it['lootId']]
                it.update(price=[float(c)], currency='virtual', cost='{:,} C.'.format(c), isPaymentItem=0, elite=1)
        for it in t['itemList']:
            if it['lootId'] in DRONES:
                cur, u = self.drone_price(it['lootId'])
                it.update(price=[float(u)], cost='{:,} {}'.format(u, 'U.' if cur == 'uridium' else 'C.'))
            prices = PETM.level_prices(it['lootId'])
            if prices:                    # seviye seçicisi: seviye başına fiyat
                it.update(price=[float(u) for u in prices])
        k = AY.carpan('magaza_fiyat')
        if k != 1.0:                      # panelin mağaza fiyatı çarpanı: istemcinin gösterdiği fiyat ve metin
            for it in t['itemList']:
                if it.get('price') and it['price'][0] > 0 and it.get('cost') != 'Payment':
                    it['price'] = [float(math.ceil(u * k - 1e-9)) for u in it['price']]
                    it['cost'] = '{:,} {}'.format(int(it['price'][0]), 'U.' if it.get('currency') == 'real' else 'C.')
        for it in t['itemList']:
            prices = PETM.level_prices(it['lootId'])
            if prices:
                # seviye düğmeleri: istemci (UIShopSystem.SetRightNumberLevel) düğme i'yi i <= MaxNum ise açıyor, MaxNum = alınabilecek
                # adet ile maxAmount'un küçüğü (3 ise hepsi). Kayıttaki maxAmount 1'di (hesapta P.E.T. yoktu), sunucu değiştirmiyordu:
                # P.E.T. seviyesi ne olursa olsun yalnız 1. seviye seçiliyordu (kullanıcı 2026-10-18). maxAmount = P.E.T.'in izin verdiği
                # en yüksek seviye (wiki: 2. seviye P.E.T. 4, 3. seviye 8); sunucunun bilmediği "3X" kademesi gösterilmez
                lv = self.pet.d['seviye'] if self.pet.owned else 0
                top = max(n for n in range(1, len(prices) + 1) if lv >= PETM.level_need(n))
                it.update(maxAmount=top, maxlevel=top, levelGrades='[%s]' % ','.join(str(n) for n in range(1, len(prices) + 1)))
            if prices and it.get('LevelDataList'):
                # seviye düğmesinin fiyatı ve metni (ClickToggle: LevelDataList[seviye]) alınanla aynı: kayıttakiler kaldı, G-HR1'de
                # 15.000 / 32.000 görünüp 32.000 / 55.000 alınıyordu; panelin çarpanı da burada
                rows = it['LevelDataList'] = [dict(r) for r in it['LevelDataList']]
                for r, u in zip(rows, it['price']):
                    r.update(price=int(u), cost='{:,} U.'.format(int(u)))
        if category == 'ammunition':
            for it in t['itemList']:
                pr = self.buy_price(it['lootId'])
                if pr and pr[1] > 0:
                    n = int(self.p.d['pilot'].get(pr[0], 0) // pr[1])
                    it['maxAmount'] = min(n, 2 ** 31 - 1) if n >= 1 else -1
        if self.featured and self.featured[0] == category and time.time() < self.featured[2]:
            # ödeme düğmesinden açılan mağaza: istemci listenin ilk ürününü seçili açıyor (odeme.py)
            t['itemList'].sort(key=lambda it: it['lootId'] != self.featured[1])
        return ('ShopItemListCommand', t)

    def feature(self, category, loot, sec=15.0):
        """Bu kategorinin sonraki listelerinde (sec saniye) bu ürün başta."""
        self.featured = (category, loot, time.time() + sec) if loot else None

    def money_msgs(self):
        pl = self.p.d['pilot']
        return [legacy('0|A|C|%d|%d' % (pl.get('credits', 0), pl.get('uridium', 0))),
                self.inv_item(self.item_id('currency_uridium'), 'currency_uridium', pl.get('uridium', 0)),
                self.inv_item(self.item_id('currency_credits'), 'currency_credits', pl.get('credits', 0))]

    def quick_buy_status(self, menu_id):
        """Kısayol çubuğundaki hızlı alım öğesi: paranın yetip yetmediğine göre etkin/pasif (kayıt: ttip_currency_missing satırı)."""
        base = self.p.menu_status_cache.get(menu_id)
        pr = self.buy_price(menu_id[4:])
        if base is None or not pr:
            return None
        st = copy(base)
        ok = self.p.d['pilot'].get(pr[0], 0) >= math.ceil(pr[1] * max(st.get('counterValue', 1), 1) - 1e-9)
        st['activatable'] = ok
        for tip in ('toolTipSlotBar', 'toolTipItemBar'):
            lines = (st.get(tip) or {}).get('commandList')
            if lines is None:
                continue
            lines[:] = [l for l in lines if l.get('baseKey') != 'ttip_currency_missing']
            if not ok:
                lines.append(copy(keyed('ttip_currency_missing', CURRENCY='ttip_' + pr[0])['commandList'][0]))
        return st

    def quick_buy_msgs(self, currency=None):
        """Para değişince hızlı alım öğelerinin güncel durumu (kayıtta her alım ve ödülden sonra gönderilir)."""
        out = []
        for mid in sorted(self.p.menu_status_cache):
            if mid.startswith('buy_'):
                pr = self.price(mid[4:])
                if pr and (currency is None or pr[0] == currency):
                    st = self.quick_buy_status(mid)
                    if st:
                        out.append(('MenuItemStatusCommand', st))
        return out

    def buy_cmd(self, loot, category, buy_category, result, amount=0, error=None, equip_ids=(), free=0):
        return ('ShopItemBuyCommand', dict(
            canEquipItemId=[float(i) for i in equip_ids], slotSet='', hintEquipTo='hint_equip_to_ship' if equip_ids else '',
            canBeSubscribedTo=False, userHasBoosterPackage=False, buyCategory=buy_category, resultId=result,
            configId=self.p.aktif_konfig if equip_ids else 0, errorMessage=error, lootId=loot, category=category,
            hangarId=self.hangar_id if equip_ids else 0, realBuyAmount=amount, isSubscriptionRunning=False,
            allowAutoEquip=1 if equip_ids else 0, sucessMessage=None, emptySlotCount=free, droneId=0, isSubscriptionPaused=False,
            secondsLeft=0, action=''))

    def free_slots(self, slot, cid=None):
        return max(0, self.capacity(slot) - len(self.p.config(cid).get(slot, [])))

    @staticmethod
    def contents(loot, amount):
        """Satın alınınca verilecekler [(lootId, adet)]: cephane, ekipman ve gemi kendisi, paketler esyalar.json odeme_paketleri'nden.
        None: sunucu bu eşyayı henüz veremiyor (tasarım, anahtar …). Gemi her zaman 1 adet."""
        pk = ESYA['odeme_paketleri'].get(loot)
        if pk:
            if any(l.startswith('ship_') and not design_base(l) and l not in ESYA['gemiler'] for l, n in pk):
                return None          # sunucuda olmayan gemi (Paladin, Basilisk …; Aşama 6): paket gösterilmez
            return [(l, 1 if l.startswith('ship_') else n * amount) for l, n in pk]
        if loot.startswith('ship_') and (loot in ESYA['gemiler'] or design_base(loot)):
            return [(loot, 1)]
        if loot in DRONES or loot in FORMS or loot == PET_LOOT or loot == PETM.HULL:
            return [(loot, 1)]
        if loot in PETM.DESIGNS:                     # P.E.T. tasarımı: envantere, P.E.T.'in görünüm yuvasına takılır
            return [(loot, amount)]
        if BOOSTER.is_booster(loot):
            return [(loot, amount)]
        if loot == 'resource_logfile' or loot in GN.KEYS or loot in ASSEMBLY_PARTS:   # log diski; ganimet anahtarları; Assembly malzemesi
            return [(loot, amount)]
        if loot in PASS_ITEMS or loot in EVENT_ITEMS:                                # Gold Pass, Battle Pass, puan, Monthly Deluxe; etkinlik paraları
            return [(loot, amount)]
        if loot.startswith(('captain_', 'resource_collectable_energy-')) or loot in NEW_RESOURCES or loot in RZ.SOURCES:  # + Ö6 rezonatör kaynakları
            return [(loot, amount)]
        if loot.startswith('ammunition_') or slot_of(loot) or loot in DESIGNS or PETM.slot_for(loot) in ('gears', 'protocols'):
            return [(loot, amount)]
        return None

    def buy(self, loot, amount, category='', buy_category='', quick=False, pet_name='', level=1):
        amount = max(1, int(amount or 1))
        try:
            level = max(1, min(3, int(level)))
        except (TypeError, ValueError):
            level = 1
        if not PETM.has_levels(loot):
            level = 1
        elif level > 1 and (not self.pet.owned or self.pet.d['seviye'] < PETM.level_need(level)):
            # wiki: 2. seviye dişli/protokol için P.E.T. seviyesi 4, 3. seviye için 8 (istemci: pet_gear_shop_level_limit)
            self.log('   satın alma yok: %s seviye %d (P.E.T. seviyesi %d gerekir)' % (loot, level, PETM.level_need(level)))
            return [] if quick else [self.buy_cmd(loot, category, buy_category, 0, error=stack_msg('pet_gear_shop_level_limit'))]
        if not self.gate_ok(loot):                  # Ö7: etkinlik dışı, alınmış (bir kez) ya da seviye dışı paket
            self.log('   satın alma yok: %s (şimdi satılmıyor)' % loot)
            return [] if quick else [self.buy_cmd(loot, category, buy_category, 0, error=stack_msg('shop_item_not_found'))]
        if (self.extra_entry.get(loot) or {}).get('bir_kez'):
            amount = 1
        pr = self.buy_price(loot, level)
        grants = self.contents(loot, amount)
        is_ammo = loot.startswith('ammunition_')
        fail = lambda key: [] if quick else [self.buy_cmd(loot, category, buy_category, 0, error=stack_msg(key))]
        if not pr or not grants:
            self.log('   satın alma yok: %s (%s)' % (loot, 'mağazada değil' if not pr else 'içeriği sunucuda henüz yok'))
            return fail('shop_item_not_found')
        owned = {s['lootId'] for s in self.p.d['gemiler'].values()}
        pkg = loot.startswith(('package_', 'deal_'))
        skipped = []
        if pkg:      # paket (S-OS-01 = Yamato + Defcom, Stellar): sahip olunan gemi, P.E.T., formasyon ve dron yeri atlanır, gerisi verilir
            grants, skipped = self.package_fit(grants, owned)
            if not grants:
                self.log('   satın alma yok: %s (içeriğinin hepsi zaten var)' % loot)
                return fail(skipped[0][2])
        if any(g in owned for g, n in grants if g.startswith('ship_') and not design_base(g)):
            self.log('   satın alma yok: %s (bu gemi zaten var)' % loot)
            return fail('items_shop_error_ship_contains_ship')        # oyunun kuralı: her gemi türünden bir tane
        for g, n in ([] if pkg else grants):
            base = design_base(g)
            if base and base not in owned:
                self.log('   satın alma yok: %s (%s yok)' % (g, base))
                return fail('dse_ship_not_exist')                      # tasarım ancak o gemiye sahipken alınır
            if base and any(g in s.get('tasarimlar', []) for s in self.p.d['gemiler'].values()):
                self.log('   satın alma yok: %s (tasarım zaten var)' % g)
                return fail('items_design_already_in_use')
        for g, n in grants:
            if g in DRONES and not self.drone_room(g):
                self.log('   satın alma yok: %s (en çok %d dron)' % (g, ESYA['dron_azami']))
                return fail('drone_have_max')
            if g in FORMS and (g == 'drone_formation_default' or g in self.p.d['formasyonlar']):
                self.log('   satın alma yok: %s (formasyon zaten var)' % g)
                return fail('items_drone_formation_already_in_use')
            if g == PET_LOOT and self.pet.owned:
                self.log('   satın alma yok: P.E.T. zaten var')
                return fail('eqt_error_generic')
        if any(g.startswith('ship_') or g in DRONES or g in FORMS or g in (PET_LOOT, PETM.HULL) for g, n in grants):
            amount = 1
        cur, unit = pr
        cost = math.ceil(unit * amount - 1e-9)
        with self.p.lock:
            pl = self.p.d['pilot']
            if pl.get(cur, 0) < cost:
                self.log('   para yetmiyor: %s x%d = %d %s (elde %d)' % (loot, amount, cost, cur, pl.get(cur, 0)))
                return fail('not_enough_' + cur)
            pl[cur] -= cost
            self.p.dirty = True
        RT.money(self.p, cur, -cost, RT.buy_desc(loot), loot, amount)           # hesap geçmişi
        msgs = self.quick_buy_msgs(cur) + self.money_msgs()
        equip_ids, free = [], 0
        for g, n in grants:
            if design_base(g):
                sid = next((k for k, s in self.p.d['gemiler'].items() if s['lootId'] == design_base(g)), None)
                if sid is None:                            # paketteki tasarım, gemi yok: depoda bekler (pending_designs)
                    if not self.p.resource(g):
                        self.p.add_resource(g, 1)
                    self.log('   tasarım saklandı: %s (%s yok)' % (g, design_base(g)))
                    continue
                if g in self.p.ship(sid).get('tasarimlar', []):
                    continue
                with self.p.lock:
                    self.p.ship(sid).setdefault('tasarimlar', []).append(g)
                    self.p.dirty = True
                msgs += [('ShipDesignAddedCommand', {'lootId': g}), legacy('0|LM|ST|LOT|%s|1' % g)]
                self.log('   yeni tasarım: %s (%s)' % (g, design_base(g)))
            elif g.startswith(('resource_', 'currency_', 'tech_', 'pet_designs_', 'captain_')) or (pkg and BOOSTER.is_booster(g)):
                msgs += self.reward(g, n)                  # paket içeriği: kaynak deposu, para, teknoloji, saatlik booster
            elif g.startswith('ship_'):
                sid = self.p.add_ship(g)
                msgs.append(legacy('0|LM|ST|LOT|%s|1' % g))
                msgs += self.ship_count_msgs([g])          # Plus tarifinin taban gemisi (Assembly sayacı)
                self.log('   yeni gemi: %s (shipId %d, hangarId %d)' % (g, sid, self.p.ship(sid)['hangarId']))
            elif g in DRONES:                              # paketteki dronlar (Stellar: 8 Iris) hepsi, yer kadar (package_fit)
                for _ in range(n):
                    did = self.p.add_drone(g)
                msgs += [legacy('0|LM|ST|LOT|%s|%d' % (g, n))] + self.drone_msgs()
                self.p.ach('formation', dron=len(self.p.d['dronlar']))
                self.log('   yeni dron: %s x%d (kimlik %d, toplam %d)' % (g, n, did, len(self.p.d['dronlar'])))
            elif g in FORMS:
                with self.p.lock:
                    self.p.d['formasyonlar'].append(g)
                    self.p.dirty = True
                st = self.p.menu_status(g)
                msgs += ([('MenuItemStatusCommand', st)] if st else []) + [legacy('0|LM|ST|LOT|%s|1' % g)]
                self.log('   yeni formasyon: %s' % g)
            elif g.startswith('ammunition_'):
                before = self.p.ammo(g)
                total = self.p.add_ammo(g, n)
                iid = self.item_id(g)
                st = self.p.menu_status(g)
                if st:
                    msgs.append(('MenuItemStatusCommand', st))
                if before == 0:
                    msgs.append(('RefreshSelectedUICategoryCommand', {}))
                kind = 'BAT' if g.startswith('ammunition_laser_') else 'ROK' if g.startswith(('ammunition_rocket_', 'ammunition_rocketlauncher_')) else 'LOT'
                msgs += [self.inv_item(iid, g, total), self.pack([self.hangar_item(iid, g, total)]),
                         legacy('0|LM|ST|%s|%s|%d' % (kind, g, n))]
            elif g == PETM.HULL:
                msgs += self.pet.upgrade_hull()            # +10.000 azami can (wiki), uzaydaysa gösterge
            elif g == PET_LOOT:
                msgs += self.grant_pet(pet_name)
            elif g == 'resource_logfile':
                msgs += self.reward(g, n)                  # pilot yetenek ağacının log diski (kapı üreticisinin sayacı)
            elif BOOSTER.is_booster(g):
                BOOSTER.add(self.p, g, n)                  # her biri 10 saat; aynı booster süresine eklenir
                msgs += [BOOSTER.update_cmd(self.p), legacy('0|LM|ST|LOT|%s|%d' % (g, n))] + self.apply_stats()
                self.log('   booster: %s x%d (kalan %d sn)' % (g, n, BOOSTER.left(self.p, g)))
            elif not slot_of(g):
                for _ in range(n):            # dron tasarımı, P.E.T. dişlisi/protokolü: envantere (hangarda takılır)
                    iid = self.p.new_item(g, level)
                    msgs += [self.inv_item(iid, g, 1), self.pack([self.hangar_item(iid, g, 1)])]
                msgs.append(legacy('0|LM|ST|LOT|%s|%d' % (g, n)))
                if level > 1:
                    self.log('   seviye %d: %s' % (level, g))
            else:
                room = self.free_slots(slot_of(g))
                free += room
                got = 0
                for _ in range(n):
                    iid = self.p.new_item(g)
                    msgs += [self.inv_item(iid, g, 1), self.pack([self.hangar_item(iid, g, 1)])]
                    if got < room:
                        equip_ids.append(iid)
                        got += 1
                EK.recharge(self.p, g, n)                  # atlama/gizlenme CPU'su: yeni hak
                msgs.append(legacy('0|LM|ST|LOT|%s|%d' % (g, n)))
        self.log('   satın alındı: %s x%d = %d %s (kalan %d)' % (loot, amount, cost, cur, self.p.d['pilot'][cur]))
        if skipped:
            self.log('   paketten verilmedi (zaten var): %s' % ', '.join('%s x%d' % (g, n) for g, n, key in skipped))
            msgs.append(self.skipped_msg(skipped))
        for cb in self.on_bought:                      # Ö7 dükkânları (dukkanlar.py)
            msgs += cb(loot, amount) or []
        for g, n in grants:                            # ipucu (bir kez): ikinci gemi -> gemi ışınlama, ilk ekipman -> hangarda tak
            msgs += self.p.hint(IP.for_purchase(self.p, g, bool(slot_of(g)) and not g.startswith('ammunition_')))
        if not quick:
            buy = self.buy_cmd(loot, category, buy_category, 1, amount, equip_ids=equip_ids, free=free)
            lst = self.shop_list(category)
            # istemci liste gelince (ShopItemListCommandHandler -> CreateItem -> OnClickItem) satın alma penceresini gizliyor:
            # "Geminde boş slotlar var, donatılsın mı?" sorusu görünür görünmez kayboluyordu (canlı test 2026-10-18). Soru
            # varsa liste önce gider, soru sonra; yoksa kayıttaki sıra (ShopItemBuyCommand, sonra liste).
            msgs += ([lst, buy] if equip_ids else [buy, lst]) if lst else [buy]
        return msgs

    def grant_pet(self, name=''):
        """P.E.T. (mağaza, paket, Assembly, kutu): yoksa verilir; çubukta simgesi, pencerenin düğmeleri."""
        if self.pet.owned:
            return []
        with self.p.lock:
            self.p.d['pet'] = PETM.new_pet(self.p)
            if len((name or '').strip()) >= 3:              # mağazadaki "P.E.T. name" alanı
                self.p.d['pet']['ad'] = name.strip()[:20]
            self.p.dirty = True
        self.log('   yeni P.E.T.: %s' % PET_LOOT)
        return [('PetPurchasedCommand', {}), self.pet.init_msg(), self.p.generate('@arayuz'),    # çubukta P.E.T. simgesi
                legacy('0|LM|ST|LOT|%s|1' % PET_LOOT)]

    def prize(self, loot, n):
        """Görev, kapı, mod, etkinlik ve Dispatch ödülü: reward()'ın panelli yolu. Kredi, uridyum, EP ve onur kendi çarpanlarıyla;
        yığılan eşyalar (cephane, kaynak, anahtar, teknoloji eşyası) 'mod_odul' çarpanıyla; tek eşyalar (gemi, lazer, tasarım,
        booster, P.E.T., bilet) aynen. Mağaza, paket, takas ve GM yolları reward()'ı kullanır (ölçeklenmez)."""
        key = PRIZE_CURRENCY.get(loot)
        if key:
            n = AY.miktar(key, n)
        elif loot.startswith(('ammunition_', 'resource_', 'tech_')) and loot not in PASS_ITEMS:
            n = AY.miktar('mod_odul', n)
        return self.reward(loot, n) if n > 0 else []

    def reward(self, loot, n):
        msgs = self._reward(loot, n)
        if loot in (GM.SHARD, GM.CHIP) or PC.restabilizable(loot):
            # Restabilize sekmesi bedel sayaçlarını ve listeyi bu komuttan alıyor (kayıtta envanter değişince yeniden geliyor);
            # OptiGrad Chip / Unstable Shard gelince sekme 0 gösterip düğmeyi kapalı tutuyordu (canlı test H70)
            msgs = list(msgs or []) + [GM.list_cmd(self.p)]
        return msgs

    def _reward(self, loot, n):
        """Görev ödülü (kredi/uridyum/EP/onur dışındakiler): cephane, ekipman (boş yuva varsa etkin gemiye takılır; kayıttaki
        gibi), gemi, gemi tasarımı, cevher, booster, kapı enerjisi, log diski. Sunucuda karşılığı olmayan ödül (Assembly kaynağı, kupon …)
        profilde saklanır (diger_esyalar)."""
        msgs = []
        RT.note(self.p, 'received_item', loot, n)                              # seyir defteri
        if loot == PET_LOOT:                       # ödül yolundan P.E.T. depoya düşüp kayboluyordu (canlı test H43)
            return self.grant_pet()
        got = SZ.reserve(loot, n)
        if got is not None:                        # Season Pass rezervi: içeriği (sezon.py; önceden görünmez depoya düşüyordu)
            for l, k in got:
                msgs += self.reward(l, k)
            self.log('   rezerv açıldı: %s x%d -> %s' % (loot, n, ', '.join('%s x%d' % x for x in got)))
            return msgs
        if loot in PASS_ITEMS and self.biletler:                               # Season Pass puanı, Gold/Extra Gold, Battle Pass, Deluxe
            sz, bp, go = self.biletler
            if loot == 'resource_battle-pass':
                return bp.grant_pass(n)
            if loot == 'resource_monthly-deluxe':
                return go.grant_deluxe(n)
            return sz.grant(loot, n)
        if self.yeni and (loot.startswith(('captain_', QF.PREFIX)) or PC.is_item(loot)):     # N.O.V.A., QFC, top/sürücü (yeni_sistemler.py)
            got = self.yeni.reward(loot, n)
            if got is not None:
                return got
        if loot in PAY_CURRENCY:                    # paketteki para / EP (hesap geçmişine ve Uridium Bank'a sayılmaz)
            field, kind = PAY_CURRENCY[loot]
            with self.p.lock:
                pl = self.p.d['pilot']
                pl[field] = pl.get(field, 0) + n
                self.p.dirty = True
            if loot == 'currency_experience':
                tot = self.p.gain()                         # seviye EP'ye göre yeniden hesaplanır
                msgs.append(legacy('0|LM|ST|EP|%d|%d|%d' % (n, tot['ep'], tot['seviye'])))
            else:
                msgs += self.money_msgs() + [legacy('0|LM|ST|%s|%d|%d' % (kind, n, self.p.d['pilot'][field]))]
            return msgs
        if loot.startswith('tech_'):                # teknoloji eşyası (Assembly ve paketler): sayaca
            TK.add(self.p, loot, n)
            st = self.p.menu_status(loot)
            return msgs + ([('MenuItemStatusCommand', st)] if st else []) + [legacy('0|LM|ST|LOT|%s|%d' % (loot, n))]
        if loot.startswith('ammunition_'):
            total = self.p.add_ammo(loot, n)
            iid = self.item_id(loot)
            st = self.p.menu_status(loot)
            if st:
                msgs.append(('MenuItemStatusCommand', st))
            kind = 'BAT' if loot.startswith('ammunition_laser_') else 'ROK' if loot.startswith('ammunition_rocket') else 'LOT'
            msgs += [self.inv_item(iid, loot, total), self.pack([self.hangar_item(iid, loot, total)]), legacy('0|LM|ST|%s|%s|%d' % (kind, loot, n))]
        elif slot_of(loot):
            slot, equipped = slot_of(loot), False
            for _ in range(n):
                iid = self.p.new_item(loot)
                msgs += [self.inv_item(iid, loot, 1), self.pack([self.hangar_item(iid, loot, 1)])]
                if self.free_slots(slot) > 0 and not pet_only(loot):
                    with self.p.lock:
                        self.p.config().setdefault(slot, []).append(iid)
                        self.p.sync_ekipman()
                        self.p.dirty = True
                    msgs.append(self.inv_item(iid, loot, 1, self.hangar_id))
                    equipped = True
            if equipped:
                msgs += [self.equipment_cmd()] + self.apply_stats()
            msgs.append(legacy('0|LM|ST|LOT|%s|%d' % (loot, n)))
            if GM.unstable(loot):                       # Restabilize listesi (canlı test H41: yalnız girişte geliyordu)
                msgs.append(GM.list_cmd(self.p))
        elif loot.startswith('ship_') and loot in ESYA['gemiler']:
            if loot not in {s['lootId'] for s in self.p.d['gemiler'].values()}:
                self.p.add_ship(loot)
                msgs.append(legacy('0|LM|ST|LOT|%s|1' % loot))
                msgs += self.pending_designs(loot) + self.ship_count_msgs([loot])
                if self.ships_tpl:
                    msgs.append(self.ships_cmd())              # hangar listesinde yeni gemi (Assembly, kapı, kutu)
        elif design_base(loot) and self.grant_design(loot):
            msgs += [('ShipDesignAddedCommand', {'lootId': loot}), legacy('0|LM|ST|LOT|%s|1' % loot)]
        elif loot in ORES.values():
            t = next(k for k, v in ORES.items() if v == loot)
            if t <= 8:                      # kargoya giren cevherler: boş yer kadar (kapı ödülündeki Xenomit gibi)
                n = min(n, self.p.cargo_free())
            if n > 0:
                msgs += [('AttributeOreCountUpdateCommand', {'oreCountList': self.p.add_ores({t: n})}), self.ore_pack([t])]
        elif loose_item(loot):     # dron / P.E.T. tasarımı, P.E.T. dişlisi ve protokolü (kapı, kutu, Assembly, Pass): envantere, hangarda takılır
            for _ in range(n):
                iid = self.p.new_item(loot)
                msgs += [self.inv_item(iid, loot, 1), self.pack([self.hangar_item(iid, loot, 1)])]
            msgs.append(legacy('0|LM|ST|LOT|%s|%d' % (loot, n)))
        elif BOOSTER.is_booster(loot):   # ödül boosterı: adet saat, süresi oyundayken işler (günlük giriş, görev)
            BOOSTER.add(self.p, loot, seconds=n * 3600)
            msgs += [BOOSTER.update_cmd(self.p), legacy('0|LM|ST|LOT|%s|%d' % (loot, n))] + self.apply_stats()
        elif loot == 'resource_extra-energy' and self.kapilar:
            msgs += self.kapilar.bonus_energy(n)       # Galaksi Kapısı üreticisinin ücretsiz enerjisi
        elif loot in DRONES:                           # Assembly/Dispatch: dron (Flax/Iris en çok dron_azami, Apis/Zeus birer)
            for _ in range(n):
                if not self.drone_room(loot):
                    break
                self.p.add_drone(loot)
            msgs += [legacy('0|LM|ST|LOT|%s|%d' % (loot, n))] + self.drone_msgs()
        elif loot in FORMS:
            if loot not in self.p.d['formasyonlar']:
                with self.p.lock:
                    self.p.d['formasyonlar'].append(loot)
                    self.p.dirty = True
            st = self.p.menu_status(loot)
            msgs += ([('MenuItemStatusCommand', st)] if st else []) + [legacy('0|LM|ST|LOT|%s|1' % loot)]
        elif loot == 'resource_repairvoucher' and self.kapilar:
            with self.p.lock:                          # onarım kuponu: ölüm ekranında (dunya.vouchers)
                self.kapilar.d['kupon'] += n
                self.p.dirty = True
            msgs.append(legacy('0|LM|ST|LOT|%s|%d' % (loot, n)))
        elif loot == 'resource_pet-fuel' and self.pet and self.pet.owned:
            with self.p.lock:
                self.p.d['pet']['yakit'] = min(PETM.PET['azami_yakit'], self.p.d['pet'].get('yakit', 0) + n)
                self.p.dirty = True
            msgs.append(legacy('0|LM|ST|LOT|%s|%d' % (loot, n)))
        elif loot == 'resource_logfile' and self.kapilar:
            with self.p.lock:                          # log diski: pilot puanına çevrilir (yetenek.py)
                self.kapilar.d['log_disk'] += n
                self.p.dirty = True
            msgs.append(legacy('0|LM|ST|LOT|%s|%d' % (loot, n)))
        elif loot == 'resource_wordpuzzle-letter' and self.hitac:
            msgs += self.hitac.grant_letter(n)         # Hitac kutusundaki harf: Word Puzzle (hitac_piyango.py)
        elif loot == 'resource_collectable_chromin' and self.chromin:
            msgs += self.chromin.gain(n)               # Chromin Rush: 160.000 sınırı, fazlası krediye (chromin.py)
        else:                            # henüz harcayan sistem yok (Assembly kaynakları, kuponlar …): depoda (profil.add_resource)
            total = self.p.add_resource(loot, n)
            if loot.startswith('resource_'):
                msgs += self.resource_msgs(loot, total, n)
            if loot in GN.KEYS and GN.key_line(self.p, GN.KEYS[loot]):         # ganimet anahtarı: HUD sayacı
                msgs.append(legacy(GN.key_line(self.p, GN.KEYS[loot])))
            if hidden(loot):        # envanterde görünmez, hiçbir sistem okumaz: bu ödül kaybolur (test_odul_yollari yakalar)
                self.log('   UYARI: ödül tanınmıyor, envanterde görünmeyecek: %s x%d (depoda saklandı, toplam %d)' % (loot, n, total))
            else:
                self.log('   ödül depoda: %s x%d (toplam %d)' % (loot, n, total))
        return msgs

    def rescue_depot(self):
        """Ödül yolunda önceden tanınmadığı için görünmez depoya düşmüş eşyaları yerine taşır (2026-10-22: Season Pass'in Hyperion dron
        tasarımı ve rezervleri, Assembly'nin P.E.T. protokolleri): tasarım, dişli ve protokol envantere; rezervler açılır (aynı
        içerik birleşir, seyir defteri dolmasın). Hâlâ tanınmayanlar depoda kalır, günlükte uyarılır. Oturum her bağlantıda bir kez,
        giriş mesajlarından önce çağırır -> taşınan [(lootId, adet)]."""
        moved, opened = [], {}
        for loot, n in sorted(self.p.d.get('diger_esyalar', {}).items()):
            n = int(n)
            if n <= 0 or not hidden(loot):
                continue
            if loose_item(loot):
                for _ in range(n):
                    self.p.new_item(loot)
            elif loot in SZ.RESERVES:
                for l, k in SZ.reserve(loot, n):
                    opened[l] = opened.get(l, 0) + k
            else:
                self.log('   UYARI: depoda envanterde görünmeyen eşya: %s x%d' % (loot, n))
                continue
            self.p.add_resource(loot, -n)
            moved.append((loot, n))
        for l, k in sorted(opened.items()):
            self.reward(l, k)
        if moved:
            self.log('   depodan kurtarıldı: %s%s' % (', '.join('%s x%d' % x for x in moved),
                                                    ' -> %s' % ', '.join('%s x%d' % x for x in sorted(opened.items())) if opened else ''))
        return moved

    def resource_msgs(self, loot, total, n):
        """Depodaki kaynağın sayacı (InventoryItemUpdatedCommand: Assembly malzeme sayaçları buradan; canlı test H31) ve günlük satırı
        (n > 0 ise "… alındı")."""
        iid = self.item_id(loot)
        return [self.inv_item(iid, loot, total), self.pack([self.hangar_item(iid, loot, total)])] +             ([legacy('0|LM|ST|LOT|%s|%d' % (loot, n))] if n > 0 else [])

    # ------------------------------------------------------------ satış
    def sale_value(self, loot, n=1):
        """Satış -> (para alanı, tutar) ya da None. İstemcinin kendi değeri (eşyanın "sellable" özelliği, hangarın eşya bilgisinde
        kredi olarak gösterilen; data/istemci_esyalari.json); yoksa fiyatın satis_orani'si (uyarlama), mağazada fiyatı olmayanda
        ref_value."""
        v = YK.ITEMS.get(loot, {}).get('satis')
        if v:
            return 'credits', int(v * n)
        pr = self.price(loot) or self.ref_value(loot)
        if not pr:
            return None
        return pr[0], int(pr[1] * n * ESYA['satis_orani'])

    def ref_value(self, loot):
        """Mağazada olmayan eşyanın değeri (esyalar.json _satis_degerleri): lazer/kalkan/hız aynı tablodaki en güçlü uridyumlu mağaza
        eşyasına gücüyle oranlanır; ötekiler önek tablosundan."""
        for table, key in STAT_TABLES:
            row = ESYA[table].get(loot)
            if row and row.get(key):
                priced = [(l, self.price(l)) for l, r in ESYA[table].items() if l != loot and r.get(key)]
                priced = [(l, pr) for l, pr in priced if pr and pr[0] == 'uridium']
                if priced:
                    ref, (cur, val) = max(priced, key=lambda x: ESYA[table][x[0]][key])
                    return cur, val * row[key] / ESYA[table][ref][key]
        return next((tuple(v) for k, v in ESYA['satis_degerleri'].items() if loot.startswith(k)), None)

    def sell(self, f):
        """HangarShipSellItemRequest {itemList: [{itemId, quantity}]}: envanterdeki takılı olmayan eşya ya da cephane. Hepsi
        satılabiliyorsa satılır (InventoryItemRemovedCommand / sayaç güncellemesi + para), yoksa hiçbiri."""
        fail = lambda: [('HangarShipSellItemCommand', dict(errorMessage=stack_msg('eqt_error_generic'), resultId=0))]
        equipped = self.p.equipped_ids()
        ammo_ids = {self.item_id(l): l for l in self.p.d['cephane']}
        plan = []
        for pk in f.get('itemList') or []:
            iid, q = int(pk.get('itemId') or 0), max(1, int(pk.get('quantity') or 1))
            loot = self.p.d['esyalar'].get(str(iid))
            if loot:
                if iid in equipped:
                    self.log('   satış yok: %s takılı' % loot)
                    return fail()
                q = 1
            elif iid in ammo_ids:
                loot = ammo_ids[iid]
                q = min(q, self.p.ammo(loot))
            val = self.sale_value(loot, q) if loot and q > 0 else None
            if not val:
                self.log('   satış yok: eşya %s (%s)' % (iid, loot))
                return fail()
            plan.append((iid, loot, q, val))
        if not plan:
            return fail()
        msgs, got = [], {}
        for iid, loot, q, (cur, amount) in plan:
            if str(iid) in self.p.d['esyalar']:
                with self.p.lock:
                    del self.p.d['esyalar'][str(iid)]
                    self.p.d.get('esya_seviye', {}).pop(str(iid), None)
                    self.p.dirty = True
                msgs.append(('InventoryItemRemovedCommand', {'itemId': iid}))
            else:
                total = self.p.add_ammo(loot, -q)
                st = self.p.menu_status(loot)
                msgs += ([('MenuItemStatusCommand', st)] if st else []) + [self.inv_item(iid, loot, total),
                                                                          self.pack([self.hangar_item(iid, loot, total)])]
            got[cur] = got.get(cur, 0) + amount
            RT.money(self.p, cur, amount, RT.sell_desc(loot), loot, q)              # hesap geçmişi
            self.log('   satıldı: %s x%d = %d %s' % (loot, q, amount, cur))
        with self.p.lock:
            for cur, amount in got.items():
                self.p.d['pilot'][cur] = self.p.d['pilot'].get(cur, 0) + amount
            self.p.dirty = True
        return msgs + self.money_msgs() + [('HangarShipSellItemCommand', dict(errorMessage=None, resultId=1))]

    def sell_drone(self, f):
        """HangarShipSellDroneRequest {droneId}: dron satılır; üstündeki eşyalar ve tasarımı envantere döner. Değer: istemcinin
        "sellable" değeri (kredi; Flax 100.000, Iris 500.000), yoksa o türden son dronun fiyatının satis_orani'si."""
        x = self.p.drone(f.get('droneId') or 0)
        if not x or DRONES[x['lootId']].get('tek'):        # Apis/Zeus satılmaz (istemcide "sellable" yok)
            return [('HangarShipSellDroneCommand', dict(resultId=0, errorMessage=stack_msg('eqt_error_generic'), drones=self.drone_views()))]
        info = DRONES[x['lootId']]
        n = sum(1 for y in self.p.d['dronlar'] if y['lootId'] == x['lootId'])
        amount = int(info['fiyatlar'][min(n, len(info['fiyatlar'])) - 1] * ESYA['satis_orani'])
        cur = info['para']
        if YK.ITEMS.get(x['lootId'], {}).get('satis'):
            cur, amount = 'credits', int(YK.ITEMS[x['lootId']]['satis'])
        with self.p.lock:
            for s in self.p.d['gemiler'].values():
                for c in s.get('dron_konfig', {}).values():
                    c.pop(str(x['kimlik']), None)
            self.p.d['dronlar'].remove(x)
            self.p.d['pilot'][cur] = self.p.d['pilot'].get(cur, 0) + amount
            self.p.sync_ekipman()
            self.p.dirty = True
        RT.money(self.p, cur, amount, 'sell_drone', x['lootId'], 1)
        self.log('   dron satıldı: %s (kimlik %d) = %d %s' % (x['lootId'], x['kimlik'], amount, cur))
        return (self.money_msgs() + [('HangarShipSellDroneCommand', dict(resultId=1, errorMessage=None, drones=self.drone_views()))]
                + self.drone_msgs() + [self.equipment_cmd()] + self.apply_stats())

    @staticmethod
    def stack(key):
        return stack_msg(key)

    def grant_design(self, loot):
        """Gemi tasarımı ödülü: gemi profilde varsa tasarımlarına eklenir -> True; yoksa False (ödül saklanır)."""
        base = design_base(loot)
        sid = next((k for k, s in self.p.d['gemiler'].items() if s['lootId'] == base), None)
        if not sid:
            return False
        with self.p.lock:
            ds = self.p.ship(sid).setdefault('tasarimlar', [])
            if loot not in ds:
                ds.append(loot)
            self.p.dirty = True
        self.log('   tasarım ödülü: %s' % loot)
        return True

    def pending_designs(self, ship_loot):
        """Gemi alındı: saklanan tasarım ödülleri (gemi yokken gelenler) artık verilir."""
        msgs = []
        for loot in [l for l in self.p.d.get('diger_esyalar', {}) if design_base(l) == ship_loot]:
            if self.grant_design(loot):
                self.p.add_resource(loot, -self.p.resource(loot))
                msgs += [('ShipDesignAddedCommand', {'lootId': loot})]
        return msgs

    def auto_buy(self, loot, n):
        """Otomatik alım CPU'su (ALB-X, RB-X): mağaza fiyatıyla sessiz alım -> mesajlar (para yetmezse boş)."""
        return self.buy(loot, n, quick=True) if self.price(loot) else []

    def auto_buy_fail(self, loot, n):
        """Otomatik alım para yetmediği için olmadıysa istemcinin metni (Ö1): 0|ammobuy_fail_uri / _cre ("Ammo purchase failed! Not
        enough Uridium." …; NetConnectionHelper.OnData) -> mesajlar ya da boş."""
        pr = self.buy_price(loot, 1) if self.price(loot) else None
        if not pr or self.p.d['pilot'].get(pr[0], 0) >= math.ceil(pr[1] * n - 1e-9):
            return []
        return [legacy('0|ammobuy_fail_%s' % ('uri' if pr[0] == 'uridium' else 'cre'))]

    def auto_buy_ammo(self, f):
        """HangarShipAutoBuyCpuAmmoRequest: otomatik alım CPU'sunun (ALB-X lazer, RB-X roket) alacağı cephane (profilde) ->
        HangarShipAutoBuyCpuAmmoCommand (istemci envanterdeki eşyanın attachedAmmo'sunu günceller)."""
        iid, ammo = f.get('itemId'), f.get('ammoLootId') or ''
        loot = self.p.d['esyalar'].get(str(iid))
        cfg = EK.X.get(loot, {}).get('oto_alim')
        ok = bool(cfg) and cfg['tur'] in ('lazer', 'roket') and ammo.startswith(
            'ammunition_laser_' if cfg['tur'] == 'lazer' else 'ammunition_rocket_') and bool(self.price(ammo))
        if ok:
            with self.p.lock:
                self.p.d.setdefault('oto_alim_cephane', {})[loot] = ammo
                self.p.dirty = True
            self.log('   otomatik alım: %s -> %s' % (loot, ammo))
        return [('HangarShipAutoBuyCpuAmmoCommand', dict(result=1 if ok else 0, cpuItemId=iid or 0, ammoLootId=ammo,
                                                          errorMessage=None if ok else stack_msg('eqt_error_generic')))]

    def auto_lab(self, item, ore, best=False):
        """Otomatik laboratuvar CPU'su (NC-AWL/AWR/AWB/AGB): yükseltme bitince kargodaki aynı (best: en iyi) cevherle yeniden."""
        opts = LAB['bonuslar'].get(str(item), {})
        if best:
            ore = max((int(t) for t in opts if self.p.ore_count(int(t)) > 0), key=lambda t: opts[str(t)], default=None)
        if ore is None or str(ore) not in opts or self.p.ore_count(ore) <= 0:
            return []
        n = min(self.p.ore_count(ore), 10000)
        self.log('   otomatik yükseltme: parça %d <- %s x%d' % (item, ORES.get(ore), n))
        return self.upgrade({'itemToUpdate': {'itemValue': item}, 'updateWith': {'oreType': {'typeValue': ore}, 'count': n}})

    def quick_buy(self, loot):
        st = self.p.menu_status_cache.get('buy_' + loot, {})
        return self.buy(loot, st.get('counterValue') or (100 if 'rocket' in loot else 1000), quick=True)

    # ------------------------------------------------------------ hangar
    def equipment_cmd(self, sid=None):
        ship = self.p.ship(sid)
        t = copy(self.equip_tpl)
        t.pop('_m', None)
        cur = ship['aktif_konfig']
        for c in t['shipConfigs']:
            pc = ship['konfigler'].get(str(c['setId']), {})
            for slot in EQUIP_SLOTS:
                c[slot] = list(pc.get(slot, []))
            c['active'] = c['setId'] == cur
        extra = self.capacity('extra', sid)
        t.update(currentConfigId=cur, lootId=ship['lootId'], hangarId=ship['hangarId'], shipId=int(sid or self.p.d['aktif_gemi']),
                 extrasSlotsSize1=extra, extrasSlotsSize2=extra,
                 droneConfigs=[self.drone_config_msg(c['setId'], c['setId'] == cur, sid) for c in t['shipConfigs']],
                 petConfigs=self.pet.config_msgs(cur))
        return ('HangarShipEquipmentCommand', t)

    def drone_config_msg(self, cid, active, sid=None):
        """Bir config'te dronlar ve takılı eşyaları (HangarDroneEquipmentMsg; eşya kimlikleri SingleDroneEquipmentMsg.defaults,
        tasarım ve görünüm design/visual; tasarımlar dronun kendisinde, her config'te aynı)."""
        dc = self.p.drone_config(cid, sid)
        drones = []
        for i, x in enumerate(self.p.d['dronlar']):
            lv = LEVELS[x['seviye'] - 1]
            drones.append(mod('SingleDroneEquipmentMsg', level=x['seviye'], visual=[x['gorunum']] if x.get('gorunum') else [],
                              shieldBouns=lv['kalkan'] * 100, repairValue='', defaults=list(dc.get(str(x['kimlik']), [])),
                              weaponBouns=lv['lazer'] * 100, damageUpgradeLevel=YK.drone_level(x), shieldUpgradeLevel=YK.drone_level(x),
                              design=[x['tasarim']] if x.get('tasarim') else [], shieldEffect=0.0, position=i, droneId=x['kimlik'],
                              damage=0.0, repairType='', weaponEffect=0.0))
        return mod('HangarDroneEquipmentMsg', setId=int(cid), active=active, position=0, setDroneEquipment=drones)

    def drone_views(self):
        """Hangar listesindeki dronlar: sıra, seviye, puan ve bir sonraki seviyenin puanı."""
        out = []
        for i, x in enumerate(self.p.d['dronlar']):
            nxt = LEVELS[min(x['seviye'], len(LEVELS) - 1)]['puan']
            out.append(mod('HangarShipDroneView', position=i, damage=0.0, droneId=x['kimlik'], points=x['puan'], level=x['seviye'],
                           lootId=x['lootId'], nextLevel=nxt, droneTypeId=DRONES[x['lootId']]['tur']))
        return out

    def drone_msgs(self):
        """Uzaydaki dronlar: "0|n|d|<kullanıcı>|<formasyon>|tür|seviye|tasarım|görünüm…" (kayıt: başka oyuncuların dronları;
        tasarım/görünüm istemcinin game.xml tasarım kimlikleri, 0 standart)."""
        ds = self.p.d['dronlar']
        if not ds:
            return []
        look = lambda x, slot: DESIGNS.get(self.p.drone_design(x, slot) or '', {}).get('id', 0)
        body = '|'.join('%d|%d|%d|%d' % (DRONES[x['lootId']]['tur'], x['seviye'], look(x, 'design'), look(x, 'visual')) for x in ds)
        return [legacy('0|n|d|%d|%d|%s' % (self.p.user_id, self.p.d.get('formasyon', 0), body))]

    def inventory_items(self):
        hm = self.p.hangar_map()
        items = [self.hangar_item(int(i), loot, 1, hm.get(int(i), 0)) for i, loot in self.p.d['esyalar'].items()]
        items += [self.hangar_item(self.item_id(loot), loot, n) for loot, n in self.p.d['cephane'].items() if n > 0]
        for m in self.p.d['madenler']:
            loot = ORES.get(m['oreType']['typeValue'])
            if loot and m['count'] > 0:
                items.append(self.hangar_item(self.item_id(loot), loot, m['count']))
        for loot, n in sorted(self.p.d.get('diger_esyalar', {}).items()):   # saklanan kaynaklar (ABR, Schism, anahtar, kupon …)
            if loot.startswith('resource_') and n > 0:
                items.append(self.hangar_item(self.item_id(loot), loot, n))
        return items

    def ships_cmd(self):
        """Hangar listesi: sahip olunan gemiler (etkin olan işaretli), her biri için tasarım listesi, ortak envanter."""
        t = copy(self.ships_tpl)
        t.pop('_m', None)
        sids = sorted(self.p.d['gemiler'], key=int)
        t['ships'] = [mod('HangarShipBriefCommand', isActive=sid == self.p.d['aktif_gemi'], lootId=self.p.ship(sid)['lootId'],
                          shipId=int(sid), isFavorite=bool(self.p.ship(sid).get('favori'))) for sid in sids]
        t['allDesignPack'] = [mod('ShipDesignPack', designList=self.designs(sid)) for sid in sids]
        # InventoryItemPack.items sayısı bayt (en çok 255): envanter 255'lik paketlere bölünür. İstemci hepsini okur
        # (InventoryItemData.RefreshItems: paketler üstünde foreach); 268 eşyalı envanterde liste kodlanamıyordu (canlı 2026-10-19)
        items = self.inventory_items()
        t['items'] = [mod('InventoryItemPack', items=items[i:i + PACK_MAX]) for i in range(0, len(items), PACK_MAX)] or \
            [mod('InventoryItemPack', items=[])]
        t['drones'] = self.drone_views()
        t['petView'] = self.pet.view()
        return ('HangarShipsCommand', t)

    def stats(self, sid=None):
        """Bir geminin etkin config'ine göre gösterilen hız, oyun içi hız, kalkan ve kalkan emme oranı."""
        active = sid is None or str(sid) == self.p.d['aktif_gemi']
        eq = self.p.d['ekipman'] if active else self.p.loadout(sid)
        gens = eq.get('generators', [])
        ship = ESYA['gemiler'].get(self.p.ship(sid)['lootId'])
        display = speed = None
        if ship:
            display = ship['temel_hiz'] + sum(ESYA['hiz_jeneratorleri'].get(g, {}).get('hiz', 0) for g in gens)
            speed = display - ESYA['hiz_farki']
        form = self.p.mods()                                # formasyon + dron tasarımları
        lab = active and self.p.lab_bonus(2)              # motor yükseltmesi (Duranium, Promerium)
        if ship:
            display = int(display * (1 + form.get('hiz', 0)) * (1 + (lab or 0)) * AY.carpan('gemi_hiz'))     # panel: geminin hızı
            if 'ust_hiz' in form:                           # Speed Burst (teknoloji.py): en az bu hız
                display = max(display, int(form['ust_hiz']))
            if 'sabit_hiz' in form:                         # gemi yetenekleri: Travel 450, Fortify 0 (kıpırdamaz)
                display = int(form['sabit_hiz'])
            if 'azami_hiz' in form:                         # yavaşlatma küresi (Barb, The Stinger, Saboteur): en çok bu hız
                display = min(display, int(form['azami_hiz']))
            speed = max(0, display - ESYA['hiz_farki'])
        # (kalkan, emme): gemideki jeneratörler + dronlardakiler (dron seviyesi bonusuyla, wiki: seviye başına +%4)
        kj = ESYA['kalkan_jeneratorleri']
        glv = (self.p.d.get('ekipman_seviye') if active else self.p.loadout_levels(sid) or {}) or {}
        glv = glv.get('generators', [])
        shields = [(kj[g]['kalkan'] * YK.factor(g, glv[i] if i < len(glv) else 0, YK.SHIELD), kj[g]['emme'])
                   for i, g in enumerate(gens) if g in kj]
        ship_gens = len(shields)
        for (x, loots), (dloot, dup, ilv) in zip(self.p.drone_loadout(sid), self.p.drone_levels(sid)):
            # dron seviyesi ve dronun tasarımı (Hercules: o dronun kalkan jeneratörlerine +%15); dronun ve jeneratörün yükseltmesi
            bonus = 1 + LEVELS[x['seviye'] - 1]['kalkan'] + DESIGNS.get(self.p.drone_design(x, 'design') or '', {}).get('dron_kalkan', 0)
            bonus *= YK.factor(dloot, dup, YK.DRONE_SHIELD)
            shields += [(kj[g]['kalkan'] * bonus * YK.factor(g, ilv[j] if j < len(ilv) else 0, YK.SHIELD), kj[g]['emme'])
                        for j, g in enumerate(loots) if g in kj]
        total = sum(k for k, e in shields)
        absorb = sum(k * e for k, e in shields) / total if total else 0.8
        absorb = max(0.0, min(1.0, absorb + form.get('emme', 0)))
        hp = ESYA['gemiler'].get(self.p.ship(sid)['lootId'], {}).get('hp')
        total *= 1 + ((active and self.p.lab_bonus(3)) or 0)     # kalkan yükseltmesi (Duranium, Promerium, Seprom, Osmium)
        # panelin geminin canı ve kalkanı çarpanları; kalkan istemciye 32 bitle gider (AttributeShieldUpdateCommand)
        shield_max = min(AY.I32, int(total * (1 + form.get('kalkan', 0)) * AY.carpan('gemi_kalkan')))
        hp_max = max(1, int(hp * (1 + form.get('can', 0)) * AY.carpan('gemi_can') + form.get('can_mutlak', 0))) if hp else None
        return dict(display=display, speed=speed, shield_max=shield_max, absorb=absorb,
                    lasers=len(eq.get('laser', [])), speed_gens=sum(1 for g in gens if g in ESYA['hiz_jeneratorleri']),
                    shield_gens=ship_gens, hp_max=hp_max)

    def detail_cmd(self, sid=None):
        t = copy(self.detail_tpl)
        t.pop('_m', None)
        sid = str(sid or self.p.d['aktif_gemi'])
        ship, s, c = self.p.ship(sid), self.stats(sid), self.p.d['cephane']
        if sid == self.p.d['aktif_gemi']:
            g = self.p.d['gemi']
            hull = dict(hp=int(g.get('hitPoints', 0)), maxHp=g.get('hitMax', 0), shield=int(g.get('shield', 0)),
                        nano=int(g.get('nanoHull', 0)), maxNano=g.get('maxNanoHull', 0))
        else:
            hp = ESYA['gemiler'].get(ship['lootId'], {}).get('hp', 0)
            gv = ship.get('govde') or {}
            hull = dict(hp=int(gv.get('hitPoints', hp)), maxHp=hp, shield=0, nano=int(gv.get('nanoHull', 0)), maxNano=hp)
        t.update(hull, laserAmmo=sum(n for k, n in c.items() if k.startswith('ammunition_laser_')),
                 rockets=sum(n for k, n in c.items() if k.startswith('ammunition_rocket_')),
                 laserCount=s['lasers'], speedGenerators=s['speed_gens'], shieldGenerators=s['shield_gens'], shipId=int(sid),
                 isActive=sid == self.p.d['aktif_gemi'], isFavorite=bool(ship.get('favori')), lootId='',
                 curDesignLootId=self.p.ship_look(sid), designList=self.designs(sid),
                 repairVouchers=int((self.p.d.get('kapilar') or {}).get('kupon', 0)))      # kapıların onarım kuponları
        if s['display']:
            t['maxSpeed'] = s['display']
        return ('HangarShipDetailCommand', t)

    def apply_stats(self):
        """Etkin gemi/config değişti: hız/kalkan/görünüm güncellemesi (kayıt: AttributeShipSpeedUpdateCommand, ShipExtensionsCommand)."""
        msgs = []
        s = self.stats()
        g = self.p.d['gemi']
        with self.p.lock:
            if s['speed'] is not None and s['speed'] != g.get('speed'):      # 0: Fortify (kıpırdamaz)
                g['speed'] = s['speed']
                self.p.d['gosterilen_hiz'] = s['display']      # girişteki hız şablonu da bunu kullanır (profil.patch_template)
                msgs.append(('AttributeShipSpeedUpdateCommand', {'newSpeed': s['speed'], 'displaySpeed': s['display']}))
            if s['hp_max'] and s['hp_max'] != g.get('hitMax'):
                g['hitMax'] = s['hp_max']                      # formasyonun can bonusu/cezası (Heart, Moth, Diamond …)
                g['hitPoints'] = min(g.get('hitPoints', 0), s['hp_max'])
                msgs.append(('HitpointInfoCommand', dict(hitpoints=int(g['hitPoints']), hitpointsMax=g['hitMax'],
                                                         nanoHull=int(g.get('nanoHull', 0)), nanoHullMax=g.get('maxNanoHull', 0))))
            if s['shield_max'] != g.get('shieldMax', 0):
                g['shieldMax'] = s['shield_max']
                g['shield'] = min(g.get('shield', 0), s['shield_max'])
                msgs.append(('AttributeShieldUpdateCommand', {'shieldNow': int(g['shield']), 'shieldMax': g['shieldMax']}))
            self.p.d['kalkan_emme'] = s['absorb']
            # kargo alanı: geminin kargosu + Logistics yeteneği (yetenek.py); ShipInitializationCommand'da görünür
            base = ESYA['gemiler'].get(self.p.ship()['lootId'], {}).get('kargo')
            if base:
                cargo = int(base * (1 + self.p.mods().get('kargo_alani', 0)) * EK.cargo_factor(self.p)    # + kargo CPU'su
                            * (1 + (self.pet.proto('kargo') if self.pet.owned else 0))      # + AI-CR (P.E.T. uzayda olmasa da)
                            * AY.carpan('kargo'))                                       # panel: kargo kapasitesi
                if cargo != g.get('cargoSpaceMax'):
                    g['cargoSpaceMax'] = cargo
                    self.p.sync_cargo()
                    # istemci (UpdateCargoSpaceCommandHandler: Hero.MaxCargo) yeni azamiyi yoksa harita değişimine dek görmüyordu (Ö1)
                    msgs.append(('UpdateCargoSpaceCommand', {'cargoSpaceMax': cargo}))
            # görünüm: lazer sayısına göre 1-3 (kayıt: 1 lazer -> 1, 2 lazer -> 2). ShipInitializationCommand.expansionStage
            # kayıtta 1'de kaldı, yalnız ShipExtensionsCommand değişti; bu yüzden ayrı tutulur (login_msgs girişte yeniden gönderir)
            mm = self.module_update()                          # gemi modüllerinin simgeleri
            if mm[1] != self.p.d.get('modul_simgeleri'):
                self.p.d['modul_simgeleri'] = mm[1]
                msgs.append(mm)
            stage = self.extension_stage()
            if stage != self.p.d.get('uzanti_asamasi', 1):
                self.p.d['uzanti_asamasi'] = stage
                msgs.append(('ShipExtensionsCommand', {'userId': self.p.user_id, 'extensionStage': stage}))
            self.p.dirty = True
        return msgs + self.p.menu_changes()                    # CPU'lar, Smart Bomb, fırlatıcı, yetenekler (canlı test H21)

    def module_update(self):
        """Etkin geminin modül yuvaları ve takılı modüllerin türleri (ShipUpgradeModuleUpdateCommand; kayıtta girişte max 3, boş)."""
        ids = self.p.config().get('upgrades', [])
        types = [MODULE_TYPE_IDS.get(GM.M.get(self.p.d['esyalar'].get(str(i), ''), {}).get('tur'), 1) for i in ids
                 if str(i) in self.p.d['esyalar']]
        return ('ShipUpgradeModuleUpdateCommand', dict(max=self.capacity('upgrades'), moduleTypeIds=types, uid=self.p.user_id))

    def extension_stage(self):
        n = len(self.p.d['ekipman'].get('laser', []))
        return max(1, min(3, math.ceil(3 * n / max(self.capacity('laser'), 1))))

    def login_msgs(self):
        """Harita yüklendikten sonra: ekipmana bağlı görünüm (kayıttaki giriş 1 ile gelir), dronlar ve eşya sayaçları."""
        stage = self.p.d.get('uzanti_asamasi', 1)
        msgs = [('ShipExtensionsCommand', {'userId': self.p.user_id, 'extensionStage': stage})] if stage != 1 else []
        import yukseltme as YK
        counts = self.count_msgs()
        disc = [('UserInventoryModule', dict(activePremiumDiscount=0, activeRebateSubDiscount=0,
                                             inventoryItemModules=[f['item'] for n, f in counts],
                                             activeHappyUpgradeDiscount=int(round(YK.bonus_hour() * 100))))] if YK.bonus_hour() else []
        return msgs + self.drone_msgs() + counts + disc        # Upgrade Hour sürüyorsa indirim (H40)

    def count_msgs(self):
        """Girişte istemcinin eşya sayaçları (InventoryItemUpdatedCommand): Assembly malzemeleri buradan sayılır; kayıttaki girişte
        yalnız dört kaynak vardı, para ve öteki malzemeler 0 görünüyordu (canlı test H33). Para, tariflerde geçen eldeki eşyalar, depodaki
        bütün kaynaklar (yükseltme/atlama/Update/Synthesis bedelleri: ABR, Diametrion, Isochronate, Horizon Shard …; yalnız Assembly
        tarifleri sayılınca bunlar 0 görünüyordu, canlı test H59) ve ekipman örnekleri."""
        import assembly as ASM
        import envanter as INV
        held = {k for k, v in self.p.d.get('diger_esyalar', {}).items() if v > 0 and k.startswith('resource_')}
        loots = ['currency_credits', 'currency_uridium'] + sorted((ASM.INGREDIENTS | held) - {'currency_credits', 'currency_uridium'})
        out = []
        for loot in loots:
            if loot.startswith(('equipment_', 'drone_', 'recipe_')):
                continue                        # örnekli eşyalar hangar envanterinden (HangarShipsCommand)
            n = INV.client_count(self.p, loot)  # gemiler (Plus tariflerinin taban gemisi) dahil
            if n > 0 or loot.startswith('currency_'):
                out.append(self.inv_item(self.item_id(loot), loot, n))
        # eşya örnekleri (seviye, takılı olduğu hangar): Assembly'nin Upgrade/Disassembly sekmeleri yalnız bunları tanıyor (H38)
        hm = self.p.hangar_map()
        for iid, loot in sorted(self.p.d['esyalar'].items(), key=lambda kv: int(kv[0])):
            if loot.startswith(('equipment_', 'drone_designs_', 'pet_designs_')):
                out.append(self.inv_item(int(iid), loot, 1, hm.get(int(iid), 0)))
        return out

    def ship_count_msgs(self, loots):
        """Gemi kazanılınca/harcanınca Assembly sayacı (yalnız tariflerde taban gemi olanlar; envanter.client_count)."""
        import assembly as ASM
        import envanter as INV
        return [self.inv_item(self.item_id(l), l, INV.client_count(self.p, l)) for l in sorted(set(loots)) if l in ASM.INGREDIENTS]

    def change_formation(self, loot):
        """Kısayol çubuğundan formasyon (MenuActionRequest drone_formation_*): DroneFormationChangeCommand, çubukta seçili öğe,
        uzaydaki dizilim ve formasyonun bonuslarıyla hız/kalkan/can."""
        if loot != 'drone_formation_default' and loot not in self.p.d['formasyonlar']:
            self.log('   formasyon yok: %s' % loot)
            return []
        old = self.p.d.get('formasyon', 0)
        new = FORMS[loot]['id']
        if old == new:
            return []
        with self.p.lock:
            self.p.d['formasyon'] = new
            self.p.dirty = True
        msgs = [('DroneFormationChangeCommand', {'uid': self.p.user_id, 'selectedFormationId': new})]
        for k, v in FORMS.items():
            if v['id'] in (old, new):
                st = self.p.menu_status(k)
                if st:
                    msgs.append(('MenuItemStatusCommand', st))
        msgs += self.drone_msgs() + self.apply_stats()
        self.log('   formasyon: %s (%d)' % (loot, new))
        self.p.ach('formation', dron=len(self.p.d['dronlar']))
        return msgs

    def favourite(self, f):
        """HangarShipFavouriteRequest {favourite, shipId}: hangarda yıldız. İstemci gemi ışınlamada yalnız favorileri listeler ("You can
        only Warp ships that are marked as your favorites!"). resultId 1 başarı (HangarShipFavouriteCommandHandler; canlı deneme
        2026-10-17: istek hiç işlenmiyordu)."""
        sid = str(f.get('shipId'))
        if sid not in self.p.d['gemiler']:
            return [('HangarShipFavouriteCommand', {'resultId': 0, 'errorMessage': stack_msg('eqt_error_generic')})]
        with self.p.lock:
            self.p.d['gemiler'][sid]['favori'] = bool(f.get('favourite'))
            self.p.dirty = True
        self.log('   hangar: %s favori %s' % (self.p.ship(sid)['lootId'], 'evet' if f.get('favourite') else 'hayır'))
        return [('HangarShipFavouriteCommand', {'resultId': 1, 'errorMessage': None}), self.ships_cmd()]

    def clear_config(self, f):
        """HangarShipClearConfigRequest {wipe, configId, shipId}: config'teki bütün eşyalar envantere (gemi yuvaları; wipe ise dronlar
        ve P.E.T. de). İstemci başarıda (resultId 1) donanımı yeniden ister (HangarShipClearConfigCommandHandler)."""
        sid = self.ship_sid(f.get('shipId'))
        ship = self.p.ship(sid)
        cid = str(f.get('configId')) if str(f.get('configId')) in ship['konfigler'] else str(ship['aktif_konfig'])
        ids = [i for lst in self.p.config(cid, sid).values() for i in lst]
        if f.get('wipe'):
            ids += [i for lst in self.p.drone_config(cid, sid).values() for i in lst]
            if self.pet.owned:
                ids += [i for lst in self.pet.config(cid).values() for i in lst]
        msgs = self.move({'items': ids, 'source': 'ship', 'destination': 'inventory', 'hangarId': ship['hangarId'],
                          'configId': int(cid)}) if ids else []
        self.log('   hangar: %s config %s temizlendi (%d eşya)' % (ship['lootId'], cid, len(ids)))
        return [('HangarShipClearConfigCommand', {'resultId': 1, 'errorMessage': None})] +             [m for m in msgs if m[0] != 'HangarShipMoveItemsCommand']

    # İstemcinin metinleri: "Saves the equipment equipped on both configuration 1 and 2 for this ship." / "Load the equipment saved …" /
    # "Transfer this ship's configuration and equipment to another ship with the same number of slots!" (canlı deneme 2026-10-17:
    # üçü de işlenmiyordu). Kayıt geminin profilinde: kayitli_konfig {config: {yuva: [eşya]}}.
    def save_config(self, f):
        sid = self.ship_sid(f.get('shipId'))
        with self.p.lock:
            ship = self.p.d['gemiler'][sid]
            ship['kayitli_konfig'] = {c: {s: list(v) for s, v in cfg.items()} for c, cfg in ship['konfigler'].items()}
            self.p.dirty = True
        self.log('   hangar: %s config kaydedildi' % self.p.ship(sid)['lootId'])
        return [('HangarShipSaveConfigCommand', {'title': stack_msg('popup_save_success_title'),
                                                 'description': stack_msg('popup_save_success_description'), 'resultId': 1})]

    def load_config(self, f):
        """Kaydı geri takar: önce iki config'in gemi yuvaları boşalır; kayıttaki eşya artık yoksa (satıldı) ya da başka gemide
        takılıysa atlanır ("Some equipment were not available …")."""
        sid = self.ship_sid(f.get('shipId'))
        ship = self.p.ship(sid)
        saved = ship.get('kayitli_konfig')
        if not saved:
            return [('HangarShipLoadConfigCommand', {'title': stack_msg('eqt_error_generic'), 'description': stack_msg('empty'),
                                                     'resultId': 0})]
        missing = 0
        with self.p.lock:
            for c, cfg in ship['konfigler'].items():
                for s in cfg:
                    cfg[s] = []
            busy = self.p.hangar_map()
            for c, slots in saved.items():
                cfg = ship['konfigler'].setdefault(c, {})
                for s, ids in slots.items():
                    for i in ids:
                        if str(i) in self.p.d['esyalar'] and busy.get(i, ship['hangarId']) == ship['hangarId']                                 and len(cfg.get(s, [])) < self.capacity(s, sid):
                            cfg.setdefault(s, []).append(i)
                        else:
                            missing += 1
            self.p.dirty = True
            self.p.sync_ekipman()
        self.log('   hangar: %s config yüklendi (%d eşya bulunamadı)' % (ship['lootId'], missing))
        desc = mod('BaseStackCommand', type=0, enumBaseKey=0, argsList=[],
                   stringBasekey='Some equipment were not available to be loaded into the saved configuration.') if missing             else stack_msg('popup_load_success_description')
        msgs = [('HangarShipLoadConfigCommand', {'title': stack_msg('popup_load_success_title'), 'description': desc, 'resultId': 1}),
                self.equipment_cmd(sid)]
        return msgs + (self.apply_stats() if sid == self.p.d['aktif_gemi'] else [])

    def import_config(self, f):
        """Transfer System: kaynak geminin iki config'indeki eşyalar hedef gemiye taşınır (hedefin eşyaları envantere). Hedefin her
        yuvası kaynaktaki eşya sayısını almalı."""
        src, dst = str(f.get('originShipId')), str(f.get('targetShipId'))
        fail = lambda: [('HangarShipImportConfigCommand', {'shipId': int(dst) if dst.isdigit() else 0,
                                                           'errorMessage': stack_msg('error_can_not_equip_to_slot'), 'resultId': 0})]
        if src == dst or src not in self.p.d['gemiler'] or dst not in self.p.d['gemiler']:
            return fail()
        a, b = self.p.ship(src), self.p.ship(dst)
        for c, cfg in a['konfigler'].items():
            for s, ids in cfg.items():
                if len(ids) > self.capacity(s, dst):
                    self.log('   hangar: aktarım yok: %s %s yuvası %d > %d' % (b['lootId'], s, len(ids), self.capacity(s, dst)))
                    return fail()
        with self.p.lock:
            for c, cfg in a['konfigler'].items():
                b['konfigler'][c] = {s: list(ids) for s, ids in cfg.items()}
                for s in cfg:
                    cfg[s] = []
            self.p.dirty = True
            self.p.sync_ekipman()
        self.log('   hangar: config %s -> %s aktarıldı' % (a['lootId'], b['lootId']))
        msgs = [('HangarShipImportConfigCommand', {'shipId': int(dst), 'errorMessage': None, 'resultId': 1}), self.equipment_cmd(dst)]
        return msgs + (self.apply_stats() if self.p.d['aktif_gemi'] in (src, dst) else [])

    def move(self, f):
        """Takma/çıkarma: istekteki hangarId hangi geminin, configId hangi config'in olduğunu söyler. Hedef/kaynak "ship",
        "inventory", "drone" (+ droneId; lazer/jeneratör "default", tasarım "design", görünüm "visual") ya da "pet" (yuva kümesi
        lasers/generators/gears/protocols; yuvayı eşyanın türü belirler)."""
        ids = [int(x) for x in f.get('items', [])]
        src, dst = (f.get('source') or '').lower(), (f.get('destination') or '').lower()
        sid = self.p.ship_by_hangar(f.get('hangarId')) or self.p.d['aktif_gemi']
        ship = self.p.ship(sid)
        cid = f.get('configId') if str(f.get('configId')) in ship['konfigler'] else ship['aktif_konfig']
        active = sid == self.p.d['aktif_gemi'] and str(cid) == str(ship['aktif_konfig'])
        to_inv = dst in INVENTORY
        drone = self.p.drone(f.get('droneId') or 0) if dst == 'drone' else None
        moved, err = [], None
        with self.p.lock:
            cfg = self.p.config(cid, sid)
            dcfg = self.p.drone_config(cid, sid)
            pcfg = self.pet.config(cid) if self.pet.owned else {}
            pet_before = {k: list(v) for k, v in pcfg.items()}
            busy = self.p.hangar_map()

            def detach(iid):
                """Eşyayı bu config'te bulunduğu yerden (gemi yuvası, dron, P.E.T.) ya da dronun tasarım yuvasından çıkarır."""
                for lst in list(cfg.values()) + list(dcfg.values()) + list(pcfg.values()):
                    if iid in lst:
                        lst.remove(iid)
                        return True
                for x in self.p.d['dronlar']:
                    for k in ('tasarim', 'gorunum'):
                        if x.get(k) == iid:
                            x[k] = None
                            return True
                return False

            def fail(why):
                nonlocal err
                err = err or 'error_can_not_equip_to_slot'
                self.log('   hangar: %s' % why)

            for iid in ids:
                loot = self.p.d['esyalar'].get(str(iid)) or ''
                slot = slot_of(loot)
                if not loot:
                    fail('bilinmeyen eşya %s' % iid)
                elif to_inv:
                    if detach(iid):
                        moved.append((iid, loot))
                elif pet_only(loot) and dst != 'pet':
                    fail('%s yalnız P.E.T.\'e takılır' % loot)
                elif loot in DESIGNS:
                    # dron tasarımı: dronun "design" ya da "visual" yuvası (eşyanın türüne göre); eskisi envantere döner
                    if dst != 'drone' or not drone:
                        fail('%s yalnız drona takılır (%r)' % (loot, dst))
                        continue
                    key = 'tasarim' if DESIGNS[loot]['yuva'] == 'design' else 'gorunum'
                    old = drone.get(key)
                    if old == iid:
                        continue
                    detach(iid)
                    drone[key] = iid
                    moved.append((iid, loot))
                    if old:
                        moved.append((old, self.p.d['esyalar'].get(str(old), '')))
                elif dst == 'pet':
                    pslot = PETM.slot_for(loot)
                    if (f.get('slotSet') or '').lower() == 'heat' and PETM.heat_slot_ok(loot):
                        pslot = 'heat'                    # HEAT yuvası: lazer ya da kalkan jeneratörü (HEAT seviyesi 4'ten etkin)
                    if not self.pet.owned or not pslot:
                        fail("%s P.E.T.'e takılamaz" % loot)
                        continue
                    lst = pcfg[pslot]
                    if iid in lst:
                        continue
                    if pslot == 'visual' and lst:         # tek görünüm yuvası: eskisi envantere döner
                        old = lst.pop()
                        moved.append((old, self.p.d['esyalar'].get(str(old), '')))
                    if busy.get(iid, ship['hangarId']) != ship['hangarId']:
                        fail('%s başka gemide takılı' % loot)
                    elif len(lst) >= self.pet.open_slots(pslot):
                        fail('P.E.T. %s yuvaları dolu (%d)' % (pslot, self.pet.open_slots(pslot)))
                    elif pslot in PETM.UNIQUE and loot in [self.p.d['esyalar'].get(str(i)) for i in lst]:
                        fail('%s zaten takılı' % loot)
                    elif self.pet.d['seviye'] < PETM.level_need(self.p.item_level(iid)):
                        fail('%s seviye %d: P.E.T. seviyesi %d gerekir' % (loot, self.p.item_level(iid),
                                                                           PETM.level_need(self.p.item_level(iid))))
                        err = 'pet_gear_requirement'
                    else:
                        detach(iid)
                        lst.append(iid)
                        moved.append((iid, loot))
                elif not slot:
                    fail('%s buraya takılamaz (%r)' % (loot, dst))
                elif dst == 'drone':
                    lst = dcfg.setdefault(str(drone['kimlik']), []) if drone else None
                    if lst is not None and iid in lst:
                        continue
                    if not drone or not loot.startswith(DRONE_ITEMS):
                        fail('%s drona takılamaz (dron %s)' % (loot, f.get('droneId')))   # dronlara yalnız lazer ve kalkan jeneratörü
                    elif busy.get(iid, ship['hangarId']) != ship['hangarId'] or len(lst) >= DRONES[drone['lootId']]['yuva']:
                        fail('dron %s dolu ya da eşya başka gemide' % f.get('droneId'))
                    else:
                        detach(iid)
                        lst.append(iid)
                        moved.append((iid, loot))
                elif dst in PANELS and PANELS[dst] in (None, slot):
                    lst = cfg.setdefault(slot, [])
                    if iid in lst:
                        continue
                    if busy.get(iid, ship['hangarId']) != ship['hangarId']:
                        fail('%s başka gemide takılı' % loot)
                    elif slot == 'upgrades' and not GM.equip_allowed(loot, ship['lootId']):
                        fail('%s bu gemiye takılmaz (%s)' % (loot, ship['lootId']))      # modülün açıklamasındaki gemiler
                    elif slot == 'QuantumFluidCore' and QF.equip_allowed(self.p, iid, ship['lootId'], lst):
                        fail('%s: %s' % (loot, QF.equip_allowed(self.p, iid, ship['lootId'], lst)))     # bağlı gemi, AX/DF birer
                    elif slot in PC.SLOTS and PC.equip_allowed(self.p, iid, slot, lst):
                        fail('%s: %s' % (loot, PC.equip_allowed(self.p, iid, slot, lst)))               # her türden bir top
                    elif len(lst) >= self.capacity(slot, sid):
                        fail('%s yuvaları dolu' % slot)
                    else:
                        detach(iid)                                       # dronda ya da P.E.T.'te takılıysa oradan alınır
                        lst.append(iid)
                        moved.append((iid, loot))
                else:
                    fail('bilinmeyen panel %r -> %r' % (src, dst))
            if moved:
                self.p.dirty = True
                self.p.sync_ekipman()
            pet_changed = {k: list(v) for k, v in pcfg.items()} != pet_before
        where = ' (dron %s%s)' % (f.get('droneId'), ' ' + f['slotSet'] if f.get('slotSet') else '') if 'drone' in (src, dst) else ''
        self.log('   hangar %s config %s: %s %s -> %s%s%s' % (ship['lootId'], cid, ', '.join(l.rsplit('_', 1)[-1] for i, l in moved) or '-',
                                                            src, dst, where, ' (hata: %s)' % err if err else ''))
        ok = bool(moved) or not err
        msgs = [('HangarShipMoveItemsCommand', {'result': 1 if ok else 0, 'errorMessage': None if ok else stack_msg(err)})]
        if moved:
            hm = self.p.hangar_map()
            msgs += [self.inv_item(i, l, 1, hm.get(i, 0)) for i, l in moved]
            msgs.append(self.equipment_cmd(sid))
            # istemcinin envanter ızgarası bu paketle yenilenir (kayıt: takmadan sonra o yuvanın eşyaları hangarId ile)
            slots = {slot_of(l) for i, l in moved}
            group = [i for c in ship['konfigler'].values() for s in slots for i in c.get(s, [])]
            group += [i for c in ship.get('dron_konfig', {}).values() for ids_ in c.values() for i in ids_]
            group += [x[k] for x in self.p.d['dronlar'] for k in ('tasarim', 'gorunum') if x.get(k)]
            if self.pet.owned:
                group += [i for c in self.pet.d['konfig'].values() for ids_ in c.values() for i in ids_]
            items = list(dict.fromkeys([i for i, l in moved] + group))
            msgs.append(self.pack([self.hangar_item(i, self.p.d['esyalar'][str(i)], 1, hm.get(i, 0)) for i in items]))
            designs = any(l in DESIGNS for i, l in moved)
            if active or designs:
                msgs += self.apply_stats()
            if designs:
                msgs += self.drone_msgs()                  # uzaydaki dronların görünümü
            if pet_changed:
                # uzaydaki P.E.T.'in dişlileri ve değerleri: yalnız P.E.T.'in donanımı değişince (gemiye lazer/jeneratör takmak da
                # P.E.T. yuvası türünden sayılıyordu, her seferinde seviye atlama efekti çıkıyordu)
                msgs += self.pet.refresh()
        return msgs

    # ------------------------------------------------------------ gemi değiştirme ve config geçişi
    def activate(self, f, in_station=True):
        """HangarShipActivateShipRequest {shipId} -> HangarShipActivateShipCommand (istemci: result 1 başarı, mesaj penceresi).
        Oyundaki gibi yalnız istasyonda. Başarılıysa (mesajlar, True): oturum gemiyi yeniden yükletir (ShipInitializationCommand)."""
        sid = str(f.get('shipId'))
        reply = lambda res, err=None, ok=None: ('HangarShipActivateShipCommand', {
            'errorMessage': err, 'successMessage': ok, 'currentShipLootId': self.p.ship()['lootId'], 'result': res})
        if sid not in self.p.d['gemiler']:
            return [reply(0, stack_msg('eqt_error_generic'))], False
        if sid == self.p.d['aktif_gemi']:
            return [reply(1, ok=stack_msg('info_text_switch_active_hangar_success'))], False
        if not in_station:
            self.log('   gemi değişmedi: istasyonda değil')
            return [reply(0, stack_msg('info_text_switch_hangar_station_only'))], False
        with self.p.lock:
            g = self.p.d['gemi']
            self.p.ship()['govde'] = {'hitPoints': int(g.get('hitPoints', 0)), 'nanoHull': int(g.get('nanoHull', 0))}
            old = self.p.ship()['lootId']
            self.p.d['aktif_gemi'] = sid
            new = self.p.ship()
            row = ESYA['gemiler'].get(new['lootId'], {})
            hp = row.get('hp', g.get('hitMax', 0))
            gv = new.get('govde') or {'hitPoints': hp, 'nanoHull': 0}
            cargo = row.get('kargo', g.get('cargoSpaceMax', 0))
            g.update(typeId=self.p.ship_look(sid), hitMax=hp, maxNanoHull=hp, hitPoints=min(gv['hitPoints'], hp), nanoHull=gv['nanoHull'],
                     cargoSpaceMax=cargo)
            self.p.sync_cargo()                                    # boş alan = yeni geminin kargosu - cevherler
            self.p.sync_ekipman()
            self.p.dirty = True
        self.apply_stats()
        self.log('   gemi değişti: %s -> %s (shipId %s)' % (old, new['lootId'], sid))
        return [reply(1, ok=stack_msg('info_text_switch_active_hangar_success'))], True

    def designs(self, sid=None):
        """Hangardaki tasarım listesi (açılır menü): geminin kendi görünümü + satın alınan tasarımlar."""
        s = self.p.ship(sid)
        return [s['lootId']] + list(s.get('tasarimlar', []))

    def change_model(self, f):
        """HangarShipChangeShipModelRequest {shipId, lootId} (hangardaki tasarım menüsü, UINewHangarSystem.DropdownValueChanged)
        -> HangarShipChangeShipModelCommand {resultId 1}. Etkin gemide görünüm değişince (mesajlar, True): oturum gemiyi yeniden
        yükletir (ShipInitializationCommand.typeId = tasarım)."""
        sid = str(f.get('shipId'))
        loot = f.get('lootId', '')
        reply = lambda res, err=None: ('HangarShipChangeShipModelCommand', {'resultId': res, 'errorMessage': err})
        if sid not in self.p.d['gemiler']:
            return [reply(0, stack_msg('dse_ship_not_exist'))], False
        if loot not in self.designs(sid):
            self.log('   tasarım yok: %s (%s)' % (loot, self.p.ship(sid)['lootId']))
            return [reply(0, stack_msg('eqt_error_generic'))], False
        with self.p.lock:
            ship = self.p.ship(sid)
            old = self.p.ship_look(sid)
            ship['tasarim'] = None if loot == ship['lootId'] else loot
            active = sid == self.p.d['aktif_gemi']
            if active:
                self.p.d['gemi']['typeId'] = self.p.ship_look(sid)
            self.p.dirty = True
        self.log('   görünüm: %s -> %s' % (old, self.p.ship_look(sid)))
        return [reply(1)], active and old != self.p.ship_look(sid)

    def switch_config(self, n):
        """İstemcinin "S|CFG|n|…" isteği (kayıt: t≈591 ve 598). Yanıt kayıttaki sırayla: arayüz yenileme, görünüm, can;
        kalkan, 0|n|e, görünüm, 0|n|INV, 0|S|CFG|n; hız."""
        ship = self.p.ship()
        n = int(n)
        if str(n) not in ship['konfigler']:
            return []
        now = time.time()
        if now - getattr(self, 'last_config', 0) < CONFIG_COOLDOWN_SN:       # kayıt: 2,4 sn sonraki ikinci geçiş reddedildi
            self.log('   config geçişi bekliyor')
            return [legacy('0|A|STM|config_change_failed_time')]
        self.last_config = now
        with self.p.lock:
            ship['aktif_konfig'] = n
            self.p.sync_ekipman()
            self.p.dirty = True
        self.apply_stats()
        g, uid = self.p.d['gemi'], self.p.user_id
        stage = ('ShipExtensionsCommand', {'userId': uid, 'extensionStage': self.p.d.get('uzanti_asamasi', 1)})
        s = self.stats()
        msgs = [('RefreshSelectedUICategoryCommand', {}), stage,
                ('HitpointInfoCommand', dict(hitpoints=int(g.get('hitPoints', 0)), hitpointsMax=g.get('hitMax', 0),
                                             nanoHull=int(g.get('nanoHull', 0)), nanoHullMax=g.get('maxNanoHull', 0))),
                ('AttributeShieldUpdateCommand', {'shieldNow': int(g.get('shield', 0)), 'shieldMax': g.get('shieldMax', 0)}),
                legacy('0|n|e|%d|0|0' % uid), stage, legacy('0|n|INV|%d|0' % uid), legacy('0|S|CFG|%d' % n)]
        if s['speed'] is not None:
            msgs.append(('AttributeShipSpeedUpdateCommand', {'newSpeed': s['speed'], 'displaySpeed': s['display']}))
        self.log('   config %d: %s' % (n, ', '.join('%s %d' % (k, len(v)) for k, v in self.p.d['ekipman'].items() if v)))
        return msgs
