"""Arkadaşlarla oyna: arkadaş sunucusu ve misafirlerin hesapları (panelin "Arkadaşlarınla Oyna" sayfası, panel/arkadas.py).

Sunucu: panel game.py'yi --cok-oyunculu ile başlatır. Oyun (8081) ve sohbet (7771) portları bütün ağlardan dinlenir; web girişi
(80, 8090) yerel kalır: her oyuncu kendi bilgisayarındaki web.py'den girer (misafirinki --uzak ile bu sunucuyu gösterir). Ayarlar
ortam değişkeninden (DO_COK_OYUNCULU, JSON; komut satırında görünmesin): sifre (katılma şifresi; boş: yok), en_cok (misafir sayısı),
anahtar (panelin yönetim anahtarı), kod (panelin sürümü: misafirin paneli karşılaştırır), adres (dinlenen adres; öntanımlı 0.0.0.0,
tek bilgisayardaki canlı testte 127.0.0.1: güvenlik duvarı sorusu çıkmasın). Aynı normal haritadaki oyuncular
uzaylıları, kutuları ve cevherleri paylaşır, birbirini görür (ortak_harita.py); sohbet ortak.

Hesap gönderimi: misafirin paneli oyuna girmeden kaydını oyun portundan HTTP ile gönderir (game.handle ilk baytlar "GET "/"POST"
ise buraya verir; oyun istemcisinin ilk paketi uzunlukla başlar).
  GET  /misafir/bilgi                     sunucunun adı, pilotu, oyuncular, şifre gerekli mi, yer var mı
  POST /misafir/giris {surum, sifre, anahtar, adres, profil}  -> {oturum, uid, surum, sohbet}
       Kayıt sunucunun belleğinde tutulur, diske yazılmaz: sunucunun Kayıtlar sayfasında görünmez. Oyuncu kimliği sunucuda benzersiz
       olsun diye geçici bir kimlikle değişir (kayıtların çoğu tohumun aynı kimliğiyle başlar), geri verilirken eskisine döner
       (kimlik alanlarında: kimlik_cevir). Aynı anahtarla yeniden giriş (bağlantı koptu, panel yeniden açıldı) oturumu ve
       sunucudaki son hâli sürdürür. adres: misafirin bu sunucuya bağlandığı adres (sohbetin adresi oradan).
  GET  /misafir/profil?oturum=&anahtar=&surum=N&bekle=25
       uzun yoklama: kayıt N'den yeni bir sürüme gelince (oyun değişince 10 sn'de bir kaydeder; MisafirProfil.save) ya da süre
       dolunca -> {surum, bagli, bitti, profil (yeniyse)}. Misafirin paneli her yeni sürümü kendi kayıt yuvasına yazar.
  POST /misafir/cikis {oturum, anahtar}   -> son hâl; oturum biter (oyun açıksa bağlantı kapanır), kayıt kısa süre sonra silinir
Gövdeler JSON; "Content-Encoding: gzip" ile sıkıştırılmış da olabilir, "Accept-Encoding: gzip" isteyene yanıt sıkıştırılır.
Yönetim (yalnız 127.0.0.1'den, panelin anahtarıyla): POST /yonetim/at {anahtar, oturum}: misafiri çıkar.
İstemci girişte (LoginRequest) web girişinin verdiği sessionID'yi gönderir: misafirinki oturum anahtarı (bul), sunucunun kendi
oyuncusununki web.py'nin SESSION'ı (AYAR['yerel']: panelin bu açılışta ürettiği belirteç; yalnız bu bilgisayardan).
Yanlış katılma şifresi adres başına sınırlı (DENEME_SINIR denemeden sonra KILIT_SN kilit, 429).
Sunucu kapatılırken (panelin "Durdur"u) misafirlerin son hâli yayımlanır ve bekleyen yoklamalara verilir (kapanis).
"""
import collections, gzip, hmac, json, os, random, secrets, socket, threading, time, zlib
from urllib.parse import parse_qs, urlparse

import profil as PF
import yollar as YOL

PROTOKOL = 1                    # hesap gönderiminin sürümü: misafirin paneliyle aynı olmalı
UID_ALT, UID_UST = 2000000000, 2100000000     # misafirlerin sunucudaki geçici kimlikleri (int32; kayıt kimlikleriyle karışmaz)
GOVDE_SINIR = 8 * 1024 * 1024   # hesap gönderimi (kayıtlar ~0,4 MB); şifreden önce okunur
DENEME_SINIR, KILIT_SN = 5, 60  # adres başına yanlış şifre: bu kadar denemeden sonra bu kadar saniye kilit
BASLIK_SINIR = 64 * 1024
BEKLE_EN_COK = 30
BOSTA_SN = 30 * 60              # bağlı değil ve yoklanmıyor: kayıt bu kadar sonra bırakılır (veri misafirin panelinde)
BITIS_SN = 120                  # biten oturumun son hâli bu kadar daha alınabilir (yoklama arasında biten oturum kaybolmasın)
SOHBET_PORTU = 7771

AYAR = {'acik': False, 'sifre': '', 'en_cok': 4, 'anahtar': None, 'kod': '', 'adres': '0.0.0.0', 'yerel': ''}
COND = threading.Condition()
MISAFIRLER = {}                 # oturum anahtarı -> Misafir
HATALI = {}                     # adres -> [yanlış şifre sayısı, kilidin bitişi]
log = print


def esit(a, b):
    """Gizli değerlerin karşılaştırması (sabit süreli; str'de ASCII dışı karakter TypeError veriyordu)."""
    return hmac.compare_digest(str(a or '').encode('utf8'), str(b or '').encode('utf8'))


def configure(raw, logger=print):
    """game.main: --cok-oyunculu ile açıldıysa (raw: DO_COK_OYUNCULU ortam değişkeni)."""
    global log
    log = logger
    try:
        d = json.loads(raw or '{}')
    except ValueError:
        d = {}
    # yerel: sunucunun kendi oyuncusunun oturumu (panel her açılışta üretir, kendi web.py'sine de verir). Sabit 'localtest'
    # tünelle açılan sunucuda (bağlantılar 127.0.0.1'den görünür) şifresiz girişti
    AYAR.update(acik=True, sifre=str(d.get('sifre') or ''), en_cok=max(1, min(16, int(d.get('en_cok') or 4))),
                anahtar=d.get('anahtar') or None, kod=str(d.get('kod') or ''), adres=str(d.get('adres') or '0.0.0.0'),
                yerel=str(d.get('yerel') or '') or secrets.token_urlsafe(24))


def yerel_mi(sid):
    """LoginRequest'in sessionID'si sunucunun kendi oyuncusunun mu."""
    return bool(AYAR['yerel']) and esit(sid, AYAR['yerel'])


def acik():
    return AYAR['acik']


# ------------------------------------------------------------------ misafirler
def kimlik_cevir(x, eski, yeni):
    """Kayıttaki oyuncu kimliklerini değiştirir (yerinde): pilot, klan haberi ve mesajı ('kim'), posta (sender_id, alici_idler),
    müzayede, klan hesabı (balanceUserId). Yalnız adı kimlik olan alanlarda: para ve sayaçlara dokunulmaz."""
    if isinstance(x, dict):
        for k, v in x.items():
            idli = k == 'kim' or k.lower().endswith(('id', 'ids', 'idler'))
            if idli and v == eski and not isinstance(v, bool):
                x[k] = yeni
            elif idli and isinstance(v, list):
                x[k] = [yeni if (e == eski and not isinstance(e, bool)) else e for e in v]
                for e in x[k]:
                    kimlik_cevir(e, eski, yeni)
            else:
                kimlik_cevir(v, eski, yeni)
    elif isinstance(x, list):
        for e in x:
            kimlik_cevir(e, eski, yeni)


class MisafirProfil(PF.Profil):
    """Misafirin kaydı: dosya yerine bellekte; her kayıt (oyunun 10 sn'lik kaydı) yeni bir sürüm yayımlar (uzun yoklamaya)."""

    def __init__(self, tohum, d, misafir):
        self.misafir = misafir
        super().__init__(tohum, path=os.path.join(YOL.LOGS, 'misafir_yok.json'), d=d)   # yol hiç yazılmaz

    def save(self, force=False):
        with self.lock:
            if not (self.dirty or force):
                return
            for k in range(5):                    # oturum profile kilitsiz yazıyor (Profil.save gibi)
                try:
                    text = json.dumps(self.d, ensure_ascii=False)
                    break
                except RuntimeError:
                    if k == 4:
                        raise
                    time.sleep(0.01)
            self.dirty = False
        self.misafir.yayimla(text)


class Misafir:
    def __init__(self, oturum, anahtar, uid, asil_uid, adres, ip):
        self.oturum, self.anahtar, self.uid, self.asil_uid = oturum, anahtar, uid, asil_uid
        self.adres, self.ip = adres, ip
        self.profil = None
        self.metin = None             # son yayımlanan kaydın JSON'u (sunucudaki kimlikle)
        self.surum = 0
        self.session = None           # bağlı oyun oturumu (game.Session)
        self.giris = time.time()
        self.son = time.time()        # son yoklama ya da bağlantı
        self.bitti = False            # bitti: oyuna girilemez; son hâl BITIS_SN boyunca alınabilir
        self.bitis = 0.0

    def yayimla(self, text):
        with COND:
            self.metin, self.surum = text, self.surum + 1
            COND.notify_all()

    def disari(self):
        """Misafirin kendi kimliğiyle kaydı (misafirin paneli yuvasına yazar)."""
        d = json.loads(self.metin)
        kimlik_cevir(d, self.uid, self.asil_uid)
        return d

    def ozet(self):
        p = self.profil.d if self.profil else {}
        pl = p.get('pilot') or {}
        return {'oturum': self.oturum[:8], 'ad': pl.get('userName', '?'), 'seviye': pl.get('level', 1), 'ip': self.ip,
                'bagli': self.session is not None, 'giris': int(self.giris)}


def _yeni_uid(dolu):
    while True:
        u = random.randrange(UID_ALT, UID_UST)
        if u not in dolu:
            return u


def gecerli_profil(d):
    """Gönderilen kayıt oynanabilir mi -> hata metni ya da None."""
    if not isinstance(d, dict):
        return 'kayıt bir JSON nesnesi değil'
    pl, g, k = d.get('pilot'), d.get('gemi'), d.get('konum')
    if not (isinstance(pl, dict) and isinstance(g, dict) and isinstance(k, dict)):
        return 'kayıtta pilot, gemi ya da konum yok'
    if not isinstance(pl.get('userId'), int) or isinstance(pl.get('userId'), bool) or not str(pl.get('userName') or '').strip():
        return 'pilotun kimliği ya da adı yok'
    if not all(isinstance(k.get(a), (int, float)) for a in ('mapId', 'x', 'y')):
        return 'kayıttaki konum geçersiz'
    return None


def giris(body, ip, tohum, sunucu_uid):
    """POST /misafir/giris -> (durum kodu, yanıt)."""
    if int(body.get('surum') or 0) != PROTOKOL:
        return 409, {'hata': 'surum', 'mesaj': 'Hesap gönderiminin sürümü farklı (sunucu %d): ikiniz de paneli güncelleyin.' % PROTOKOL}
    if AYAR['sifre']:
        now = time.time()
        with COND:
            h = HATALI.get(ip)
            if h and h[1] > now:
                return 429, {'hata': 'bekle', 'mesaj': 'Çok fazla yanlış şifre: %d saniye sonra yeniden dene.' % (h[1] - now + 1)}
        if not esit(body.get('sifre'), AYAR['sifre']):
            with COND:
                h = HATALI.setdefault(ip, [0, 0])
                h[0] += 1
                if h[0] >= DENEME_SINIR:
                    h[:] = [0, now + KILIT_SN]
                    log('arkadaş: %s için yanlış şifre sınırı, %d sn kilit' % (ip, KILIT_SN))
            return 403, {'hata': 'sifre', 'mesaj': 'Katılma şifresi yanlış.'}
        with COND:
            HATALI.pop(ip, None)
    anahtar = str(body.get('anahtar') or '')
    if len(anahtar) < 16:
        return 400, {'hata': 'anahtar', 'mesaj': 'Misafir anahtarı eksik.'}
    with COND:
        eski = next((m for m in MISAFIRLER.values() if esit(m.anahtar, anahtar) and not m.bitti), None)
        if eski:                                  # yeniden giriş: sunucudaki son hâl sürer
            eski.son, eski.ip = time.time(), ip
            eski.adres = str(body.get('adres') or eski.adres)
            log('misafir yeniden geldi: %s (%s)' % (eski.ozet()['ad'], ip))
            return 200, {'oturum': eski.oturum, 'uid': eski.uid, 'surum': eski.surum, 'devam': True}
        if sum(1 for m in MISAFIRLER.values() if not m.bitti) >= AYAR['en_cok']:
            return 503, {'hata': 'dolu', 'mesaj': 'Sunucu dolu (en çok %d misafir).' % AYAR['en_cok']}
    d = body.get('profil')
    err = gecerli_profil(d)
    if err:
        return 400, {'hata': 'profil', 'mesaj': 'Kayıt geçersiz: %s.' % err}
    with COND:
        uid = _yeni_uid({sunucu_uid} | {m.uid for m in MISAFIRLER.values()})
        m = Misafir(secrets.token_urlsafe(18), anahtar, uid, d['pilot']['userId'], str(body.get('adres') or ''), ip)
        kimlik_cevir(d, m.asil_uid, uid)
        m.profil = MisafirProfil(tohum, d, m)
        m.yayimla(json.dumps(m.profil.d, ensure_ascii=False))
        MISAFIRLER[m.oturum] = m
    log('misafir geldi: %s (%s), sunucudaki kimlik %d' % (d['pilot'].get('userName'), ip, uid))
    return 200, {'oturum': m.oturum, 'uid': uid, 'surum': m.surum, 'devam': False}


def _misafir(q):
    """Oturum ve anahtar tutan misafir ya da None."""
    with COND:
        m = MISAFIRLER.get(str(q.get('oturum') or ''))
    if m and esit(m.anahtar, q.get('anahtar')):
        return m
    return None


def profil_yokla(q):
    """GET /misafir/profil: N'den yeni sürüm gelene ya da süre dolana dek bekler."""
    m = _misafir(q)
    if not m:
        return 404, {'hata': 'oturum', 'mesaj': 'Bu sunucuda böyle bir misafir oturumu yok.'}
    try:
        have, wait = int(q.get('surum') or 0), min(BEKLE_EN_COK, max(0.0, float(q.get('bekle') or 0)))
    except ValueError:
        return 400, {'hata': 'istek'}
    end = time.time() + wait
    with COND:
        while m.surum <= have and not m.bitti and time.time() < end:
            COND.wait(max(0.05, end - time.time()))
        m.son = time.time()
        out = {'surum': m.surum, 'bagli': m.session is not None, 'bitti': m.bitti}
        yeni = m.surum > have
    if yeni:
        out['profil'] = m.disari()
    return 200, out


def cikis(q, kapat_oturum):
    """POST /misafir/cikis: bağlıysa oyun bağlantısı kapanır, son hâl verilir, kayıt silinir."""
    m = _misafir(q)
    if not m:
        return 404, {'hata': 'oturum', 'mesaj': 'Bu sunucuda böyle bir misafir oturumu yok.'}
    if not m.bitti:
        bitir(m, kapat_oturum, 'misafir ayrıldı')
    return 200, {'surum': m.surum, 'profil': m.disari(), 'bitti': True}


def bitir(m, kapat_oturum, neden):
    s = m.session
    if s is not None:
        kapat_oturum(s)                           # oturum kapanırken son kaydı yayımlar (game.Session.run)
        end = time.time() + 5
        while m.session is not None and time.time() < end:
            time.sleep(0.05)
    if m.profil:
        m.profil.save(force=True)
    with COND:
        m.bitti, m.bitis = True, time.time()
        COND.notify_all()
    log('misafir oturumu bitti (%s): %s' % (neden, m.ozet()['ad']))


def bul(sid):
    """LoginRequest'in sessionID'si -> misafir (yoksa None)."""
    with COND:
        m = MISAFIRLER.get(str(sid or ''))
        return m if m and not m.bitti else None


def liste():
    with COND:
        return [m for m in MISAFIRLER.values() if not m.bitti]


def tick(kapat_oturum):
    """Bağlı olmayan ve uzun süredir yoklanmayan misafir oturumları biter, bitenlerin kaydı bırakılır (game.autosave)."""
    now = time.time()
    for m in liste():
        if m.session is None and now - m.son > BOSTA_SN:
            bitir(m, kapat_oturum, 'uzun süre bağlanmadı')
    with COND:
        for k in [k for k, m in MISAFIRLER.items() if m.bitti and now - m.bitis > BITIS_SN]:
            del MISAFIRLER[k]


def kapanis(bekle=2.0):
    """Sunucu kapanıyor: misafirlerin son hâli yayımlanır, yoklamalar bitti diye yanıtlanır; panellerin almasına kısa süre."""
    ms = liste()
    for m in ms:
        if m.profil:
            m.profil.save(force=True)
    with COND:
        for m in ms:
            m.bitti, m.bitis = True, time.time()
        COND.notify_all()
    if ms:
        time.sleep(bekle)


# ------------------------------------------------------------------ gönderme kuyruğu
class Kuyruk:
    """Arkadaş sunucusunda her bağlantının gönderme kuyruğu: dünya kilidi altındaki gönderim ağı beklemez (yavaş bir misafir öteki
    oyuncuların döngüsünü durdurmasın). Sıra korunur; birikim SINIR'ı aşarsa bağlantı kapanır."""
    SINIR = 16 * 1024 * 1024

    def __init__(self, sock):
        self.sock = sock
        self.cond = threading.Condition()
        self.parcalar = collections.deque()
        self.boyut = 0
        self.kapali = False
        self.bitir = False
        threading.Thread(target=self.calis, daemon=True).start()

    def put(self, data):
        with self.cond:
            if self.kapali or self.bitir:
                raise ConnectionError('bağlantı kapandı')
            self.parcalar.append(data)
            self.boyut += len(data)
            if self.boyut > self.SINIR:
                self._kes()
                raise ConnectionError('gönderme kuyruğu doldu (istemci okumuyor)')
            self.cond.notify()

    def calis(self):
        while True:
            with self.cond:
                while not self.parcalar and not self.kapali and not self.bitir:
                    self.cond.wait()
                if self.kapali:
                    return
                if not self.parcalar:             # bitir: kalanlar gitti, bağlantı kapanır
                    self._kes(shutdown=True)
                    return
                data = b''.join(self.parcalar)
                self.parcalar.clear()
                self.boyut = 0
            try:
                self.sock.sendall(data)
            except OSError:
                with self.cond:
                    self._kes()
                return

    def kapat(self):
        """Kuyruktakiler gidince bağlantıyı kapat (çıkış, misafiri çıkarma)."""
        with self.cond:
            self.bitir = True
            self.cond.notify()

    def _kes(self, shutdown=False):
        self.kapali = True
        try:
            if shutdown:
                self.sock.shutdown(socket.SHUT_RDWR)
            else:
                self.sock.close()
        except OSError:
            pass


# ------------------------------------------------------------------ HTTP (oyun portunda)
def http_mi(ilk):
    return ilk[:4] in (b'GET ', b'POST', b'HEAD')


def _oku(c):
    """-> (yöntem, yol, başlıklar, gövde) ya da None."""
    buf = b''
    while b'\r\n\r\n' not in buf:
        d = c.recv(65536)
        if not d:
            return None
        buf += d
        if len(buf) > BASLIK_SINIR and b'\r\n\r\n' not in buf[:BASLIK_SINIR]:
            return None
    head, body = buf.split(b'\r\n\r\n', 1)
    lines = head.decode('latin-1').split('\r\n')
    try:
        method, path, _ = lines[0].split(' ', 2)
    except ValueError:
        return None
    hdr = {}
    for ln in lines[1:]:
        if ':' in ln:
            k, v = ln.split(':', 1)
            hdr[k.strip().lower()] = v.strip()
    n = int(hdr.get('content-length') or 0)
    if n < 0 or n > GOVDE_SINIR:
        return None
    while len(body) < n:
        d = c.recv(min(1 << 20, n - len(body)))
        if not d:
            return None
        body += d
    if hdr.get('content-encoding') == 'gzip' and body:
        z = zlib.decompressobj(16 + zlib.MAX_WBITS)
        body = z.decompress(body, GOVDE_SINIR)            # sınırlı açılır (sıkıştırma bombası)
        if z.unconsumed_tail:
            return None
    return method, path, hdr, body


def _yanit(c, code, obj, gz=False):
    data = json.dumps(obj, ensure_ascii=False).encode('utf8')
    extra = ''
    if gz and len(data) > 2048:
        data = gzip.compress(data, 6)
        extra = 'Content-Encoding: gzip\r\n'
    status = {200: 'OK', 400: 'Bad Request', 403: 'Forbidden', 404: 'Not Found', 409: 'Conflict', 429: 'Too Many Requests',
              503: 'Service Unavailable'}.get(code, 'OK')
    c.sendall(('HTTP/1.1 %d %s\r\nContent-Type: application/json; charset=utf-8\r\nContent-Length: %d\r\n%sConnection: close\r\n'
               'X-DarkOrbit: arkadas\r\n\r\n' % (code, status, len(data), extra)).encode('latin-1') + data)


def http(c, addr, game):
    """Oyun portuna gelen HTTP isteği (hesap gönderimi ve yönetim). game: game.py modülü."""
    try:
        c.settimeout(BEKLE_EN_COK + 15)
        req = _oku(c)
        if not req:
            return
        method, path, hdr, body = req
        u = urlparse(path)
        q = {k: v[0] for k, v in parse_qs(u.query).items()}
        gz = 'gzip' in hdr.get('accept-encoding', '')
        try:
            b = json.loads(body.decode('utf8') or '{}') if method == 'POST' else {}
        except ValueError:
            return _yanit(c, 400, {'hata': 'json'})
        if not isinstance(b, dict):
            return _yanit(c, 400, {'hata': 'json'})
        ip = addr[0]
        if u.path == '/misafir/bilgi':
            code, out = 200, game.sunucu_bilgisi()
        elif u.path == '/misafir/giris' and method == 'POST':
            code, out = giris(b, ip, game.SABLON.giris.get('tohum'), game.PROFIL.user_id)
        elif u.path == '/misafir/profil':
            code, out = profil_yokla(q)
        elif u.path == '/misafir/cikis' and method == 'POST':
            code, out = cikis(b, game.kapat_oturum)
        elif u.path == '/yonetim/at' and method == 'POST' and ip in ('127.0.0.1', '::1') and AYAR['anahtar'] \
                and esit(b.get('anahtar'), AYAR['anahtar']):
            m = next((x for x in liste() if x.oturum.startswith(str(b.get('oturum') or '-'))), None)
            if m:
                bitir(m, game.kapat_oturum, 'sunucu çıkardı')
            code, out = (200, {'tamam': True}) if m else (404, {'hata': 'oturum'})
        else:
            code, out = 404, {'hata': 'yok'}
        if u.path != '/misafir/profil':
            log('arkadaş: %s %s <- %s -> %d' % (method, u.path, ip, code))
        _yanit(c, code, out, gz)
    except (OSError, ValueError) as e:
        log('arkadaş: istek hatası %s: %r' % (addr[0], e))
    finally:
        try:
            c.close()
        except OSError:
            pass
