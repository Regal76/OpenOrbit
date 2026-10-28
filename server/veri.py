"""Oyun verisi ve dünyalar (Dünya Editörü): data/<dosya> + seçili dünyanın o dosyaya yamaları.

Dünya: panelin Dünya Editörü'nde oluşturulan değişiklik katmanı (save/dunyalar/<kimlik>.json). Sunucular onu DO_DUNYA ortam
değişkeninden alır (panel/surecler.py); yoksa standart dünya (data/ olduğu gibi). Biçim:
  {"ad": …, "yamalar": {"npc.json": {"/tipler/84": {...}, "/haritalar/5/npc": [...]}, "magaza": {"/urunler/<lootId>": {...}}}}
Yama: JSON Pointer (RFC 6901) -> tam değer (varlık düzeyinde değiştirme); {"$sil": true} siler. Ebeveyni olmayan yol atlanır.
Sanal dosyalar (SANAL): data/'da karşılığı olmayan, yalnız dünyanın tanımladığı içerik (mağaza ürünlerinin fiyatı ve satışı).
Modüller içe aktarırken yukle() çağırır: dünya oyun açılırken seçilir. Oyun açıkken yalnız CANLI dosyaların değişikliği uygulanır
(tazele: dosya değişince yeniden okunur; game.dunya_izle mağazayı ve açık artırmayı yeniler); ötekiler sunucu yeniden başlayınca.
Yalnız standart kitaplık (panel de kullanır).
"""
import copy, json, os

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, 'data')
SIL = '$sil'
SANAL = {'magaza': {'urunler': {}}}      # magaza.py: {lootId: {fiyat, para ('C' | 'U'), satista}}
CANLI = ('magaza', 'sosyal.json')        # oyun açıkken uygulananlar: mağaza fiyatları ve satışı, açık artırma lotları
_DUNYA = None
_ZAMAN = None                            # okunan dünya dosyasının değişme zamanı
_ATLANAN = []                            # uygulanamayan yamalar (dosya, yol): günlük için


def dunya():
    """Seçili dünya (DO_DUNYA) ya da {} (standart). Okunamazsa standart."""
    global _DUNYA, _ZAMAN
    if _DUNYA is None:
        p, _DUNYA = os.environ.get('DO_DUNYA'), {}
        try:
            if p:
                _ZAMAN = os.path.getmtime(p)
                with open(p, encoding='utf8') as fh:
                    _DUNYA = json.load(fh)
        except (OSError, ValueError):
            pass
        if not isinstance(_DUNYA, dict):
            _DUNYA = {}
    return _DUNYA


def tazele():
    """Dünya dosyası okunduktan sonra değiştiyse yeniden okur -> CANLI dosyalardan değişenler (yoksa boş)."""
    global _DUNYA
    p = os.environ.get('DO_DUNYA')
    if not p or _DUNYA is None:
        return []
    try:
        t = os.path.getmtime(p)
    except OSError:
        return []
    if t == _ZAMAN:
        return []
    eski = (_DUNYA.get('yamalar') or {})
    _DUNYA = None
    yeni = (dunya().get('yamalar') or {})
    return [d for d in CANLI if eski.get(d) != yeni.get(d)]


def yol_parcalari(yol):
    """'/a/b~1c' -> ['a', 'b/c'] (JSON Pointer)."""
    return [p.replace('~1', '/').replace('~0', '~') for p in yol.split('/')[1:]]


def yol_yap(*parcalar):
    return ''.join('/' + str(p).replace('~', '~0').replace('/', '~1') for p in parcalar)


def uygula(veri, yamalar, dosya=''):
    """Yamaları veri üstüne uygular (yerinde); uygulananların sayısı. Liste ebeveyninde parça sıra numarasıdır."""
    n = 0
    for yol, deger in (yamalar or {}).items():
        parca = yol_parcalari(yol)
        if not parca:
            continue
        ust = veri
        try:
            for p in parca[:-1]:
                ust = ust[int(p)] if isinstance(ust, list) else ust[p]
            son = parca[-1]
            sil = isinstance(deger, dict) and deger.get(SIL)
            if isinstance(ust, list):
                i = int(son)
                if sil:
                    del ust[i]
                elif i == len(ust):
                    ust.append(copy.deepcopy(deger))
                else:
                    ust[i] = copy.deepcopy(deger)
            elif isinstance(ust, dict):
                if sil:
                    ust.pop(son, None)
                else:
                    ust[son] = copy.deepcopy(deger)
            else:
                raise TypeError(type(ust).__name__)
            n += 1
        except (KeyError, IndexError, ValueError, TypeError):
            _ATLANAN.append((dosya, yol))
    return n


def ham(dosya):
    """Standart dünyadaki hâli (yamasız)."""
    if dosya in SANAL:
        return copy.deepcopy(SANAL[dosya])
    with open(os.path.join(DATA, dosya), encoding='utf8') as fh:
        return json.load(fh)


def yukle(dosya, yamalar=None):
    """data/<dosya> + dünyanın (verilmezse seçili dünyanın) o dosyaya yamaları."""
    d = ham(dosya)
    uygula(d, (dunya().get('yamalar') or {}).get(dosya) if yamalar is None else yamalar, dosya)
    return d


def ozet():
    """Günlük satırı: seçili dünyanın adı, yama sayısı ve atlananlar."""
    w = dunya()
    if not w:
        return 'dünya: standart'
    n = sum(len(v or {}) for v in (w.get('yamalar') or {}).values())
    return 'dünya: %s (%d değişiklik%s)' % (w.get('ad') or '?', n, ', atlanan: %s' % _ATLANAN if _ATLANAN else '')
