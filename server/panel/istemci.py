"""Oyun istemcisi (orijinal Unity istemcisi): klasör doğrulama, kendiliğinden bulma, sürüm, başlatma argümanları.

Klasör: içinde DarkOrbit.exe ve DarkOrbit_Data/ olan klasör (DarkOrbit_Version1.1.115 gibi). Panel ayarı boşsa proje kökündeki
en yeni sürüm klasörü kullanılır; güncelleme gelirse ya da klasör taşınırsa panelden seçilir. Bilgisayarda yoksa panel indirir
(indirme.py; yarım indirmenin geçici klasörü aday sayılmaz). Sunucu 1.1.115'in protokolüyle
yazıldı (data/protocol*.json istemcinin kodundan): başka sürümde panel uyarır.
İstemci dosyaları değiştirilmez; yalnız başlatma argümanı verilir (yerel web girişi 127.0.0.1:8090).
"""
import glob, os, re, subprocess

from dil import t as _
from indirme import GECICI

PANEL_DIR = os.path.dirname(os.path.abspath(__file__))
SERVER = os.path.dirname(PANEL_DIR)
ROOT = os.path.dirname(SERVER)
EXE = 'DarkOrbit.exe'
DATA_DIR = 'DarkOrbit_Data'
DESTEKLENEN = '1.1.115'          # etkin protokolün sürümü yoksa (server/data/protokol/surum.txt; protokol_guncelle.py yazar)
SURUM_DOSYASI = os.path.join(SERVER, 'data', 'protokol', 'surum.txt')


def supported():
    """Sunucunun etkin protokolünün istemci sürümü."""
    try:
        return open(SURUM_DOSYASI, encoding='utf8').read().strip() or DESTEKLENEN
    except OSError:
        return DESTEKLENEN
GIRIS_URL = 'http://127.0.0.1:8090/#darkorbit://'
COZUNURLUKLER = [(1280, 720), (1366, 768), (1440, 900), (1600, 900), (1680, 1050), (1920, 1080), (2560, 1440), (3840, 2160)]


def version_of(folder):
    """Sürüm: klasör adından (DarkOrbit_Version1.1.115), yoksa exe'nin dosya sürümünden; bilinmiyorsa None."""
    m = re.search(r'(\d+\.\d+\.\d+)', os.path.basename(os.path.normpath(folder)))
    if m:
        return m.group(1)
    try:
        import ctypes
        from ctypes import wintypes
        exe = os.path.join(folder, EXE)
        size = ctypes.windll.version.GetFileVersionInfoSizeW(exe, None)
        if not size:
            return None
        buf = ctypes.create_string_buffer(size)
        ctypes.windll.version.GetFileVersionInfoW(exe, 0, size, buf)
        p, n = ctypes.c_void_p(), wintypes.UINT()
        ctypes.windll.version.VerQueryValueW(buf, '\\', ctypes.byref(p), ctypes.byref(n))
        ffi = ctypes.cast(p, ctypes.POINTER(wintypes.DWORD * 13)).contents
        ms, ls = ffi[2], ffi[3]
        return '%d.%d.%d' % (ms >> 16, ms & 0xFFFF, ls >> 16)
    except Exception:
        return None


def check(folder):
    """Klasörü doğrula -> {'gecerli', 'yol', 'exe', 'veri', 'surum', 'uyumlu', 'sorunlar' [...], 'boyut_mb'}."""
    out = {'yol': folder or '', 'gecerli': False, 'exe': False, 'veri': False, 'surum': None, 'uyumlu': False, 'sorunlar': []}
    if not folder:
        out['sorunlar'].append(_('İstemci klasörü seçilmedi.'))
        return out
    if not os.path.isdir(folder):
        out['sorunlar'].append(_('Klasör bulunamadı.'))
        return out
    out['exe'] = os.path.isfile(os.path.join(folder, EXE))
    out['veri'] = os.path.isdir(os.path.join(folder, DATA_DIR))
    if not out['exe']:
        out['sorunlar'].append(_('Klasörde %s yok.', EXE))
    if not out['veri']:
        out['sorunlar'].append(_('Klasörde %s klasörü yok.', DATA_DIR))
    out['gecerli'] = out['exe'] and out['veri']
    if out['gecerli']:
        out['surum'] = version_of(folder)
        out['uyumlu'] = out['surum'] == supported()
        if out['surum'] and not out['uyumlu']:
            out['sorunlar'].append(_('Sunucu %s sürümü için yazıldı; %s sürümünde protokol farklıysa giriş ya da bazı pencereler '
                                     'çalışmayabilir.', supported(), out['surum']))
        out['metadata'] = os.path.isfile(os.path.join(folder, DATA_DIR, 'il2cpp_data', 'Metadata', 'global-metadata.dat'))
    return out


def candidates():
    """Olası istemci klasörleri: proje kökü, Program Files, LocalAppData, masaüstü, İndirilenler (en yeni sürüm önce)."""
    pats = [os.path.join(ROOT, 'DarkOrbit*'), os.path.join(ROOT, '*', 'DarkOrbit*')]
    for env in ('PROGRAMFILES', 'PROGRAMFILES(X86)', 'LOCALAPPDATA', 'APPDATA'):
        base = os.environ.get(env)
        if base:
            pats += [os.path.join(base, 'DarkOrbit*'), os.path.join(base, 'Bigpoint', '*'), os.path.join(base, 'DarkOrbit*', '*')]
    home = os.path.expanduser('~')
    for sub in ('Desktop', 'Downloads', 'Masaüstü', 'İndirilenler', 'Documents'):
        pats += [os.path.join(home, sub, 'DarkOrbit*'), os.path.join(home, sub, 'DarkOrbit*', 'DarkOrbit*')]
    seen, out = set(), []
    for pat in pats:
        for d in glob.glob(pat):
            d = os.path.normpath(d)
            key = d.lower()
            if key in seen or not os.path.isdir(d) or GECICI.lower() in key.split(os.sep):
                continue
            seen.add(key)
            c = check(d)
            if c['gecerli']:
                out.append(c)
    vkey = lambda c: tuple(int(x) for x in (c['surum'] or '0.0.0').split('.'))
    out.sort(key=lambda c: (c['uyumlu'], vkey(c)), reverse=True)
    return out


def resolve(configured):
    """Ayardaki klasör, yoksa bulunan en uygun klasör (None olabilir)."""
    if configured:
        return configured
    c = candidates()
    return c[0]['yol'] if c else None


def args(cfg, log_file):
    """Unity başlatma argümanları (panel ayarlarından)."""
    a = [GIRIS_URL]
    mode = cfg.get('pencere_modu')
    if mode == 'tam_ekran':
        a += ['-screen-fullscreen', '1', '-window-mode', 'exclusive']
    elif mode == 'kenarliksiz':                       # kenarlıksız tam ekran pencere (Unity 2019.3+)
        a += ['-screen-fullscreen', '1', '-window-mode', 'borderless']
    else:
        a += ['-screen-fullscreen', '0']
    a += ['-screen-width', str(cfg.get('genislik')), '-screen-height', str(cfg.get('yukseklik'))]
    if cfg.get('monitor'):
        a += ['-monitor', str(cfg.get('monitor'))]
    extra = (cfg.get('ek_argumanlar') or '').strip()
    if extra:
        import shlex
        a += shlex.split(extra, posix=False)
    a += ['-logFile', log_file]
    return a


def running_clients():
    """Açık DarkOrbit.exe süreçlerinin kimlikleri (panelin açmadıkları dahil)."""
    try:
        r = subprocess.run(['tasklist', '/FI', 'IMAGENAME eq %s' % EXE, '/FO', 'CSV', '/NH'], capture_output=True, text=True,
                           timeout=10, creationflags=0x08000000)
        return [int(line.split('","')[1]) for line in r.stdout.splitlines() if line.startswith('"%s"' % EXE)]
    except Exception:
        return []
