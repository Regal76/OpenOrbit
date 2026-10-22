"""Etkinlik takvimi (yol haritası Aşama 7, E8; veri data/etkinlikler.json).

Bir etkinlik ya yılın belli günlerinde ('donemler': [[başlangıç, bitiş]], bitiş günü dahil; yılı aşan dönem olabilir) ya da haftanın
belli günlerinde ve saatlerinde etkindir; saatler yerel saatle. Dönem ucu:
  - "AA-GG": her yıl
  - "YYYY-AA-GG": yalnız o yıl (gerçek oyunun koşuları). Bilinen son günden ('takvim_bilinen') sonra son 52 haftanın koşuları 52
    haftalık adımlarla yinelenir (haftanın günü korunur: Çarşamba başlayan etkinlik yine Çarşamba başlar)
  - "paskalya+N", "cin_yeni_yili-N", "sukran_gunu+N": o yılın bayramından N gün sonra / önce (Kasım'ın 4. perşembesi)
Dönemin üçüncü öğesi o günlerin saatleri ([[başlangıç, bitiş]]; 24'ü aşan bitiş ertesi güne taşar). Haftalık: 'gunler'
(0=pazartesi), 'saatler', 'ay_haftasi' (ayın kaçıncı o günü: [1, 3] = ayın 1. ve 3. cuması), 'hafta_dongu' [n, i] (n haftalık
döngünün i. haftası, HAFTA_BASI'ndan sayılır), 'birlikte' (yalnız bu etkinliklerden biri sürerken). Harita bölümlerinin de kendi 'donemler'i ve doğuş saatleri ('saatler',
'saatler_hafta_sonu') olabilir (window; panelin seans_hep_acik ayarı saatleri kaldırır, zorla açılan etkinlikte ikisi de yok).
Etkin etkinlikler:
  - istemciye EventUpdateCommand {timestamp, activeCommands [EventModule {type, id, timeLeft, lang}], utcTimeOffset}: süresiz
    özellik bayrakları ('surekli') ve etkin etkinliklerin istemci türleri (kalan süre dönemin sonuna); Command Center haberleri
    BE_<haber kimliği> türleriyle (news)
  - harita süsleri: EventActivationStateCommand (etkinliğin 'sus'u; mood_cmds)
  - başarımlar (basarim.ACTIVE_EVENTS): etkinliğin 'basarim' grupları
  - sistemler: Upgrade Hour, Dispatch Day, kapı enerjisi indirimi, Kronos günü, altın kutu, harita etkinlikleri, Battle Pass …
Oyuncunun seçimi: yönetim panelinin Etkinlikler sayfası (ayar.py event_state: her etkinlik için açık / kapalı / takvime göre;
yıllık ve haftalık etkinliklerin hepsi; oyuna girişte bildirilir) önce gelir. Oyun sunucusu seçeneği: --etkinlik ad1,ad2 tarihten
bağımsız açar (haftalıkları da); --etkinlik hepsi bütün yıllık etkinlikleri, --etkinlik yok hiçbir yıllık etkinliği açmaz (haftalıklar sürer).
"""
import datetime, json, os, sys, time

import ayar as AY

HERE = os.path.dirname(os.path.abspath(__file__))
D = json.load(open(os.path.join(HERE, 'data', 'etkinlikler.json'), encoding='utf8'))
EVENTS = D['etkinlikler']
ALWAYS = D['surekli']['turler']
FORCED, MODE = set(), 'takvim'          # takvim | hepsi | yok (yıllıklar için)
# hafta döngüleri ('hafta_dongu') bu pazartesiden sayılır; ISO hafta paritesi 53 haftalık yılda (2026) üç haftalık ara bırakıyordu
HAFTA_BASI = datetime.date(2024, 1, 8)
DAY, CYCLE = datetime.timedelta(days=1), datetime.timedelta(weeks=52)
KNOWN = datetime.datetime.strptime(D['takvim_bilinen'], '%Y-%m-%d') + DAY     # bilinen son günün sonu (yıla özgü dönemler)
# Çin Yeni Yılı (ay takvimi; tablo dışındaki yıllarda o dönem yok)
CNY = {2020: (1, 25), 2021: (2, 12), 2022: (2, 1), 2023: (1, 22), 2024: (2, 10), 2025: (1, 29), 2026: (2, 17), 2027: (2, 6),
       2028: (1, 26), 2029: (2, 13), 2030: (2, 3), 2031: (1, 23), 2032: (2, 11), 2033: (1, 31), 2034: (2, 19), 2035: (2, 8),
       2036: (1, 28), 2037: (2, 15), 2038: (2, 4), 2039: (1, 24), 2040: (2, 12)}
EVENT_IDS = {}                        # EventModule.id: tür adı başına sabit


def configure(argv=None):
    """--etkinlik seçeneği: 'hepsi', 'yok' ya da virgülle etkinlik adları."""
    global MODE
    argv = sys.argv if argv is None else argv
    FORCED.clear()
    MODE = 'takvim'
    for i, a in enumerate(argv):
        val = a.split('=', 1)[1] if a.startswith('--etkinlik=') else (argv[i + 1] if a == '--etkinlik' and i + 1 < len(argv) else None)
        if val is None:
            continue
        for x in val.split(','):
            x = x.strip().lower()
            if x in ('hepsi', 'yok'):
                MODE = x
            elif x in EVENTS:
                FORCED.add(x)


def _dt(now):
    return datetime.datetime.fromtimestamp(time.time() if now is None else now)


def _easter(y):
    """Paskalya (Gregoryen; anonim algoritma)."""
    a, b, c = y % 19, y // 100, y % 100
    h = (19 * a + b - b // 4 - (b - (b + 8) // 25 + 1) // 3 + 15) % 30
    l = (32 + 2 * (b % 4) + 2 * (c // 4) - h - c % 4) % 7
    m = (a + 11 * h + 22 * l) // 451
    return datetime.date(y, (h + l - 7 * m + 114) // 31, (h + l - 7 * m + 114) % 31 + 1)


def _thanksgiving(y):
    first = datetime.date(y, 11, 1)
    return first + datetime.timedelta(days=(3 - first.weekday()) % 7 + 21)


HOLIDAYS = {'paskalya': _easter, 'sukran_gunu': _thanksgiving,
            'cin_yeni_yili': lambda y: datetime.date(y, *CNY[y]) if y in CNY else None}


def _day(s, y):
    """Yıllık dönem ucu ("AA-GG" ya da "bayram±N") y yılında -> datetime (yoksa None)."""
    name, sign, n = s.partition('+') if '+' in s else s.partition('-') if s[0].isalpha() else (s, '', '')
    if name in HOLIDAYS:
        d = HOLIDAYS[name](y)
        return d and datetime.datetime.combine(d, datetime.time()) + (DAY * int(n or 0) * (-1 if sign == '-' else 1))
    m, d = s.split('-')
    return datetime.datetime(y, int(m), int(d))


def _spans(entries, t):
    """t'yi içerebilecek dönemler [(başlangıç, bitiş, saatler)] (datetime; bitiş hariç)."""
    out, dated = [], []
    for a, b, *h in entries:
        if a[:4].isdigit() and len(a) == 10:
            dated.append((datetime.datetime.strptime(a, '%Y-%m-%d'), datetime.datetime.strptime(b, '%Y-%m-%d') + DAY, h))
            continue
        for y in (t.year - 1, t.year):
            s, e = _day(a, y), _day(b, y)
            if s and e:
                out.append((s, (e if e >= s else _day(b, y + 1)) + DAY, h))
    if dated and t >= KNOWN:                    # bilinen son günden sonra: son 52 haftanın koşuları 52 haftada bir
        n = (t - KNOWN) // CYCLE + 1
        out += [(s + k * CYCLE, e + k * CYCLE, h) for s, e, h in dated if KNOWN - CYCLE <= s < KNOWN for k in (n - 1, n) if k]
    return out + dated


def _hours(t, hours, first=None, last=None):
    """t'yi kapsayan saat penceresi (başlangıç, bitiş) ya da None; hours: [[a, b]] ya da gün -> [[a, b]]. Önceki günün 24'ü aşan
    penceresi de sayılır; first/last: pencerenin başladığı gün bu aralıkta olmalı."""
    day = t.replace(hour=0, minute=0, second=0, microsecond=0)
    for d in (day - DAY, day):
        if first and not first <= d < last:
            continue
        for a, b in hours(d) if callable(hours) else hours:
            s, e = d + datetime.timedelta(hours=a), d + datetime.timedelta(hours=b)
            if s <= t < e:
                return s, e
    return None


def _span_at(entries, t):
    for s, e, h in _spans(entries, t):
        if s <= t < e:
            return _hours(t, h[0], s, e) if h else (s, e)
    return None


def _week_day(e, d):
    """Haftalık etkinlik bu gün var mı ('gunler', 'ay_haftasi', 'hafta_dongu')."""
    if d.weekday() not in e.get('gunler', range(7)) or (e.get('ay_haftasi') and (d.day - 1) // 7 + 1 not in e['ay_haftasi']):
        return False
    n, i = e.get('hafta_dongu', (1, 0))
    return (d.date() - HAFTA_BASI).days // 7 % n == i


def period(key, now=None):
    """Etkinliğin şu anki (ya da yoksa None) dönemi: (başlangıç, bitiş) zaman damgası; bitiş hariç."""
    e, t = EVENTS[key], _dt(now)
    if e.get('birlikte') and not any(is_active(k, now) for k in e['birlikte']):       # yalnız bu etkinliklerden biri sürerken (Fever)
        return None
    if 'donemler' in e:
        p = _span_at(e['donemler'], t)
    else:
        p = _hours(t, lambda d: e.get('saatler', [[0, 24]]) if _week_day(e, d) else [])
    return p and (p[0].timestamp(), p[1].timestamp())


def window(s, now=None):
    """Harita bölümü şu an açık mı: kendi 'donemler'i ve doğuş saatleri ('saatler', hafta sonu 'saatler_hafta_sonu'). Panelin
    seans_hep_acik ayarı açıksa yalnız dönemler."""
    t = _dt(now)
    if 'donemler' in s and not _span_at(s['donemler'], t):
        return False
    if 'saatler' not in s or AY.get('seans_hep_acik'):
        return True
    return _hours(t, lambda d: s.get('saatler_hafta_sonu', s['saatler']) if d.weekday() >= 5 else s['saatler']) is not None


def upcoming(key, now=None, days=366):
    """Etkinliğin şimdiden sonraki 'days' gün içindeki dönemleri [(başlangıç, bitiş)] (datetime; günlük saatler hariç; panel)."""
    e, t = EVENTS[key], _dt(now)
    if 'donemler' not in e:
        return []
    end = t + DAY * days
    found = {(s, f) for x in (t, t + DAY * (days // 2), end) for s, f, h in _spans(e['donemler'], x) if f > t and s < end}
    return sorted(found)


def is_active(key, now=None):
    e = EVENTS.get(key)
    if not e:
        return False
    st = AY.event_state(key)
    if st:
        return st == 'acik'
    yearly = 'donemler' in e
    if key in FORCED or (yearly and MODE == 'hepsi'):
        return True
    if yearly and MODE == 'yok':
        return False
    return period(key, now) is not None


def forced(key):
    """Etkinlik tarihten bağımsız açık mı (panelde 'acik', --etkinlik ad ya da hepsi): harita bölümlerinin pencereleri sayılmaz."""
    return AY.event_state(key) == 'acik' or key in FORCED or (MODE == 'hepsi' and 'donemler' in EVENTS[key])


def active(now=None):
    return {k for k in EVENTS if is_active(k, now)}


def has_type(t, now=None):
    """Etkinlik türü (EventModule.type, ör. CandyCargo) şu an etkin mi."""
    return t in ALWAYS or any(t in EVENTS[k].get('turler', []) for k in active(now))


def time_left(key, now=None):
    """Kalan saniye (zorla açılmış etkinlikte 30 gün)."""
    p = period(key, now)
    now = time.time() if now is None else now
    return max(0, int(p[1] - now)) if p else 30 * 86400


def gate_rewards(key, now=None):
    """Etkin etkinliklerin Galaksi Kapısı ödülleri ('kapi_odulu'): [(lootId, adet, olasılık)] (Empyrian / Prosperous Fragment …)."""
    return [tuple(r) for k in sorted(active(now)) for s in EVENTS[k].get('kapi_odulu', []) if key in s['kapilar']
            for r in s.get('esyalar', [])]


def gate_choices(key, now=None):
    """Etkin etkinliklerin bu kapıdaki seçimli ödülleri ('kapi_odulu' satırının 'secim'i: 'olasilik'la [[lootId, adet]]'ten biri;
    'yinelenmez': sahip olunan tasarım çıkmaz): GG Special Rewards Weekend paketleri, LF-4 günü."""
    return [s for k in sorted(active(now)) for s in EVENTS[k].get('kapi_odulu', []) if key in s['kapilar'] and s.get('secim')]


def gate_packages(key, now=None):
    """Etkin etkinliklerin bu kapıdaki ödül paketleri ('kapi_odulu' satırının 'paket'i): başarımın CollectPackage koşulu için."""
    return [s['paket'] for k in sorted(active(now)) for s in EVENTS[k].get('kapi_odulu', []) if key in s['kapilar'] and s.get('paket')]


def achievement_groups(now=None):
    return {g for k in active(now) for g in EVENTS[k].get('basarim', [])}


MON = ('Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec')
MONTH = ('January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December')


def news(key, now=None):
    """Etkinliğin bu koşusunun Command Center haberleri (istemcinin resource_news'undaki bn_<kimlik>; tools/takvim_e8.py): 'haber'
    kalıbı dönemin başlangıcıyla ({Y}, {m}, {Mon}, {mon}, {Month}); istemcide yoksa 'haber_varsayilan'; artı 'haber_ek'."""
    e = EVENTS[key]
    if 'haberler' not in e:
        return []
    p = period(key, now)
    d = datetime.date.fromtimestamp(p[0] if p else time.time() if now is None else now)
    ids = [x.format(Y=d.year, m='%02d' % d.month, Mon=MON[d.month - 1], mon=MON[d.month - 1].lower(), Month=MONTH[d.month - 1])
           for x in e['haber']]
    main = next((x for x in ids if x in e['haberler']), e.get('haber_varsayilan'))
    return ([main] if main else []) + e.get('haber_ek', [])


def _id(t):
    if t not in EVENT_IDS:
        EVENT_IDS[t] = 13000 + len(EVENT_IDS)
    return EVENT_IDS[t]


def event_cmd(now=None):
    """EventUpdateCommand (girişte; kayıttaki komutun yerine)."""
    now = time.time() if now is None else now
    mods, seen = [], set()
    for t in ALWAYS:
        mods.append(dict(_='EventModule', type=t, timeLeft=210030 * 3600, id=_id(t), lang='all'))
        seen.add(t)
    for k in sorted(active(now)):
        left = time_left(k, now)
        for t in EVENTS[k].get('turler', []) + ['BE_' + n for n in news(k, now)]:      # BE_<kimlik>: Command Center haberi
            if t not in seen:
                seen.add(t)
                mods.append(dict(_='EventModule', type=t, timeLeft=left, id=_id(t), lang='all'))
    offset = -time.timezone if not time.localtime(now).tm_isdst else -time.altzone        # saniye (kayıt: 7200)
    return ('EventUpdateCommand', dict(timestamp=int(now * 1000), activeCommands=mods, utcTimeOffset=int(offset)))


def moods(keys):
    """Etkinliklerin harita süsleri {istemcinin EventType'ı: 'sus'} (Prometheus hologramı, buzdağları, Paskalya, Carnival, Breach)."""
    return {EVENTS[k]['sus']['tur']: EVENTS[k]['sus'] for k in sorted(keys) if 'sus' in EVENTS[k]}


def mood_cmds(keys, before=None):
    """Süslerin EventActivationStateCommand'ları (hazır demetinde açık olanlar; 'before' verilirse yalnız açılan ve kapananlar).
    'deger': EventActivationIntegerAttributeModule (buzdağı boyutu)."""
    on, old = moods(keys), moods(before or ())
    cmd = lambda s, a: ('EventActivationStateCommand', dict(type=s['tur'], active=a, attributes=[
        dict(_='EventActivationIntegerAttributeModule', value=s['deger'])] if 'deger' in s else []))
    return ([cmd(s, True) for t, s in sorted(on.items()) if before is None or t not in old]
            + [cmd(s, False) for t, s in sorted(old.items()) if t not in on])


configure()
