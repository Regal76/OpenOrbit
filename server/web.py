"""Yerel web sunucusu: DarkOrbit Unity istemcisinin web girişini taklit eder (links.php, login.php, maps.php).

Kullanım: python -I web.py <log_klasörü> [--profil=<yol>]   (--profil: kayıt yuvasının profili; panel ve canlı testler verir;
game.py ile aynı olmalı. Verilmezse etkin yuvanınki, yollar.py)
HTTP: 8090 (gömülü tarayıcı), 80 (unityApi). Bilinmeyen her isteği kaydeder.
Arkadaş sunucusunun misafiri (panelin "Arkadaşlarınla Oyna"sı, panel/arkadas.py): --uzak=<adres:8081> --sohbet=<adres:7771>
--oturum=<anahtar> --uid=<kimlik> ile istemci oyuna ve sohbete arkadaşın sunucusunda girer (oturum anahtarı profili orada bulur;
kimlik sunucunun verdiği). --adres: dinlenen yerel adres (öntanımlı 127.0.0.1).
"""
import sys, os, threading, socket, time, json
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from urllib.request import Request, urlopen

log_dir = [a for a in sys.argv[1:] if not a.startswith('--')][0]


def arg(name, default=None):
    return next((a.split('=', 1)[1] for a in sys.argv if a.startswith('--%s=' % name)), default)


PROFIL_YOLU = arg('profil')
os.makedirs(log_dir, exist_ok=True)
lock = threading.Lock()
SESSION = arg('oturum', 'localtest')
ADRES = arg('adres', '127.0.0.1')
CHAT_HOST = arg('sohbet', '127.0.0.1:7771')
UID = arg('uid')


def log(name, text):
    with lock:
        with open(os.path.join(log_dir, name), 'a', encoding='utf8') as fh:
            fh.write(time.strftime('%H:%M:%S ') + text + '\n')


BASE = 'http://%s/' % ADRES


def default_profile():
    import yollar
    return yollar.profile_path()


def profile():
    """Oyun sunucusunun profili varsa kullanıcı kimliği, gemi, harita ve 2D seçimi oradan gelir."""
    p = PROFIL_YOLU or default_profile()
    try:
        d = json.load(open(p, encoding='utf8'))
        use2d = bool(((d.get('ayarlar') or {}).get('displaySettingsModule') or {}).get('displayUse2d'))
        return d['pilot']['userId'], d['gemi']['typeId'], d['konum']['mapId'], use2d
    except (OSError, KeyError, ValueError):
        return 1, 'ship_goliath', 1, False


def web_settings_path():
    """Web tarafının ayarları (giriş ekranında seçilen dil) profilin yanında ayrı dosyada: profili oyun sunucusu yazıyor."""
    p = PROFIL_YOLU or default_profile()
    return os.path.join(os.path.dirname(os.path.abspath(p)), 'web_ayarlari.json')


def web_settings():
    try:
        d = json.load(open(web_settings_path(), encoding='utf8'))
        return d if isinstance(d, dict) else {}
    except (OSError, ValueError):
        return {}


def stored_lang():
    """Kayıtlı giriş dili (doğrulanmış) ya da None."""
    import re
    lang = str(web_settings().get('lang') or '')
    return lang if re.fullmatch(r'[a-z]{2}(_[a-z]{2})?', lang) else None


def set_lang(body):
    """Giriş ekranında dil seçilince istemci (LaunchShow.DropdownValueChanged) POST /unityApi/setLang.php "lang=tr" gönderiyor.
    Saklanmıyordu, dil her açılışta İngilizceye dönüyordu (canlı test H88, kullanıcı bildirimi): artık web_ayarlari.json'da; giriş
    sayfası lang çerezi (istemci dili buradan alıyor, redirect_page) ve web girişinin lang alanı olarak verilir."""
    import re
    from urllib.parse import parse_qs
    lang = (parse_qs(body.decode('utf8', 'replace')).get('lang') or [''])[0].strip().lower()
    if re.fullmatch(r'[a-z]{2}(_[a-z]{2})?', lang):
        d = dict(web_settings(), lang=lang)
        p = web_settings_path()
        with lock:
            with open(p + '.tmp', 'w', encoding='utf8') as fh:
                json.dump(d, fh, ensure_ascii=False, indent=1)
            os.replace(p + '.tmp', p)
    return 'text/plain', ''


def login_node():
    # DarkOrbit.LoginNodeData alan türleri il2types.py ile doğrulandı (long/bool/Uri/ServerInfo/Hangars)
    now = int(time.time())
    user_id, ship, map_id, use2d = profile()
    user_id = int(UID) if UID else user_id
    lang = stored_lang() or 'en'
    hangar = {'modelId': 10, 'slotNumber': 1, 'mapId': map_id, 'hangarId': 1, 'shipName': ship.replace('ship_', '').title(), 'tooltipIcon': '',
              'shipDestroyed': False, 'shipId': ship, 'hangarActive': True}
    return {
        'gameclientHash': 'local', 'chatHost': CHAT_HOST, 'profileXmlHash': '1', 'loadingscreenHash': '1',
        'pid': 175, 'opid': 0, 'sessionID': SESSION, 'userID': user_id, 'platform': 'client',
        'loadingscreenAssetsXmlHash': '1', 'showAdvertisingHint': False, 'useHash': 0, 'resourceJumpGateXmlHash': '1',
        'browser': 'unity', 'host': BASE, 'useDeviceFonts': 0, 'theme': BASE, 'mapID': map_id, 'lang': lang,
        'itemXmlHash': '1', 'eventStreamContext': '', 'resourcesXmlHash': '1', 'allowChat': 0, 'nextAction': 'internalWebGL',
        'requestScheme': 'http', 'resources3dparticlesXmlHash': '1', 'cdn': BASE, 'resourceEventsXmlHash': '1',
        'gameclientAllowedInitDelay': 0, 'gameclientPath': 'spacemap/', 'helpLink': BASE, 'basePath': 'spacemap',
        # serverInfo: istemci (GameLoadingManager.StartGame) saati "h:mm tt / hh:mm tt / H:mm / HH:mm", tarihi "dd.MM.yyyy" ile
        # ayrıştırıp oyun saatini kuruyor; saniyeli saat ve ISO tarih ayrıştırılamıyor, HUD saati her girişte 08:47'den başlıyordu
        # (canlı test N1 -> H78)
        'fullscreen': 0, 'serverInfo': {'timeStamp': now, 'serverDate': time.strftime('%d.%m.%Y'), 'instanceName': 'Local',
                                        'serverTime': time.strftime('%H:%M')},
        # display2d: istemci her girişte 2D/3D kipini buradan kurar (GameLoadingManager.UpdateWebData -> Settings, 1 = 3D, 2 = 2D;
        # yerel force2D ile aynı kodlama). Hep 1 gidiyordu: ayarlarda 2D seçilip yeniden girilince 3D açılıyordu (canlı test H73,
        # kullanıcı bildirimi). Seçim oyun sunucusunda DisplaySettingsRequest.displayUse2d ile profile yazılıyor
        'sharedImages': BASE + 'do_img/', 'display2d': 2 if use2d else 1, 'resourceachievementsXmlHash': '1', 'loadingClaim': '',
        'resources3dXmlHash': '1', 'hangars': {'data': {'faction': '1', 'hangars': [hangar]}}, 'autoStartEnabled': 1,
        'boardLink': BASE, 'crossdomainHash': '1', 'userProfileImage': '',
    }


def links():
    return {'forum': BASE, 'help': BASE, 'credits': BASE, 'imprint': BASE, 'support': BASE, 'accountCenter': BASE}


def login():
    # LoginDataNew { [JsonProperty("data")] string LoginData } -> içindeki JSON metni LoginNodeData olarak ikinci kez ayrıştırılır
    n = login_node()
    return dict(n, success=1, message='', data=json.dumps(n), loginData=json.dumps(n))


GAME_SERVER = arg('uzak', '127.0.0.1:8081')
_MAP_IDS = None


def maps_xml():
    # Harita kimlikleri istemcinin kendi maps-config.xml dosyasından (Unity paketinden çıkarıldı)
    global _MAP_IDS
    if _MAP_IDS is None:
        import re
        src = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', 'maps-config.xml')
        try:
            _MAP_IDS = sorted(set(int(x) for x in re.findall(r'<map id="(\d+)"', open(src, encoding='utf8').read())))
        except OSError:
            _MAP_IDS = list(range(1, 30))
    body = ''.join('<map id="%d"><gameserverIP>%s</gameserverIP></map>' % (i, GAME_SERVER) for i in _MAP_IDS)
    return '<?xml version="1.0" encoding="UTF-8"?><maps>' + body + '</maps>'


# Kapı penceresinin "ödüller" rehberi (istemci: UIGalaxyGatesSystem.LoadXmlDataGate -> GalaxyGatesRewardInfo). Kök öğenin her
# çocuğu bir kapı (name = kapının istemcideki adı: alpha … hades, streuner), içindeki item'lar: id = lootId, chance = olasılık
# sınıfı 1-5 ("dispatch_tooltip_description_dropChance-N": çok düşük … çok yüksek), min = adet (simge kademesi). Değerler
# data/kapilar.json'un tamamlama ödülleri (oyunun kendi değerleri; panelin çarpanları uygulanmaz).
GATE_LOOT = {'xenomit': 'resource_ore_xenomit', 'log_disk': 'resource_logfile', 'kupon': 'resource_repairvoucher',
             'enerji': 'resource_extra-energy', 'abr': 'resource_collectable_axion-beam-regulator',
             'schism': 'resource_collectable_schism', 'yesil_anahtar': 'resource_booty-key'}


def chance_class(p):
    return 5 if p >= 1 else 4 if p >= 0.5 else 3 if p >= 0.2 else 2 if p >= 0.05 else 1


def gate_rewards_xml():
    from xml.sax.saxutils import quoteattr
    src = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', 'kapilar.json')
    try:
        gates = json.load(open(src, encoding='utf8'))['kapilar']
    except (OSError, ValueError, KeyError):
        gates = {}
    out = []
    for key, g in gates.items():
        R = g.get('odul') or {}
        rows = [('currency_experience', R.get('ep', 0), 1.0), ('currency_honour', R.get('onur', 0), 1.0),
                ('currency_uridium', R.get('uridyum', 0), 1.0)]
        rows += [(loot, n, 1.0) for loot, n in sorted((R.get('cephane') or {}).items())]
        rows += [(GATE_LOOT[k], R.get(k, 0), 1.0) for k in ('xenomit', 'log_disk', 'kupon', 'enerji')]
        rows += [(GATE_LOOT.get(k, k), n, 1.0) for k, n in sorted((R.get('ganimet') or {}).items())]
        for s in R.get('sans', []):
            opts = s.get('secenekler') if s.get('esya') == 'tasarim_secimi' else [s.get('esya')]
            rows += [(loot, s.get('adet', 1), s.get('olasilik', 0) / max(1, len(opts))) for loot in opts or []]
        items = ''.join('<item id=%s chance="%d" min="%d"/>' % (quoteattr(loot), chance_class(p), n) for loot, n, p in rows
                        if loot and n)
        out.append('<gate name=%s>%s</gate>' % (quoteattr(key), items))
    return '<?xml version="1.0" encoding="UTF-8"?><ggRewards>' + ''.join(out) + '</ggRewards>'


def galaxy_trek_xml(kind):
    here = os.path.dirname(os.path.abspath(__file__))
    if here not in sys.path:
        sys.path.insert(0, here)          # -I ile çalışınca betiğin klasörü yolda değil
    import galaxy_trek as GTR
    return GTR.planets_xml() if kind == 'gezegen' else GTR.rewards_xml()


ROUTES = {
    '/spacemap/xml/maps.php': lambda h: ('text/xml', maps_xml()),
    '/unityApi/events/spaceSearch.php': lambda h: ('text/xml;charset=UTF-8', galaxy_trek_xml('gezegen')),    # Galaxy Trek (Ö3)
    '//unityApi/events/spaceSearch.php': lambda h: ('text/xml;charset=UTF-8', galaxy_trek_xml('gezegen')),
    '/unityApi/events/ssRewards.php': lambda h: ('text/xml;charset=UTF-8', galaxy_trek_xml('odul')),
    '//unityApi/events/ssRewards.php': lambda h: ('text/xml;charset=UTF-8', galaxy_trek_xml('odul')),
    '/unityApi/guide/ggRewards.php': lambda h: ('text/xml;charset=UTF-8', gate_rewards_xml()),
    '/unityApi/links.php': lambda h: ('application/json', json.dumps(links())),
    '/unityApi/login.php': lambda h: ('application/json', json.dumps(login())),
    '/unityApi/setLang.php': lambda h: set_lang(h.body),
    '/unityApi/agent.php': lambda h: ('text/plain', ''),          # istemcinin olay izleme bildirimi (ör. Unity_ChangeLanguagetr)
}

CDN_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'cdn')
CDN_TYPES = {'.xml': 'application/xml', '.php': 'text/xml;charset=UTF-8', '.png': 'image/png', '.jpg': 'image/jpeg',
             '.jpeg': 'image/jpeg', '.gif': 'image/gif', '.webp': 'image/webp', '.json': 'application/json', '.webm': 'video/webm'}
CDN_RESMI = 'https://darkorbit-22.bpsecure.com/'      # oyunun görselleri (Bigpoint'in) depoda yok: ilk istenişte buradan
cdn_olmayan = set()                                    # inmeyenler (internet yok, resmî CDN'de yok): yeniden denenmez


def cdn_fetch(rel, p):
    """Yerelde olmayan oyun görseli (do_img/) resmî CDN'den bir kez indirilip saklanır; olmazsa False (istemci görselsiz)."""
    if not rel.startswith('do_img/') or rel in cdn_olmayan:
        return False
    try:
        with urlopen(Request(CDN_RESMI + rel, headers={'User-Agent': 'Mozilla/5.0'}), timeout=8) as r:
            data = r.read()
    except Exception as e:
        cdn_olmayan.add(rel)
        log('unknown.log', 'CDN indirilemedi: %s (%s)' % (rel, e))
        return False
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p + '.part', 'wb') as fh:
        fh.write(data)
    os.replace(p + '.part', p)
    return True


def cdn_file(base):
    """İstemcinin CDN isteği yerel kopyada varsa (oyunun görselleri ilk istenişte resmî CDN'den iner) -> (içerik türü, baytlar)."""
    rel = base.lstrip('/')
    while '//' in rel:
        rel = rel.replace('//', '/')
    if not rel or '..' in rel.split('/'):
        return None
    p = os.path.join(CDN_DIR, *rel.split('/'))
    if not os.path.isfile(p) and not cdn_fetch(rel, p):
        return None
    return CDN_TYPES.get(os.path.splitext(p)[1].lower(), 'application/octet-stream'), open(p, 'rb').read()


def redirect_page():
    """Gömülü tarayıcının ilk sayfası: oturum çerezi ve oyun girişine yönlendirme. Kayıtlı giriş dili varsa önce istemciye
    "Unity_ChangeLanguage<dil>" mesajı gider: istemci sayfanın konsol iletilerini dinliyor (GameLoadingManager.UpdateMessage,
    ConsoleMessageLogged -> UpdateWebData: WebGlData.message -> Settings.Language). İstemcinin öteki dil kaynağı tarayıcının lang çerezi (OpenWebLogin) ama tarayıcı her açılışta çerezsiz
    başlıyor ve istemcinin çerez okuması boş dönüyor; web girişinin lang alanını da kullanmıyor (canlı test H88)."""
    lang = stored_lang()
    js = 'document.cookie="dosid=%s; path=/";' % SESSION
    js += 'var gone=false;function go(){if(!gone){gone=true;location.href="/indexInternal.es?action=internalWebGL";}}'
    if lang:
        msg = json.dumps({'success': 1, 'message': 'Unity_ChangeLanguage' + lang})
        js += ('document.cookie="lang=%s; path=/";' % lang +
               'setTimeout(function(){console.log(%s);setTimeout(go,400);},300);' % json.dumps(msg))
    else:
        js += 'go();'
    return ('<!doctype html><html><body style="background:#000;color:#9cf;font-family:Verdana">DarkOrbit yerel sunucu<script>'
            + js + '</script></body></html>')


class H(BaseHTTPRequestHandler):
    protocol_version = 'HTTP/1.1'

    def _all(self):
        n = int(self.headers.get('Content-Length') or 0)
        body = self.body = self.rfile.read(n) if n else b''
        path = self.path.split('#')[0]
        base = path.split('?')[0]
        port = self.server.server_address[1]
        status = 200
        if base in ROUTES:
            ctype, out = ROUTES[base](self)
        elif port == 8090 and base == '/':
            ctype, out = 'text/html; charset=utf-8', redirect_page()
        elif 'indexInternal.es' in path:
            ctype, out = 'text/plain', SESSION
        elif cdn_file(base):
            ctype, out = cdn_file(base)
        else:                    # istemcinin bilinen uçları yukarıda; bilinmeyen istek boş 200 yerine 404 (http.log'da görünür)
            ctype, out, status = 'text/plain', '', 404
            log('unknown.log', '%s :%d %s body=%r' % (self.command, port, self.path, body[:500]))
        out = out.encode('utf8') if isinstance(out, str) else out
        log('http.log', '%s :%d %s cookie=%s body=%r -> %d, %d bytes %s' % (self.command, port, self.path, self.headers.get('Cookie'), body[:300], status, len(out), out[:160]))
        self.send_response(status)
        self.send_header('Content-Type', ctype)
        self.send_header('X-Custom-Header', 'DarkOrbitUnity')   # GetPost bu başlık olmadan girişi reddediyor
        self.send_header('Content-Length', str(len(out)))
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(out)

    do_GET = do_POST = do_PUT = do_HEAD = _all

    def log_message(self, *a):
        pass


class Sunucu(ThreadingHTTPServer):
    def handle_error(self, request, client_address):
        """İstemcinin kopardığı bağlantıda http.server'ın yığın dökümü (stderr) yerine errors.log'a tek satır."""
        log('errors.log', 'http %s: %r' % (client_address[0], sys.exc_info()[1]))


def serve_http(port):
    try:
        Sunucu((ADRES, port), H).serve_forever()
    except OSError as e:
        log('errors.log', 'http %d: %s' % (port, e))


def serve_tcp(port):
    try:
        s = socket.socket(); s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind((ADRES, port)); s.listen(5)
    except OSError as e:
        log('errors.log', 'tcp %d: %s' % (port, e)); return
    while True:
        c, addr = s.accept()
        log('tcp.log', 'tcp %d connect from %s' % (port, addr))

        def rd(c=c):
            c.settimeout(300)
            try:
                while True:
                    d = c.recv(65536)
                    if not d:
                        break
                    log('tcp.log', 'tcp %d recv %d: %s' % (port, len(d), d[:256].hex()))
            except Exception as e:
                log('tcp.log', 'tcp %d closed: %s' % (port, e))
        threading.Thread(target=rd, daemon=True).start()


if __name__ == '__main__':          # içe aktarınca (testler) sunucu açılmaz
    for p in (80, 8090):
        threading.Thread(target=serve_http, args=(p,), daemon=True).start()
    for p in (843, 9339, 8082):         # 7771: yerel sohbet sunucusu oyun sürecinde (sohbet.py)
        threading.Thread(target=serve_tcp, args=(p,), daemon=True).start()
    log('server.log', 'web started')
    while True:
        time.sleep(3600)
