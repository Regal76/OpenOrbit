"""Sunucu ve istemci süreçleri (panel).

  web   web.py: 80, 8090 (web girişi; 843, 9339, 8082 sahte TCP)
  oyun  game.py: 8081 (oyun), 7771 (sohbet), 8099 (kontrol kanalı, ayarla)
Sunucular konsolsuz (CREATE_NO_WINDOW) çalışır; çıktıları logs/<ad>_konsol.log'a (çökme izi orada). Oyun sunucusu --durdur=<dosya>
ile durdurulur: dosya belirince profili kaydedip çıkar (zorla kapatmada son kaydedilmemiş saniyeler gitmesin); yanıt vermezse
sonlandırılır. Portu başka süreç tutuyorsa (önceki oturumdan kalan sunucu, başka program) kim olduğu bulunur; panel yalnız bu
projenin web.py / game.py süreçlerini kapatabilir.
"""
import os, socket, subprocess, sys, threading, time

from dil import t as _

PANEL_DIR = os.path.dirname(os.path.abspath(__file__))
SERVER = os.path.dirname(PANEL_DIR)
NO_WINDOW = 0x08000000
PORTS = {'web': (8090, 80), 'oyun': (8081, 7771)}
PORT_ADLARI = {8090: 'Web girişi', 80: 'Web API', 8081: 'Oyun', 7771: 'Sohbet', 8099: 'Kontrol kanalı'}
SCRIPTS = {'web': 'web.py', 'oyun': 'game.py'}
ERKEN_KAPANMA_SN = 15


def python_exe():
    """Sunucular için python.exe (panel pythonw.exe ile açıldıysa yanındaki python.exe)."""
    d, b = os.path.split(sys.executable)
    if b.lower() == 'pythonw.exe' and os.path.exists(os.path.join(d, 'python.exe')):
        return os.path.join(d, 'python.exe')
    return sys.executable


def listeners():
    """Dinleyen IPv4 TCP soketleri {port: pid} (Windows TCP tablosu: GetExtendedTcpTable). Porta bağlanılmaz: bağlanmak oyun
    sunucusunda sahte bir oturum açıp günlüğe 'connect/disconnect' yazdırıyordu. Windows dışında None."""
    if os.name != 'nt':
        return None
    import ctypes
    from ctypes import wintypes
    size = wintypes.DWORD(0)
    fn = ctypes.windll.iphlpapi.GetExtendedTcpTable
    fn(None, ctypes.byref(size), False, 2, 3, 0)                      # AF_INET, TCP_TABLE_OWNER_PID_LISTENER
    for _ in range(3):
        buf = ctypes.create_string_buffer(size.value + 4096)
        size = wintypes.DWORD(len(buf))
        if fn(buf, ctypes.byref(size), False, 2, 3, 0) == 0:
            break
    else:
        return None
    n = ctypes.cast(buf, ctypes.POINTER(wintypes.DWORD))[0]
    rows = ctypes.cast(ctypes.addressof(buf) + 4, ctypes.POINTER(wintypes.DWORD * 6))
    out = {}
    for i in range(n):
        r = rows[i]
        out.setdefault(socket.ntohs(r[2] & 0xFFFF), r[5])
    return out


def listening(port, table=None):
    """Port dinleniyor mu (bağlanmadan; tablo yoksa bağlanarak)."""
    t = table if table is not None else listeners()
    if t is not None:
        return port in t
    with socket.socket() as s:
        s.settimeout(0.25)
        return s.connect_ex(('127.0.0.1', port)) == 0


def port_owners(ports):
    """{port: pid} dinleyen süreçler (TCP tablosu, yoksa netstat)."""
    t = listeners()
    if t is not None:
        return {p: pid for p, pid in t.items() if p in ports}
    try:
        r = subprocess.run(['netstat', '-ano', '-p', 'TCP'], capture_output=True, text=True, timeout=10, creationflags=NO_WINDOW)
    except Exception:
        return {}
    out = {}
    for line in r.stdout.splitlines():
        parts = line.split()
        # dinleyen soket: yabancı adres *:0 (durum sözcüğü Windows diline göre değişir)
        if len(parts) >= 5 and parts[0] == 'TCP' and parts[2].endswith(':0'):
            try:
                port = int(parts[1].rsplit(':', 1)[1])
                pid = int(parts[-1])
            except (ValueError, IndexError):
                continue
            if port in ports and pid:
                out.setdefault(port, pid)
    return out


def process_info(pid):
    """{'pid', 'ad', 'komut'} (PowerShell CIM; bulunamazsa ad '?')."""
    try:
        cmd = ('$p = Get-CimInstance Win32_Process -Filter "ProcessId=%d"; if ($p) { $p.Name; $p.CommandLine }' % int(pid))
        r = subprocess.run(['powershell', '-NoProfile', '-NonInteractive', '-Command', cmd], capture_output=True, text=True,
                           timeout=15, creationflags=NO_WINDOW, encoding='utf8', errors='replace')
        lines = r.stdout.splitlines()
        return {'pid': pid, 'ad': lines[0].strip() if lines else '?', 'komut': lines[1].strip() if len(lines) > 1 else ''}
    except Exception:
        return {'pid': pid, 'ad': '?', 'komut': ''}


def is_our_server(info):
    """Bu projenin web.py / game.py süreci mi (komut satırından)?"""
    c = (info.get('komut') or '').lower().replace('/', '\\')
    return 'python' in (info.get('ad') or '').lower() and any(os.path.join(SERVER, s).lower() in c or
                                                             ('\\server\\%s' % s) in c for s in SCRIPTS.values())


def kill(pid):
    subprocess.run(['taskkill', '/PID', str(int(pid)), '/T', '/F'], capture_output=True, timeout=15, creationflags=NO_WINDOW)


def tail(path, lines=200, max_bytes=512 * 1024):
    """Dosyanın son satırları (büyük günlükte yalnız sonu okunur)."""
    try:
        with open(path, 'rb') as fh:
            fh.seek(0, 2)
            size = fh.tell()
            fh.seek(max(0, size - max_bytes))
            data = fh.read()
    except OSError:
        return []
    text = data.decode('utf8', 'replace').splitlines()
    if size > max_bytes:
        text = text[1:]
    return text[-lines:]


class Surec:
    """Panelin açtığı bir sunucu süreci."""

    def __init__(self, ad, cmd, konsol, durdur=None):
        self.ad, self.cmd, self.konsol, self.durdur = ad, cmd, konsol, durdur
        self.proc = None
        self.basla = None
        self.durduruldu = False

    def start(self):
        os.makedirs(os.path.dirname(self.konsol), exist_ok=True)
        if self.durdur and os.path.exists(self.durdur):
            os.remove(self.durdur)
        fh = open(self.konsol, 'a', encoding='utf8')
        fh.write('\n==== %s başlatıldı: %s\n' % (time.strftime('%Y-%m-%d %H:%M:%S'), ' '.join(self.cmd[1:])))
        fh.flush()
        env = dict(os.environ, PYTHONIOENCODING='utf8', PYTHONUNBUFFERED='1')
        self.proc = subprocess.Popen(self.cmd, cwd=SERVER, stdout=fh, stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL,
                                     creationflags=NO_WINDOW, env=env)
        fh.close()
        self.basla = time.time()
        self.durduruldu = False
        return self

    @property
    def alive(self):
        return self.proc is not None and self.proc.poll() is None

    @property
    def crashed(self):
        """Panel durdurmadan kapandı mı (çıkış kodu)?"""
        return self.proc is not None and self.proc.poll() is not None and not self.durduruldu

    def stop(self, timeout=6.0):
        if not self.alive:
            return
        self.durduruldu = True
        if self.durdur:
            with open(self.durdur, 'w') as fh:
                fh.write('durdur')
            try:
                self.proc.wait(timeout)
                return
            except subprocess.TimeoutExpired:
                pass
        self.proc.terminate()
        try:
            self.proc.wait(5)
        except subprocess.TimeoutExpired:
            kill(self.proc.pid)

    def status(self):
        if self.proc is None:
            return {'durum': 'kapali'}
        code = self.proc.poll()
        if code is None:
            return {'durum': 'acik', 'pid': self.proc.pid, 'sure_sn': int(time.time() - self.basla)}
        return {'durum': 'kapali' if self.durduruldu else 'coktu', 'cikis_kodu': code}


class Yonetici:
    """Sunucular ve istemci: başlatma sırası, durum, istemci kapanınca yapılacaklar."""

    def __init__(self, logs, log=print):
        self.logs, self.log = logs, log
        self.lock = threading.RLock()
        self.sunucular = {}                 # ad -> Surec
        self.profil = None                  # açık sunucuların profil yolu
        self.slot = None
        self.istemci = None                 # Popen
        self.istemci_basla = None
        self.istemci_son = None             # {'sure_sn', 'erken', 'kod'}
        self.on_client_exit = None          # panel bağlar: (erken) -> None

    # ------------------------------------------------------------ sunucular
    def servers_alive(self):
        return {ad: s.alive for ad, s in self.sunucular.items()}

    def running(self):
        """Panelin açtığı oyun sunucusu çalışıyor mu?"""
        s = self.sunucular.get('oyun')
        return bool(s and s.alive)

    def foreign_ports(self):
        """Panelin açmadığı süreçlerin tuttuğu portlar -> [{'port', 'ad', 'pid', 'surec', 'komut', 'bizim'}]."""
        ours = {s.proc.pid for s in self.sunucular.values() if s.alive}
        table = listeners()
        busy = [p for p in PORT_ADLARI if listening(p, table)]
        if not busy:
            return []
        owners = {p: pid for p, pid in table.items() if p in busy} if table is not None else port_owners(set(busy))
        out = []
        for port in busy:
            pid = owners.get(port)
            if pid in ours:
                continue
            info = process_info(pid) if pid else {'pid': None, 'ad': '?', 'komut': ''}
            out.append({'port': port, 'ad': _(PORT_ADLARI[port]), 'pid': pid, 'surec': info['ad'], 'komut': info['komut'][:300],
                        'bizim': is_our_server(info)})
        return out

    def start_servers(self, profil, ayarlar, kontrol=False, slot=None):
        """Web ve oyun sunucusu (açık değilse) -> başlatılanların adları. Port doluysa ya da sunucu açılmazsa RuntimeError."""
        with self.lock:
            if self.running() and self.profil and os.path.normcase(self.profil) != os.path.normcase(profil):
                self.stop_servers()                               # başka kayıt: yeniden başlat
            started = []
            py = python_exe()
            for ad in ('web', 'oyun'):
                s = self.sunucular.get(ad)
                if s and s.alive:
                    continue
                busy = [p for p in PORTS[ad] if listening(p)]
                if busy:
                    raise RuntimeError(_('%s portu (%s) başka bir süreçte açık. Sunucu sayfasından kapatın ya da o programı kapatın.',
                                         '/'.join(map(str, busy)), _(PORT_ADLARI[busy[0]])))
                cmd = [py, '-I', os.path.join(SERVER, SCRIPTS[ad]), self.logs, '--profil=%s' % profil]
                durdur = None
                if ad == 'oyun':
                    durdur = os.path.join(self.logs, '.durdur_oyun')
                    cmd += ['--ayarlar=%s' % ayarlar, '--durdur=%s' % durdur] + (['--kontrol'] if kontrol else [])
                self.sunucular[ad] = Surec(ad, cmd, os.path.join(self.logs, '%s_konsol.log' % ad), durdur).start()
                started.append(ad)
            self.profil, self.slot = profil, slot
            deadline = time.time() + 20
            while time.time() < deadline:
                if all(listening(PORTS[ad][0]) for ad in ('web', 'oyun')):
                    break
                dead = [ad for ad in ('web', 'oyun') if not self.sunucular[ad].alive]
                if dead:
                    lines = tail(self.sunucular[dead[0]].konsol, 12)
                    raise RuntimeError(_('%s sunucusu açılırken kapandı:\n%s', _({'web': 'Web', 'oyun': 'Oyun'}[dead[0]]),
                                         '\n'.join(lines)))
                time.sleep(0.15)
            else:
                raise RuntimeError(_('Sunucular 20 saniyede dinlemeye başlamadı (günlükleri inceleyin).'))
            if started:
                self.log('sunucular başlatıldı: %s (%s)' % (', '.join(started), profil))
            return started

    def stop_servers(self):
        with self.lock:
            for ad in ('oyun', 'web'):
                s = self.sunucular.get(ad)
                if s:
                    s.stop()
            self.log('sunucular durduruldu')
            self.profil = self.slot = None

    # ------------------------------------------------------------ istemci
    def client_alive(self):
        return self.istemci is not None and self.istemci.poll() is None

    def start_client(self, folder, args):
        with self.lock:
            if self.client_alive():
                raise RuntimeError(_('İstemci zaten açık.'))
            exe = os.path.join(folder, 'DarkOrbit.exe')
            self.istemci = subprocess.Popen([exe] + args, cwd=folder)
            self.istemci_basla = time.time()
            self.istemci_son = None
            self.log('istemci başlatıldı: %s %s' % (exe, ' '.join(args)))
            threading.Thread(target=self._watch_client, args=(self.istemci,), daemon=True).start()

    def _watch_client(self, proc):
        code = proc.wait()
        dur = time.time() - (self.istemci_basla or time.time())
        early = dur < ERKEN_KAPANMA_SN
        self.istemci_son = {'sure_sn': int(dur), 'erken': early, 'kod': code, 'zaman': time.strftime('%H:%M:%S')}
        self.log('istemci kapandı (%d sn, kod %s)%s' % (dur, code, ' — erken kapandı, sunucular açık kalır' if early else ''))
        if self.on_client_exit:
            try:
                self.on_client_exit(early)
            except Exception as e:
                self.log('istemci kapanış işlemi hatası: %r' % e)

    def stop_client(self):
        if self.client_alive():
            self.istemci.terminate()

    # ------------------------------------------------------------ durum
    def status(self):
        srv = {ad: (s.status() if s else {'durum': 'kapali'}) for ad, s in ((a, self.sunucular.get(a)) for a in ('web', 'oyun'))}
        table = listeners()
        for ad, st in srv.items():
            st['portlar'] = {p: listening(p, table) for p in PORTS[ad]}
        cl = {'durum': 'acik' if self.client_alive() else 'kapali'}
        if self.client_alive():
            cl.update(pid=self.istemci.pid, sure_sn=int(time.time() - self.istemci_basla))
        cl['son'] = self.istemci_son
        return {'sunucular': srv, 'istemci': cl, 'profil': self.profil, 'kayit': self.slot,
                'kontrol_kanali': listening(8099, table)}
