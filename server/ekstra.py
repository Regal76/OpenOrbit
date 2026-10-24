"""Ekstralar ve CPU'lar (veri esyalar.json "ekstralar" ← belgeler/wiki/extras_cpu_tech.md; yalnız etkin config'te takılı olanlar etkili).

Pasif etkiler (bu modül sorgular, ilgili modüller uygular):
  ek_yuva          ekstra yuvası (SL-01..04 +2/+4/+6/+10; config başına bir yuva CPU'su, o config'in yuvası)    magaza.capacity
  kargo_carpan     kargo alanı çarpanı (G3X-CRGO-X)                                                          magaza.apply_stats
  roket_bekleme    roket beklemesi çarpanı (R0K-T01 0,5)                                                     dunya.rocket
  mayin_bekleme    mayın ve mayından yapılan eşyaların beklemesi (MIN-T01 -%25, MIN-T02 -%50)                dunya (mayınlar)
  oto_onarim       can eksilince onarım robotu kendiliğinden çalışır (NC-RRB-X)                              dunya.auto_tick
  oto_alim         {tur: lazer|roket|yakit, esik, adet}: eşiğin altına inince alır (ALB-X, RB-X, FB-X)       dunya.auto_tick
  oto_lab          [parça]: yükseltme bitince aynı cevherle ya da (en_iyi) en iyi cevherle yeniden (NC-AWL/AWR/AWB/AGB)
  her_yerde_satis  cevher her yerde satılır, adet sınırı (HM-7, 100 satış)                                  dunya.at_trade
Etkin olanlar (kısayol çubuğundan; savas_esya.py):
  atlama           {haritalar | yasak}: ana haritaya atlama (JP-01 10, JP-02 20 hak); gelismis_atlama: AJP-01 istenen haritaya
  gizlenme         gizlenme CPU'su (CL04K-XS 1, M 10, XL 50 hak)       nisan  AIM-01/02 ıska oranı -%25/-%50 (10 Xenomit)
  aninda_kalkan    Insta-Shield (ISH-01)                                akilli_bomba  Smart Bomb (SMB-01)
  oto_roket        AROL-X: lazer saldırısında seçili roket             oto_fircatici  RL-LB1: lazer saldırısında dolu fırlatıcı
Hak (hak): profilde (ekstra_haklari), ilk takılışta tam; satın alınınca eklenir (recharge).
"""
import json, os

HERE = os.path.dirname(os.path.abspath(__file__))
E = json.load(open(os.path.join(HERE, 'data', 'esyalar.json'), encoding='utf8'))
X = E.get('ekstralar', {})


def equipped(p, sid=None):
    """Etkin (ya da verilen) geminin etkin config'indeki ekstraların lootId'leri."""
    if sid is None or str(sid) == str(p.d['aktif_gemi']):
        return list(p.d.get('ekipman', {}).get('extra', []))
    return p.loadout(sid).get('extra', [])


def props(p, key, sid=None):
    """Takılı ekstraların bir özelliği: [(lootId, değer)]."""
    return [(l, X[l][key]) for l in equipped(p, sid) if l in X and key in X[l]]


def has(p, key, sid=None):
    return bool(props(p, key, sid))


def slot_bonus(p, sid=None, cid=None):
    """Yuva CPU'sunun ekstra yuvası: geminin bir config'inde (varsayılan: etkin gemi, etkin config) takılı olanın."""
    return slot_bonus_of(equipped(p, sid) if cid is None else p.loadout(sid, cid).get('extra', []))


def slot_bonus_of(loots):
    """Ekstraların arasındaki yuva CPU'sunun (SL-01..04) bonusu (config başına bir tane takılır)."""
    return max((X[l]['ek_yuva'] for l in loots if 'ek_yuva' in X.get(l, {})), default=0)


def cargo_factor(p):
    f = 1.0
    for l, v in props(p, 'kargo_carpan'):
        f = max(f, v)
    return f


def rocket_factor(p):
    return min((v for l, v in props(p, 'roket_bekleme')), default=1.0)


def mine_factor(p):
    return 1 + min((v for l, v in props(p, 'mayin_bekleme')), default=0.0)


def uses(p, loot):
    """Kullanım sınırlı ekstranın kalan hakkı (HM-7 satış, Jump CPU atlama, gizlenme): profilde, ilk takılışta tam."""
    st = p.d.setdefault('ekstra_haklari', {})
    if loot not in st:
        st[loot] = X.get(loot, {}).get('hak', 0)
    return st[loot]


def recharge(p, loot, n=1):
    """Hakkı olan ekstra satın alındı: n tanesinin hakkı eklenir."""
    if 'hak' not in X.get(loot, {}):
        return
    with p.lock:
        st = p.d.setdefault('ekstra_haklari', {})
        st[loot] = st.get(loot, 0) + X[loot]['hak'] * n
        p.dirty = True


def attached(p, loot):
    """Otomatik alım CPU'sunun hangarda seçilen cephanesi (HangarShipAutoBuyCpuAmmoRequest) ya da None."""
    return p.d.get('oto_alim_cephane', {}).get(loot)


def use(p, loot, n=1):
    with p.lock:
        left = uses(p, loot) - n
        p.d['ekstra_haklari'][loot] = max(0, left)
        p.dirty = True
    return max(0, left)
