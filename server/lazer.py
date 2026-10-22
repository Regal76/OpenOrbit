"""Lazerlerin özel nitelikleri (veri esyalar.json "lazerler" ← belgeler/wiki/lasers_ammo.md). Set bonusları ve adede bağlı etkiler yalnız
gemideki lazerleri sayar (dronlardakiler sayılmaz; wiki "ship only").

  hasar_aralik      [en az, en çok]: her isabette rastgele (Unstable LF-4 128-220; dağılım bilinmiyor, düzgün alındı)
  uzayli_bonus      uzaylılara oransal bonus (LF-3 +%15)
  uzayli_ek         uzaylılara düz ek hasar (LF-4 Paritydrill "+5 PvE"; wiki yüzde mi düz mü demiyor, düz alındı)
  hedef_carpan      {ad: çarpan}: adı eşleşen uzaylıya bu lazerin hasarı (Prometheus x3,5 Black Light uzaylılarına, AA-1/AAP-1
                    yapay zekâ gemilerine: Mimesis)
  ek_hasar_5sn      5 sn'de bir sonraki isabete düz ek, lazer başına (SL-01 +38, SL-02 +75, SL-03 +150, Prometheus +200)
  menzil            lazer menzili değişimi (SL-01/02/03 -%25; gemide bir tane bile varsa)
  can_lazer_basina  gemideki her biri için can bonusu (LF-4 Hyperplasmoid +%0,5)                         profil.ship_mods
  set_bonus         gemideki adede göre hasar bonusu (adet-1 sırası; sonrası son değer) (LF-5 Mortifier, Asmodeus)
  ofke              Asmodeus "Fervor": uzaylı öldürdükçe basamak (en çok 5); ilk öldürmeden sonra ilk_sn, sonra sonraki_sn
                    içinde yeni öldürme gelmezse sıfırlanır
  kritik            {lazer_basina, set_esik, set, azami, carpan}: Odysseus kritik vuruş şansı ve ek hasarı (lazerin hasarı x carpan)
  yavaslatma        [[adet, şans, yavaşlatma, sn]]: gemideki adede göre isabette uzaylıyı yavaşlatma (LF-5 Anchorlock)
  pvp_hasar, pvp_ek, pvp_set   oyunculara (bot oyuncular gelince; MP-1, SLL, Magmadrill, Anchorlock)
"""
import json, os, random, re

HERE = os.path.dirname(os.path.abspath(__file__))
LZ = json.load(open(os.path.join(HERE, 'data', 'esyalar.json'), encoding='utf8'))['lazerler']
OVERDRIVE_SN = 5.0


def name_match(table, target):
    """{ad: çarpan} tablosunda hedefin adına uyan ilk çarpan (kelime sınırıyla: Sibelon, Sibelonit'e uymaz; büyük/küçük harf
    ayrımsız: Demaner, demaNeR'e uyar) ya da None."""
    if target is None:
        return None
    for ad, c in table.items():
        if re.search(r'(?<![A-Za-z])%s(?![A-Za-z])' % re.escape(ad), target.d['ad'], re.I):
            return c
    return None


def hit(loot, target=None):
    """Bir lazerin uzaylıya isabet hasarı (cephane ve formasyon çarpanından önce)."""
    d = LZ[loot]
    h = random.randint(*d['hasar_aralik']) if 'hasar_aralik' in d else d['hasar']
    h = h * (1 + d.get('uzayli_bonus', 0)) + d.get('uzayli_ek', 0)
    c = name_match(d.get('hedef_carpan', {}), target)
    return h * c if c else h


def _table(tab, n):
    return tab[min(n, len(tab)) - 1] if n > 0 else 0


def set_bonus(ship):
    return sum(_table(LZ[l]['set_bonus'], ship.count(l)) for l in set(ship) if 'set_bonus' in LZ.get(l, {}))


def crit_chance(ship):
    out = 0.0
    for l in set(ship):
        k = LZ.get(l, {}).get('kritik')
        if k:
            n = ship.count(l)
            out = max(out, min(k['azami'], n * k['lazer_basina'] + (k['set'] if n >= k['set_esik'] else 0)))
    return out


def crit_damage(ship):
    return sum(LZ[l]['hasar'] * LZ[l]['kritik']['carpan'] for l in ship if 'kritik' in LZ.get(l, {}))


def overdrive(ship):
    return sum(LZ[l].get('ek_hasar_5sn', 0) for l in ship if l in LZ)


def range_factor(ship):
    return 1 + min((LZ[l].get('menzil', 0) for l in ship if l in LZ), default=0)


def hp_bonus(ship):
    return sum(LZ[l].get('can_lazer_basina', 0) for l in ship if l in LZ)


def slow_proc(ship):
    """LF-5 Anchorlock: gemideki adede göre -> (şans, yavaşlatma, sn) ya da None."""
    best = None
    for l in set(ship):
        n = ship.count(l)
        for adet, sans, yv, sn in LZ.get(l, {}).get('yavaslatma', []):
            if n >= adet:
                best = (sans, yv, sn)
    return best


def _fervor_cfg(ship):
    return next((LZ[l]['ofke'] for l in ship if 'ofke' in LZ.get(l, {})), None)


class Ofke:
    """Asmodeus "Fervor" basamağı (dünya başına; haritadan çıkınca sıfırlanır)."""

    def __init__(self):
        self.level, self.until = 0, 0.0

    def kill(self, ship, now):
        cfg = _fervor_cfg(ship)
        if not cfg:
            return
        if now >= self.until:
            self.level = 0
        self.level = min(len(cfg['basamak']), self.level + 1)
        self.until = now + (cfg['ilk_sn'] if self.level == 1 else cfg['sonraki_sn'])

    def bonus(self, ship, now):
        cfg = _fervor_cfg(ship)
        if not cfg or now >= self.until:
            self.level = 0
            return 0.0
        return sum(cfg['basamak'][:self.level])
