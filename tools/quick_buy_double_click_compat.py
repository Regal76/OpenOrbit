#!/usr/bin/env python3
"""Require the native double-click callback only for buy_* menu items.

Default operation is read-only. Apply/restore require a closed native client.
The exact input includes the earlier native fixes; none are removed.
"""
import argparse
import hashlib
import json
from pathlib import Path
import struct

from cbs_hangar_button_compat import atomic_write, native_client_running

ORIGINAL_SHA256 = '44b3c32e22f637767900f762b4665fac990d0e8ff085a7d82448e5ad8e1c7a1f'
ENTRY_RVA = 0x10c04a0
PROLOGUE = bytes.fromhex('55 8b ec 83 ec 28')


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def trampoline(rva):
    """No allocation, external calls, absolute addresses, or mutable state.

    Native x86 arguments are this, byte isDoubleClick, MethodInfo*. Preserve
    every register/flag; inspect only this.ItemMenuVo.ID and the bool byte.
    Null/malformed context takes the original native path.
    """
    code = bytearray()
    refs = []
    def emit(raw):
        code.extend(bytes.fromhex(raw))
    def original(op):
        emit(op)
        refs.append(len(code))
        code.extend(b'\0' * 4)
    emit('9c 60')                         # entry ESP - 36
    emit('80 7c 24 2c 00')                # bool low byte only
    original('0f 85')
    emit('8b 44 24 28 85 c0')             # this
    original('0f 84')
    emit('8b 80 80 00 00 00 85 c0')       # UISlotAndItemBarElement.ItemMenuVo
    original('0f 84')
    emit('8b 40 30 85 c0')                # ItemMenuVo.ID
    original('0f 84')
    emit('83 78 08 04')                   # managed string >= 4 UTF-16 chars
    original('0f 82')
    emit('81 78 0c 62 00 75 00')          # exact lowercase b,u
    original('0f 85')
    emit('81 78 10 79 00 5f 00')          # exact y,_
    original('0f 85')
    emit('61 9d c3')                      # ignore only buy_* single click
    fallback = len(code)
    emit('61 9d')
    code.extend(PROLOGUE)
    emit('e9')
    code.extend(struct.pack('<i', ENTRY_RVA + len(PROLOGUE) - (rva + len(code) + 4)))
    for at in refs:
        struct.pack_into('<i', code, at, fallback - at - 4)
    return bytes(code)


def patch_bytes(original):
    if digest(original) != ORIGINAL_SHA256:
        raise ValueError('Unsupported native DLL fingerprint')
    pe = struct.unpack_from('<I', original, 0x3c)[0]
    optional = pe + 24
    if (original[pe:pe+4] != b'PE\0\0' or
            struct.unpack_from('<H', original, pe+4)[0] != 0x14c or
            struct.unpack_from('<H', original, optional)[0] != 0x10b):
        raise ValueError('Expected x86 PE32 image')
    count = struct.unpack_from('<H', original, pe+6)[0]
    table = optional + struct.unpack_from('<H', original, pe+20)[0]
    sections = [struct.unpack_from('<IIII', original, table+40*i+8) for i in range(count)]
    def offset(rva):
        for _, start, size, raw in sections:
            if start <= rva < start+size:
                return raw+rva-start
        raise ValueError('Native hook outside section')
    site = offset(ENTRY_RVA)
    if original[site:site+len(PROLOGUE)] != PROLOGUE:
        raise ValueError('Native UserItem hook differs')
    header = table+40*(count-1)
    vsize, start, size, raw = sections[-1]
    if (original[header:header+8] != b'.cbsloop' or
            struct.unpack_from('<I', original, header+36)[0] != 0x60000020 or
            raw+size != len(original) or vsize > size):
        raise ValueError('Expected final executable compatibility section without overlay')
    sa, fa = struct.unpack_from('<II', original, optional+32)
    align = lambda value, unit: (value+unit-1)//unit*unit
    destination = start+size
    guard = trampoline(destination)
    new_size = align(size+len(guard), fa)
    result = bytearray(original)
    result.extend(guard+b'\0'*(new_size-size-len(guard)))
    struct.pack_into('<I', result, header+8, size+len(guard))
    struct.pack_into('<I', result, header+16, new_size)
    struct.pack_into('<I', result, optional+4,
                     struct.unpack_from('<I', original, optional+4)[0]+new_size-size)
    struct.pack_into('<I', result, optional+56, align(start+size+len(guard), sa))
    result[site:site+6] = b'\xe9'+struct.pack('<i', destination-ENTRY_RVA-5)+b'\x90'
    return bytes(result)


def backup_path(path):
    return Path(str(path)+'.quick-buy-double.original')


def manifest_path(path):
    return Path(str(path)+'.quick-buy-double.json')


def verified_manifest(path):
    manifest = json.loads(manifest_path(path).read_text())
    backup = backup_path(path).read_bytes()
    if (manifest.get('original_sha256') != ORIGINAL_SHA256 or
            digest(backup) != ORIGINAL_SHA256 or
            manifest.get('modified_sha256') != digest(patch_bytes(backup))):
        raise ValueError('Unknown quick-buy manifest or backup fingerprint')
    return manifest


def apply(path):
    path = Path(path)
    if native_client_running():
        raise RuntimeError('Close DarkOrbit before changing its native DLL')
    current = path.read_bytes()
    if digest(current) != ORIGINAL_SHA256:
        manifest = verified_manifest(path)
        if digest(current) != manifest['modified_sha256']:
            raise ValueError('Current native fingerprint differs')
        return manifest
    modified = patch_bytes(current)
    backup = backup_path(path)
    if backup.exists() and digest(backup.read_bytes()) != ORIGINAL_SHA256:
        raise ValueError('Existing backup fingerprint differs')
    if not backup.exists():
        with backup.open('xb') as stream:
            stream.write(current)
    manifest = dict(original_sha256=ORIGINAL_SHA256, modified_sha256=digest(modified),
                    scope='buy_* single callbacks only', entry_rva=ENTRY_RVA)
    atomic_write(manifest_path(path), (json.dumps(manifest, indent=2)+'\n').encode())
    if native_client_running():
        raise RuntimeError('Close DarkOrbit before changing its native DLL')
    if path.read_bytes() != current:
        raise ValueError('Native DLL changed during operation')
    atomic_write(path, modified)
    return manifest


def restore(path):
    path = Path(path)
    if native_client_running():
        raise RuntimeError('Close DarkOrbit before restoring its native DLL')
    current = path.read_bytes()
    if digest(current) == ORIGINAL_SHA256:
        return dict(status='original', sha256=ORIGINAL_SHA256)
    manifest = verified_manifest(path)
    if digest(current) != manifest['modified_sha256']:
        raise ValueError('Current native fingerprint differs')
    if native_client_running():
        raise RuntimeError('Close DarkOrbit before restoring its native DLL')
    if path.read_bytes() != current:
        raise ValueError('Native DLL changed during operation')
    atomic_write(path, backup_path(path).read_bytes())
    return dict(status='restored', sha256=ORIGINAL_SHA256)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('dll', type=Path)
    group = parser.add_mutually_exclusive_group()
    group.add_argument('--apply', action='store_true')
    group.add_argument('--restore', action='store_true')
    parser.add_argument('--output', type=Path, help='Prepare a separate corrected file')
    args = parser.parse_args()
    if args.output:
        if args.apply or args.restore or args.output.resolve() == args.dll.resolve():
            parser.error('--output requires a separate destination and no apply/restore')
        raw = patch_bytes(args.dll.read_bytes())
        with args.output.open('xb') as stream:
            stream.write(raw)
        result = dict(output=str(args.output), sha256=digest(raw))
    else:
        result = (apply(args.dll) if args.apply else restore(args.dll) if args.restore else
                  dict(current_sha256=digest(args.dll.read_bytes()),
                       expected_original_sha256=ORIGINAL_SHA256, read_only=True))
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
