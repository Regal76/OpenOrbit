"""Etkinlik takvimi (yol haritası Aşama 7; veri data/etkinlikler.json).

Bir etkinlik ya yılın belli günlerinde ('donemler': [["AA-GG", "AA-GG"]], bitiş günü dahil; yılı aşan dönem olabilir) ya da haftanın
belli günlerinde ve saatlerinde ('gunler' 0=pazartesi, 'saatler' [[başlangıç, bitiş]], 'cift_hafta': çift ISO haftaları) etkindir;
saatler yerel saatle. Etkin etkinlikler:
  - istemciye EventUpdateCommand {timestamp, activeCommands [EventModule {type, id, timeLeft, lang}], utcTimeOffset}: süresiz
    özellik bayrakları ('surekli') ve etkin etkinliklerin istemci türleri (kalan süre dönemin sonuna)
  - başarımlar (basarim.ACTIVE_EVENTS): etkinliğin 'basarim' grupları
  - sistemler: Upgrade Hour, Dispatch Day, kapı enerjisi indirimi, Kronos günü, altın kutu, harita etkinlikleri, Battle Pass …
Oyuncunun seçimi: yönetim panelinin Etkinlikler sayfası (ayar.py event_state: her etkinlik için açık / kapalı / takvime göre;
yıllık ve haftalık etkinliklerin hepsi; oyuna girişte bildirilir) önce gelir. Oyun sunucusu seçeneği: --etkinlik ad1,ad2 tarihten
bağımsız açar; --etkinlik hepsi bütün yıllık etkinlikleri, --etkinlik yok hiçbir yıllık etkinliği açmaz (haftalıklar sürer).
"""
import datetime, json, os, sys, time

import ayar as AY

HERE = os.path.dirname(os.path.abspath(__file__))
D = json.load(open(os.path.join(HERE, 'data', 'etkinlikler.json'), encoding='utf8'))
EVENTS = D['etkinlikler']
ALWAYS = D['surekli']['turler']
FORCED, MODE = set(), 'takvim'          # takvim | hepsi | yok (yıllıklar için)
EVENT_IDS = {}                          # EventModule.id: tür adı başına sabit


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


def _md(s):
    m, d = s.split('-')
    return int(m), int(d)


def period(key, now=None):
    """Etkinliğin şu anki (ya da yoksa None) dönemi: (başlangıç, bitiş) zaman damgası; bitiş hariç."""
    e, t = EVENTS[key], _dt(now)
    if 'donemler' in e:
        for a, b in e['donemler']:
            for y in (t.year - 1, t.year):
                s = datetime.datetime(y, *_md(a))
                end = datetime.datetime(y + (1 if _md(b) < _md(a) else 0), *_md(b)) + datetime.timedelta(days=1)
                if s <= t < end:
                    return s.timestamp(), end.timestamp()
        return None
    if t.weekday() not in e.get('gunler', range(7)):
        return None
    if e.get('cift_hafta') and t.isocalendar()[1] % 2:
        return None
    day = t.replace(hour=0, minute=0, second=0, microsecond=0)
    for a, b in e.get('saatler', [[0, 24]]):
        s, end = day + datetime.timedelta(hours=a), day + datetime.timedelta(hours=b)
        if s <= t < end:
            return s.timestamp(), end.timestamp()
    return None


def is_active(key, now=None):
    e = EVENTS.get(key)
    if not e:
        return False
    st = AY.event_state(key)
    if st:
        return st == 'acik'
    yearly = 'donemler' in e
    if yearly and (key in FORCED or MODE == 'hepsi'):
        return True
    if yearly and MODE == 'yok':
        return False
    return period(key, now) is not None


def active(now=None):
    return {k for k in EVENTS if is_active(k, now)}


def time_left(key, now=None):
    """Kalan saniye (zorla açılmış etkinlikte 30 gün)."""
    p = period(key, now)
    now = time.time() if now is None else now
    return max(0, int(p[1] - now)) if p else 30 * 86400


def gate_rewards(key, now=None):
    """Etkin etkinliklerin Galaksi Kapısı ödülleri ('kapi_odulu'): [(lootId, adet, olasılık)] (Empyrian / Prosperous Fragment …)."""
    return [tuple(r) for k in sorted(active(now)) for s in EVENTS[k].get('kapi_odulu', []) if key in s['kapilar'] for r in s['esyalar']]


def gate_packages(key, now=None):
    """Etkin etkinliklerin bu kapıdaki ödül paketleri ('kapi_odulu' satırının 'paket'i): başarımın CollectPackage koşulu için."""
    return [s['paket'] for k in sorted(active(now)) for s in EVENTS[k].get('kapi_odulu', []) if key in s['kapilar'] and s.get('paket')]


def achievement_groups(now=None):
    return {g for k in active(now) for g in EVENTS[k].get('basarim', [])}


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
        for t in EVENTS[k].get('turler', []):
            if t not in seen:
                seen.add(t)
                mods.append(dict(_='EventModule', type=t, timeLeft=left, id=_id(t), lang='all'))
    offset = -time.timezone if not time.localtime(now).tm_isdst else -time.altzone        # saniye (kayıt: 7200)
    return ('EventUpdateCommand', dict(timestamp=int(now * 1000), activeCommands=mods, utcTimeOffset=int(offset)))


configure()
