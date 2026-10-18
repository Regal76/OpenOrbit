"""darkorbit-protocol.dll -> komut tablosu: kimlik, alanlar (tür/ofset) ve write() kodlaması (otomatik çözüm).

write() kalıbı (x86, BigEndian EndianBinaryWriter sanal çağrıları):
  vtable +0x100 -> bool, +0x118 -> byte[] (öncesinde short uzunluk = UTF-8 metin), +0x148 -> short, +0x158 -> int,
  +0x160 -> long, +0x138 -> float?, +0x168 -> double?  (gözlenen ofsetler kayıt altına alınır)
Alan dönüşümleri: (x >>> a | x << b) bit döndürme, short için ((x>>>a)&mask | x<<b).
"""
import sys, re, json, struct
import capstone
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))     # python -I ile de: yanındaki modüller
from symbols import Symbols
from il2types import describe, S as S2, m as M, type_name

S = S2
md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
SLOT = {0x100: 'bool', 0x118: 'bytes', 0x148: 'short', 0x158: 'int', 0x160: 'long', 0x138: 'float', 0x168: 'double', 0x120: 'byte'}


def insns(addr, limit=1500):
    off = S.pe.va2off(addr)
    out = []
    for ins in md.disasm(S.pe.b[off:off + limit * 8], addr):
        out.append(ins)
        if ins.mnemonic == 'ret' or len(out) >= limit:
            break
    return out


def module_id(cls):
    a = S.name2addr.get(cls + '$$getLibcomModuleId')
    if not a:
        return None
    ins = insns(a, 4)
    if ins and ins[0].mnemonic == 'mov' and ins[0].op_str.startswith('eax, '):
        return int(ins[0].op_str.split(', ')[1], 0)
    if ins and ins[0].mnemonic == 'xor' and ins[0].op_str == 'eax, eax':
        return 0
    return None


def analyze_write(cls, fields_by_off):
    """write() içindeki yazma çağrılarını sırayla çıkarır: [(tür, alan, dönüşüm)]."""
    a = S.name2addr.get(cls + '$$write')
    if not a:
        return None
    seq = []
    last_field = None
    shifts = []
    for ins in insns(a, 3000):
        op = ins.op_str
        m1 = re.search(r'\[(e[a-d]x|e[sd]i|ebx) \+ (0x[0-9a-f]+)\]', op)
        if ins.mnemonic in ('mov', 'movsx', 'movzx', 'movss', 'movsd') and m1:
            off = int(m1.group(2), 16)
            if off in fields_by_off and not op.startswith('dword ptr ['):
                last_field = fields_by_off[off]
                shifts = []
        if ins.mnemonic in ('shl', 'shr', 'sar', 'rol', 'ror') and ', ' in op:
            try:
                shifts.append((ins.mnemonic, int(op.split(', ')[1], 0)))
            except ValueError:
                pass
        if ins.mnemonic == 'push' and op.startswith('dword ptr [eax + 0x'):
            slot = int(op.split('+ ')[1].rstrip(']'), 16) - 4
            if slot in SLOT:
                seq.append([SLOT[slot], last_field, list(shifts)])
                shifts = []
        if ins.mnemonic == 'call' and op.startswith('0x'):
            tgt = S.addr2name.get(int(op, 16), '')
            if tgt.endswith('$$write') and 'darkorbit' in tgt:
                seq.append(['module', last_field, tgt.split('$$')[0].split('.')[-1]])
    return seq


def build():
    img = [i for i in M.images if i['name'] == 'darkorbit-protocol.dll'][0]
    out = {}
    for ti in range(img['typeStart'], img['typeStart'] + img['typeCount']):
        cls = S.type_name(ti)
        mid = module_id(cls)
        if mid is None:
            continue
        flds = describe(ti)
        by_off = {off: name for name, tn, off in flds if off is not None}
        out[cls] = {'id': mid, 'fields': [[n, t, o] for n, t, o in flds], 'write': analyze_write(cls, by_off)}
    return out


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    table = build()
    json.dump(table, open(sys.argv[1], 'w', encoding='utf8'), ensure_ascii=False, indent=0)
    print('commands', len(table))
    for q in sys.argv[2:]:
        for k, v in table.items():
            if k.endswith('.' + q):
                print('==', k, 'id', v['id'])
                for f in v['fields']:
                    print('   field', f)
                for w in v['write'] or []:
                    print('   write', w)
