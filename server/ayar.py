"""Oyun ayarları (yönetim paneli, panel/): çarpanlar, etkinlik seçimi, müzayede rakipleri, sunucu seçenekleri.

Ayarların tek tanımı SCHEMA: panel arayüzü bundan kurulur, sunucu değerleri get() ile okur. Değerler save/ayarlar.json'da
({anahtar: değer, 'etkinlikler': {etkinlik: 'acik' | 'kapali'}}); dosyada olmayan anahtar varsayılandır, bilinmeyenler yok sayılır,
sayılar sınırlara kırpılır, bozuk dosya varsayılanlara döner.
Dosya değişince (panelden kaydedilince) en geç YENILE_SN içinde yeniden okunur, oyun açıkken de geçerli olur. Her ayarın
'uygulama' alanı ne zaman etkili olduğunu söyler:
  anında    bir sonraki olayda (hasar, ödül, kutu içeriği …)
  harita    harita yeniden kurulunca (harita değişimi, ölüm sonrası doğma): NPC ve kutu sayısı
  giriş     oyuna yeniden girince (etkinlikler istemciye girişte bildirilir; açılır pencereler)
  başlatma  sunucu yeniden başlayınca
Oyun sunucusu configure() ile dosyayı bağlar (game.main, --ayarlar=<yol> seçeneği ya da save/ayarlar.json). Bağlanmamışken
(testler, araçlar) bütün ayarlar varsayılandır: kullanıcının ayarları testleri etkilemez.
"""
import json, os, random, sys, threading, time

HERE = os.path.dirname(os.path.abspath(__file__))
VARSAYILAN_YOL = os.path.join(HERE, 'save', 'ayarlar.json')
YENILE_SN = 1.0

GRUPLAR = (('savas', 'Savaş'), ('odul', 'Ödüller'), ('dunya', 'Dünya'), ('ekonomi', 'Ekonomi'), ('sure', 'Süreler'),
           ('muzayede', 'Müzayede'), ('arayuz', 'Arayüz'), ('gelistirici', 'Geliştirici'))
RAKIP_SEVIYELERI = ('Kapalı', 'Çekingen', 'Ilımlı', 'Rekabetçi', 'Agresif')


def _c(key, ad, grup, aciklama, uygulama='anında', lo=0.0, hi=10.0, adim=0.1, varsayilan=1.0):
    return dict(anahtar=key, ad=ad, grup=grup, tur='carpan', varsayilan=varsayilan, min=lo, max=hi, adim=adim, aciklama=aciklama,
                uygulama=uygulama)


def _b(key, ad, grup, aciklama, uygulama='anında', varsayilan=False):
    return dict(anahtar=key, ad=ad, grup=grup, tur='bool', varsayilan=varsayilan, aciklama=aciklama, uygulama=uygulama)


def _n(key, ad, grup, aciklama, uygulama='anında', lo=0, hi=10, varsayilan=1, birim=''):
    """Tam sayı (adet, saat): panelde sayı kutusu."""
    return dict(anahtar=key, ad=ad, grup=grup, tur='sayi', varsayilan=varsayilan, min=lo, max=hi, birim=birim, aciklama=aciklama,
                uygulama=uygulama)


SCHEMA = [
    # ---------------------------------------------------------------- savaş
    _c('npc_hasar', 'Uzaylıların verdiği hasar', 'savas', 'Uzaylıların (NPC) gemine, P.E.T.\'ine ve dost gemilere verdiği hasar. '
       '0: hiç hasar almazsın.'),
    _c('oyuncu_hasar', 'Verdiğin hasar', 'savas', 'Lazer, roket, fırlatıcı, mayın, Smart Bomb, top, P.E.T. ve yeteneklerle '
       'uzaylılara verdiğin hasar.', lo=0.1),
    _c('npc_can', 'Uzaylıların canı ve kalkanı', 'savas', 'Uzaylıların can ve kalkanı. Düşük değer uzaylıları çabuk '
       'öldürür.', uygulama='harita', lo=0.1),
    _b('dokunulmaz', 'Dokunulmaz gemi', 'savas', 'Uzaylıların atışları görünür ama gemin can ve kalkan kaybetmez.'),
    _b('sonsuz_cephane', 'Sonsuz cephane', 'savas', 'Lazer cephanesi, roketler, fırlatıcı cephanesi ve mayınlar harcanmaz (en az '
       'bir tane olmalı).'),
    _c('radyasyon', 'Radyasyon hasarı', 'savas', 'Harita sınırının dışındaki radyasyonun gövdeye verdiği hasar. 0: radyasyon '
       'zarar vermez.', lo=0.0, hi=5.0),
    # ---------------------------------------------------------------- ödüller
    _c('kredi', 'Kredi kazancı', 'odul', 'Uzaylı, kutu, görev, kapı ve etkinliklerden kazanılan kredi (satış ve iadeler '
       'hariç).', hi=50.0),
    _c('uridyum', 'Uridyum kazancı', 'odul', 'Uzaylı, kutu, görev, kapı ve etkinliklerden kazanılan uridyum.', hi=50.0),
    _c('ep', 'Deneyim (EP) kazancı', 'odul', 'Kazanılan deneyim puanı: seviye atlama hızı.', hi=50.0),
    _c('onur', 'Onur kazancı', 'odul', 'Kazanılan onur puanı.', hi=50.0),
    _c('toplama', 'Toplanan eşya miktarı', 'odul', 'Kutulardaki cephane ve eşyalar, uzaylıların kargo kutularındaki ve '
       'madenden toplanan cevher, uzaylıların ek ödülleri (Palladium, etkinlik paraları …). Kutudan çıkan kredi ve uridyum '
       'kendi çarpanıyla.', hi=50.0),
    _c('dusme', 'Eşya düşme şansı', 'odul', 'Uzaylılardan booster, ekipman, kaynak ve etkinlik kutusu düşme olasılığı; '
       'Galaksi Kapısı şanslı ödülleri (en çok %100).', hi=20.0),
    _c('kapi_parca', 'Kapı parçası şansı', 'odul', 'Galaksi Kapısı üreticisinde bir enerjiyle kapı parçası çıkma olasılığı '
       '(oyunun değeri %13; pencerenin olasılık listesi de değişir).', lo=0.1, hi=7.0),
    _c('kapi_enerji', 'Kapı enerjisi miktarı', 'odul', 'Bonus kutularından çıkan ücretsiz Galaksi Kapısı enerjisinin miktarı '
       '(5-2 tüccarındaki Palladium takası ve paketler değişmez).', hi=20.0),
    _n('kapi_bonus_adet', 'Bonuslu Galaksi Kapısı sayısı', 'odul', 'Kapı penceresinde aynı anda süreli bonus ödülü olan kapı '
       'sayısı. Kapılar ve ödülleri her dönemin başında rastgele seçilir; kapıyı dönem bitmeden tamamlayınca (Dispatch\'in kapı '
       'gönderimi dahil) bonus bir kez verilir. 0: bonus yok.', lo=0, hi=11, varsayilan=3, birim='kapı'),
    _c('kapi_bonus_carpan', 'Kapı bonusu miktarı', 'odul', 'Kapı bonusunun miktarı (onur, uridyum, cephane, log diski, anahtar); '
       'lazer ve tasarım gibi tek eşyalar bir tane kalır.', lo=0.1, hi=20.0),
    _n('kapi_bonus_saat', 'Kapı bonusu dönemi', 'odul', 'Bonuslu kapıların değiştiği aralık (gece yarısına hizalı; 24: her gün). '
       'Değiştirilince seçim hemen yenilenir.', lo=1, hi=168, varsayilan=24, birim='saat'),
    # ---------------------------------------------------------------- dünya
    _c('kutu_bolluk', 'Bonus kutusu bolluğu', 'dunya', 'Haritalardaki bonus kutusu sayısı (etkinlik kutuları dahil).',
       uygulama='harita', hi=10.0),
    _c('kutu_yenilenme', 'Kutuların yeniden çıkma süresi', 'dunya', 'Toplanan kutunun yerine yenisinin gelme süresi. '
       'Düşük değer: daha çabuk.', lo=0.1, hi=5.0),
    _c('npc_sayi', 'Uzaylı sayısı', 'dunya', 'Haritalardaki uzaylı sayısı (patronlar dahil; kapı ve mod dalgaları hariç).',
       uygulama='harita', hi=5.0),
    _c('npc_yenilenme', 'Uzaylıların yeniden doğma süresi', 'dunya', 'Ölen uzaylının yerine yenisinin gelme süresi. '
       'Düşük değer: daha çabuk.', lo=0.1, hi=5.0),
    _n('en_cok_gorev', 'Aynı anda alınabilen görev', 'dunya', 'Görev penceresinde aynı anda sürdürebileceğin görev sayısı (oyunun '
       'değeri 5). Dolunca yeni görev alınamaz; biri bitince ya da iptal edilince yer açılır. Düşürülürse süren görevler iptal '
       'edilmez.', lo=1, hi=10, varsayilan=5, birim='görev'),
    # ---------------------------------------------------------------- ekonomi
    _c('magaza_fiyat', 'Mağaza fiyatları', 'ekonomi', 'Mağazada kredi ve uridyumla satılan her şeyin fiyatı.', lo=0.0,
       hi=5.0),
    _c('tamir_ucreti', 'Ölüm sonrası tamir ücreti', 'ekonomi', 'Portalda ve bulunduğun yerde tamirin uridyum bedeli.',
       lo=0.0, hi=5.0),
    _c('kargo', 'Kargo kapasitesi', 'ekonomi', "Geminin kargo alanı (Logistics, kargo CPU'su ve P.E.T. protokolüyle birlikte).",
       lo=0.5, hi=10.0),
    _c('pet_yakit', 'P.E.T. yakıt tüketimi', 'ekonomi', "P.E.T.'in dakikalık yakıt tüketimi. 0: yakıt harcamaz.", lo=0.0, hi=5.0),
    # ---------------------------------------------------------------- süreler
    _c('bekleme', 'Üretim ve bekleme süreleri', 'sure', 'Assembly üretimi, Skylab yükseltmeleri ve taşıma, Dispatch gönderimleri, '
       'eşya yükseltmeleri. Düşük değer: daha çabuk (yeni başlayanlara uygulanır).', lo=0.01, hi=5.0),
    _c('yetenek_bekleme', 'Yetenek ve eşya beklemeleri', 'sure', "Gemi yetenekleri, CPU'lar, mayınlar, Smart Bomb, Insta-Shield, "
       'teknoloji eşyaları ve özel roketlerin bekleme süresi.', lo=0.1, hi=5.0),
    _c('booster_sure', 'Booster süresi', 'sure', 'Boosterların etkin kalma süresi (yeni etkinleştirilenlere uygulanır).', lo=0.1,
       hi=10.0),
    _b('seviye_kisiti_yok', 'Seviye kısıtları kapalı', 'sure', "Portalların ve atlama CPU'sunun seviye şartı yok: her haritaya "
       'girebilirsin.'),
    _b('seans_hep_acik', 'Seanslı etkinlikler hep açık', 'sure', 'Saatle açılan etkinlikler (Vortex of Greed, Treacherous Domain, '
       'Mimesis Mutiny) etkinlik süresince her an açık: portal hep açık, seans/savaş/sefer girince başlar.'),
    # ---------------------------------------------------------------- müzayede
    dict(anahtar='muzayede_rakip', ad='Sanal rakipler', grup='muzayede', tur='seviye', varsayilan=0,
         secenekler=list(RAKIP_SEVIYELERI), uygulama='anında',
         aciklama='Müzayedede sana rakip olan sanal teklifçiler. Çekingen ve Ilımlı: biraz teklif verirler ama seni hiç geçmezler, '
                  'teklif verdiğin lot hep senin olur. Rekabetçi ve Agresif: geçtiğinde karşılık verirler; bütçelerini aşmadıkça '
                  'lotu kaybedebilirsin (kredin geri gelir). Bot oyuncular gelene dek.'),
    # ---------------------------------------------------------------- arayüz
    _b('karanlik', 'Karanlık haritalar (el feneri)', 'arayuz', 'Trial of Terrors kapısının haritalarında ekran kararır, yalnız '
       'geminin baktığı yön aydınlıktır (istemcinin el feneri etkisi). Kapatılırsa haritalar aydınlık.', uygulama='harita',
       varsayilan=True),
    _b('sinematik', 'Sinematik patron girişleri', 'arayuz', 'Etkinlik patronu doğunca ve Galaksi Kapısının son dalgasında kamera '
       'birkaç saniye patrona döner (kontroller o sürede kilitli), sonra gemine geri gelir.', varsayilan=True),
    _b('ipuclari', 'Yeni başlayan ipuçları', 'arayuz', 'Bir şey ilk kez olunca (kargo doldu, cephane bitti, başka firmanın haritası) '
       've seviye atladıkça yeni özellikleri anlatan ipucu pencereleri, süren etkinliğin açıklaması. Her biri bir kez; kapattığın '
       'ipuçları açılmaz, ipucu arşivinden yeniden okunabilir.', varsayilan=True),
    _b('seri_oldurme', 'Seri öldürme duyuruları', 'arayuz', 'Kısa aralıklarla art arda uzaylı yok edince ekranda "Triple Kill", '
       '"Unstoppable", "Godlike", "Like a Boss" duyurusu ve sesi (3, 6, 10, 15 öldürme; aralık en çok 10 sn).'),
    _b('reklamsiz', 'Açılış pencerelerini gösterme', 'arayuz', 'Girişte kendiliğinden açılan günlük bonus, ipucu ve Season Pass '
       'pencereleri gönderilmez (menülerden açılabilirler).', uygulama='giriş'),
    # ---------------------------------------------------------------- geliştirici
    _b('yakin_npc', 'Yakında uzaylı doğur', 'gelistirici', 'Test kolaylığı: ilk dört uzaylı türünden birer tane geminin hemen '
       'yanında doğar.', uygulama='harita'),
    _b('gm_konsol', 'GM konsolu', 'gelistirici', 'Oyunun gizli yönetici penceresi: oyunda Ctrl, ardından Shift, ardından Z. Haritaya '
       'ışınlanma, uzaylı ve kutu doğurma, eşya ve paket verme, görevleri bitirme, kapı kurma, bekleme sürelerini sıfırlama, '
       'dokunulmazlık. Açıkken rütbe simgesi boş görünebilir (istemci yöneticiyi rütbe 6000 ile tanıyor).', uygulama='giriş'),
    _b('kontrol', 'Canlı test kontrol kanalı', 'gelistirici', 'Geliştirici aracı (kontrol.py, 127.0.0.1:8099): mesaj izi ve '
       'istek enjeksiyonu.', uygulama='başlatma'),
]
BY_KEY = {s['anahtar']: s for s in SCHEMA}
DEFAULTS = {s['anahtar']: s['varsayilan'] for s in SCHEMA}
ETKINLIK_DURUMLARI = ('acik', 'kapali')         # yoksa takvime göre

# hazır ayarlar (panelin "Hazır ayarlar" listesi): yalnız değişen anahtarlar, ötekiler varsayılan
HAZIR = {
    'varsayilan': {'ad': 'Varsayılan', 'aciklama': 'Oyunun kendi değerleri.', 'degerler': {}},
    'rahat': {'ad': 'Rahat', 'aciklama': 'Daha az hasar alırsın, ödüller ve kutular bol.',
              'degerler': {'npc_hasar': 0.5, 'kredi': 2.0, 'uridyum': 2.0, 'ep': 2.0, 'onur': 2.0, 'toplama': 2.0, 'dusme': 2.0,
                           'kutu_bolluk': 2.0, 'kutu_yenilenme': 0.5}},
    'hizli': {'ad': 'Hızlı ilerleme', 'aciklama': 'Ödüller beş kat, uzaylılar kalabalık ve çabuk doğar.',
              'degerler': {'kredi': 5.0, 'uridyum': 5.0, 'ep': 5.0, 'onur': 5.0, 'toplama': 5.0, 'dusme': 3.0, 'kutu_bolluk': 3.0,
                           'kutu_yenilenme': 0.3, 'npc_sayi': 1.5, 'npc_yenilenme': 0.3, 'magaza_fiyat': 0.5}},
    'zorlu': {'ad': 'Zorlu', 'aciklama': 'Uzaylılar daha sert vurur ve dayanıklıdır, ödüller az, rakipler agresif.',
              'degerler': {'npc_hasar': 2.0, 'npc_can': 1.5, 'kredi': 0.75, 'uridyum': 0.75, 'kutu_bolluk': 0.5,
                           'tamir_ucreti': 2.0, 'muzayede_rakip': 4}},
}

_lock = threading.Lock()
_state = {'yol': None, 'mtime': None, 'okuma': 0.0, 'd': {}}


def clean(raw):
    """Dosyadan gelen sözlük -> geçerli değerler (bilinmeyen anahtar yok, sayılar sınırda, türler doğru)."""
    out = {}
    if not isinstance(raw, dict):
        return out
    for key, v in raw.items():
        s = BY_KEY.get(key)
        if s is None:
            continue
        try:
            if s['tur'] == 'carpan':
                v = float(v)
                if v != v:                                # NaN
                    continue
                out[key] = min(s['max'], max(s['min'], v))
            elif s['tur'] == 'bool':
                out[key] = bool(v)
            elif s['tur'] == 'seviye':
                out[key] = min(len(s['secenekler']) - 1, max(0, int(v)))
            elif s['tur'] == 'sayi':
                v = float(v)
                if v != v:                                # NaN
                    continue
                out[key] = min(s['max'], max(s['min'], int(round(v))))
        except (TypeError, ValueError):
            continue
    ev = raw.get('etkinlikler')
    if isinstance(ev, dict):
        out['etkinlikler'] = {str(k): v for k, v in ev.items() if v in ETKINLIK_DURUMLARI}
    return out


def read(path):
    """Dosyadaki ayarlar (temizlenmiş); dosya yoksa ya da bozuksa {}."""
    try:
        with open(path, encoding='utf8') as fh:
            return clean(json.load(fh))
    except (OSError, ValueError):
        return {}


def write(path, values):
    """Ayarları atomik yaz (panel). Varsayılana eşit değerler de yazılır: dosya kullanıcının seçimidir."""
    d = clean(values)
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    tmp = path + '.tmp'
    with open(tmp, 'w', encoding='utf8', newline='\n') as fh:
        json.dump(d, fh, ensure_ascii=False, indent=1)
    os.replace(tmp, path)
    return d


def configure(argv=None, path=None):
    """Ayar dosyasını bağla: path, yoksa --ayarlar=<yol> seçeneği, yoksa save/ayarlar.json. path=False: bağı çöz (varsayılanlar)."""
    if path is None:
        argv = sys.argv if argv is None else argv
        path = next((a.split('=', 1)[1] for a in argv if a.startswith('--ayarlar=')), VARSAYILAN_YOL)
    with _lock:
        _state.update(yol=path or None, mtime=None, okuma=0.0, d={})
    return path


def _current():
    with _lock:
        if not _state['yol']:
            return _state['d']
        now = time.monotonic()
        if _state['mtime'] is not None and now - _state['okuma'] < YENILE_SN:
            return _state['d']
        _state['okuma'] = now
        try:
            m = os.stat(_state['yol']).st_mtime_ns
        except OSError:
            m = 0
        if m != _state['mtime']:
            _state['mtime'] = m
            _state['d'] = read(_state['yol']) if m else {}
        return _state['d']


def get(key):
    return _current().get(key, DEFAULTS[key])


def carpan(key):
    return float(get(key))


def adet(key, n):
    """Sayıyı (uzaylı, kutu adedi) çarpanla ölçekle: yuvarlanır, pozitif sayı en az 1 kalır (patron kaybolmaz); çarpan 0 ise 0."""
    m = carpan(key)
    if m == 1.0 or not n or n < 0:
        return n
    return 0 if m <= 0 else max(1, int(round(n * m)))


def miktar(key, n):
    """Miktarı (ödül, toplanan eşya) çarpanla ölçekle: kesir olasılıkla yuvarlanır (x1,5 ile 1 -> yarı yarıya 1 ya da 2),
    beklenen değer tam çarpan kadar."""
    m = carpan(key)
    if m == 1.0 or not n or n < 0:
        return n
    v = n * m
    whole = int(v)
    return whole + (1 if random.random() < v - whole else 0)


def sure(sec):
    """Üretim ve bekleme süresi (panelin 'bekleme' çarpanı): Assembly, Skylab, Dispatch, eşya yükseltme -> saniye (en az 1)."""
    m = carpan('bekleme')
    return sec if m == 1.0 else max(1, int(round(sec * m)))


def chance(key, p):
    """Olasılığı çarpanla ölçekle (0..1)."""
    m = carpan(key)
    return p if m == 1.0 else min(1.0, max(0.0, p * m))


def event_state(key):
    """Oyuncunun etkinlik seçimi: 'acik', 'kapali' ya da None (takvime göre)."""
    return (_current().get('etkinlikler') or {}).get(key)


def summary(values=None):
    """Varsayılandan farklı ayarlar [(ad, değer metni)] (panelin özet çipleri)."""
    d = _current() if values is None else clean(values)
    out = []
    for s in SCHEMA:
        v = d.get(s['anahtar'], s['varsayilan'])
        if v == s['varsayilan']:
            continue
        if s['tur'] == 'carpan':
            out.append((s['ad'], 'x%g' % v))
        elif s['tur'] == 'bool':
            out.append((s['ad'], 'açık' if v else 'kapalı'))
        elif s['tur'] == 'sayi':
            out.append((s['ad'], ('%d %s' % (v, s.get('birim', ''))).strip()))
        else:
            out.append((s['ad'], s['secenekler'][v]))
    return out
