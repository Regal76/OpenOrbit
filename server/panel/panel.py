"""DarkOrbit yerel sunucu yönetim paneli: oyunu başlatır, ayarları, kayıtları ve sunucuları yönetir.

Başlatma: ana dizindeki "DarkOrbit Panel.pyw" (çift tıkla; konsolsuz) ya da python server/panel/panel.py.
Panel 127.0.0.1:8077'de yerel bir web arayüzü açar ve onu Edge'in (yoksa Chrome'un) uygulama penceresinde gösterir (adres çubuğu
yok, internet gerekmez). Pencere kapanınca: oyun sürüyorsa istemci kapanana dek bekler (ayar), sonra panelin açtığı sunucuları
kapatıp çıkar. Panel zaten açıksa ikinci başlatma yalnız pencereyi yeniden açar.
API: /api/... (JSON). İstekler sayfadaki belirteci (X-Panel-Belirteci) taşımalı: başka sitelerin tarayıcıdan panele istek
göndermesini engeller. Yalnız 127.0.0.1'e bağlanır.
Yollar: yollar.py (save/kayitlar, save/panel.json, save/ayarlar.json, logs/).
Dil: Türkçe ya da İngilizce (dil.py; metinler Türkçe yazılır, İngilizceleri arayuz/en.json). İlk açılışta arayüz kurulum sihirbazını
açar: dil, oyun klasörü, ilk pilot, oyun ayarları (panel.json 'dil', 'kurulum_tamam'). Oyun bilgisayarda bulunamazsa sihirbazın oyun
klasörü adımı onu indirmeye başlar (indirme.py; İstemci sayfasından da).
Güncelleme (guncelleme.py): açılıştan biraz sonra ve GUNCELLEME_SN'de bir GitHub'daki son sürüm denetlenir; panel ayarı 'guncelleme'
otomatikse ve oyun, sunucular, indirme ya da başka bir iş sürmüyorsa kurulur, ardından panel yeniden başlar (yeni süreç aynı portu
alır, açık pencere sayfayı yeniler).
"""
import datetime, json, os, re, secrets, shutil, subprocess, sys, threading, time, traceback
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse
from urllib.request import Request, urlopen

PANEL_DIR = os.path.dirname(os.path.abspath(__file__))
SERVER = os.path.dirname(PANEL_DIR)
ROOT = os.path.dirname(SERVER)
sys.path.insert(0, SERVER)
sys.path.insert(0, PANEL_DIR)
import yollar as YOL          # noqa: E402
import ayar as AY             # noqa: E402
import dil as D               # noqa: E402
from dil import t as _        # noqa: E402
import istemci as IST         # noqa: E402
import surecler as SR         # noqa: E402
from kayitlar import Kayitlar, KayitHatasi, FIRMALAR  # noqa: E402
from yapilandirma import PanelConfig  # noqa: E402
from testler import Testler  # noqa: E402
from protokol import Uyarlayici  # noqa: E402
from indirme import Indirici, IndirmeHatasi  # noqa: E402
from guncelleme import Guncelleyici, GuncellemeHatasi  # noqa: E402

SURUM = '1.0'
PORT = 8077
ARAYUZ = os.path.join(PANEL_DIR, 'arayuz')
SABLONLAR = os.path.join(YOL.SAVE, 'ayar_sablonlari.json')
TARAYICI_PROFILI = os.path.join(os.environ.get('LOCALAPPDATA') or YOL.SAVE, 'DarkOrbitPanel', 'tarayici')
GUNLUKLER = ('gs.log', 'http.log', 'client.log', 'oyun_konsol.log', 'web_konsol.log', 'panel.log', 'errors.log', 'unknown.log')
NABIZ_SN = 180                      # tarayıcı penceresi izlenemiyorsa: bu kadar istek gelmezse pencere kapandı sayılır
DEVIR_SN = 10                       # tarayıcı süreci bundan önce çıkarsa pencereyi açık bir sürece devretmiştir (watch_window)
GUNCELLEME_SN = 6 * 3600            # GitHub'da yeni sürüm denetimi aralığı (başarısızsa bir saat sonra yeniden)
ETKINLIK_ACIKLAMA = {
    'yukseltme_saati': "Assembly'de ekipman yükseltmesi %25 daha az uridyum.",
    'dispatch_gunu': 'Dispatch gönderimlerinin etkinlik günü.',
    'kapi_hafta_sonu': 'Galaksi Kapısı enerjisi %15 indirimli.',
    'kronos_gunu': 'Kronos kapısının parçası iki kat gelir.',
    'altin_kutu': "Haritalarda Altın Booty Box'lar çıkar.",
    'halloween': "X-2..X-8'de Curcubitor'lar ve Boss Curcubitor, Candy Corn kutuları, balkabakları, Trial of Terrors kapısı "
                 "(X-4; karanlık haritalar), Battle Pass.",
    'agatus': "Spinel'ler ve Agatus; etkinlik paraları ve Assembly tarifleri.",
    'hitac': "Underling'ler ve Underboss; Hitac ana gemisi haritadan haritaya dolaşır.",
    'immortal_union': 'Lanatum, Styxus ve Charopos; etkinlik paraları.',
    'protegit': "Chaos Protegit'ler; etkinlik paraları.",
    'kis': "Ice Meteoroid'ler, hediye kutuları ve Santa.",
    'thanksgiving': "Ice Meteoroid'ler.",
    'plutus': 'Gauntlet of Plutus kapısı (Easy X-1, Normal X-8; günde bir).',
    'labirent': "Frozen Labyrinth: X-1'den 16 haritalık labirent, Labyrinth Key'ler ve Synk.",
    'dogum_gunu': 'Birthday Gate (X-1).',
    'empyrian': 'Empyrian kutuları; anahtarlar Galaksi Kapısı ödülünden.',
    'prosperous': 'Prosperous kutuları; anahtarlar Galaksi Kapısı ödülünden.',
    'bahar': 'Bahar yumurtaları ve kutuları.',
    'chaos_omen': 'Chaos Omen harita etkinliği (Protegit Pandemonium öncesi).',
    'gg_cift_odul': 'Galaksi Kapılarının EP, onur, Xenomit, log diski, kupon ve Assembly kaynağı ödülleri ile şanslı ödül '
                    'olasılığı iki kat (Dispatch hariç).',
    'lf4_gunu': 'Delta, Epsilon, Lambda ve Kuiper kapılarından LF-4 ya da 10.000 UCB-100 şansı.',
    'lf4_gelismis': "Delta'dan LF-4-HP, Kappa'dan LF-4-PD, Zeta'dan LF-4-MD şansı.",
    'gg_hafta_sonu_1': 'Delta, Epsilon, Kuiper ve Lambda kapılarından tasarım ve lazer paketi şansı.',
    'gg_hafta_sonu_3': 'Delta, Epsilon, Kuiper ve Lambda kapılarından tasarım ve lazer paketi şansı.',
    'gg_hafta_sonu_4': 'Delta, Epsilon, Kuiper ve Lambda kapılarından tasarım ve lazer paketi şansı.',
    'nova_hafta_sonu': 'Delta, Epsilon, Lambda ve Kuiper kapıları N.E.U. verir.',
    'obsidian_booty': "Haritalarda Obsidian Booty Box'lar çıkar.",
    'rb_booty': "Haritalarda kırmızı ve mavi Booty Box'lar çıkar.",
    'apocalypse_booty': "Haritalarda Apocalypse Booty Box'lar çıkar.",
    'fever': 'Listedeki gemilere güçlenme; yalnız Gauntlet of Plutus, Mimesis Mutiny ve Protegit sürerken.',
}
GUNLER = {'tr': ('Pzt', 'Sal', 'Çar', 'Per', 'Cum', 'Cmt', 'Paz'), 'en': ('Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun')}
AYLAR = {'tr': ('Oca', 'Şub', 'Mar', 'Nis', 'May', 'Haz', 'Tem', 'Ağu', 'Eyl', 'Eki', 'Kas', 'Ara'),
         'en': ('Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec')}

os.makedirs(YOL.LOGS, exist_ok=True)
_log_lock = threading.Lock()


def log(text):
    with _log_lock:
        try:
            with open(os.path.join(YOL.LOGS, 'panel.log'), 'a', encoding='utf8') as fh:
                fh.write(time.strftime('%Y-%m-%d %H:%M:%S ') + text + '\n')
        except OSError:
            pass


CFG = PanelConfig(YOL.PANEL)
D.bagla(lambda: CFG.get('dil'))
YON = SR.Yonetici(YOL.LOGS, log)
KAY = Kayitlar(CFG, python=SR.python_exe())
KAY.in_use = lambda slot: YON.running() and YON.slot == slot
TEST = Testler(SERVER, SR.python_exe(), log, SR.NO_WINDOW)     # panelden testler (testler.py)
UYAR = Uyarlayici(ROOT, SR.python_exe(), log, SR.NO_WINDOW)    # yeni istemciye protokol uyarlaması (protokol.py)
UPD = Guncelleyici(ROOT, YOL.SAVE, log)                          # GitHub'dan güncelleme (guncelleme.py)
TOKEN = secrets.token_hex(16)
STATE = {'oyna': {'calisiyor': False, 'adimlar': [], 'hata': None, 'bitti': None, 'sadece_sunucu': False},
         'nabiz': time.time(), 'pencere_kapandi': False, 'pencere_izleniyor': False, 'son_yedek': 0.0, 'kapaniyor': False,
         'sonraki_denetim': time.time() + 8, 'guncellendi': '--guncellendi' in sys.argv, 'srv': None, 'acilis': time.time()}


class Hata(Exception):
    """Kullanıcıya gösterilen hata."""


# ------------------------------------------------------------------ yardımcılar
def read_json(path, default):
    try:
        with open(path, encoding='utf8') as fh:
            return json.load(fh)
    except (OSError, ValueError):
        return default


def write_json(path, d):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = path + '.tmp'
    with open(tmp, 'w', encoding='utf8', newline='\n') as fh:
        json.dump(d, fh, ensure_ascii=False, indent=1)
    os.replace(tmp, path)


def game_settings():
    return AY.read(YOL.AYARLAR)


def client_folder():
    return IST.resolve(CFG.get('istemci_klasoru'))


def _downloaded(path):
    """İndirme bitti: kullanılan istemci geçersizse yeni klasör kullanılsın (kendiliğinden bulunuyorsa ayar boş kalır)."""
    if not IST.check(client_folder())['gecerli']:
        auto = IST.resolve(None)
        same = auto and os.path.normcase(os.path.normpath(auto)) == os.path.normcase(os.path.normpath(path))
        CFG.update({'istemci_klasoru': None if same else path})


DL = Indirici(ROOT, IST.check, log, on_done=_downloaded)       # oyun istemcisini indirme (indirme.py)


def _dl_pct(st):
    return int(100 * st['alinan'] / st['toplam']) if st['toplam'] else 0


_dialog_lock = threading.Lock()


def dialog(kind, **kw):
    """Yerel dosya/klasör penceresi (tkinter; panelin önünde açılır) -> seçilen yol ya da ''."""
    with _dialog_lock:
        import tkinter as tk
        from tkinter import filedialog
        root = tk.Tk()
        root.withdraw()
        root.attributes('-topmost', True)
        try:
            fn = {'klasor': filedialog.askdirectory, 'ac': filedialog.askopenfilename, 'kaydet': filedialog.asksaveasfilename}[kind]
            return fn(parent=root, **kw) or ''
        finally:
            root.destroy()


def open_folder(path):
    if not os.path.exists(path):
        raise Hata(_('Klasör yok: %s', path))
    os.startfile(path)


# ------------------------------------------------------------------ etkinlikler
def _period_text(a, b, lang):
    (ma, da), (mb, db) = (a.month, a.day), (b.month, b.day)
    months = AYLAR[lang]
    if lang == 'en':
        return '%s %d – %s %d' % (months[ma - 1], da, months[mb - 1], db)
    return '%d %s – %d %s' % (da, months[ma - 1], db, months[mb - 1])


def event_list():
    import takvim as TK
    lang = D.current()
    now = time.time()
    t = datetime.datetime.fromtimestamp(now)
    sel = game_settings().get('etkinlikler') or {}
    out = []
    for key, e in TK.EVENTS.items():
        yearly = 'donemler' in e
        if yearly:                                      # önümüzdeki yılın dönemleri (takvim.upcoming; bitiş günü dahil)
            spans = TK.upcoming(key, now)
            when = ', '.join(_period_text(a, b - datetime.timedelta(days=1), lang) for a, b in spans[:4]) + (
                ' …' if len(spans) > 4 else '') or _('Takvimde yeni dönemi yok')
        else:
            days = e.get('gunler', range(7))
            when = (_('Her gün') if len(list(days)) == 7 else ', '.join(GUNLER[lang][d] for d in days))
            hrs = e.get('saatler')
            if hrs:
                when += ' ' + ', '.join('%02d:00–%02d:00' % (a, b) for a, b in hrs)
            if e.get('ay_haftasi'):
                when += ' ' + _('(ayın %s. haftası)', '/'.join(map(str, e['ay_haftasi'])))
            if e.get('hafta_dongu'):
                when += ' ' + _('(%s haftada bir)', e['hafta_dongu'][0])
        per = TK.period(key, now)
        nxt = None
        if yearly and not per:
            best = next((s for s, f in spans if s > t), None)
            nxt = (best - t).days + 1 if best else None
        st = sel.get(key)
        out.append({'anahtar': key, 'ad': _(e.get('ad', key)), 'tur': 'yillik' if yearly else 'haftalik', 'zaman': when,
                    'takvimde': per is not None, 'kalan_sn': int(per[1] - now) if per else None, 'sonraki_gun': nxt,
                    'durum': st, 'etkin': (st == 'acik') if st else per is not None,
                    'aciklama': _(ETKINLIK_ACIKLAMA.get(key, ''))})
    out.sort(key=lambda x: (x['tur'] != 'yillik', not x['etkin'], x['ad'].lower()))
    return out


def settings_summary(values):
    """Varsayılandan farklı oyun ayarları [{'ad', 'deger'}] (Oyna sayfasının çipleri; ayar.summary'nin panel dilindeki hâli)."""
    d = AY.clean(values)
    out = []
    for s in AY.SCHEMA:
        v = d.get(s['anahtar'], s['varsayilan'])
        if v == s['varsayilan']:
            continue
        if s['tur'] == 'carpan':
            text = 'x%g' % v
        elif s['tur'] == 'bool':
            text = _('açık') if v else _('kapalı')
        elif s['tur'] == 'sayi':
            text = ('%d %s' % (v, _(s['birim']) if s.get('birim') else '')).strip()
        else:
            text = _(s['secenekler'][v])
        out.append({'ad': _(s['ad']), 'deger': text})
    return out


def set_events(body):
    vals = game_settings()
    ev = dict(vals.get('etkinlikler') or {})
    import takvim as TK
    if 'hepsi' in body:
        to = body['hepsi']
        for k, e in TK.EVENTS.items():
            if body.get('tur') and body['tur'] != ('yillik' if 'donemler' in e else 'haftalik'):
                continue
            if to in AY.ETKINLIK_DURUMLARI:
                ev[k] = to
            else:
                ev.pop(k, None)
    for k, v in (body.get('degisiklik') or {}).items():
        if k not in TK.EVENTS:
            continue
        if v in AY.ETKINLIK_DURUMLARI:
            ev[k] = v
        else:
            ev.pop(k, None)
    vals['etkinlikler'] = ev
    AY.write(YOL.AYARLAR, vals)
    return event_list()


# ------------------------------------------------------------------ uyarılar ve durum
def try_migrate():
    """Eski tek kayıt (save/profil.json) varsa yuvaya taşı; portlar açıksa (o profille açılmış bir sunucu olabilir) sonraya."""
    if not os.path.isfile(YOL.ESKI_PROFIL) or YON.running():
        return None
    table = SR.listeners()
    if any(SR.listening(p, table) for p in (8081, 8090)):
        if not STATE.get('tasima_bekliyor'):
            log('eski kayıt taşınmadı: oyun portları açık (Baslat.bat ile açılmış bir sunucu kullanıyor olabilir)')
        STATE['tasima_bekliyor'] = True
        return None
    STATE['tasima_bekliyor'] = False
    moved = KAY.migrate()
    if moved:
        log('eski kayıt (save/profil.json) yuvaya taşındı: %s' % moved)
    return moved


def warnings():
    out = []
    if STATE.get('tasima_bekliyor'):
        out.append({'tur': 'uyari', 'metin': _('Eski kaydın (server/save/profil.json) kayıt yuvasına taşınması bekliyor: önce dışarıda açık '
                                               'olan sunucuyu kapatın (Sunucu > Portlar).'), 'sayfa': 'sunucu'})
    slot = KAY.active()
    if not slot:
        out.append({'tur': 'hata', 'metin': _('Henüz kayıt yok: Kayıtlar sayfasından yeni bir kayıt oluşturun.'), 'sayfa': 'kayitlar'})
    c = IST.check(client_folder())
    if not c['gecerli'] and DL.running():
        out.append({'tur': 'uyari', 'metin': _('Oyun istemcisi indiriliyor: %%%d. Bitince oynayabilirsin.', _dl_pct(DL.state())),
                    'sayfa': 'istemci'})
    elif not c['gecerli']:
        out.append({'tur': 'hata', 'metin': _('Oyun istemcisi bulunamadı: %s İstemci sayfasından klasörü seçin ya da oyunu indirin.',
                                              ' '.join(c['sorunlar'])), 'sayfa': 'istemci'})
    elif not c['uyumlu']:
        out.append({'tur': 'uyari', 'metin': c['sorunlar'][-1], 'sayfa': 'istemci'})
    missing = [n for n in YOL.SABLONLAR if not YOL.sablon(n)]       # kendi kaydın ya da paylaşılabilir kopya (data/varsayilan)
    if missing:
        out.append({'tur': 'uyari', 'metin': _('Giriş şablonları eksik (%s): oyun en küçük girişle açılır, bazı pencereler ve mağaza '
                                               'boş kalabilir.', ', '.join(missing)), 'sayfa': 'sunucu'})
    u = UPD.state()
    if u['durum'] in ('indiriliyor', 'kuruluyor'):
        out.append({'tur': 'uyari', 'metin': _('Panel güncelleniyor; bitince kendiliğinden yeniden başlar.'), 'sayfa': 'panel'})
    elif u['durum'] == 'var' and CFG.get('guncelleme') != 'kapali':
        auto = CFG.get('guncelleme') == 'otomatik' and CFG.get('kurulum_tamam')
        out.append({'tur': 'uyari', 'metin': _('Yeni sürüm var (%s): oyun ve sunucular kapanınca kendiliğinden kurulur.', u['son']['surum'][:7])
                    if auto else _('Yeni sürüm var (%s): Panel sayfasından kurabilirsin.', u['son']['surum'][:7]), 'sayfa': 'panel'})
    elif u['durum'] == 'kuruldu':
        out.append({'tur': 'uyari', 'metin': _('Güncelleme kuruldu: oyun ve sunucular kapanınca panel yeniden başlar.'), 'sayfa': 'panel'})
    alive = YON.servers_alive()
    table = SR.listeners()
    foreign = [p for ad, ports in SR.PORTS.items() for p in ports if not alive.get(ad) and SR.listening(p, table)]
    if foreign:
        out.append({'tur': 'uyari', 'metin': _('Panelin açmadığı bir süreç oyun portlarını tutuyor (%s). Önceki oturumdan kalan bir '
                                               'sunucu olabilir: Sunucu sayfasından inceleyin.', ', '.join(map(str, foreign))),
                    'sayfa': 'sunucu'})
    for ad, s in YON.sunucular.items():
        if s.crashed:
            out.append({'tur': 'hata', 'metin': _('%s sunucusu beklenmedik biçimde kapandı (çıkış kodu %s). Ayrıntı: Sunucu > Günlükler > '
                                                  '%s_konsol.log', _({'oyun': 'Oyun', 'web': 'Web'}[ad]), s.proc.poll(), ad),
                        'sayfa': 'sunucu'})
    return out


def status():
    STATE['nabiz'] = time.time()
    if STATE.get('tasima_bekliyor'):
        try_migrate()
    slot = KAY.active()
    try:
        aktif = KAY.summary(slot) if slot else None
    except (OSError, KayitHatasi):
        aktif = None
    vals = game_settings()
    ev = [e['ad'] for e in event_list() if e['etkin'] and e['tur'] == 'yillik']
    slots = KAY.slots()
    return {'surecler': YON.status(), 'aktif': aktif, 'kayit_sayisi': len(slots),
            'ayar_ozet': settings_summary(vals), 'etkinlikler': ev,
            'uyarilar': warnings(), 'oyna': STATE['oyna'], 'istemci_klasoru': client_folder(),
            'panel': {'surum': SURUM, 'pencere_kapandi': STATE['pencere_kapandi'], 'dil': CFG.get('dil'),
                      'kurulum_tamam': CFG.get('kurulum_tamam'), 'guncellendi': STATE['guncellendi'],
                      'acik_sn': int(time.time() - STATE['acilis'])}}


# ------------------------------------------------------------------ oyna
def _step(text, durum='calisiyor'):
    o = STATE['oyna']
    if o['adimlar'] and o['adimlar'][-1]['durum'] == 'calisiyor':
        o['adimlar'][-1]['durum'] = 'tamam'
    o['adimlar'].append({'metin': text, 'durum': durum, 'zaman': time.strftime('%H:%M:%S')})


def launch(sadece_sunucu=False):
    o = STATE['oyna']
    try:
        _step(_('Denetleniyor'))
        slot = KAY.active()
        if not slot:
            raise Hata(_('Önce Kayıtlar sayfasından bir kayıt oluşturun.'))
        folder = client_folder()
        if not sadece_sunucu:
            c = IST.check(folder)
            if not c['gecerli'] and DL.running():
                raise Hata(_('Oyun istemcisi henüz iniyor (%%%d). Bitince oynayabilirsin.', _dl_pct(DL.state())))
            if not c['gecerli']:
                raise Hata(_('İstemci klasörü geçersiz: %s', ' '.join(c['sorunlar'])))
            if YON.client_alive():
                raise Hata(_('Oyun zaten açık.'))
            others = IST.running_clients()
            if others:
                raise Hata(_('Başka bir DarkOrbit istemcisi açık (süreç %s). Önce onu kapatın.', ', '.join(map(str, others))))
        prof = KAY.profile(slot)
        same = YON.running() and YON.slot == slot
        if CFG.get('yedek_acilista') and not same:
            _step(_('Kayıt yedekleniyor'))
            KAY.backup(slot, 'oto', _('Oyna (açılış)'))
            STATE['son_yedek'] = time.time()
        if not YON.running() and CFG.get('gunluk_dondur'):
            import baslat
            baslat.rotate_logs(YOL.LOGS, names=('gs.log', 'http.log', 'client.log', 'oyun_konsol.log', 'web_konsol.log',
                                                'panel.log'))
        _step(_('Sunucular başlatılıyor') if not same else _('Sunucular açık'))
        YON.start_servers(prof, YOL.AYARLAR, kontrol=bool(game_settings().get('kontrol')), slot=slot)
        if not sadece_sunucu:
            _step(_('Oyun açılıyor'))
            YON.start_client(folder, IST.args(CFG, os.path.join(YOL.LOGS, 'client.log')))
            m = KAY.meta(slot)
            KAY.set_meta(slot, son_oynama=time.strftime('%Y-%m-%d %H:%M:%S'), oynama_sayisi=int(m.get('oynama_sayisi') or 0) + 1)
        _step(_('Hazır') if sadece_sunucu else _('Oyun açıldı: iyi uçuşlar!'), 'tamam')
        o['bitti'] = time.time()
    except (Hata, KayitHatasi, RuntimeError, OSError) as e:
        o['hata'] = str(e)
        _step(str(e), 'hata')
        log('oyna hatası: %s' % e)
    except Exception as e:
        o['hata'] = _('Beklenmeyen hata: %r', e)
        _step(o['hata'], 'hata')
        log('oyna hatası: %s' % traceback.format_exc())
    finally:
        o['calisiyor'] = False


def start_launch(sadece_sunucu=False):
    o = STATE['oyna']
    if o['calisiyor']:
        raise Hata(_('Başlatma sürüyor.'))
    o.update(calisiyor=True, adimlar=[], hata=None, bitti=None, sadece_sunucu=bool(sadece_sunucu))
    threading.Thread(target=launch, args=(sadece_sunucu,), daemon=True).start()
    return o


def on_client_exit(early):
    if early:
        return
    if CFG.get('istemci_kapaninca') == 'kapat':
        YON.stop_servers()
    if STATE['pencere_kapandi']:
        threading.Thread(target=shutdown, daemon=True).start()


YON.on_client_exit = on_client_exit


def idle(strict=False):
    """Güncelleme kurulabilir mi: oyun, sunucular, başlatma, istemci indirmesi, protokol aracı ve testler durmuş (strict: panelin
    açmadığı DarkOrbit istemcisi de yok; tasklist çalışır)."""
    busy = (YON.running() or YON.client_alive() or STATE['oyna']['calisiyor'] or DL.running() or UYAR.state()['calisiyor']
            or TEST.calisiyor)
    return not busy and not (strict and IST.running_clients())


def update_tick(now):
    """GitHub denetimi (GUNCELLEME_SN'de bir), otomatik kurulum ve kurulumdan sonra yeniden başlatma (boştayken)."""
    mode = CFG.get('guncelleme')
    st = UPD.state()
    if st['calisiyor']:
        return
    if st['durum'] == 'kuruldu':
        if idle(strict=True):
            restart()
        return
    if mode == 'kapali':
        return
    if now >= STATE['sonraki_denetim']:
        st = UPD.check()
        STATE['sonraki_denetim'] = now + (3600 if st['durum'] == 'hata' else GUNCELLEME_SN)
    if st['durum'] == 'var' and mode == 'otomatik' and CFG.get('kurulum_tamam') and idle(strict=True):
        UPD.install_async()


def restart():
    """Güncellemeden sonra yeniden başla: yeni süreç (pencere açmadan) eski kapanınca aynı portu alır; açık pencere sayfayı yeniler."""
    STATE['kapaniyor'] = True
    args = [sys.executable, os.path.join(PANEL_DIR, 'panel.py'), '--pencere-yok', '--guncellendi', '--port=%d' % PORT]
    log('panel güncellendi: yeniden başlatılıyor')
    try:
        subprocess.Popen(args, cwd=ROOT, close_fds=True, creationflags=0x00000008 | 0x00000200)   # DETACHED, yeni süreç grubu
        if STATE['srv']:
            STATE['srv'].server_close()
    finally:
        os._exit(0)


def ticker():
    """Oyun sürerken aralıklı yedek; pencere kapandıysa ve iş kalmadıysa çıkış; güncelleme (update_tick)."""
    while not STATE['kapaniyor']:
        time.sleep(5)
        try:
            update_tick(time.time())
            iv = CFG.get('yedek_aralik_dk')
            if YON.client_alive() and YON.slot and iv and time.time() - STATE['son_yedek'] >= iv * 60:
                KAY.backup(YON.slot, 'oto', _('Oyun sırasında'))
                STATE['son_yedek'] = time.time()
            if not STATE['pencere_izleniyor'] and time.time() - STATE['nabiz'] > NABIZ_SN:
                STATE['pencere_kapandi'] = True
            if STATE['pencere_kapandi'] and not YON.client_alive() and not STATE['oyna']['calisiyor']:
                shutdown()
        except Exception:
            log('zamanlayıcı hatası: %s' % traceback.format_exc())


def shutdown():
    if STATE['kapaniyor']:
        return
    STATE['kapaniyor'] = True
    log('panel kapanıyor')
    try:
        DL.cancel()                                   # indirme: açılmış dosyalar kalır, sonra kaldığı yerden
        if not YON.client_alive():
            YON.stop_servers()
        w = STATE.get('pencere')
        if w and w.poll() is None:                    # panelin açtığı uygulama penceresi de kapansın
            w.terminate()
    finally:
        os._exit(0)


# ------------------------------------------------------------------ pencere
def browser():
    cands = []
    for env in ('PROGRAMFILES(X86)', 'PROGRAMFILES', 'LOCALAPPDATA'):
        base = os.environ.get(env)
        if base:
            cands += [os.path.join(base, 'Microsoft', 'Edge', 'Application', 'msedge.exe'),
                      os.path.join(base, 'Google', 'Chrome', 'Application', 'chrome.exe')]
    return next((c for c in cands if os.path.isfile(c)), None)


def open_window(url):
    """Uygulama penceresi (Edge/Chrome --app, panelin kendi tarayıcı profili) -> izlenebilen süreç ya da None."""
    b = browser()
    if not b:
        import webbrowser
        webbrowser.open(url)
        return None
    os.makedirs(TARAYICI_PROFILI, exist_ok=True)
    return subprocess.Popen([b, '--app=%s' % url, '--user-data-dir=%s' % TARAYICI_PROFILI, '--window-size=1360,880',
                             '--no-first-run', '--no-default-browser-check', '--disable-features=Translate,msEdgeSidebarV2',
                             '--disable-background-mode', '--disable-sync', '--lang=%s' % D.current()])


def watch_window(proc):
    STATE['pencere'] = proc
    STATE['pencere_izleniyor'] = True
    t0 = time.time()
    proc.wait()
    STATE['pencere_izleniyor'] = False
    if time.time() - t0 < DEVIR_SN:
        # aynı profil klasörüyle açık bir tarayıcı süreci varsa yeni süreç pencereyi ona devredip hemen çıkar (18, 20 ve 22 Ekim:
        # panel açılır açılmaz "kapandı" sayılıp kapanıyordu): pencere açık, kapanışı sayfanın nabzından anlaşılır (ticker)
        STATE['nabiz'] = time.time()
        log('panel penceresi açık bir tarayıcı sürecine devredildi; nabızla izleniyor')
        return
    log('panel penceresi kapandı')
    if CFG.get('pencere_kapaninca') == 'kapat':
        YON.stop_client()
        shutdown()
    STATE['pencere_kapandi'] = True


def create_shortcut():
    target = os.path.join(os.path.dirname(sys.executable), 'pythonw.exe')
    if not os.path.isfile(target):
        target = sys.executable
    script = os.path.join(ROOT, 'DarkOrbit Panel.pyw')
    folder = client_folder()
    icon = os.path.join(folder, 'DarkOrbit.exe') if folder and os.path.isfile(os.path.join(folder, 'DarkOrbit.exe')) else target
    ps = ("$d=[Environment]::GetFolderPath('Desktop'); $s=(New-Object -ComObject WScript.Shell).CreateShortcut((Join-Path $d "
          "'DarkOrbit.lnk')); $s.TargetPath=$env:DO_HEDEF; $s.Arguments=('\"'+$env:DO_BETIK+'\"'); $s.WorkingDirectory=$env:DO_KOK; "
          "$s.IconLocation=($env:DO_SIMGE+',0'); $s.Description=$env:DO_ACIKLAMA; $s.Save(); Join-Path $d 'DarkOrbit.lnk'")
    env = dict(os.environ, DO_HEDEF=target, DO_BETIK=script, DO_KOK=ROOT, DO_SIMGE=icon, DO_ACIKLAMA=_('DarkOrbit yerel sunucu paneli'))
    r = subprocess.run(['powershell', '-NoProfile', '-NonInteractive', '-Command', ps], capture_output=True, text=True, env=env,
                       timeout=30, creationflags=SR.NO_WINDOW, encoding='utf8', errors='replace')
    if r.returncode:
        raise Hata(_('Kısayol oluşturulamadı: %s', r.stderr.strip()[-300:]))
    return r.stdout.strip().splitlines()[-1]


# ------------------------------------------------------------------ API
def screen_size():
    try:
        import ctypes
        u = ctypes.windll.user32
        u.SetProcessDPIAware()
        return [u.GetSystemMetrics(0), u.GetSystemMetrics(1)]
    except Exception:
        return None


def _schema_row(s):
    out = dict(s, ad=_(s['ad']), aciklama=_(s['aciklama']))
    if s.get('secenekler'):
        out['secenekler'] = [_(x) for x in s['secenekler']]
    if s.get('secenek_aciklama'):
        out['secenek_aciklama'] = [_(x) for x in s['secenek_aciklama']]
    if s.get('birim'):
        out['birim'] = _(s['birim'])
    return out


def api_settings():
    hazir = {k: dict(p, ad=_(p['ad']), aciklama=_(p['aciklama'])) for k, p in AY.HAZIR.items()}
    return {'sema': [_schema_row(s) for s in AY.SCHEMA], 'gruplar': [{'anahtar': k, 'ad': _(a)} for k, a in AY.GRUPLAR],
            'degerler': game_settings(), 'varsayilan': AY.DEFAULTS, 'hazir': hazir, 'sablonlar': read_json(SABLONLAR, {}),
            'sunucu_acik': YON.running()}


def api_client():
    sel = CFG.get('istemci_klasoru')
    used = client_folder()
    return {'secili': sel, 'kullanilan': used, 'kontrol': IST.check(used), 'adaylar': IST.candidates(),
            'cozunurlukler': IST.COZUNURLUKLER, 'ekran': screen_size(), 'ayarlar': CFG.all(),
            'komut': ['DarkOrbit.exe'] + IST.args(CFG, 'logs\\client.log'), 'desteklenen': IST.supported(),
            'protokol': UYAR.state(), 'indirme': DL.state()}


def slot_arg(q):
    sid = q.get('id')
    if not sid or not KAY.exists(sid):
        raise Hata(_('Kayıt bulunamadı.'))
    return sid


def profile_values(sid):
    d = read_json(KAY.profile(sid), {})
    pl, g = d.get('pilot') or {}, d.get('gemi') or {}
    return {'pilot': pl.get('userName', ''), 'kredi': pl.get('credits', 0), 'uridyum': pl.get('uridium', 0),
            'onur': pl.get('honourPoints', 0), 'ep': pl.get('ep', 0), 'seviye': pl.get('level', 1),
            'can': g.get('hitPoints', 0), 'can_azami': g.get('hitMax', 0), 'kalkan': g.get('shield', 0),
            'kalkan_azami': g.get('shieldMax', 0), 'firma': FIRMALAR.get(pl.get('factionId'), '?'),
            'kullanimda': KAY.in_use(sid)}


def h_get(path, q):
    if path == '/api/durum':
        return status()
    if path == '/api/ayarlar':
        return api_settings()
    if path == '/api/etkinlikler':
        return event_list()
    if path == '/api/kayitlar':
        return {'liste': KAY.list(), 'aktif': KAY.active(), 'silinenler': KAY.deleted(), 'firmalar': FIRMALAR}
    if path == '/api/kayit_profili':
        return profile_values(slot_arg(q))
    if path == '/api/yedekler':
        sid = slot_arg(q)
        return {'liste': KAY.backups(sid), 'kayit': KAY.summary(sid), 'ayarlar': CFG.all()}
    if path == '/api/istemci':
        return api_client()
    if path == '/api/panel_ayarlari':
        return CFG.all()
    if path == '/api/portlar':
        return YON.foreign_ports()
    if path == '/api/gunluk':
        name = q.get('ad', 'gs.log')
        if name not in GUNLUKLER:
            raise Hata(_('Bilinmeyen günlük.'))
        p = os.path.join(YOL.LOGS, name)
        n = min(5000, max(50, int(q.get('satir', 400))))
        return {'ad': name, 'var': os.path.isfile(p), 'boyut': os.path.getsize(p) if os.path.isfile(p) else 0,
                'satirlar': SR.tail(p, n), 'liste': [{'ad': g, 'boyut': os.path.getsize(os.path.join(YOL.LOGS, g))
                                                       if os.path.isfile(os.path.join(YOL.LOGS, g)) else None} for g in GUNLUKLER]}
    if path == '/api/testler':
        return TEST.state()
    if path == '/api/istemci/indirme':              # istemci indirmenin durumu (indirme.py)
        return DL.state()
    if path == '/api/guncelleme':                   # GitHub'dan güncelleme (guncelleme.py)
        return dict(UPD.state(), ayar=CFG.get('guncelleme'), bosta=idle())
    if path == '/api/protokol':                     # protokol uyarlamasının durumu (protokol.py)
        return dict(UYAR.state(), etkin=IST.supported())
    if path == '/api/esya_listesi':                 # kayıt düzenleyicinin "eşya ver" listesi
        return {'esyalar': KAY.loot_list()}
    if path == '/api/canli':                        # canlı durum (oyun sunucusunun canli_durum.json'u; canli_durum.py)
        p = os.path.join(YOL.LOGS, 'canli_durum.json')
        d = read_json(p, None)
        if not d or (not YON.running() and time.time() - d.get('zaman', 0) > 15):    # eski dosya: sunucu kapalı
            return {'var': False, 'sunucu_acik': YON.running()}
        import takvim as TK
        d['etkinlik_adlari'] = [_(TK.EVENTS.get(k, {}).get('ad', k)) for k in d.get('etkinlikler', [])]
        return {'var': True, 'sunucu_acik': True, 'yas': max(0, time.time() - d.get('zaman', 0)), 'durum': d}
    if path == '/api/hakkinda':
        return {'surum': SURUM, 'python': sys.version.split()[0], 'kok': ROOT, 'sunucu': SERVER, 'kayitlar': YOL.KAYITLAR,
                'gunlukler': YOL.LOGS, 'ayarlar': YOL.AYARLAR, 'panel': YOL.PANEL, 'port': PORT, 'dil': D.current()}
    raise Hata(_('Bilinmeyen istek: %s', path))


def h_post(path, b):
    # ---- oyun ve sunucular
    if path == '/api/oyna':
        return start_launch(b.get('sadece_sunucu'))
    if path == '/api/sunucu/durdur':
        if YON.client_alive():
            raise Hata(_('Oyun açıkken sunucu durdurulamaz: önce oyunu kapatın.'))
        YON.stop_servers()
        return YON.status()
    if path == '/api/sunucu/yeniden':
        slot = YON.slot or KAY.active()
        if not slot:
            raise Hata(_('Kayıt yok.'))
        YON.stop_servers()
        YON.start_servers(KAY.profile(slot), YOL.AYARLAR, kontrol=bool(game_settings().get('kontrol')), slot=slot)
        return YON.status()
    if path == '/api/istemci/kapat':
        YON.stop_client()
        return YON.status()
    if path == '/api/portlar/kapat':
        pid = int(b.get('pid') or 0)
        info = SR.process_info(pid)
        if not (SR.is_our_server(info) or info['ad'].lower() == 'darkorbit.exe'):
            raise Hata(_('Bu süreç (%s) panelin sunucusu değil; panel kapatmaz. Gerekirse kendiniz kapatın.', info['ad']))
        m = re.search(r'"--durdur=([^"]+)"|--durdur=(\S+)', info.get('komut') or '')
        if m:                                       # önceki panelin oyun sunucusu: önce kaydedip kendisi çıksın
            try:
                open(m.group(1) or m.group(2), 'w').close()
                end = time.time() + 6
                while time.time() < end and pid in (SR.listeners() or {}).values():
                    time.sleep(0.2)
            except OSError:
                pass
        if pid in (SR.listeners() or {}).values() or not m:
            SR.kill(pid)
        log('eski süreç kapatıldı: %s %s' % (pid, info['ad']))
        time.sleep(0.5)
        return YON.foreign_ports()
    # ---- oyun ayarları
    if path == '/api/ayarlar':
        vals = game_settings()
        for k, v in (b.get('degerler') or {}).items():
            if k in AY.BY_KEY:
                vals[k] = v
        AY.write(YOL.AYARLAR, vals)
        return api_settings()
    if path == '/api/ayarlar/sifirla':
        vals = game_settings()
        keys = b.get('anahtarlar') or list(AY.BY_KEY)
        for k in keys:
            vals.pop(k, None)
        AY.write(YOL.AYARLAR, vals)
        return api_settings()
    if path == '/api/ayarlar/hazir':
        name = b.get('ad')
        user = read_json(SABLONLAR, {})
        preset = AY.HAZIR.get(name, {}).get('degerler') if name in AY.HAZIR else (user.get(name) or {}).get('degerler')
        if preset is None:
            raise Hata(_('Hazır ayar bulunamadı.'))
        vals = {k: v for k, v in game_settings().items() if k not in AY.BY_KEY}     # etkinlik seçimleri kalır
        vals.update(preset)
        AY.write(YOL.AYARLAR, vals)
        return api_settings()
    if path == '/api/ayarlar/sablon_kaydet':
        name = (b.get('ad') or '').strip()[:40]
        if not name:
            raise Hata(_('Şablona bir ad verin.'))
        user = read_json(SABLONLAR, {})
        vals = {k: v for k, v in game_settings().items() if k in AY.BY_KEY and v != AY.DEFAULTS[k]}
        user[name] = {'ad': name, 'aciklama': b.get('aciklama') or _('Kendi ayarın'), 'degerler': vals}
        write_json(SABLONLAR, user)
        return api_settings()
    if path == '/api/ayarlar/sablon_sil':
        user = read_json(SABLONLAR, {})
        user.pop(b.get('ad'), None)
        write_json(SABLONLAR, user)
        return api_settings()
    if path == '/api/etkinlikler':
        return set_events(b)
    # ---- kayıtlar
    if path == '/api/kayitlar/yeni':
        sid = KAY.create(b.get('ad'), b.get('pilot'), b.get('firma'), b.get('kredi'), b.get('uridyum'), b.get('seviye'), b.get('onur'),
                         b.get('lazer'), b.get('roket'))
        if b.get('aktif_yap', True):
            KAY.set_active(sid)
        log('yeni kayıt: %s' % sid)
        return {'id': sid}
    if path == '/api/kayitlar/aktif':
        return {'id': KAY.set_active(slot_arg(b))}
    if path == '/api/kayitlar/adlandir':
        return KAY.rename(slot_arg(b), b.get('ad'))
    if path == '/api/kayitlar/not':
        return KAY.set_note(slot_arg(b), b.get('not'))
    if path == '/api/kayitlar/kopyala':
        return {'id': KAY.duplicate(slot_arg(b), b.get('ad'))}
    if path == '/api/kayitlar/sil':
        return {'dosya': KAY.delete(slot_arg(b))}
    if path == '/api/kayitlar/geri_al':
        return {'id': KAY.undelete(b.get('dosya'))}
    if path == '/api/kayitlar/cop_bosalt':
        return {'silinen': KAY.purge(b.get('dosya'))}
    if path == '/api/kayitlar/disari':
        sid = slot_arg(b)
        name = '%s_%s.zip' % (sid, time.strftime('%Y%m%d'))
        dest = dialog('kaydet', title=_('Kaydı dışa aktar'), initialfile=name, defaultextension='.zip',
                      filetypes=[(_('DarkOrbit kaydı'), '*.zip')])
        if not dest:
            return {'iptal': True}
        KAY.export(sid, dest, bool(b.get('yedeklerle', True)))
        return {'yol': dest}
    if path == '/api/kayitlar/iceri':
        src = dialog('ac', title=_('Kayıt içe aktar'), filetypes=[(_('DarkOrbit kaydı'), '*.zip *.json'), (_('Tümü'), '*.*')])
        if not src:
            return {'iptal': True}
        return {'id': KAY.import_file(src)}
    if path == '/api/kayitlar/duzenle':
        return {'degisen': KAY.edit(slot_arg(b), b.get('degerler') or {})}
    # ---- yedekler
    if path == '/api/yedekler/al':
        return {'dosya': KAY.backup(slot_arg(b), 'elle', b.get('not') or '')}
    if path == '/api/yedekler/geri_yukle':
        return {'guvenlik': KAY.restore(slot_arg(b), b.get('dosya'))}
    if path == '/api/yedekler/sil':
        KAY.delete_backup(slot_arg(b), b.get('dosya'))
        return {}
    if path == '/api/yedekler/not':
        KAY.set_backup_note(slot_arg(b), b.get('dosya'), b.get('not'))
        return {}
    if path == '/api/yedekler/yeni_kayit':
        return {'id': KAY.backup_as_new(slot_arg(b), b.get('dosya'), b.get('ad'))}
    # ---- istemci ve panel ayarları
    if path == '/api/panel_ayarlari':
        CFG.update({k: v for k, v in (b.get('degerler') or {}).items() if k != 'aktif_kayit'})
        return api_client()
    if path == '/api/istemci/sec':
        start = client_folder() or ROOT
        p = dialog('klasor', title=_('DarkOrbit oyun klasörünü seçin (içinde DarkOrbit.exe ve DarkOrbit_Data olan)'), initialdir=start)
        if not p:
            return dict(api_client(), iptal=True)
        p = os.path.normpath(p)
        c = IST.check(p)
        if not c['gecerli'] and os.path.basename(p).lower() == IST.DATA_DIR.lower() and IST.check(os.path.dirname(p))['gecerli']:
            p = os.path.dirname(p)                    # DarkOrbit_Data seçildiyse üst klasörü
            c = IST.check(p)
        if not c['gecerli']:
            sub = [x for x in IST.candidates() if os.path.normcase(x['yol']).startswith(os.path.normcase(p))]
            if sub:
                p, c = sub[0]['yol'], sub[0]
            else:
                raise Hata(_('Seçilen klasör bir DarkOrbit istemcisi değil: %s', ' '.join(c['sorunlar'])))
        CFG.update({'istemci_klasoru': p})
        return api_client()
    if path == '/api/istemci/kullan':
        p = os.path.normpath(b.get('yol') or '')
        if not IST.check(p)['gecerli']:
            raise Hata(_('Klasör geçerli bir istemci değil.'))
        CFG.update({'istemci_klasoru': p})
        return api_client()
    if path == '/api/istemci/otomatik':
        CFG.update({'istemci_klasoru': None})
        return api_client()
    if path == '/api/guncelleme/denetle':
        UPD.check()
        STATE['sonraki_denetim'] = time.time() + GUNCELLEME_SN
        return h_get('/api/guncelleme', {})
    if path == '/api/guncelleme/kur':
        if not idle(strict=True):
            raise Hata(_('Önce oyunu, sunucuları ve süren işleri kapatın.'))
        try:
            UPD.install_async()
        except GuncellemeHatasi as e:
            raise Hata(str(e))
        return h_get('/api/guncelleme', {})
    if path == '/api/istemci/indir':                # oyunu indir ve proje köküne aç (sürer, kaldığı yerden)
        return DL.start()
    if path == '/api/istemci/indir_durdur':
        return DL.cancel()
    if path == '/api/istemci/indir_sil':            # yarım indirmenin geçici klasörü
        try:
            return DL.discard()
        except IndirmeHatasi as e:
            raise Hata(str(e))
    if path == '/api/protokol/uret':                # yeni istemciden protokol üret ve farkı raporla (etkin dosyalara dokunmaz)
        try:
            return UYAR.generate(os.path.normpath(b.get('yol') or client_folder() or ''))
        except RuntimeError as e:
            raise Hata(str(e))
    if path == '/api/protokol/uygula':              # üretilen sürümü etkin yap (oyun sunucusu yeniden başlatılınca)
        if YON.running():
            raise Hata(_('Önce oyun sunucusunu durdurun: protokol açılışta yükleniyor.'))
        try:
            return UYAR.activate(b.get('surum'))
        except RuntimeError as e:
            raise Hata(str(e))
    if path == '/api/testler/calistir':
        try:
            return TEST.start(b.get('adlar') or None)
        except RuntimeError as e:
            raise Hata(str(e))
    if path == '/api/testler/durdur':
        return TEST.stop()
    if path == '/api/gunluk/temizle':
        name = b.get('ad')
        if name not in GUNLUKLER:
            raise Hata(_('Bilinmeyen günlük.'))
        try:
            open(os.path.join(YOL.LOGS, name), 'w').close()
        except OSError:
            raise Hata(_('Günlük şu an bir sunucuda açık; sunucuyu durdurup yeniden deneyin.'))
        return {}
    if path == '/api/klasor_ac':
        what = b.get('ne')
        paths = {'proje': ROOT, 'kayitlar': YOL.KAYITLAR, 'gunlukler': YOL.LOGS, 'istemci': client_folder() or ROOT,
                 'sunucu': SERVER}
        if what in ('kayit', 'yedek'):
            sid = slot_arg(b)
            p = KAY.dir(sid) if what == 'kayit' else KAY.backup_dir(sid)
            os.makedirs(p, exist_ok=True)
            open_folder(p)
        elif what in paths:
            os.makedirs(paths[what], exist_ok=True) if what in ('kayitlar', 'gunlukler') else None
            open_folder(paths[what])
        else:
            raise Hata(_('Bilinmeyen klasör.'))
        return {}
    if path == '/api/kisayol':
        return {'yol': create_shortcut()}
    if path == '/api/kapat':
        if YON.client_alive() and not b.get('zorla'):
            raise Hata(_('Oyun açık: önce oyunu kapatın.'))
        YON.stop_client()
        threading.Thread(target=lambda: (time.sleep(0.3), shutdown()), daemon=True).start()
        return {}
    raise Hata(_('Bilinmeyen istek: %s', path))


TYPES = {'.html': 'text/html; charset=utf-8', '.css': 'text/css; charset=utf-8', '.js': 'application/javascript; charset=utf-8',
         '.svg': 'image/svg+xml', '.png': 'image/png', '.ico': 'image/x-icon', '.woff2': 'font/woff2'}


class Handler(BaseHTTPRequestHandler):
    server_version = 'DarkOrbitPanel/' + SURUM

    def log_message(self, fmt, *args):
        pass

    def _send(self, code, body, ctype='application/json; charset=utf-8', extra=None):
        data = body if isinstance(body, bytes) else json.dumps(body, ensure_ascii=False).encode('utf8')
        self.send_response(code)
        self.send_header('Content-Type', ctype)
        self.send_header('Content-Length', str(len(data)))
        self.send_header('Cache-Control', 'no-store')
        self.send_header('X-Content-Type-Options', 'nosniff')
        for k, v in (extra or {}).items():
            self.send_header(k, v)
        try:
            self.end_headers()
            self.wfile.write(data)
        except (ConnectionError, OSError):          # pencere yenilendi / kapandı: yanıtı bekleyen yok
            pass

    def _host_ok(self):
        host = (self.headers.get('Host') or '').split(':')[0]
        return host in ('127.0.0.1', 'localhost')

    def _api(self, fn, arg):
        if self.headers.get('X-Panel-Belirteci') != TOKEN:
            return self._send(403, {'hata': _('Geçersiz belirteç: paneli yeniden açın.')})
        try:
            out = fn(urlparse(self.path).path, arg)
        except (Hata, KayitHatasi, RuntimeError, ValueError) as e:
            return self._send(400, {'hata': str(e)})
        except Exception as e:
            log('API hatası %s: %s' % (self.path, traceback.format_exc()))
            return self._send(500, {'hata': _('Beklenmeyen hata: %r', e)})
        return self._send(200, out)

    def do_GET(self):
        if not self._host_ok():
            return self._send(403, {'hata': 'host'})
        u = urlparse(self.path)
        if u.path == '/api/ping':
            return self._send(200, {'panel': 'darkorbit', 'surum': SURUM, 'pid': os.getpid()})
        if u.path.startswith('/api/'):
            return self._api(h_get, {k: v[0] for k, v in parse_qs(u.query).items()})
        name = 'index.html' if u.path in ('/', '/index.html') else u.path.lstrip('/')
        p = os.path.normpath(os.path.join(ARAYUZ, name))
        if not p.startswith(ARAYUZ + os.sep) or not os.path.isfile(p):
            return self._send(404, b'yok', 'text/plain')
        data = open(p, 'rb').read()
        if name == 'index.html':
            data = data.replace(b'{{BELIRTEC}}', TOKEN.encode())
        self._send(200, data, TYPES.get(os.path.splitext(p)[1], 'application/octet-stream'),
                   {'Content-Security-Policy': "default-src 'self'; img-src 'self' data:; style-src 'self' 'unsafe-inline'"})

    def do_POST(self):
        if not self._host_ok():
            return self._send(403, {'hata': 'host'})
        u = urlparse(self.path)
        n = int(self.headers.get('Content-Length') or 0)
        raw = self.rfile.read(n) if n else b''
        if u.path == '/api/goster':                  # ikinci başlatma: pencereyi yeniden aç
            threading.Thread(target=open_window, args=('http://127.0.0.1:%d/' % PORT,), daemon=True).start()
            return self._send(200, {})
        if u.path == '/api/kapandi':                 # sayfa kapanıyor (sendBeacon): pencere izlenmiyorsa nabız erken düşsün
            if not STATE['pencere_izleniyor']:
                STATE['nabiz'] = time.time() - NABIZ_SN + 8
            return self._send(200, {})
        try:
            body = json.loads(raw.decode('utf8') or '{}')
        except ValueError:
            return self._send(400, {'hata': _('JSON değil')})
        return self._api(h_post, body if isinstance(body, dict) else {})


class Sunucu(ThreadingHTTPServer):
    # HTTPServer SO_REUSEADDR açıyor; Windows'ta bu, dinlenen porta ikinci bir süreci de bağlatıyor: ikinci başlatma açık paneli
    # görmeden aynı portta ikinci bir panel açıyordu (canlı tur 2). Kapalıyken bağlanamaz, açık panelin penceresini açtırır (main)
    allow_reuse_address = False


def main():
    global PORT
    PORT = next((int(a.split('=', 1)[1]) for a in sys.argv if a.startswith('--port=') and a.split('=', 1)[1].isdigit()), PORT)
    srv = None
    if STATE['guncellendi']:                          # güncellemeden sonra: eski süreç portu bırakana dek bekle
        for _k in range(75):
            try:
                srv = Sunucu(('127.0.0.1', PORT), Handler)
                break
            except OSError:
                time.sleep(0.2)
    try:
        srv = srv or Sunucu(('127.0.0.1', PORT), Handler)
    except OSError:
        try:                                          # panel zaten açık mı?
            with urlopen('http://127.0.0.1:%d/api/ping' % PORT, timeout=2) as r:
                if json.load(r).get('panel') == 'darkorbit':
                    urlopen(Request('http://127.0.0.1:%d/api/goster' % PORT, data=b'{}', method='POST'), timeout=5).read()
                    return
        except Exception:
            pass
        srv = Sunucu(('127.0.0.1', 0), Handler)       # port başka programda: boş bir port
        PORT = srv.server_address[1]
    srv.daemon_threads = True
    STATE['srv'] = srv
    log('panel açıldı: http://127.0.0.1:%d/ (python %s)%s' % (PORT, sys.version.split()[0], ' (güncellemeden sonra)' if STATE['guncellendi'] else ''))
    try_migrate()
    if not CFG.get('aktif_kayit') and KAY.slots():
        CFG.update({'aktif_kayit': KAY.slots()[0]})
    threading.Thread(target=ticker, daemon=True).start()
    if '--pencere-yok' not in sys.argv:
        proc = open_window('http://127.0.0.1:%d/' % PORT)
        if proc:
            threading.Thread(target=watch_window, args=(proc,), daemon=True).start()
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        shutdown()


if __name__ == '__main__':
    try:
        main()
    except Exception:
        log('panel başlatılamadı: %s' % traceback.format_exc())
        try:
            import ctypes
            ctypes.windll.user32.MessageBoxW(0, _('Panel başlatılamadı. Ayrıntı: server\\logs\\panel.log\n\n%s',
                                                  traceback.format_exc()[-900:]), 'DarkOrbit Panel', 0x10)
        except Exception:
            pass
        raise
