"""Anahtarlı ganimet kutuları (yol haritası Aşama 5; veri data/kutular.json <- tools/kutular.py, wiki + istemcinin adları).

Haritada AddBoxCommand {boxType: PIRATE_BOOTY | PIRATE_BOOTY_GOLD | PIRATE_BOOTY_RED | PIRATE_BOOTY_BLUE | BLACK_BOOTY_BOX |
PIRATE_BOOTY_SILVER | UNSTABLE_BLACKLIGHT_CACHE | BLACKLIGHT-CRYPT | ASTRAL_BOOTY_BOX | ASTRAL_PRIME_BOOTY_BOX | MASQUE_BOOTY_BOX
(Apocalypse) | PERSEUS_BLESSING_BOOTY_BOX | PROMETHEUS_BOOTY_BOX | LAUREL_BOX (son ikisi E8'in etkinliklerinde) | etkinlik kutuları};
toplarken (CollectBoxRequest) türün anahtarı yoksa kutu yerinde
kalır ve istemcinin metni gelir (0|A|STM|msg_loot_failed_no_booty-key-…); varsa bir anahtar harcanır, HUD sayacı güncellenir
("0|A|<kod>|<kalan>"), içerikten bir ödül çekilir (ağırlıkla; sahip olunan gemi/tasarım/dron çekilmez) ve mağazanın ödül işleviyle
verilir. Black Light Cache'teki tasarıma zaten sahipse 10.000 uridyum (wiki). Yeşil anahtar yoksa ve ayarlarda otomatik alım açıksa
(autoBuyGreenBootyKeys) mağaza fiyatıyla bir anahtar alınır.
Haritalar: X-2..X-8 (1-2 … 3-8), X-1..X-8 (Perseus, Laurel), 4-X, 5-X (5-1..5-3), 5-4 (gümüş), BL (BL-1..3). Altın kutular iki
haftada bir cuma (wiki).
"""
import json, os, random, re, time

HERE = os.path.dirname(os.path.abspath(__file__))
K = json.load(open(os.path.join(HERE, 'data', 'kutular.json'), encoding='utf8'))
BOXES = K['kutular']
MAPS = {k: re.compile(v) for k, v in K['haritalar'].items()}
GREEN_KEY = 'resource_booty-key'
BL_CACHE = 'UNSTABLE_BLACKLIGHT_CACHE'
KEYS = {}                                     # anahtar -> onu kullanan ilk kutu türü (HUD kodu için)
for _k, _b in BOXES.items():
    KEYS.setdefault(_b['anahtar'], _k)
CODES = {b['kod']: KEYS[b['anahtar']] for b in BOXES.values() if b.get('kod')}   # HUD kodu -> kutu türü (girişteki "0|A|BKP|0" satırları)


def active(kind, now=None):
    """Takvim (kutunun 'takvim'i takvim.py'deki etkinliğin adı): altın kutu ayın 2. ve 4. cuması, Obsidian / R&B / Apocalypse
    haftalık rotasyonda (E8), etkinlik kutuları (Empyrian, Prosperous, Lucent Egg) etkinlik sürerken; liste: biri sürerken (Battle
    Pass Box)."""
    return bool(BOXES[kind].get('takvim') is None or box_event(kind, now))


def box_event(kind, now=None):
    """Kutunun takvimindeki etkin etkinlik (yoksa None)."""
    import takvim as TK
    cal = BOXES[kind].get('takvim')
    return next((k for k in (cal if isinstance(cal, list) else [cal]) if k in TK.EVENTS and TK.is_active(k, now)), None)


def spawns(map_name, now=None):
    """Bu haritada doğan kutular -> [(tür, adet)]."""
    return [(k, b['adet']) for k, b in BOXES.items()
            if active(k, now) and any(MAPS[m].match(map_name or '') for m in b['haritalar'])]


def respawn_delay(kind):
    lo, hi = BOXES[kind]['yeniden_sn']
    return random.uniform(lo, hi)


def owned(p, loot):
    """Tekil ödüle sahip mi: gemi, gemi tasarımı (gemide ya da depoda), P.E.T. tasarımı ve dronlar (depoda)."""
    if '_design_' in loot:
        if any(loot in s.get('tasarimlar', []) for s in p.d['gemiler'].values()):
            return True
        return p.resource(loot) > 0
    if loot.startswith('ship_'):
        return any(s['lootId'] == loot for s in p.d['gemiler'].values())
    if loot.startswith('drone_'):
        return any(d.get('lootId') == loot for d in p.d.get('dronlar', [])) or p.resource(loot) > 0
    return p.resource(loot) > 0


def unique(loot):
    return loot.startswith(tuple(K['tekil'])) or '_design_' in loot


def pick(p, kind, rng=random):
    """İçerikten bir ödül -> (lootId, adet). Sahip olunan tekil ödüller (gemi, tasarım, dron) çekilmez; 'odul_etkinlik'li kutuda
    (Battle Pass Box) süren etkinliğin satırları."""
    rows = BOXES[kind]['odul'] or BOXES[kind].get('odul_etkinlik', {}).get(box_event(kind)) or []
    if not rows:                             # etkinlik bitmişken toplanan Battle Pass Box: anahtar geri
        return BOXES[kind]['anahtar'], 1
    if kind == BL_CACHE:                     # wiki: tasarım rastgele, zaten varsa 10.000 uridyum
        loot = rng.choice(rows)[0]
        return ('currency_uridium', K['bl_tekrar_uridyum']) if owned(p, loot) else (loot, 1)
    pool = [r for r in rows if not (unique(r[0]) and owned(p, r[0]))] or [r for r in rows if not unique(r[0])]
    loot, amount, _ = rng.choices(pool, [r[2] for r in pool])[0]
    if isinstance(amount, list):
        amount = rng.randint(amount[0], amount[1])
    return loot, int(amount)


def key_line(p, kind):
    """HUD'daki anahtar sayacı (eski protokol: SetAttributeAssemblyHelper.AssembleBootyKeysUpdate); sayacı olmayan anahtarda
    (Echo Key) None."""
    b = BOXES[kind]
    return '0|A|%s|%d' % (b['kod'], p.resource(b['anahtar'])) if b.get('kod') else None
