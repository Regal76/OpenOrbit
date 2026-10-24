"""İstemcinin bellekteki yamaları: panel istemciyi açınca çalışan süreçte birkaç bayt değişir (dosyalara dokunulmaz, istemci
yeniden açılınca kalkar). Yalnız bilinen sürümün (1.1.115 GameAssembly.dll) baytları birebir tutarsa yazılır; tutmazsa hiçbir şey
değişmez (günlüğe yazılır). README'deki "istemci yamalanmaz" kuralının kullanıcı onaylı istisnası (2026-10-24).

Müzayede sayacı (CANLI_TEST H175; istemcinin kendi hatası, sunucu her listede doğru süreyi gönderiyor):
  UIAuctionSystem.StartCountdown her çağrıda yeni bir DOTween sayacı kurar, eskisini durdurmaz; sayaçların yazıcısı (b__1) o an
  seçili sekmenin alanına ve tek süre yazısına yazar. Sayaç yalnız pencerenin ilk listesinde ve sekme tıklamasında kurulur (sonraki
  listeler, yenile ve sayacın bitince istediği liste kurmaz). Sonuç: saatlik dönem bitince saatlik sekmede günlük sayaç görünür
  (22:57:22), hiç sekme gezilmediyse 00:00:00'da kalır; sekme tıklaması son listenin bayat süresini kullanır.
  P1 SetAuctionInfo: her listede seçili sekmenin sayacı listenin süresiyle yeniden kurulur (OnChickBTN; sekme değişmez)
  P2 StartCountdown: son kurulan sayaç kaydedilir
  P3, P4 sayacın yazıcısı ve bitişi: son sayaç değilse hiçbir şey yapmaz (eski sayaçlar yazmaz, bitince liste istemez)
  P5 OnChickBTN: sekme tıklamasında bayat süreyle kurmak yerine liste ister (RefreshUI); yanıtı P1 kurar

Rütbe penceresi (Hall of Fame "Your Rank"; kullanıcı bildirimi 2026-10-24: Sergeant olunca da "You currently have the lowest rank."):
  UIHallOfFameSystem.UpdateDailyRankForServer alt satırı yourRanking'e göre kurar ("hof_your_rank_below" rütbe 2-20, "hof_rank_lowest"
  1, "hof_rank_highest" 21) ama sonucu atıp metin dizisine hep GetTextById("hof_rank_lowest") koyar.
  R1 kurulan satır yığına itilir (çöp toplayıcı yığını tarar: dize yaşar), R2 dizideki GetTextById onu döndürür, R3 yığın geri alınır.
"""
import ctypes, os, struct, threading, time
from ctypes import wintypes as wt

TABAN = 0x10000000                   # GameAssembly.dll'in tercih ettiği yükleme adresi (adresler buna göre)
SET_INFO, ON_TAB, START, REFRESH = 0x104330e0, 0x1042fe60, 0x10434a10, 0x10431db0
GUN, HAFTA = 0x133d0c58, 0x133ca8bc  # 'day', 'week' dize sabitlerinin yuvaları (OnChickBTN TabType'a bunları yazar)
GET_VIEW, GET_TEXT = 0x11015400, 0x11075660     # UIHallOfFame.get_View, LocalizationManager.GetTextById
EN_ALT = 0x133d77b0                  # 'hof_rank_lowest' dize sabitinin yuvası


class Mem:
    """Başka bir sürecin belleği (32 bitlik istemci; panel 64 bit olabilir)."""
    def __init__(self, pid):
        self.k = k = ctypes.WinDLL('kernel32', use_last_error=True)
        k.OpenProcess.restype = wt.HANDLE
        k.VirtualAllocEx.restype = ctypes.c_void_p
        k.VirtualAllocEx.argtypes = [wt.HANDLE, ctypes.c_void_p, ctypes.c_size_t, wt.DWORD, wt.DWORD]
        k.ReadProcessMemory.argtypes = [wt.HANDLE, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_size_t, ctypes.POINTER(ctypes.c_size_t)]
        k.WriteProcessMemory.argtypes = [wt.HANDLE, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_size_t, ctypes.POINTER(ctypes.c_size_t)]
        k.VirtualProtectEx.argtypes = [wt.HANDLE, ctypes.c_void_p, ctypes.c_size_t, wt.DWORD, ctypes.POINTER(wt.DWORD)]
        k.FlushInstructionCache.argtypes = [wt.HANDLE, ctypes.c_void_p, ctypes.c_size_t]
        k.CloseHandle.argtypes = [wt.HANDLE]
        self.pid = pid
        self.h = k.OpenProcess(0x0400 | 0x0008 | 0x0010 | 0x0020, False, pid)   # QUERY_INFORMATION, VM_OPERATION, VM_READ, VM_WRITE
        if not self.h:
            raise OSError('süreç açılamadı (%d)' % ctypes.get_last_error())

    def close(self):
        self.k.CloseHandle(self.h)

    def read(self, addr, n):
        buf, got = ctypes.create_string_buffer(n), ctypes.c_size_t()
        if not self.k.ReadProcessMemory(self.h, addr, buf, n, ctypes.byref(got)) or got.value != n:
            return None
        return buf.raw

    def write(self, addr, data, code=True):
        old = wt.DWORD()
        if code and not self.k.VirtualProtectEx(self.h, addr, len(data), 0x40, ctypes.byref(old)):   # PAGE_EXECUTE_READWRITE
            raise OSError('koruma değişmedi (%d)' % ctypes.get_last_error())
        n = ctypes.c_size_t()
        ok = self.k.WriteProcessMemory(self.h, addr, data, len(data), ctypes.byref(n))
        if code:
            self.k.VirtualProtectEx(self.h, addr, len(data), old.value, ctypes.byref(old))
            self.k.FlushInstructionCache(self.h, addr, len(data))
        if not ok or n.value != len(data):
            raise OSError('yazılamadı (%d)' % ctypes.get_last_error())

    def alloc(self, n):
        a = self.k.VirtualAllocEx(self.h, None, n, 0x3000, 0x40)            # MEM_COMMIT | MEM_RESERVE, PAGE_EXECUTE_READWRITE
        if not a or a >= 1 << 32:
            raise OSError('bellek ayrılamadı')
        return a

    def module(self, name):
        """Modülün yükleme adresi ya da None (32 bitlik sürecin modülleri de: TH32CS_SNAPMODULE32)."""
        class ME(ctypes.Structure):
            _fields_ = [('dwSize', wt.DWORD), ('th32ModuleID', wt.DWORD), ('th32ProcessID', wt.DWORD), ('GlblcntUsage', wt.DWORD),
                        ('ProccntUsage', wt.DWORD), ('modBaseAddr', ctypes.c_void_p), ('modBaseSize', wt.DWORD), ('hModule', wt.HMODULE),
                        ('szModule', ctypes.c_wchar * 256), ('szExePath', ctypes.c_wchar * 260)]
        k = self.k
        k.CreateToolhelp32Snapshot.restype = wt.HANDLE
        snap = k.CreateToolhelp32Snapshot(0x08 | 0x10, self.pid)
        if not snap or snap == wt.HANDLE(-1).value:
            return None
        try:
            e = ME()
            e.dwSize = ctypes.sizeof(ME)
            ok = k.Module32FirstW(snap, ctypes.byref(e))
            while ok:
                if e.szModule.lower() == name.lower():
                    return e.modBaseAddr
                ok = k.Module32NextW(snap, ctypes.byref(e))
            return None
        finally:
            k.CloseHandle(snap)


class Kod:
    """Elle x86 (32 bit) kod: göreli atlamalar gerçek adreslerle."""
    def __init__(self, at):
        self.at, self.b = at, bytearray()

    @property
    def pc(self):
        return self.at + len(self.b)

    def __call__(self, *bs):
        self.b += bytes(bs)
        return self

    def d(self, v):
        self.b += struct.pack('<I', v & 0xffffffff)
        return self

    def rel(self, op, hedef):                       # E9 jmp, E8 call
        self.b.append(op)
        self.b += struct.pack('<i', hedef - (self.pc + 4))
        return self


def muzayede(m, base):
    """Müzayede sayacı yamaları (P1-P5) -> None; baytlar tutmazsa ValueError (hiçbir şey yazılmadan)."""
    va = lambda x: base + (x - TABAN)
    p1, p2, p3, p4, p5 = va(0x104332e9), va(0x10434a98), va(0x1042e2f0), va(0x1042e450), va(0x10430061)
    beklenen = {p1: bytes.fromhex('837e48007532'),                                # cmp [esi+48h],0 / jne (TabType null mı)
                p2: bytes.fromhex('8bd86a0053'),                                  # mov ebx,eax / push 0 / push ebx (kapanış nesnesi)
                p3: b'\x55\x8b\xec\x80\x3d' + struct.pack('<I', va(0x134fb50a)) + b'\x00',
                p4: b'\x55\x8b\xec\x80\x3d' + struct.pack('<I', va(0x134fb50b)) + b'\x00',
                p5: b'\xe8' + struct.pack('<i', START - 0x10430066)}            # call StartCountdown
    for a, b in beklenen.items():
        if m.read(a, len(b)) != b:
            raise ValueError('bilinmeyen istemci baytları (%#x)' % (a - base + TABAN))
    cave = m.alloc(0x1000)
    son, p1de = cave, cave + 4                     # son kurulan sayacın kapanış nesnesi; P1 OnChickBTN'u çağırıyor mu
    k = Kod(cave + 0x10)
    c1 = k.pc                                      # P1: TabType null -> eski yol; değilse sekmenin sırası (0 saat, 1 gün, 2 hafta)
    k(0x8B, 0x46, 0x48, 0x85, 0xC0, 0x75, 0x05).rel(0xE9, va(0x104332ef))
    k(0x31, 0xC9, 0x3B, 0x05).d(va(GUN))(0x75, 0x02, 0xB1, 0x01)
    k(0x3B, 0x05).d(va(HAFTA))(0x75, 0x02, 0xB1, 0x02)
    k(0xC7, 0x05).d(p1de).d(1)(0x6A, 0x00, 0x51, 0x6A, 0x01, 0x56).rel(0xE8, va(ON_TAB))(0x83, 0xC4, 0x10)
    k(0xC7, 0x05).d(p1de).d(0).rel(0xE9, va(0x10433321))
    c2 = k.pc                                      # P2: mov ebx,eax / mov [son],eax / push 0 / push ebx
    k(0x8B, 0xD8, 0xA3).d(son)(0x6A, 0x00, 0x53).rel(0xE9, va(0x10434a9d))
    yeni = []
    for orj, bayrak, geri in ((p3, 0x134fb50a, 0x1042e2fa), (p4, 0x134fb50b, 0x1042e45a)):
        yeni.append(k.pc)                          # P3/P4: son sayacın değilse dön; öyleyse özgün giriş
        k(0x8B, 0x44, 0x24, 0x04, 0x3B, 0x05).d(son)(0x74, 0x01, 0xC3)
        k(0x55, 0x8B, 0xEC, 0x80, 0x3D).d(va(bayrak))(0x00).rel(0xE9, va(geri))
    c5 = k.pc                                      # P5: P1'den geliyorsa StartCountdown, sekme tıklamasıysa RefreshUI (liste iste)
    k(0x83, 0x3D).d(p1de)(0x00, 0x74, 0x05).rel(0xE9, va(START)).rel(0xE9, va(REFRESH))
    m.write(cave, bytes(16), code=False)
    m.write(k.at, bytes(k.b), code=False)
    jmp = lambda at, to, n, op=0xE9: Kod(at).rel(op, to)(*[0x90] * (n - 5)).b
    for at, to, n, op in ((p2, c2, 5, 0xE9), (p3, yeni[0], 10, 0xE9), (p4, yeni[1], 10, 0xE9), (p5, c5, 5, 0xE8), (p1, c1, 6, 0xE9)):
        m.write(at, bytes(jmp(at, to, n, op)))


def rutbe_penceresi(m, base):
    """Rütbe penceresinin alt satırı yamaları (R1-R3) -> None; baytlar tutmazsa ValueError (hiçbir şey yazılmadan)."""
    va = lambda x: base + (x - TABAN)
    r1, r2, r3 = va(0x10509e44), va(0x10509fc3), va(0x10509fc8)
    beklenen = {r1: b'\x6a\x00\x57\xe8' + struct.pack('<i', GET_VIEW - 0x10509e4c),     # push 0 / push edi / call get_View
                va(0x10509fbd): b'\xff\x35' + struct.pack('<I', va(EN_ALT)),            # push 'hof_rank_lowest'
                r2: b'\xe8' + struct.pack('<i', GET_TEXT - 0x10509fc8),                # call GetTextById
                r3: bytes.fromhex('83c414')}                                            # add esp,14h
    for a, b in beklenen.items():
        if m.read(a, len(b)) != b:
            raise ValueError('bilinmeyen istemci baytları (%#x)' % (a - base + TABAN))
    k = Kod(m.alloc(0x1000))
    c1 = k.pc                                      # R1: push eax (kurulan satır) / push 0 / push edi / call get_View
    k(0x50, 0x6A, 0x00, 0x57).rel(0xE8, va(GET_VIEW)).rel(0xE9, va(0x10509e4c))
    c2 = k.pc                                      # R2: itilen satır [esp+18h] (dönüş, GetTextById'nin 3, dizi yazıcısının 2 argümanı)
    k(0x8B, 0x44, 0x24, 0x18, 0xC3)
    m.write(k.at, bytes(k.b), code=False)
    m.write(r1, bytes(Kod(r1).rel(0xE9, c1)(0x90, 0x90, 0x90).b))
    m.write(r2, bytes(Kod(r2).rel(0xE8, c2).b))
    m.write(r3, bytes.fromhex('83c418'))           # R3: add esp,18h (itilen satır da)


YAMALAR = (('müzayede sayacı', muzayede), ('rütbe penceresi', rutbe_penceresi))


def uygula(pid, log=print, sure=90):
    """İstemci sürecine yamaları uygular (GameAssembly.dll yüklenip yerleşene dek bekler) -> True / False."""
    if os.name != 'nt':
        return False
    try:
        m = Mem(pid)
    except OSError as e:
        log('istemci yaması: %s' % e)
        return False
    try:
        end, son_hata, yapilan = time.time() + sure, None, set()
        while time.time() < end:
            base = m.module('GameAssembly.dll')
            if base:
                for ad, yama in YAMALAR:
                    if ad in yapilan:
                        continue
                    try:
                        yama(m, base)
                        yapilan.add(ad)
                        log('istemci yaması: %s (süreç %d)' % (ad, pid))
                    except ValueError as e:        # yükleyici adresleri henüz yerleştirmemiş olabilir: biraz daha bekle
                        son_hata = e
                if len(yapilan) == len(YAMALAR):
                    return True
            time.sleep(0.25)
        eksik = ', '.join(ad for ad, yama in YAMALAR if ad not in yapilan)
        log('istemci yaması uygulanmadı (süreç %d, %s): %s' % (pid, eksik, son_hata or 'GameAssembly.dll yüklenmedi'))
        return False
    except OSError as e:
        log('istemci yaması uygulanmadı (süreç %d): %s' % (pid, e))
        return False
    finally:
        m.close()


def arka_planda(pid, log=print):
    threading.Thread(target=uygula, args=(pid, log), daemon=True).start()
