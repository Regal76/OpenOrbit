"""İstemciyi Windows dışında açan katman (panel): orijinal istemci 32 bitlik bir Windows programı (DarkOrbit.exe, Unity); Linux ve
macOS'ta Wine ya da Proton ile açılır. Windows'ta komut yalnız exe ve argümanlarıdır.

Panel ayarları (yapilandirma.py):
  calistirici       otomatik | wine | proton | ozel. otomatik: Linux'ta Proton (umu-run ya da Steam'in Proton'u), yoksa Wine; macOS'ta
                    Wine (Proton yalnız Linux'ta).
  calistirici_yolu  wine: wine programı; proton: Proton klasörü (içinde proton betiği olan); ozel: istemcinin önüne eklenecek komut
                    (ör. CrossOver'ın wine'ı --bottle ile). Boşsa kendiliğinden bulunur (ozel'de gerekli).
  wine_onek         Wine öneki (WINEPREFIX) ya da Proton'un veri klasörü (STEAM_COMPAT_DATA_PATH). Boşsa save/wine ya da save/proton:
                    istemci öteki Wine programlarından ayrı bir önekte; önek ilk açılışta kurulur (yarım dakika kadar sürebilir).
Proton Steam'siz açılır: umu-run kuruluysa onunla (Steam Linux Runtime kabında; PROTONPATH bulunan Proton, yoksa umu kendi Proton'unu
indirir), değilse "proton run" ile (STEAM_COMPAT_CLIENT_INSTALL_PATH Steam'in klasörü; Steam yoksa veri klasörü). Fiil "run": ek
istemciler (coklu.py) aynı önekte birlikte açılır (waitforexitandrun öncekinin kapanmasını beklerdi). İstemciye verilen dosya yolları
Z: sürücüsünden (Wine ve Proton öneklerinde Unix kökü). Wine'ın çıktısı logs/wine.log'a (surecler.istemci_ac).
"""
import functools, glob, os, re, shlex, shutil, subprocess, sys

from dil import t as _

WINDOWS, LINUX, MAC = os.name == 'nt', sys.platform.startswith('linux'), sys.platform == 'darwin'   # testler değiştirir


def varsayilan_onek(tur):
    """save/wine ya da save/proton (yollar burada içe aktarılır: istemci.py'yi yalnız panel/ yoluyla içe aktaranlar var)."""
    import yollar
    return os.path.join(yollar.SAVE, tur)


def win_yolu(p):
    """Wine'daki Windows programına verilecek dosya yolu (Z: Unix kökü); Windows'ta aynen."""
    return p if WINDOWS else 'Z:' + os.path.abspath(p).replace('/', '\\')


def steam_klasorleri():
    """Steam'in kurulu olduğu klasörler (yerel paket, Flatpak, Snap)."""
    home, out = os.path.expanduser('~'), []
    for p in ('.steam/root', '.steam/steam', '.local/share/Steam', '.var/app/com.valvesoftware.Steam/data/Steam',
              'snap/steam/common/.local/share/Steam'):
        d = os.path.realpath(os.path.join(home, p))
        if d not in out and os.path.isdir(os.path.join(d, 'steamapps')):
            out.append(d)
    return out


def _surum_anahtari(ad):
    """Proton - Experimental en yeni; ötekiler adlarındaki sayılarla (Proton 9.0, GE-Proton10-3)."""
    return (999,) if 'experimental' in ad.lower() else tuple(int(x) for x in re.findall(r'\d+', ad)) or (0,)


def protonlar():
    """Bulunan Proton kurulumları [{'ad', 'yol', 'steam'}], en yeni önce: Steam kütüphanelerindeki Proton'lar (steamapps/common) ve ek
    uyumluluk araçları (compatibilitytools.d: GE-Proton …). Linux dışında boş."""
    if not LINUX:
        return []
    dirs = []
    for steam in steam_klasorleri():
        libs = [steam]
        try:
            with open(os.path.join(steam, 'steamapps', 'libraryfolders.vdf'), encoding='utf8', errors='replace') as fh:
                libs += re.findall(r'"path"\s+"([^"]+)"', fh.read())
        except OSError:
            pass
        for lib in libs:
            dirs += [(d, steam) for d in glob.glob(os.path.join(lib, 'steamapps', 'common', 'Proton*'))]
        dirs += [(d, steam) for d in glob.glob(os.path.join(steam, 'compatibilitytools.d', '*'))]
    dirs += [(d, None) for d in glob.glob('/usr/share/steam/compatibilitytools.d/*')]
    seen, out = set(), []
    for d, steam in dirs:
        d = os.path.realpath(d)
        if d not in seen and os.path.isfile(os.path.join(d, 'proton')):
            seen.add(d)
            out.append({'ad': os.path.basename(d), 'yol': d, 'steam': steam})
    out.sort(key=lambda p: _surum_anahtari(p['ad']), reverse=True)
    return out


def wineler():
    """Bulunan wine programları: PATH ve bilinen yerler (macOS'ta Wine uygulamaları ve Homebrew; Finder'dan açılınca PATH kısa)."""
    cands = [shutil.which('wine')]
    if MAC:
        cands += ['/Applications/Wine %s.app/Contents/Resources/wine/bin/wine' % k for k in ('Stable', 'Devel', 'Staging')]
        cands += ['/opt/homebrew/bin/wine', '/usr/local/bin/wine']
    seen, out = set(), []
    for c in cands:
        if c and os.path.isfile(c) and os.access(c, os.X_OK) and os.path.realpath(c) not in seen:
            seen.add(os.path.realpath(c))
            out.append(c)
    return out


@functools.lru_cache(maxsize=8)
def wine_surumu(wine):
    try:
        return subprocess.run([wine, '--version'], capture_output=True, text=True, timeout=15).stdout.strip() or None
    except (OSError, subprocess.SubprocessError):
        return None


def bul(cfg):
    """Kullanılacak çalıştırıcı -> {'tur': yerel|wine|proton|ozel, 'yol', 'ad', 'onek', 'umu', 'steam', 'hata'}. yol: wine programı,
    Proton klasörü ya da özel komut; hata: istemci açılamaz (kullanıcıya gösterilir)."""
    r = {'tur': 'yerel', 'yol': None, 'ad': None, 'onek': None, 'umu': None, 'steam': None, 'hata': None}
    if WINDOWS:
        return r
    secim, yol, onek = cfg.get('calistirici'), cfg.get('calistirici_yolu').strip(), cfg.get('wine_onek').strip()
    umu = shutil.which('umu-run') if LINUX else None
    if secim == 'otomatik':
        secim = 'proton' if LINUX and (umu or protonlar()) else 'wine'
    r['tur'] = secim
    if secim == 'ozel':
        r.update(yol=yol, onek=os.path.expanduser(onek) if onek else None)
        if not yol:
            r['hata'] = _('Özel komut boş: İstemci sayfasında Wine / Proton kartından yaz.')
        return r
    r['onek'] = os.path.expanduser(onek) if onek else varsayilan_onek(secim)
    if secim == 'proton':
        if not LINUX:
            r['hata'] = _("Proton yalnız Linux'ta çalışır: Wine'ı seç.")
            return r
        bulunan = protonlar()
        p = bulunan[0] if bulunan else None
        if yol:
            d = os.path.expanduser(yol)
            d = os.path.dirname(d) if os.path.basename(d) == 'proton' else d
            if not os.path.isfile(os.path.join(d, 'proton')):
                r['hata'] = _('Proton bulunamadı: %s klasöründe proton betiği yok.', d)
                return r
            p = next((x for x in bulunan if x['yol'] == os.path.realpath(d)), {'ad': os.path.basename(d), 'yol': d, 'steam': None})
        if not p and not umu:
            r['hata'] = _("Proton bulunamadı: Steam'de bir Proton sürümü kur (Kütüphane > Araçlar) ya da Wine'ı seç.")
            return r
        steam = (p and p['steam']) or next(iter(steam_klasorleri()), None)
        r.update(yol=p and p['yol'], ad=p['ad'] if p else 'UMU-Proton', umu=umu, steam=steam)
        return r
    w = shutil.which(os.path.expanduser(yol)) if yol else next(iter(wineler()), None)
    if not w:
        if yol:
            r['hata'] = _('Wine bulunamadı: %s', yol)
        elif not LINUX:
            r['hata'] = _('Wine bulunamadı: Wine kur (ör. brew install --cask wine-stable).')
        elif cfg.get('calistirici') == 'otomatik':
            r['hata'] = _("Wine ya da Proton bulunamadı: Steam'de bir Proton sürümü kur (Kütüphane > Araçlar) ya da Wine kur (ör. sudo apt "
                          "install wine).")
        else:
            r['hata'] = _("Wine bulunamadı: Wine kur (ör. sudo apt install wine) ya da Proton'u seç.")
        return r
    r.update(yol=w, ad=wine_surumu(w) or 'wine')
    return r


def komut(cfg, exe, args):
    """İstemcinin başlatma komutu ve ortamı -> (komut, ortam); ortam None: panelinki. Çalıştırıcı yoksa RuntimeError."""
    r = bul(cfg)
    if r['tur'] == 'yerel':
        return [exe] + args, None
    if r['hata']:
        raise RuntimeError(r['hata'])
    env = dict(os.environ)
    if r['tur'] == 'ozel':
        if r['onek']:
            env['WINEPREFIX'] = r['onek']
        return shlex.split(r['yol']) + [exe] + args, env
    if r['tur'] == 'wine':
        env['WINEPREFIX'] = r['onek']
        env.setdefault('WINEDLLOVERRIDES', 'mscoree,mshtml=')     # yeni önekte Mono/Gecko kurulum pencereleri çıkmasın (istemci kullanmaz)
        env.setdefault('WINEDEBUG', 'fixme-all')                 # wine.log yalnız hatalar
        return [r['yol'], exe] + args, env
    if r['umu']:
        env.update(WINEPREFIX=r['onek'], PROTON_VERB='run')
        if r['yol']:
            env['PROTONPATH'] = r['yol']
        return [r['umu'], exe] + args, env
    env.update(STEAM_COMPAT_DATA_PATH=r['onek'], STEAM_COMPAT_CLIENT_INSTALL_PATH=r['steam'] or r['onek'])
    return [os.path.join(r['yol'], 'proton'), 'run', exe] + args, env


def ozet(cfg):
    """İstemci sayfasının Wine / Proton kartı: seçilen ve bulunan çalıştırıcılar (Windows'ta None)."""
    if WINDOWS:
        return None
    return dict(bul(cfg), platform='darwin' if MAC else sys.platform, protonlar=protonlar(), wineler=wineler(),
                varsayilan_onek={k: varsayilan_onek(k) for k in ('wine', 'proton')})
