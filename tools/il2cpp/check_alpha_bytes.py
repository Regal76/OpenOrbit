import ctypes, subprocess

out = subprocess.check_output('tasklist /FI "IMAGENAME eq DarkOrbit.exe" /FO CSV /NH', shell=True, text=True)
pid = int(out.split(',')[1].strip('"\n\r '))
PROCESS_ALL_ACCESS = 0x1F0FFF
hProcess = ctypes.windll.kernel32.OpenProcess(PROCESS_ALL_ACCESS, False, pid)

ga_base = 0x6d880000
delta = ga_base - 0x10000000
va = 0x10736592 + delta

buf = (ctypes.c_byte * 8)()
n = ctypes.c_size_t()
ctypes.windll.kernel32.ReadProcessMemory(hProcess, ctypes.c_void_p(va), buf, 8, ctypes.byref(n))
bytes_hex = ' '.join(f'{b & 0xFF:02x}' for b in buf)
print(f'Bytes at {hex(va)}: {bytes_hex}')
ctypes.windll.kernel32.CloseHandle(hProcess)
