"""İstemcinin düzeltmeleri BepInEx ile (yalnız Windows): panel BepInEx 6'yı (Unity IL2CPP, 32 bit) istemci klasörüne kurar ve
eklenti/OpenOrbitYama.dll'i BepInEx/plugins'e koyar. Yamalar (müzayede sayacı, rütbe penceresi, mağaza tutarı) eklentinin kaynağında:
eklenti/Yamalar.cs. README'deki "istemci yamalanmaz" kuralının kullanıcı onaylı istisnası (2026-10-24; BepInEx'e geçiş 2026-10-25,
önceki bellek yamalarının yerine).

İstemcinin kendi dosyaları değişmez; yanına BepInEx'in dosyaları eklenir (winhttp.dll, doorstop_config.ini, .doorstop_version,
changelog.txt, BepInEx/, dotnet/). Doorstop ayarda kapalı: panel istemciyi --doorstop-enabled true ile açar (istemci.komut), aynı
istemci başka yoldan (resmî başlatıcı) açılırsa BepInEx yüklenmez. BepInEx'in konsol penceresi kapalı (BepInEx/config/BepInEx.cfg).
Eklentinin kopyası her açılışta paneldekiyle aynı mı diye bakılır (panel güncellenince yenilenir).

Kurulum: kurulum sihirbazının oyun klasörü adımında, istemci indirilince, İstemci sayfasından ya da ilk OYNA'da. BepInEx arşivi ve
Unity'nin temel kitaplıkları (BepInEx ilk açılışta indirirdi; önceden konunca ilk açılış da internetsiz) belleğe iner, SHA-256'ları
tutarsa açılır; bitince KAYIT yazılır (yarım kurulum kurulu sayılmaz). İstemcinin ilk açılışında BepInEx istemcinin kodundan interop
derlemelerini üretir (yarım dakika kadar; sonraki açılışlar hızlı). Kurulamazsa oyun düzeltmeler olmadan açılır.
"""
import hashlib, http.client, io, json, os, shutil, threading, time, zipfile
from urllib.request import Request, urlopen

from dil import t as _
from indirme import PARCA, ZAMAN_ASIMI, IndirmeHatasi, Iptal, safe_path

PANEL_DIR = os.path.dirname(os.path.abspath(__file__))
WINDOWS = os.name == 'nt'
# BepInEx bleeding edge (builds.bepinex.dev): be.788 (2026-09-01) 1.1.115'te denendi (Unity 2022.3.58, IL2CPP metadata v31).
# Değiştirince sha256 de değişir; kurulu eskisinin üstüne yeniden kurulur.
BEPINEX = {'ad': 'BepInEx 6.0.0-be.788',
           'url': 'https://builds.bepinex.dev/projects/bepinex_be/788/BepInEx-Unity.IL2CPP-win-x86-6.0.0-be.788%2B5b766a3.zip',
           'sha256': 'd5954a5993ec39cd1133603d85bff93875d30b6411b712cc13dcf03c8e08a4d3', 'boyut': 31440336}
UNITY = {'ad': 'Unity 2022.3.58', 'url': 'https://unity.bepinex.dev/libraries/2022.3.58.zip',
         'sha256': '37b5b6d5f3a8761ecd8415302f0283e86c552c822a456faaec33aae533ba32ae', 'boyut': 1898155,
         'yol': 'BepInEx/unity-libs/2022.3.58.zip'}
EKLENTI = os.path.join(PANEL_DIR, 'eklenti', 'OpenOrbitYama.dll')
EKLENTI_YOLU = 'BepInEx/plugins/OpenOrbitYama.dll'
AYAR = 'BepInEx/config/BepInEx.cfg'
KAYIT = 'BepInEx/openorbit.json'        # kurulumun bittiğini ve sürümünü söyler
ARGUMANLAR = ['--doorstop-enabled', 'true']


def yol(folder, rel):
    return os.path.join(folder, *rel.split('/'))


def kurulu(folder):
    """BepInEx bu klasöre kurulmuş mu (kurulum bitmiş, sürümü güncel)?"""
    try:
        with open(yol(folder, KAYIT), encoding='utf8') as fh:
            d = json.load(fh)
    except (OSError, ValueError):
        return False
    return d.get('bepinex') == BEPINEX['sha256'] and os.path.isfile(os.path.join(folder, 'winhttp.dll'))


def eklenti(folder):
    """Eklentinin kopyası paneldekinden farklıysa (yoksa) yenile."""
    with open(EKLENTI, 'rb') as fh:
        yeni = fh.read()
    p = yol(folder, EKLENTI_YOLU)
    try:
        with open(p, 'rb') as fh:
            if fh.read() == yeni:
                return
    except OSError:
        pass
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, 'wb') as fh:
        fh.write(yeni)


def argumanlar(folder):
    """İstemciyi BepInEx'le açan argümanlar (Windows dışında ya da kurulu değilse yok); eklentinin kopyası önce yenilenir."""
    if not WINDOWS or not kurulu(folder):
        return []
    eklenti(folder)
    return list(ARGUMANLAR)


class Yamaci:
    def __init__(self, log=print, opener=urlopen):
        self.log, self.opener = log, opener
        self.lock = threading.Lock()
        self.stop = threading.Event()
        self.d = self._blank('yok', None)

    @staticmethod
    def _blank(durum, folder):
        return {'durum': durum, 'calisiyor': False, 'alinan': 0, 'toplam': BEPINEX['boyut'] + UNITY['boyut'], 'hata': None,
                'klasor': folder}

    def state(self, folder):
        """folder'daki kurulumun durumu (başka klasörün biten işi sayılmaz)."""
        with self.lock:
            d = dict(self.d)
        if not d['calisiyor'] and (not folder or not d['klasor'] or os.path.normcase(os.path.abspath(d['klasor']))
                                   != os.path.normcase(os.path.abspath(folder))):
            d = self._blank('yok', folder)
        if not d['calisiyor'] and folder and kurulu(folder):
            d['durum'] = 'kurulu'
        d.update(gerekli=WINDOWS, ad=BEPINEX['ad'])
        return d

    def running(self):
        with self.lock:
            return self.d['calisiyor']

    def start(self, folder):
        """BepInEx'i ve eklentiyi istemci klasörüne kur (Windows değilse, sürüyorsa ya da kuruluysa bir şey yapmaz) -> durum."""
        with self.lock:
            if WINDOWS and folder and not self.d['calisiyor'] and not kurulu(folder):
                self.stop.clear()
                self.d = dict(self._blank('indiriliyor', folder), calisiyor=True)
                threading.Thread(target=self._run, args=(folder,), daemon=True).start()
        return self.state(folder)

    def cancel(self):
        self.stop.set()

    def bekle(self, folder, adim=None):
        """Kurulum bitene dek bekle (adim: (yüzde) -> None, ilerleme) -> kuruldu mu."""
        self.start(folder)
        while self.running():
            if adim:
                st = self.state(folder)
                adim(int(100 * st['alinan'] / st['toplam']))
            time.sleep(0.3)
        return kurulu(folder)

    def _indir(self, parca):
        """Arşivi belleğe indir ve SHA-256'sını doğrula -> bayt."""
        buf = bytearray()
        try:
            with self.opener(Request(parca['url'], headers={'User-Agent': 'OpenOrbit'}), timeout=ZAMAN_ASIMI) as r:
                while True:
                    if self.stop.is_set():
                        raise Iptal()
                    b = r.read(PARCA)
                    if not b:
                        break
                    buf += b
                    with self.lock:
                        self.d['alinan'] += len(b)
        except (OSError, http.client.HTTPException) as e:
            raise IndirmeHatasi(_('İndirme sunucusuna bağlanılamadı (internet bağlantını denetle): %s', e))
        if hashlib.sha256(buf).hexdigest() != parca['sha256']:
            raise IndirmeHatasi(_('%s beklenen dosya değil (SHA-256 tutmadı): yeniden dene.', parca['ad']))
        return bytes(buf)

    def _run(self, folder):
        try:
            self.log('BepInEx indiriliyor: %s, %s' % (BEPINEX['url'], UNITY['url']))
            arsiv, unity = self._indir(BEPINEX), self._indir(UNITY)
            with self.lock:
                self.d['durum'] = 'kuruluyor'
            with zipfile.ZipFile(io.BytesIO(arsiv)) as z:
                for m in z.infolist():
                    p = safe_path(folder, m.filename)
                    if m.is_dir():
                        os.makedirs(p, exist_ok=True)
                        continue
                    os.makedirs(os.path.dirname(p), exist_ok=True)
                    with z.open(m) as src, open(p, 'wb') as out:
                        shutil.copyfileobj(src, out)
            p = os.path.join(folder, 'doorstop_config.ini')      # Doorstop kapalı: BepInEx'i yalnız panelin argümanı açar
            with open(p, 'rb') as fh:
                ini = fh.read()
            with open(p, 'wb') as fh:
                fh.write(ini.replace(b'enabled = true', b'enabled = false', 1))
            p = yol(folder, AYAR)
            if not os.path.isfile(p):                           # konsol penceresi açılmasın (öteki ayarları BepInEx ekler)
                os.makedirs(os.path.dirname(p), exist_ok=True)
                with open(p, 'wb') as fh:
                    fh.write(b'[Logging.Console]\n\nEnabled = false\n')
            p = yol(folder, UNITY['yol'])
            os.makedirs(os.path.dirname(p), exist_ok=True)
            with open(p, 'wb') as fh:
                fh.write(unity)
            eklenti(folder)
            with open(yol(folder, KAYIT), 'w', encoding='utf8') as fh:
                json.dump({'bepinex': BEPINEX['sha256'], 'unity': UNITY['sha256'], 'ad': BEPINEX['ad'],
                           'zaman': time.strftime('%Y-%m-%d %H:%M:%S')}, fh, indent=1)
            with self.lock:
                self.d.update(durum='kurulu', alinan=self.d['toplam'])
            self.log('BepInEx kuruldu: %s (%s)' % (BEPINEX['ad'], folder))
        except Iptal:
            with self.lock:
                self.d['durum'] = 'durdu'
            self.log('BepInEx kurulumu durduruldu')
        except IndirmeHatasi as e:
            with self.lock:
                self.d.update(durum='hata', hata=str(e))
            self.log('BepInEx kurulamadı: %s' % e)
        except OSError as e:
            with self.lock:
                self.d.update(durum='hata', hata=_('Dosya yazılamadı: %s', e))
            self.log('BepInEx kurulamadı: %r' % e)
        except Exception as e:
            with self.lock:
                self.d.update(durum='hata', hata=repr(e))
            self.log('BepInEx: beklenmeyen hata: %r' % e)
        finally:
            with self.lock:
                self.d['calisiyor'] = False
