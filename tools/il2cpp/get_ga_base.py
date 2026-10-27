import ctypes, ctypes.wintypes, subprocess

out = subprocess.check_output('tasklist /FI "IMAGENAME eq DarkOrbit.exe" /FO CSV /NH', shell=True, text=True)
pid = int(out.split(',')[1].strip('"\n\r '))
print('PID:', pid)

TH32CS_SNAPMODULE = 0x00000008
TH32CS_SNAPMODULE32 = 0x00000010

class MODULEENTRY32(ctypes.Structure):
    _fields_ = [
        ('dwSize', ctypes.wintypes.DWORD),
        ('th32ModuleID', ctypes.wintypes.DWORD),
        ('th32ProcessID', ctypes.wintypes.DWORD),
        ('GlblcntUsage', ctypes.wintypes.DWORD),
        ('ProccntUsage', ctypes.wintypes.DWORD),
        ('modBaseAddr', ctypes.c_void_p),
        ('modBaseSize', ctypes.wintypes.DWORD),
        ('hModule', ctypes.wintypes.HMODULE),
        ('szModule', ctypes.c_char * 256),
        ('szExePath', ctypes.c_char * 260)
    ]

hSnap = ctypes.windll.kernel32.CreateToolhelp32Snapshot(TH32CS_SNAPMODULE | TH32CS_SNAPMODULE32, pid)
me = MODULEENTRY32()
me.dwSize = ctypes.sizeof(MODULEENTRY32)
found = False
if ctypes.windll.kernel32.Module32First(hSnap, ctypes.byref(me)):
    while True:
        name = me.szModule.decode('latin1')
        if 'gameassembly' in name.lower():
            print(f'{name}: {hex(me.modBaseAddr)}')
            found = True
            break
        if not ctypes.windll.kernel32.Module32Next(hSnap, ctypes.byref(me)):
            break
ctypes.windll.kernel32.CloseHandle(hSnap)
if not found:
    print('GameAssembly.dll not found via snapshot')
