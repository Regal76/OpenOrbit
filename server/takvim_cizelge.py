"""Panelin etkinlik takvimi (panel.py /api/takvim): etkinliklerin [bas, bit) içindeki açık aralıkları ve seansları.

- etkinlik: takvim.intervals (period ile aynı kural; panelin elle seçimi ayrı: panel 'durum' olarak verir)
- harita bölümleri ('harita', 'harita_ek'): kendi dönemleri ya da doğuş saatleri olanlar (takvim.section_intervals)
- büyük içeriklerin seansları: data/buyuk_icerikler.json ve ek_etkinlikler.json. Kural oyundakiyle aynı (vortex.session,
  dunya_patronu.window, apotheosis.window, mimesis.run_state, unvan_avi.in_window) ama o modüller dünyayı yüklediği için veriden
  hesaplanır; test_etkinlik_takvimi.py ikisini karşılaştırır.
Panelin seans_hep_acik ayarında seanslar ve doğuş saatleri hep açık (hep_acik).
Zamanlar yerel saatle; çıktı zaman damgası (saniye).
"""
import datetime, json, os

import takvim as TK

HERE = os.path.dirname(os.path.abspath(__file__))
DAY = datetime.timedelta(days=1)


def _veri(name):
    try:
        return json.load(open(os.path.join(HERE, 'data', name), encoding='utf8'))
    except (OSError, ValueError):
        return {}


BUYUK, EK = _veri('buyuk_icerikler.json'), _veri('ek_etkinlikler.json')


def _hm(s):
    h, m = s.split(':')
    return datetime.timedelta(hours=int(h), minutes=int(m))


def _starts(a, b, times, days=range(7), sure=0):
    """Günlük başlangıçlar [(başlangıç, gün)] — [a, b)'ye dokunan seanslar (önceki günün uzun seansı dahil)."""
    out = []
    for d in TK._days(a, b):
        if d.weekday() in days:
            out += [(d + t, d) for t in times if d + t < b and d + t + datetime.timedelta(seconds=sure) > a]
    return out


def seanslar(a, b):
    """Büyük içeriklerin seansları: [{'kimlik', 'etkinlik', 'araliklar': [[başlangıç, bitiş, işaret]]}] (datetime; işaret: vortex'te
    çift ödüllü seans 1, mimesis'te girişin kapanışı)."""
    out = []
    v = BUYUK.get('vortex')
    if v:
        sure, cift = v.get('seans_sn', 900), v.get('cift_saat')
        out.append({'kimlik': 'vortex', 'etkinlik': v.get('etkinlik'), 'araliklar': [
            [s, s + datetime.timedelta(seconds=sure), int(d.isoweekday() in v.get('cift_gunler', []) and s - d == _hm(cift or '99:00'))]
            for s, d in _starts(a, b, [_hm(x) for x in v.get('seanslar', [])], sure=sure)]})
    for kimlik, anahtar, gunler in (('dunya_patronu', 'dunya_patronu', range(7)), ('kristallon', 'kristallon_apotheosis', None)):
        p = BUYUK.get(anahtar)
        if p:
            days = p.get('gunler', range(7)) if gunler is None else gunler
            out.append({'kimlik': kimlik, 'etkinlik': p.get('etkinlik'), 'araliklar': [
                [d + _hm(x), d + _hm(y), 0] for d in TK._days(a, b) if d.weekday() in days for x, y in p.get('pencereler', [])
                if d + _hm(x) < b and d + _hm(y) > a]})
    m = BUYUK.get('mimesis')
    if m:
        sure, giris = m.get('sure_sn', 2700), m.get('giris_sn', 300)
        out.append({'kimlik': 'mimesis', 'etkinlik': m.get('etkinlik'), 'araliklar': [
            [s, s + datetime.timedelta(seconds=sure), s + datetime.timedelta(seconds=giris)]
            for s, _ in _starts(a, b, [datetime.timedelta(hours=h) for h in m.get('saatler', [])], sure=sure)]})
    u = EK.get('unvan_avi')
    if u:
        out.append({'kimlik': 'unvan_avi', 'etkinlik': u.get('etkinlik', 'unvan_avi'),
                    'araliklar': [[s, e, 0] for s, e in TK._daily(a, b, lambda d: u.get('saatler', []))]})
    for x in out:
        x['araliklar'] = [r for r in x['araliklar'] if r[1] > a and r[0] < b]
    return out


def _bolumler(e):
    for k in ('harita', 'harita_ek'):
        v = e.get(k)
        for s in (v if isinstance(v, list) else [v] if v else []):
            if 'saatler' in s or 'donemler' in s:
                yield s


def _ts(r):
    return [x.timestamp() if isinstance(x, datetime.datetime) else x for x in r]


def _kes(iv, etkin):
    """Seans aralıklarını [başlangıç, bitiş, işaret] etkinliğin açık aralıklarıyla keser (işaret korunur)."""
    return [[max(s, p), min(e, q)] + r for s, e, *r in iv for p, q in etkin if max(s, p) < min(e, q)]


def cizelge(bas, bit, hep_acik=False, durumlar=None):
    """[bas, bit) (zaman damgası) -> {anahtar: {'araliklar' (takvim), 'etkin' (elle seçimle: 'acik' bütün aralık, 'kapali' boş),
    'seanslar': [{'kimlik', 'tur', 'haritalar', 'araliklar' [[s, e, işaret]]}]}}. Seanslar yalnız etkinlik açıkken (oyundaki gibi).
    durumlar: anahtar -> panelin elle seçimi ('acik' / 'kapali'; yoksa takvim)."""
    a, b = datetime.datetime.fromtimestamp(bas), datetime.datetime.fromtimestamp(bit)
    durumlar = durumlar or {}
    out = {}
    for k in TK.EVENTS:
        iv = [_ts(r) for r in TK.intervals(k, a, b)]
        st = durumlar.get(k)
        out[k] = {'araliklar': iv, 'etkin': [[bas, bit]] if st == 'acik' else [] if st == 'kapali' else iv, 'seanslar': []}
    for k, e in TK.EVENTS.items():
        for i, s in enumerate(_bolumler(e)):
            iv = [_ts(r) + [0] for r in TK.section_intervals(s, a, b, hep_acik)]
            out[k]['seanslar'].append({'kimlik': 'harita_%d' % i, 'tur': 'uzayli' if 'uzaylilar' in s else 'kutu' if 'kutular' in s else 'harita',
                                       'haritalar': s.get('haritalar', []), 'araliklar': _kes(iv, out[k]['etkin'])})
    for x in seanslar(a, b):
        if x['etkinlik'] in out:
            iv = [[bas, bit, 0]] if hep_acik else [_ts(r) for r in x['araliklar']]
            out[x['etkinlik']]['seanslar'].append({'kimlik': x['kimlik'], 'tur': 'seans', 'haritalar': [],
                                                   'araliklar': _kes(iv, out[x['etkinlik']]['etkin'])})
    return out


def sonraki(key, now, gun=400):
    """Etkinliğin şimdiki ya da sonraki aralığı [başlangıç, bitiş] (zaman damgası; 'gun' gün içinde yoksa None)."""
    a = datetime.datetime.fromtimestamp(now)
    iv = TK.intervals(key, a, a + DAY * gun)
    return _ts(iv[0]) if iv else None
