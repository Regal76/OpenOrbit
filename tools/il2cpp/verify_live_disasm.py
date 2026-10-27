import ctypes, subprocess, capstone

out = subprocess.check_output('tasklist /FI "IMAGENAME eq DarkOrbit.exe" /FO CSV /NH', shell=True, text=True)
pid = int(out.split(',')[1].strip('"\n\r '))
PROCESS_ALL_ACCESS = 0x1F0FFF
hProcess = ctypes.windll.kernel32.OpenProcess(PROCESS_ALL_ACCESS, False, pid)

ga_base = 0x6d880000
delta = ga_base - 0x10000000
va = 0x10736584 + delta

buf = (ctypes.c_byte * 35)()
n = ctypes.c_size_t()
ctypes.windll.kernel32.ReadProcessMemory(hProcess, ctypes.c_void_p(va), buf, 35, ctypes.byref(n))

cs = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
for ins in cs.disasm(bytes(buf), va):
    print(f'0x{ins.address:08x}: {ins.mnemonic:8s} {ins.op_str:30s}')

ctypes.windll.kernel32.CloseHandle(hProcess)
