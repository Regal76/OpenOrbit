#!/usr/bin/env python3
"""Allow exact local resonator artwork names through 1.1.115's unknown-item guard.

Only icon methods and resonator tooltip formatting change. No item definitions, stats, categories,
names, descriptions or unknown-item flags change. Requires the separate atlas
compatibility aliases. Default operation is read-only; close the client to apply.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import struct
import subprocess
import tempfile

# Exact existing drone-angle-compatible client, preserving that patch in full.
ORIGINAL_SHA256 = '9140fffebe780ef77bc32983fdc108b63a5abd4e7be5c5d633e677fbd360872c'
TIERS = ('c', 'uc', 'r', 'ep', 'ma', 'leg', 'ul')
LOOT_IDS = tuple('equipment_xenoresonator_' + tier + '-' + kind + '-resonator'
                 for kind in ('strike', 'aegis') for tier in TIERS) + tuple(
    'resource_' + name for name in (
        'attack-expansion', 'attack-collapse', 'attack-evernight',
        'attack-aftershock', 'attack-stagnation', 'attack-adhesion',
        'defensive-grav-tolerance', 'defensive-entry-buffer',
        'defensive-zone-adaptation', 'defensive-slowing-resistance', 'defensive-detachment'))
GET_LOOT_RVA = 0xef27b0
METHODS = {
    '30x30': dict(entry=0xef1790, check=0xef17bd, normal=0xef17c3, unknown=0xef17d9,
                  initialized=0x34fd4aa, suffix_global=0x33c9bf0, unknown_global=0x3419ff4),
    '100x100': dict(entry=0xef1740, check=0xef176d, normal=0xef1773, unknown=0xef1789,
                    initialized=0x34fd4ab, suffix_global=0x33c9934, unknown_global=0x3419f68),
}
CHECK_BYTES = bytes.fromhex('80 78 50 00 75 16')
FORMAT_VERSION = 2
PREVIOUS_SHA256 = '5c6586229c893704011b5ba9fc75e42cf964aba639a8aebc554a6fcd8366c97c'
TOOLTIP_CALL_RVA = 0x57dbcb
CONCAT4_RVA = 0x208b800
MODIFIER_KEYS = tuple('items_equipment_shipupgrade_modifiertype_' + name for name in (
    'expansion', 'collapse', 'evernight', 'aftershock', 'stagnation',
    'grav_tolerance', 'zone_adaptation', 'slowing_resistance', 'detachment',
    'adhesion', 'entry_buffer'))  # Last two values are seconds, the other nine percentages.



def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def trampoline(rva, spec):
    """Position-independent x86 exact UTF-16 allowlist; preserve all registers.

    EAX is the native ItemVo. Only an unknown item's full LootID at +8 is
    inspected. No managed allocation or application calls occur in this guard.
    """
    code = bytearray()
    labels, references = {}, []
    def emit(raw):
        code.extend(bytes.fromhex(raw))
    def jump(op, label):
        emit(op)
        references.append((len(code), label))
        code.extend(b'\0' * 4)
    emit('9c 60')                         # pushfd / pushad
    emit('80 78 50 00')                   # original isUnknown comparison
    jump('0f 84', 'allowed')
    emit('8b 70 08 85 f6')                # ItemVo.LootID; null stays unknown
    jump('0f 84', 'unknown')
    emit('e8 00 00 00 00')                # local EIP, no image-base relocations
    eip = len(code)
    emit('5b 81 c3')                     # pop ebx; add ebx, table-eip
    table_reference = len(code)
    code.extend(b'\0' * 4)
    emit('ba')
    code.extend(struct.pack('<I', len(LOOT_IDS)))
    labels['next'] = len(code)
    emit('8b 0b 83 c3 04 3b 4e 08')       # table length vs managed string length
    jump('0f 85', 'skip')
    emit('56 8d 76 0c 89 df fc f3 66 a7 5e') # save string, exact UTF16 compare
    jump('0f 84', 'allowed')
    labels['skip'] = len(code)
    emit('8b 4b fc 8d 1c 4b 4a')          # skip chars, decrement table count
    jump('0f 85', 'next')
    labels['unknown'] = len(code)
    emit('61 9d')                         # restore registers / flags
    jump('e9', spec['unknown'])
    labels['allowed'] = len(code)
    emit('61 9d')
    jump('e9', spec['normal'])
    labels['table'] = len(code)
    for loot in LOOT_IDS:
        raw = loot.encode('utf-16le')
        code.extend(struct.pack('<I', len(raw) // 2) + raw)
    struct.pack_into('<i', code, table_reference, labels['table'] - eip)
    for at, target in references:
        destination = rva + labels[target] if isinstance(target, str) else target
        struct.pack_into('<i', code, at, destination - (rva + at + 4))
    return bytes(code)



def modifier_trampoline(rva):
    """Scope one native Concat4 call to 11 complete localization keys.

    ReturnModifiers has already prepared +value, a generic percent separator and
    a localized description. Replace the token with the correct value/unit,
    retaining the localized prose and existing modifier accumulator. Unrelated
    attributes tail-call the original native Concat4 with unchanged arguments.
    Managed allocation/string operations use the shipped IL2CPP helper ABI.
    """
    code = bytearray()
    labels, references = {}, []
    def emit(raw):
        code.extend(bytes.fromhex(raw))
    def jump(op, target):
        emit(op)
        references.append((len(code), target))
        code.extend(b'\0' * 4)
    def native_call(target):
        emit('8d 83')  # lea eax,[ebx+target RVA]; call eax (ASLR-safe)
        code.extend(struct.pack('<I', target))
        emit('ff d0')
    def metadata(global_rva):
        emit('8d 83')
        code.extend(struct.pack('<I', global_rva))
        emit('50')
        native_call(0x1ef640)
        emit('83 c4 04')
    emit('9c 60 85 f6')                 # preserve flags/GPRs; ESI=localization key
    jump('0f 84', 'fallback')
    emit('e8 00 00 00 00')
    table_eip = len(code)
    emit('5b 81 c3')
    table_ref = len(code)
    code.extend(b'\0' * 4)
    emit('ba')
    code.extend(struct.pack('<I', len(MODIFIER_KEYS)))
    labels['next'] = len(code)
    emit('8b 0b 83 c3 04 3b 4e 08')
    jump('0f 85', 'skip')
    emit('56 8d 76 0c 89 df fc f3 66 a7 5e')
    jump('0f 84', 'selected')
    labels['skip'] = len(code)
    emit('8b 4b fc 8d 1c 4b 4a')
    jump('0f 85', 'next')
    labels['fallback'] = len(code)
    emit('61 9d')
    jump('e9', CONCAT4_RVA)
    labels['selected'] = len(code)
    # EDX is remaining table entries: final two are time-valued attributes.
    emit('83 fa 02 0f 97 c0 0f b6 c0 89 44 24 1c')
    emit('61 9d 55 8b ec 53 56 57 83 ec 04 89 45 f0')
    emit('e8 00 00 00 00')
    image_eip = rva + len(code)
    emit('5b 81 eb')
    code.extend(struct.pack('<I', image_eip))  # EBX=image base
    emit('8b 75 0c')                      # prepared numeric fragment
    emit('66 83 7e 0c 2b')               # remove only a leading '+'
    jump('0f 85', 'number_ready')
    emit('6a 00 6a 01 56')
    native_call(0x2092560)                # String.Substring(startIndex=1)
    emit('83 c4 0c 89 c6')
    labels['number_ready'] = len(code)
    emit('83 7d f0 00')
    jump('0f 84', 'unit_ready')
    metadata(0x33e082c)                   # shipped '%' literal
    emit('6a 00 ff b3')
    code.extend(struct.pack('<I', 0x33e082c))
    emit('56')
    native_call(0x208be80)                # String.Concat(value, "%")
    emit('83 c4 0c 89 c6')
    labels['unit_ready'] = len(code)
    metadata(0x33e6550)                   # shipped '%VALUE%' literal
    emit('6a 00 56 ff b3')
    code.extend(struct.pack('<I', 0x33e6550))
    emit('ff 75 14')
    native_call(0x2091090)                # String.Replace(template,token,value)
    emit('83 c4 10 6a 00 50 ff 75 08')
    native_call(0x208be80)                # String.Concat(accumulator,description)
    emit('83 c4 0c 83 c4 04 5f 5e 5b 8b e5 5d c3')
    labels['table'] = len(code)
    for key in MODIFIER_KEYS:
        raw = key.encode('utf-16le')
        code.extend(struct.pack('<I', len(raw) // 2) + raw)
    struct.pack_into('<i', code, table_ref, labels['table'] - table_eip)
    for at, target in references:
        destination = rva + labels[target] if isinstance(target, str) else target
        struct.pack_into('<i', code, at, destination - (rva + at + 4))
    return bytes(code)


def patch_bytes(original):
    if digest(original) != ORIGINAL_SHA256:
        raise ValueError('Unsupported native DLL fingerprint')
    pe = struct.unpack_from('<I', original, 0x3c)[0]
    if original[pe:pe + 4] != b'PE\0\0' or struct.unpack_from('<H', original, pe + 4)[0] != 0x14c:
        raise ValueError('Expected x86 PE image')
    count = struct.unpack_from('<H', original, pe + 6)[0]
    optional = pe + 24
    if struct.unpack_from('<H', original, optional)[0] != 0x10b:
        raise ValueError('Expected PE32 optional header')
    optional_size = struct.unpack_from('<H', original, pe + 20)[0]
    table = optional + optional_size
    sections = []
    for i in range(count):
        header = table + 40 * i
        vsize, rva, rsize, offset = struct.unpack_from('<IIII', original, header + 8)
        sections.append((vsize, rva, rsize, offset))
    def offset(rva):
        for _, start, size, raw in sections:
            if start <= rva < start + size:
                return raw + rva - start
        raise ValueError('RVA outside original section')
    section_alignment, file_alignment = struct.unpack_from('<II', original, optional + 32)
    align = lambda value, unit: (value + unit - 1) // unit * unit
    header = table + count * 40
    if header + 40 > min(s[3] for s in sections) or any(original[header:header + 40]):
        raise ValueError('No verified unused section header')
    end = max(s[3] + s[2] for s in sections)
    if len(original) != end:
        raise ValueError('Unexpected overlay; refusing to move it')
    new_rva = align(max(s[1] + max(s[0], s[2]) for s in sections), section_alignment)
    new_offset = align(len(original), file_alignment)
    payload = bytearray()
    destinations = {}
    for size, spec in METHODS.items():
        at = offset(spec['check'])
        if original[at:at + 6] != CHECK_BYTES:
            raise ValueError('Native icon method check differs')
        destinations[size] = new_rva + len(payload)
        payload.extend(trampoline(destinations[size], spec))
    tooltip_at = offset(TOOLTIP_CALL_RVA)
    expected_call = b'\xe8' + struct.pack('<i', CONCAT4_RVA - TOOLTIP_CALL_RVA - 5)
    if original[tooltip_at:tooltip_at + 5] != expected_call:
        raise ValueError('Native modifier concat call differs')
    tooltip_rva = new_rva + len(payload)
    payload.extend(modifier_trampoline(tooltip_rva))
    raw_size = align(len(payload), file_alignment)
    result = bytearray(original)
    result.extend(b'\0' * (new_offset - len(result)))
    result.extend(payload)
    result.extend(b'\0' * (raw_size - len(payload)))
    result[header:header + 40] = struct.pack('<8sIIIIIIHHI', b'.rezicon', len(payload), new_rva,
                                           raw_size, new_offset, 0, 0, 0, 0, 0x60000020)
    struct.pack_into('<H', result, pe + 6, count + 1)
    old_code = struct.unpack_from('<I', original, optional + 4)[0]
    struct.pack_into('<I', result, optional + 4, old_code + raw_size)
    struct.pack_into('<I', result, optional + 56, align(new_rva + len(payload), section_alignment))
    for size, spec in METHODS.items():
        at = offset(spec['check'])
        result[at:at + 6] = b'\xe9' + struct.pack('<i', destinations[size] - (spec['check'] + 5)) + b'\x90'
    result[tooltip_at:tooltip_at + 5] = b'\xe8' + struct.pack('<i', tooltip_rva - TOOLTIP_CALL_RVA - 5)
    return bytes(result)


def native_client_running():
    if os.name == 'nt':
        lines = subprocess.check_output(['tasklist', '/FO', 'CSV', '/NH'], text=True)
        return any(line.split(',')[0].strip('"').casefold() == 'darkorbit.exe' for line in lines.splitlines())
    lines = subprocess.check_output(['ps', '-axo', 'comm='], text=True)
    return any(line.strip().replace('\\', '/').rsplit('/', 1)[-1].casefold() == 'darkorbit.exe'
               for line in lines.splitlines())


def backup_path(path):
    return Path(str(path) + '.resonator-icons.original')


def manifest_path(path):
    return Path(str(path) + '.resonator-icons.json')


def atomic_write(path, raw):
    path = Path(path)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(dir=path.parent, prefix='.' + path.name + '.', delete=False) as stream:
            temporary = Path(stream.name)
            stream.write(raw)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        if temporary is not None and temporary.exists():
            temporary.unlink()


def verified_manifest(path):
    manifest = json.loads(manifest_path(path).read_text())
    if manifest.get('original_sha256') != ORIGINAL_SHA256 or manifest.get('loot_ids') != list(LOOT_IDS):
        raise ValueError('Unrecognized native compatibility manifest')
    version = manifest.get('format_version', 1)
    if version == 1:
        if manifest.get('modified_sha256') != PREVIOUS_SHA256:
            raise ValueError('Unknown legacy native fingerprint')
    elif version != FORMAT_VERSION:
        raise ValueError('Unknown native compatibility version')
    if digest(backup_path(path).read_bytes()) != ORIGINAL_SHA256:
        raise ValueError('Native backup fingerprint differs')
    return manifest


def apply(path):
    path = Path(path)
    if native_client_running():
        raise RuntimeError('Close DarkOrbit before changing its native DLL')
    original = path.read_bytes()
    if digest(original) != ORIGINAL_SHA256:
        manifest = verified_manifest(path)
        if manifest.get('format_version', 1) != FORMAT_VERSION:
            raise ValueError('Restore native compatibility v1 before applying v2')
        if digest(original) != manifest['modified_sha256']:
            raise ValueError('Native current fingerprint differs')
        return manifest
    patched = patch_bytes(original)
    backup = backup_path(path)
    if backup.exists() and digest(backup.read_bytes()) != ORIGINAL_SHA256:
        raise ValueError('Existing native backup fingerprint differs')
    if not backup.exists():
        with backup.open('xb') as stream:
            stream.write(original)
    manifest = {'format_version': FORMAT_VERSION, 'original_sha256': ORIGINAL_SHA256, 'modified_sha256': digest(patched),
                'loot_ids': list(LOOT_IDS), 'scope': 'Exact local resonator/source artwork names and 11 resonator modifier descriptions'}
    atomic_write(manifest_path(path), (json.dumps(manifest, indent=2) + '\n').encode())
    atomic_write(path, patched)
    return manifest


def restore(path):
    path = Path(path)
    if native_client_running():
        raise RuntimeError('Close DarkOrbit before restoring its native DLL')
    current = path.read_bytes()
    if digest(current) == ORIGINAL_SHA256:
        return {'status': 'original', 'sha256': ORIGINAL_SHA256}
    manifest = verified_manifest(path)
    if digest(current) != manifest['modified_sha256']:
        raise ValueError('Native current fingerprint differs; refusing unrelated changes')
    atomic_write(path, backup_path(path).read_bytes())
    return {'status': 'restored', 'sha256': ORIGINAL_SHA256}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('dll', type=Path)
    actions = parser.add_mutually_exclusive_group()
    actions.add_argument('--apply', action='store_true')
    actions.add_argument('--restore', action='store_true')
    args = parser.parse_args()
    if args.apply:
        result = apply(args.dll)
    elif args.restore:
        result = restore(args.dll)
    else:
        result = {'current_sha256': digest(args.dll.read_bytes()), 'expected_original_sha256': ORIGINAL_SHA256,
                  'loot_ids': LOOT_IDS, 'read_only': True}
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
