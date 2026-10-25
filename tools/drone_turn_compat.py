#!/usr/bin/env python3
"""Reversible angle-wrap correction for the exact OpenOrbit 1.1.115 x86 client.

Normalizes rotation-only Retarget2D targets within the native Euler domain
[-360, 360]. Translation and out-of-domain values pass through untouched.
No binaries are distributed. Use only on a stopped local client.
"""
import argparse
import hashlib
import os
from pathlib import Path
import struct
import subprocess
import tempfile

ORIGINAL_SHA256 = '1ae406f311cd38927f435e9335704e3adc84b92b4048b19bc6ec948cdcc6bec5'
ENTRY_RVA = 0x352F80
CAVE_RVA = 0x27DB24
PROLOG = bytes.fromhex('55 8b ec 83 ec 0c')


def entry_jump():
    return b'\xe9' + struct.pack('<i', CAVE_RVA - ENTRY_RVA - 5) + b'\x90'


def trampoline():
    """Position-independent x86 hook; replay prolog, preserve flags and XMM0."""
    code = bytearray(PROLOG)
    labels, branches = {}, []

    def emit(value):
        code.extend(bytes.fromhex(value))

    def branch(op, label):
        emit(op)
        branches.append((len(code), label))
        code.append(0)

    emit('9c')                             # preserve flags from original SUB
    emit('80 7d 18 00')                    # isRotation?
    branch('74', 'done')
    emit('81 7d 14 00 00 00 80')           # preserve negative zero
    branch('74', 'done')
    emit('83 7d 14 00')
    branch('7d', 'positive')                # positive IEEE float bit patterns
    emit('81 7d 14 00 00 b4 c3')           # reject z < -360, negative NaN/Inf
    branch('77', 'done')
    emit('83 ec 10 f3 0f 7f 04 24')        # preserve full XMM0
    emit('f3 0f 10 45 14')                 # load target.z
    emit('68 00 00 b4 43')                 # 360.0 constant on stack, no VA fixup
    emit('f3 0f 58 04 24 83 c4 04')        # z += 360
    emit('f3 0f 11 45 14')
    emit('f3 0f 6f 04 24 83 c4 10')        # restore full XMM0 and stack
    labels['positive'] = len(code)
    emit('81 7d 14 00 00 b4 43')           # also clamp rounded 360 back to zero
    branch('75', 'done')
    emit('c7 45 14 00 00 00 00')
    labels['done'] = len(code)
    emit('9d')
    for offset, label in branches:
        distance = labels[label] - (offset + 1)
        if not -128 <= distance <= 127:
            raise ValueError('Hook exceeds short-branch bounds')
        code[offset] = distance & 255
    code.extend(b'\xe9' + struct.pack('<i', ENTRY_RVA + len(PROLOG) - (CAVE_RVA + len(code) + 5)))
    return bytes(code)


def _sha(data):
    return hashlib.sha256(data).hexdigest()


def patch_bytes(original):
    if _sha(original) != ORIGINAL_SHA256:
        raise ValueError('Unsupported or altered GameAssembly.dll; no changes made')
    pe = struct.unpack_from('<I', original, 0x3c)[0]
    if original[pe:pe+4] != b'PE\0\0' or struct.unpack_from('<H', original, pe+4)[0] != 0x14c:
        raise ValueError('Expected x86 PE image')
    count = struct.unpack_from('<H', original, pe+6)[0]
    optional_size = struct.unpack_from('<H', original, pe+20)[0]
    sections = []
    for i in range(count):
        header = pe + 24 + optional_size + i*40
        name = original[header:header+8].rstrip(b'\0')
        vsize, rva, raw_size, raw_offset = struct.unpack_from('<IIII', original, header+8)
        flags = struct.unpack_from('<I', original, header+36)[0]
        sections.append((name, header, vsize, rva, raw_size, raw_offset, flags))

    def offset(rva):
        for _, _, _, start, size, raw, _ in sections:
            if start <= rva < start+size:
                return raw + rva-start
        raise ValueError('RVA outside file-backed sections')

    text = next(s for s in sections if s[0] == b'.text')
    _, header, vsize, rva, raw_size, raw, flags = text
    hook = trampoline()
    if CAVE_RVA != rva+vsize or vsize+len(hook) > raw_size or flags & 0x60000000 != 0x60000000:
        raise ValueError('Expected executable section tail is unavailable')
    entry, cave = offset(ENTRY_RVA), offset(CAVE_RVA)
    if original[entry:entry+6] != PROLOG or any(original[cave:cave+len(hook)]):
        raise ValueError('Native prolog or unused section bytes disagree')
    result = bytearray(original)
    result[entry:entry+6] = entry_jump()
    result[cave:cave+len(hook)] = hook
    # Make the new code explicitly part of the executable section virtual size;
    # the file size, alignment, next section RVA and image size stay unchanged.
    struct.pack_into('<I', result, header+8, vsize+len(hook))
    return bytes(result)


def native_client_running():
    if os.name == 'nt':
        output = subprocess.check_output(['tasklist', '/FO', 'CSV', '/NH'], text=True)
        return any(line.split(',')[0].strip('"').casefold() == 'darkorbit.exe' for line in output.splitlines())
    output = subprocess.check_output(['ps', '-axo', 'comm='], text=True)
    return any(line.strip().replace('\\', '/').rsplit('/', 1)[-1].casefold() == 'darkorbit.exe' for line in output.splitlines())


def _write(path, data):
    path = Path(path)
    fd, temporary = tempfile.mkstemp(prefix=path.name+'.', dir=path.parent)
    try:
        with os.fdopen(fd, 'wb') as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.chmod(temporary, path.stat().st_mode & 0o777)
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def _guard():
    if native_client_running():
        raise RuntimeError('Close DarkOrbit.exe before applying or restoring the correction')


def apply(path):
    _guard()
    path = Path(path)
    current = path.read_bytes()
    backup = path.with_name(path.name+'.drone-turn.original')
    original = backup.read_bytes() if backup.exists() else current
    patched = patch_bytes(original)
    if current == patched:
        return 'already applied'
    if current != original:
        raise ValueError('Client changed since backup; refusing overwrite')
    if not backup.exists():
        # Exclusive create never overwrites an existing recovery copy. A partial
        # backup after interruption fails its hash guard on the next invocation.
        with backup.open('xb') as stream:
            stream.write(original)
            stream.flush()
            os.fsync(stream.fileno())
    _guard()
    if path.read_bytes() != current:
        raise ValueError('Client changed during operation; refusing overwrite')
    _write(path, patched)
    return 'applied'


def restore(path):
    _guard()
    path = Path(path)
    backup = path.with_name(path.name+'.drone-turn.original')
    original = backup.read_bytes()
    patched = patch_bytes(original)
    current = path.read_bytes()
    if current == original:
        return 'already restored'
    if current != patched:
        raise ValueError('Client differs from this correction; refusing overwrite')
    _guard()
    if path.read_bytes() != current:
        raise ValueError('Client changed during operation; refusing overwrite')
    _write(path, original)
    return 'restored (backup retained)'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('operation', choices=['apply', 'restore', 'inspect'])
    parser.add_argument('dll', type=Path)
    args = parser.parse_args()
    if args.operation == 'inspect':
        current = args.dll.read_bytes()
        backup = args.dll.with_name(args.dll.name+'.drone-turn.original')
        original = backup.read_bytes() if backup.exists() else current
        patched = patch_bytes(original)
        print('original' if current == original else 'patched' if current == patched else 'unrecognized')
    else:
        print((apply if args.operation == 'apply' else restore)(args.dll))


if __name__ == '__main__':
    main()
