"""macOS: istemciyi açan Wine'ı panel kendisi kurar (calistirici 'motor', macOS'ta Otomatik'in seçimi). Açık kaynak bir Wine derlemesi
(MOTOR) ve DXMT (Direct3D 11'i Metal'e çeviren katman, github.com/3Shain/dxmt) save/wine_motoru/'na iner; kullanıcı hiçbir şey kurmaz.
Apple Silicon'da yalnız Rosetta 2 gerekir (Wine x86_64): panelin düğmesi macOS'un yönetici penceresiyle kurar (rosetta_kur).

Neden bu ikisi: istemci 32 bitlik ve yalnız Direct3D 11 (Unity 2022.3). macOS'un OpenGL'i 4.1'de kaldığı için Wine'ın kendi D3D11'i
(wined3d) açılmıyor; DXVK MoltenVK üzerinde 32 bitte çalışmıyor (GitHub issue #7). DXMT çalışıyor ama Wine'ın winemac.drv'si DXMT'nin
istediği işlevleri (macdrv_functions) dışa açmalı (WineHQ'nun düz macOS derlemeleri açmıyor) ve gömülü tarayıcı (Vuplex) paylaşılan
D3D11 dokusu açtığı için Wine 10.18 ya da daha yenisi gerekiyor (D3DKMT; Wine 10.0 tabanlı motorlarda Vuplex çöküyor). MOTOR ikisini
de karşılar.

Arşivler diske kaydedilmez: HTTP'den akarak açılır (indirme.HttpFile; kopan bağlantı aynı bayttan sürer). SHA-256 akarken hesaplanır,
tutmazsa açılan her şey silinir. Arşivden yalnız 'kok' altı alınır. DXMT'nin builtin DLL'leri motorun lib/wine/<mimari>/ klasörlerine
kopyalanır: her önekte d3d11, dxgi ve d3d10core DXMT olur (öneğe DLL konmaz, geçersiz kılma gerekmez). Kurulum geçici klasörde
toplanır, bitince adını alır: yarım kurulum kullanılmaz. Aynı anda tek iş.
"""
import functools, hashlib, json, os, platform, shutil, subprocess, sys, tarfile, threading, time

from dil import t as _
from indirme import PARCA, HttpFile, IndirmeHatasi, Iptal

MAC = sys.platform == 'darwin'
# MOTOR: frankea/Whisky'nin Wine çalışma zamanı: CrossOver'ın açık kaynak Wine'ı (winecx) Wine 11.16 tabanında, GitHub'da CI ile
# derlenir (github.com/frankea/winecx-gptk); arşivden yalnız Wine alınır. 2026-10-25'te Apple M4 / macOS 27'de istemci (Vuplex girişi
# dahil) bununla açıldı. Sikarugir'in Wine 11.0'ı ve Wine Staging 11.8 + DXMT de DXMT'nin işlevlerini dışa açıyor (denenmedi).
# Değiştirince sha256 de değişir; eski motor yeni kurulumda silinir.
MOTOR = {'ad': 'Wine 11.16 (winecx)', 'surum': 'whisky-4.6.4-beta.1',
         'url': 'https://github.com/frankea/Whisky/releases/download/v4.6.4-beta.1/Libraries.tar.gz',
         'sha256': 'c8e6a10dfeb54fc16d3dd3382ee2e9d2cec3eb1f5641613cad8b07903818cb12', 'boyut': 481348675, 'kok': 'Libraries/Wine'}
DXMT = {'ad': 'DXMT 0.80', 'surum': '0.80', 'url': 'https://github.com/3Shain/dxmt/releases/download/v0.80/dxmt-v0.80-builtin.tar.gz',
        'sha256': '8f260e36b5739e68f3bad613381441385c4dc7b85b78ba8de653d5a6a264529d', 'boyut': 18681669, 'kok': 'v0.80'}
DXMT_MIMARILERI = ('x86_64-unix', 'x86_64-windows', 'i386-windows')
EN_DUSUK_MACOS = (14, 0)                # DXMT: macOS 14 Sonoma
KAYIT = 'kurulum.json'                  # kurulumun bittiğini ve sürümlerini söyler


@functools.lru_cache(maxsize=1)
def apple_silicon():
    """Apple Silicon Mac mi (Python Rosetta altında x86_64 çalışsa da)?"""
    if not MAC:
        return False
    try:
        return subprocess.run(['sysctl', '-n', 'hw.optional.arm64'], capture_output=True, text=True, timeout=5).stdout.strip() == '1'
    except (OSError, subprocess.SubprocessError):
        return platform.machine() == 'arm64'


_rosetta = {'var': False, 'zaman': 0.0}


def rosetta_var():
    """Rosetta 2 kurulu mu (Intel Mac'te ve macOS dışında gerekmez: True)? Durum yoklamaları sık: kurulu bulununca hep True, yoksa
    birkaç saniyede bir yeniden denenir."""
    if not apple_silicon() or _rosetta['var']:
        return True
    if time.monotonic() - _rosetta['zaman'] < 3:
        return False
    try:
        var = subprocess.run(['/usr/bin/arch', '-x86_64', '/usr/bin/true'], capture_output=True, timeout=10).returncode == 0
    except (OSError, subprocess.SubprocessError):
        var = False
    _rosetta.update(var=var, zaman=time.monotonic())
    return var


def macos_surumu():
    try:
        return tuple(int(x) for x in platform.mac_ver()[0].split('.')[:2])
    except ValueError:
        return (0, 0)


class _Ozet:
    """Okunan baytların SHA-256'sı (tarfile akışının altında). tarfile 10 KB'lık parçalarla okuyor; HTTPS'ten öyle okumak saniyede
    1 MB'ı geçmiyordu (1 MB'lık okumalarla 40 MB/sn'den çok): okumalar PARCA'lık tampondan verilir (kısa okuma, akış için yeter)."""

    def __init__(self, f):
        self.f, self.h = f, hashlib.sha256()
        self.buf, self.pos = b'', 0

    def read(self, n=-1):
        if n is None or n < 0:
            b = self.buf[self.pos:] + self.f.read()
        else:
            if self.pos >= len(self.buf):
                self.buf, self.pos = self.f.read(max(n, PARCA)), 0
            b = self.buf[self.pos:self.pos + n]
        self.pos += len(b)
        self.h.update(b)
        return b

    def sonuna_dek(self):
        while self.read(1 << 20):
            pass
        return self.h.hexdigest()


def _ac(tf, kok, hedef):
    """tarfile akışından kok/ altını hedefe aç (yollar hedefin içinde kalır; bağlar da)."""
    on = kok.strip('/') + '/'
    os.makedirs(hedef, exist_ok=True)
    hedef_gercek = os.path.realpath(hedef)
    for m in tf:
        if not m.name.startswith(on):
            continue
        rel = m.name[len(on):].strip('/')
        parts = [p for p in rel.split('/') if p not in ('', '.')]
        if not parts:
            continue
        if any(p == '..' for p in parts):
            raise IndirmeHatasi(_('Arşivde geçersiz yol: %s', m.name))
        p = os.path.join(hedef, *parts)
        if m.isdir():
            os.makedirs(p, exist_ok=True)
        elif m.issym():
            t = os.path.normpath(os.path.join(os.path.dirname(p), m.linkname))
            if os.path.isabs(m.linkname) or not os.path.realpath(t).startswith(hedef_gercek + os.sep):
                raise IndirmeHatasi(_('Arşivde geçersiz bağ: %s', m.name))
            os.makedirs(os.path.dirname(p), exist_ok=True)
            if os.path.lexists(p):
                os.remove(p)
            os.symlink(m.linkname, p)
        elif m.islnk():                                 # sert bağ: hedefi daha önce açıldı (akışta sırayla)
            src = m.linkname[len(on):] if m.linkname.startswith(on) else None
            if not src or '..' in src.split('/'):
                raise IndirmeHatasi(_('Arşivde geçersiz bağ: %s', m.name))
            os.makedirs(os.path.dirname(p), exist_ok=True)
            shutil.copy2(os.path.join(hedef, *src.split('/')), p)
        elif m.isfile():
            os.makedirs(os.path.dirname(p), exist_ok=True)
            with tf.extractfile(m) as src, open(p, 'wb') as out:
                shutil.copyfileobj(src, out, 1 << 20)
            os.chmod(p, 0o755 if m.mode & 0o111 else 0o644)


class WineMotoru:
    def __init__(self, save_dir, log=print, opener=None):
        self.kok = os.path.join(save_dir, 'wine_motoru')
        self.log, self.opener = log, opener
        self.lock = threading.Lock()
        self.stop = threading.Event()
        self.d = self._blank('yok')
        self.samples = []
        self.ros = {'durum': 'bos', 'hata': None}

    @staticmethod
    def _blank(durum):
        return {'durum': durum, 'calisiyor': False, 'alinan': 0, 'toplam': 0, 'hiz': 0, 'kalan_sn': None, 'hata': None, 'parca': None}

    # ------------------------------------------------------------ kurulu motor
    def klasor(self):
        return os.path.join(self.kok, MOTOR['surum'])

    def wine(self):
        """Kurulu motorun wine programı ya da None (kurulum bitmemiş, sürümü eski)."""
        k = self.klasor()
        try:
            with open(os.path.join(k, KAYIT), encoding='utf8') as fh:
                d = json.load(fh)
        except (OSError, ValueError):
            return None
        w = os.path.join(k, 'bin', 'wine')
        return w if d.get('motor') == MOTOR['sha256'] and d.get('dxmt') == DXMT['sha256'] and os.path.isfile(w) else None

    def ad(self):
        return '%s + %s' % (MOTOR['ad'], DXMT['ad'])

    def state(self):
        with self.lock:
            d = json.loads(json.dumps(self.d))
            ros = dict(self.ros)
        kurulu = self.wine()
        if not d['calisiyor'] and kurulu:
            d['durum'] = 'kurulu'
        d.update(yol=kurulu, ad=self.ad(), boyut=MOTOR['boyut'] + DXMT['boyut'], klasor=self.klasor(),
                 rosetta=dict(ros, gerekli=apple_silicon(), var=rosetta_var()),
                 macos=platform.mac_ver()[0] if MAC else None, macos_eski=MAC and macos_surumu() < EN_DUSUK_MACOS)
        return d

    def running(self):
        with self.lock:
            return self.d['calisiyor']

    # ------------------------------------------------------------ kurulum
    def start(self):
        """Motoru ve DXMT'yi indir ve kur (sürüyorsa ya da kuruluysa bir şey yapmaz) -> durum."""
        with self.lock:
            busy = self.d['calisiyor']
            if not busy and not self.wine():
                self.stop.clear()
                self.d = dict(self._blank('indiriliyor'), calisiyor=True, toplam=MOTOR['boyut'] + DXMT['boyut'])
                self.samples = []
                threading.Thread(target=self._run, daemon=True).start()
        return self.state()

    def cancel(self):
        self.stop.set()
        return self.state()

    def _count(self, n):
        now = time.monotonic()
        with self.lock:
            self.d['alinan'] += n
            self.samples.append((now, self.d['alinan']))
            while len(self.samples) > 2 and now - self.samples[0][0] > 8:
                self.samples.pop(0)
            t0, b0 = self.samples[0]
            if now - t0 >= 1:
                self.d['hiz'] = int((self.d['alinan'] - b0) / (now - t0))
                left = max(0, self.d['toplam'] - self.d['alinan'])
                self.d['kalan_sn'] = int(left / self.d['hiz']) if self.d['hiz'] > 0 else None

    def _indir_ac(self, parca, hedef):
        """Arşivi akarak hedefe aç ve SHA-256'sını doğrula."""
        with self.lock:
            self.d['parca'] = parca['ad']
        kw = {'opener': self.opener} if self.opener else {}
        f = HttpFile(parca['url'], self.stop, self._count, **kw)
        try:
            src = _Ozet(f)
            with tarfile.open(fileobj=src, mode='r|*') as tf:
                _ac(tf, parca['kok'], hedef)
            ozet = src.sonuna_dek()
        except tarfile.TarError as e:
            raise IndirmeHatasi(_('Arşiv bozuk geldi (%s): yeniden dene.', e))
        finally:
            f.close()
        if ozet != parca['sha256']:
            raise IndirmeHatasi(_('%s arşivi beklenen dosya değil (SHA-256 tutmadı): yeniden dene.', parca['ad']))

    def _run(self):
        gecici = os.path.join(self.kok, '.kuruluyor')
        try:
            if os.path.isdir(gecici):
                shutil.rmtree(gecici)
            os.makedirs(gecici)
            free = shutil.disk_usage(self.kok).free
            if free < 1600 << 20:
                raise IndirmeHatasi(_('Diskte yer yetmiyor: %.1f GB gerekli, %.1f GB boş.', 1.6, free / float(1 << 30)))
            self.log('Wine motoru indiriliyor: %s, %s' % (MOTOR['url'], DXMT['url']))
            motor, dxmt = os.path.join(gecici, 'motor'), os.path.join(gecici, 'dxmt')
            self._indir_ac(MOTOR, motor)
            self._indir_ac(DXMT, dxmt)
            with self.lock:
                self.d.update(durum='kuruluyor', parca=None)
            for arch in DXMT_MIMARILERI:                 # DXMT builtin DLL'leri motorun kendi DLL'lerinin yerine
                src, dst = os.path.join(dxmt, arch), os.path.join(motor, 'lib', 'wine', arch)
                if not os.path.isdir(src):
                    continue
                if not os.path.isdir(dst):
                    raise IndirmeHatasi(_('Wine motorunda %s klasörü yok.', arch))
                for name in os.listdir(src):
                    shutil.copy2(os.path.join(src, name), os.path.join(dst, name))
            if not os.path.isfile(os.path.join(motor, 'bin', 'wine')):
                raise IndirmeHatasi(_('Wine motorunda bin/wine yok.'))
            with open(os.path.join(motor, KAYIT), 'w', encoding='utf8') as fh:
                json.dump({'motor': MOTOR['sha256'], 'dxmt': DXMT['sha256'], 'ad': self.ad(), 'zaman': time.strftime('%Y-%m-%d %H:%M:%S')},
                          fh, indent=1)
            hedef = self.klasor()
            if os.path.isdir(hedef):
                shutil.rmtree(hedef)
            os.rename(motor, hedef)
            for eski in os.listdir(self.kok):           # önceki sürümlerin motorları
                p = os.path.join(self.kok, eski)
                if eski != MOTOR['surum'] and not eski.startswith('.') and os.path.isdir(p):
                    shutil.rmtree(p, ignore_errors=True)
            with self.lock:
                self.d.update(durum='kurulu', alinan=self.d['toplam'], kalan_sn=0)
            self.log('Wine motoru kuruldu: %s (%s)' % (self.ad(), hedef))
        except Iptal:
            with self.lock:
                self.d['durum'] = 'durdu'
            self.log('Wine motoru kurulumu durduruldu')
        except IndirmeHatasi as e:
            with self.lock:
                self.d.update(durum='hata', hata=str(e))
            self.log('Wine motoru kurulamadı: %s' % e)
        except OSError as e:
            with self.lock:
                self.d.update(durum='hata', hata=_('Dosya yazılamadı: %s', e))
            self.log('Wine motoru kurulamadı: %r' % e)
        except Exception as e:
            with self.lock:
                self.d.update(durum='hata', hata=repr(e))
            self.log('Wine motoru: beklenmeyen hata: %r' % e)
        finally:
            shutil.rmtree(gecici, ignore_errors=True)
            with self.lock:
                self.d['calisiyor'], self.d['hiz'], self.d['parca'] = False, 0, None

    def bekle(self, adim=None):
        """Kurulum bitene dek bekle (adim: (yüzde) -> None, ilerleme) -> wine programı. Kurulamazsa RuntimeError."""
        self.start()
        while self.running():
            if adim:
                st = self.state()
                adim(int(100 * st['alinan'] / st['toplam']) if st['toplam'] else 0)
            time.sleep(0.5)
        st = self.state()
        if not st['yol']:
            raise RuntimeError(st['hata'] or _('Wine motoru kurulmadı.'))
        return st['yol']

    # ------------------------------------------------------------ Rosetta 2
    def rosetta_kur(self):
        """Rosetta 2'yi macOS'un yönetici penceresiyle kur (arka planda; kullanıcı şifresini o pencereye yazar) -> durum."""
        if rosetta_var():
            return self.state()
        with self.lock:
            if self.ros['durum'] == 'kuruluyor':
                return self.state()
            self.ros = {'durum': 'kuruluyor', 'hata': None}

        def run():
            komut = '/usr/sbin/softwareupdate --install-rosetta --agree-to-license'
            istem = _('OpenOrbit, oyunu açan Wine için Rosetta 2\'yi kuracak.')
            betik = 'do shell script "%s" with administrator privileges with prompt "%s"' % (komut, istem.replace('"', "'"))
            try:
                r = subprocess.run(['osascript', '-e', betik], capture_output=True, text=True, timeout=1800)
                if rosetta_var():
                    ros = {'durum': 'kuruldu', 'hata': None}
                    self.log('Rosetta 2 kuruldu')
                elif '-128' in r.stderr:
                    ros = {'durum': 'bos', 'hata': _('Rosetta kurulumu iptal edildi.')}
                else:
                    ros = {'durum': 'hata', 'hata': _('Rosetta kurulamadı: %s', (r.stderr or r.stdout).strip()[-300:])}
                    self.log('Rosetta kurulamadı: %s' % (r.stderr or r.stdout).strip()[-300:])
            except (OSError, subprocess.SubprocessError) as e:
                ros = {'durum': 'hata', 'hata': _('Rosetta kurulamadı: %s', e)}
            with self.lock:
                self.ros = ros
        threading.Thread(target=run, daemon=True).start()
        return self.state()
