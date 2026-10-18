"""Oyun istemcisini indirme (bilgisayarda istemci bulunamazsa; kurulum sihirbazı ve İstemci sayfası): Bigpoint'in arşivi (URL,
1.1.114 zip) proje köküne açılır, istemci dosyaları değiştirilmez.

Arşiv diske kaydedilmez: HTTP aralık istekleriyle okunur (HttpFile), zipfile dosyaları sırayla doğrudan açar. Böylece arşivin
kendisi için ayrıca yer gerekmez (açılmış hâli kadar, ≈4,4 GB). Bağlantı koparsa aynı bayttan yeniden bağlanır (DENEME kez);
iş durdurulur ya da panel kapanırsa açılmış dosyalar kalır, yeniden başlatınca yalnız eksikler iner. Her dosya önce .part'a yazılır,
zip'in CRC'siyle doğrulanınca adını alır. Dosyalar geçici klasörde (GECICI) toplanır; hepsi bitip istemci doğrulanınca klasör
arşivdeki adı (DarkOrbit_Version1.1.114) alır: yarım indirme geçerli istemci gibi görünmez. Aynı anda tek iş.
"""
import http.client, json, os, shutil, threading, time, zipfile
from urllib.request import Request, urlopen

from dil import t as _

URL = 'https://alicdn-oss-prod.darkorbit.com/release/archive/DarkOrbit_Version1.1.114.zip'
GECICI = 'istemci_indiriliyor'      # proje kökünde; .gitignore'da
PARCA = 1 << 20
DENEME = 8                          # kopan bağlantıda üst üste yeniden bağlanma
ZAMAN_ASIMI = 30
PAY = 200 << 20                     # disk denetiminde fazladan yer
GB = float(1 << 30)


def bekleme(k):
    """k. yeniden bağlanmadan önce beklenen saniye (testler kısaltır)."""
    return min(30, 2 ** k)


class IndirmeHatasi(Exception):
    """Kullanıcıya gösterilen hata."""


class Iptal(Exception):
    pass


class HttpFile:
    """HTTP aralık istekleriyle okunan, konumlanabilir salt-okunur dosya (zipfile için). Sıralı okumada tek bağlantı sürer;
    bağlantı koparsa aynı yerden yeniden açılır. Arşiv sunucuda değişirse (ETag) durur."""

    def __init__(self, url, stop, on_bytes=None, opener=urlopen):
        self.url, self.stop, self.on_bytes, self.opener = url, stop, on_bytes, opener
        self.pos, self.resp, self.rpos, self.etag = 0, None, None, None
        try:
            r = self._request(0, 0)
        except (OSError, http.client.HTTPException) as e:
            raise IndirmeHatasi(_('İndirme sunucusuna bağlanılamadı (internet bağlantını denetle): %s', e))
        cr = r.headers.get('Content-Range') or ''
        r.close()
        try:
            self.size = int(cr.rsplit('/', 1)[1])
        except (IndexError, ValueError):
            raise IndirmeHatasi(_('İndirme sunucusu kaldığı yerden sürdürmeyi desteklemiyor.'))

    def _request(self, start, end=None):
        h = {'Range': 'bytes=%d-%s' % (start, '' if end is None else end), 'User-Agent': 'DarkOrbit-Server-Emulator'}
        if self.etag:
            h['If-Range'] = self.etag
        r = self.opener(Request(self.url, headers=h), timeout=ZAMAN_ASIMI)
        if r.status != 206:
            r.close()
            raise IndirmeHatasi(_('İndirme sunucusu kaldığı yerden sürdürmeyi desteklemiyor ya da arşiv değişti; yeniden başlatın.'))
        self.etag = self.etag or r.headers.get('ETag')
        return r

    def _close(self):
        if self.resp is not None:
            try:
                self.resp.close()
            except Exception:
                pass
        self.resp = self.rpos = None

    def close(self):
        self._close()

    def seekable(self):
        return True

    def readable(self):
        return True

    def tell(self):
        return self.pos

    def seek(self, off, whence=0):
        self.pos = off if whence == 0 else self.pos + off if whence == 1 else self.size + off
        return self.pos

    def read(self, n=-1):
        n = self.size - self.pos if n is None or n < 0 else min(n, self.size - self.pos)
        out, tries = [], 0
        while n > 0:
            if self.stop.is_set():
                raise Iptal()
            try:
                if self.resp is None or self.rpos != self.pos:
                    self._close()
                    self.resp, self.rpos = self._request(self.pos), self.pos
                data = self.resp.read(min(n, PARCA))
                if not data:
                    raise ConnectionError('bağlantı kapandı')
            except (OSError, http.client.HTTPException) as e:          # URLError, zaman aşımı, kopan bağlantı
                self._close()
                tries += 1
                if tries > DENEME:
                    raise IndirmeHatasi(_('Bağlantı koptu: %s', e))
                if self.stop.wait(bekleme(tries)):
                    raise Iptal()
                continue
            tries = 0
            self.pos += len(data)
            self.rpos = self.pos
            n -= len(data)
            out.append(data)
            if self.on_bytes:
                self.on_bytes(len(data))
        return b''.join(out)


def top_folder(names):
    """Bütün girdiler tek bir üst klasördeyse onun adı, değilse ''."""
    tops = {n.split('/', 1)[0] for n in names}
    return tops.pop() if len(tops) == 1 and all('/' in n or n.endswith('/') for n in names) else ''


def safe_path(base, rel):
    """Arşivdeki yolu klasörün içinde tut (../ ve mutlak yollar geçersiz)."""
    parts = [p for p in rel.replace('\\', '/').split('/') if p not in ('', '.')]
    if not parts or any(p == '..' or ':' in p for p in parts):
        raise IndirmeHatasi(_('Arşivde geçersiz yol: %s', rel))
    return os.path.join(base, *parts)


class Indirici:
    def __init__(self, root, check, log=print, on_done=None, url=URL, opener=urlopen):
        self.root, self.check, self.log, self.on_done, self.url, self.opener = root, check, log, on_done, url, opener
        self.stage = os.path.join(root, GECICI)
        self.lock = threading.Lock()
        self.stop = threading.Event()
        self.d = self._blank('bos')
        self.samples = []

    @staticmethod
    def _blank(durum):
        return {'durum': durum, 'calisiyor': False, 'alinan': 0, 'toplam': 0, 'acik_boyut': 0, 'dosya': '', 'biten_dosya': 0,
                'dosya_sayisi': 0, 'hiz': 0, 'kalan_sn': None, 'hata': None, 'hedef': None, 'baslangic': None, 'bitis': None}

    def state(self):
        with self.lock:
            d = json.loads(json.dumps(self.d))
        if d['toplam']:
            d['alinan'] = min(d['alinan'], d['toplam'])
        d['url'] = self.url
        d['yarim'] = not d['calisiyor'] and os.path.isdir(self.stage)       # önceki indirmeden kalan dosyalar
        return d

    def running(self):
        with self.lock:
            return self.d['calisiyor']

    def start(self):
        with self.lock:
            busy = self.d['calisiyor']
            if not busy:
                self.stop.clear()
                self.d = dict(self._blank('hazirlaniyor'), calisiyor=True, baslangic=time.time())
                self.samples = []
        if not busy:
            threading.Thread(target=self._run, daemon=True).start()
        return self.state()

    def cancel(self):
        self.stop.set()
        return self.state()

    def discard(self):
        """Yarım kalan indirmenin geçici klasörünü sil (iş durmuşken; yalnız GECICI)."""
        if self.running():
            raise IndirmeHatasi(_('İndirme sürüyor: önce durdurun.'))
        if os.path.isdir(self.stage):
            shutil.rmtree(self.stage)
            self.log('yarım istemci indirmesi silindi: %s' % self.stage)
        with self.lock:
            self.d = self._blank('bos')
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

    def _set(self, **kw):
        with self.lock:
            self.d.update(kw)

    def _target(self, name):
        """Son klasör: proje kökünde arşivdeki ad; o ad doluysa (başka bir klasör) "ad (2)" …"""
        p, k = os.path.join(self.root, name), 2
        while os.path.exists(p):
            p, k = os.path.join(self.root, '%s (%d)' % (name, k)), k + 1
        return p

    def _run(self):
        f = None
        try:
            f = HttpFile(self.url, self.stop, self._count, self.opener)
            z = zipfile.ZipFile(f)
            infos = sorted(z.infolist(), key=lambda i: i.header_offset)
            top = top_folder([i.filename for i in infos])
            files = []
            for i in infos:
                rel = i.filename[len(top) + 1:] if top else i.filename
                if rel.strip('/'):
                    files.append((i, safe_path(self.stage, rel)))
            items = [(i, p) for i, p in files if not i.is_dir()]
            done = {p for i, p in items if os.path.isfile(p) and os.path.getsize(p) == i.file_size}
            need = sum(i.file_size for i, p in items if p not in done)
            free = shutil.disk_usage(self.root).free
            if free < need + PAY:
                raise IndirmeHatasi(_('Diskte yer yetmiyor: %.1f GB gerekli, %.1f GB boş.', (need + PAY) / GB, free / GB))
            self._set(durum='indiriliyor', toplam=sum(i.compress_size for i, p in items), acik_boyut=sum(i.file_size for i, p in items),
                      alinan=sum(i.compress_size for i, p in items if p in done), dosya_sayisi=len(items), biten_dosya=len(done))
            self.log('istemci indiriliyor: %s (%d dosya, %d zaten var)' % (self.url, len(items), len(done)))
            for i, p in files:
                if self.stop.is_set():
                    raise Iptal()
                if i.is_dir():
                    os.makedirs(p, exist_ok=True)
                    continue
                if p in done:
                    continue
                self._set(dosya=os.path.relpath(p, self.stage))
                os.makedirs(os.path.dirname(p), exist_ok=True)
                part = p + '.part'
                with z.open(i) as src, open(part, 'wb') as out:      # zipfile sonda CRC'yi denetler (BadZipFile)
                    while True:
                        b = src.read(PARCA)
                        if not b:
                            break
                        out.write(b)
                os.replace(part, p)
                with self.lock:
                    self.d['biten_dosya'] += 1
            self._set(durum='dogrulaniyor', dosya='')
            c = self.check(self.stage)
            if not c['gecerli']:
                raise IndirmeHatasi(_('İndirilen klasör bir DarkOrbit istemcisi değil: %s', ' '.join(c['sorunlar'])))
            target = self._target(top or os.path.splitext(os.path.basename(self.url))[0])
            for k in range(10):                     # virüs tarayıcısı bir dosyayı tutuyorsa biraz bekle
                try:
                    os.rename(self.stage, target)
                    break
                except OSError:
                    if k == 9:
                        raise
                    time.sleep(1)
            self._set(durum='bitti', hedef=target, alinan=self.d['toplam'], kalan_sn=0)
            self.log('istemci indirildi: %s' % target)
            if self.on_done:
                self.on_done(target)
        except Iptal:
            self._set(durum='durdu')
            self.log('istemci indirme durduruldu')
        except IndirmeHatasi as e:
            self._set(durum='hata', hata=str(e))
            self.log('istemci indirme hatası: %s' % e)
        except zipfile.BadZipFile as e:
            self._set(durum='hata', hata=_('Arşiv bozuk geldi (%s). Yeniden başlatın: yalnız eksik dosyalar iner.', e))
            self.log('istemci indirme: bozuk arşiv: %s' % e)
        except OSError as e:
            self._set(durum='hata', hata=_('Dosya yazılamadı: %s', e))
            self.log('istemci indirme: yazma hatası: %r' % e)
        except Exception as e:
            self._set(durum='hata', hata=repr(e))
            self.log('istemci indirme: beklenmeyen hata: %r' % e)
        finally:
            if f is not None:
                f.close()
            with self.lock:
                self.d['calisiyor'], self.d['bitis'] = False, time.time()
                self.d['hiz'] = 0
