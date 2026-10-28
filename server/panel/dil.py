"""Panelin dili (ilk açılışta kurulum sihirbazında seçilir; save/panel.json 'dil', Panel sayfasından değişir).

Metinler kodda Türkçe yazılır; öbür dillerinki arayuz/<kod>.json'da, anahtar Türkçe metnin kendisi (gettext gibi). Arayüz (panel.js
T()) ve Python (t()) aynı sözlükleri kullanır. Sözlükte olmayan metin önce İngilizceye, o da yoksa Türkçeye düşer: yarım bir çeviri de
kullanılabilir. Biçim: Python metinlerinde %s, arayüzde {0} {1} … Eksik ya da biçimi tutmayan çevirileri test/test_panel_dil.py yakalar.

Yeni dil: DILLER'e ekle, arayuz/<kod>.json'u yaz. Eksik metinler (İngilizceleriyle): python dil.py <kod>
"""
import json, os, sys, threading

# kod -> (kendi dilinde adı, tarih/sayı biçimi için yerel ayar)
DILLER = {
    'tr': ('Türkçe', 'tr-TR'),
    'en': ('English', 'en-US'),
    'de': ('Deutsch', 'de-DE'),
    'es': ('Español', 'es-ES'),
    'fr': ('Français', 'fr-FR'),
    'pl': ('Polski', 'pl-PL'),
    'pt': ('Português (Brasil)', 'pt-BR'),
    'ru': ('Русский', 'ru-RU'),
}
ARAYUZ = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'arayuz')
SOZLUK = os.path.join(ARAYUZ, 'en.json')
_secili = None                  # panel bağlar: () -> DILLER'den bir kod | None
_sozluk = {}
_lock = threading.Lock()


def bagla(fn):
    """Seçili dili veren işlevi bağla (panel: CFG.get('dil'))."""
    global _secili
    _secili = fn


def current():
    try:
        d = _secili() if _secili else None
    except Exception:
        d = None
    return d if d in DILLER else 'tr'


def sozluk(kod='en'):
    with _lock:
        if kod not in _sozluk:
            try:
                with open(os.path.join(ARAYUZ, kod + '.json'), encoding='utf8') as fh:
                    _sozluk[kod] = json.load(fh)
            except (OSError, ValueError):
                _sozluk[kod] = {}
        return _sozluk[kod]


def liste():
    """Arayüzün dil seçimi: kod, ad, yerel ayar ve çevrilmiş metin oranı (İngilizce sözlüğe göre)."""
    tam = len(sozluk('en')) or 1
    return [{'kod': k, 'ad': ad, 'yerel': yerel,
             'kapsam': 100 if k in ('tr', 'en') else min(100, round(100 * len(sozluk(k)) / tam))}
            for k, (ad, yerel) in DILLER.items()]


def t(text, *args):
    """Metnin seçili dildeki hâli (yoksa İngilizcesi, o da yoksa Türkçesi); args varsa % ile biçimlenir."""
    lang = current()
    if text and lang != 'tr':
        text = sozluk(lang).get(text) or sozluk('en').get(text, text)
    return text % args if args else text


if __name__ == '__main__':      # çevirmenler için: bir dilde eksik metinler, İngilizceleriyle (JSON)
    kod = sys.argv[1] if len(sys.argv) > 1 else ''
    if kod not in DILLER or kod == 'tr':
        sys.exit('kullanım: python dil.py <%s>' % '|'.join(k for k in DILLER if k != 'tr'))
    sys.stdout.reconfigure(encoding='utf-8')
    have = sozluk(kod)
    json.dump({k: v for k, v in sozluk('en').items() if k not in have}, sys.stdout, ensure_ascii=False, indent=0)
    print()
