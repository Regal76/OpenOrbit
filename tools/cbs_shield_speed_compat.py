#!/usr/bin/env python3
"""Reversible CBS-only half-speed shield artwork for the exact 1.1.115 client.

2D changes only the Animator instance created by DeflectorShieldEffect2D.
3D changes only the two ParticleSystems inside shield_deflector.prefab.
Game time, shield reserves/downtime and unrelated invulnerability are untouched.
Default operation reports fingerprints without writing. Close the native client
before --apply or --restore. UnityPy is needed only for the particle bundle.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import struct
import subprocess
import tempfile

RATE = 0.5
ORIGINAL_SHA256 = {
    'native': '5a4c77bf160928d8359b6cd4c6277166e179f76894c3fa7514bc91253c82a4eb',
    'particles': 'b28115f7dd3defd5fb02a41c67ea5cd03db5b65688019e9930a74e4f98cde50d',
}
INIT_CALL_RVA = 0x7640d9
BASE_INIT_RVA = 0x1024cd0
PARTICLE_IDS = {8739867819059555350, -5388967337541391338}
PREFAB = 'Assets/Res/Prefabs/ParticleEffects/Others/shield_deflector.prefab'


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def trampoline(rva):
    """Replay the unique CBS InitClass call, then set only its Animator speed.

    Preserve the original helper's return registers, EFLAGS and all XMM registers.
    Native/managed Unity calls use their shipped x86 cdecl signatures. All code
    and method-info references are position independent; no PE relocation edits.
    """
    code = bytearray()
    branches = []
    def emit(raw):
        code.extend(bytes.fromhex(raw))
    def jump_done():
        emit('0f 84')
        branches.append(len(code))
        code.extend(b'\0' * 4)
    def native_call(target):
        emit('8d 83')
        code.extend(struct.pack('<I', target))
        emit('ff d0')
    emit('55 8b ec ff 75 10 ff 75 0c ff 75 08 e8')
    code.extend(struct.pack('<i', BASE_INIT_RVA - (rva + len(code) + 4)))
    # Keep the forwarded argument stack until after restoring post-call flags.
    emit('9c 60 81 ec 80 00 00 00')
    for register in range(8):
        emit('f3 0f 7f')
        code.extend(bytes([0x84 | (register << 3), 0x24]))
        code.extend(struct.pack('<I', 16 * register))
    emit('83 7d 0c 00')
    jump_done()
    emit('e8 00 00 00 00')
    image_eip = rva + len(code)
    emit('5b 81 eb')
    code.extend(struct.pack('<I', image_eip))
    emit('8d 83')
    code.extend(struct.pack('<I', 0x340a03c))
    emit('50')
    native_call(0x1ef640)                 # Resolve GetComponentInChildren<Animator>.
    emit('83 c4 04 ff b3')
    code.extend(struct.pack('<I', 0x340a03c))
    emit('ff 75 0c')
    native_call(0x17ef440)                # (GameObject, MethodInfo*)
    emit('83 c4 08 85 c0')
    jump_done()
    emit('6a 00 68 00 00 00 3f 50')
    native_call(0x28e4630)                # Animator.set_speed(this, 0.5f, metadata)
    emit('83 c4 0c')
    done = len(code)
    for register in range(8):
        emit('f3 0f 6f')
        code.extend(bytes([0x84 | (register << 3), 0x24]))
        code.extend(struct.pack('<I', 16 * register))
    emit('81 c4 80 00 00 00 61 9d 8d 64 24 0c 5d c3')
    for at in branches:
        struct.pack_into('<i', code, at, done - (at + 4))
    return bytes(code)


def patch_native(original):
    pe = struct.unpack_from('<I', original, 0x3c)[0]
    if original[pe:pe + 4] != b'PE\0\0' or struct.unpack_from('<H', original, pe + 4)[0] != 0x14c:
        raise ValueError('Expected x86 PE image')
    optional, count = pe + 24, struct.unpack_from('<H', original, pe + 6)[0]
    if struct.unpack_from('<H', original, optional)[0] != 0x10b:
        raise ValueError('Expected PE32 optional header')
    table = optional + struct.unpack_from('<H', original, pe + 20)[0]
    sections = [struct.unpack_from('<IIII', original, table + 40 * i + 8) for i in range(count)]
    def offset(rva):
        for _, start, size, raw in sections:
            if start <= rva < start + size:
                return raw + rva - start
        raise ValueError('Call RVA outside file-backed sections')
    at = offset(INIT_CALL_RVA)
    expected = b'\xe8' + struct.pack('<i', BASE_INIT_RVA - INIT_CALL_RVA - 5)
    if original[at:at + 5] != expected:
        raise ValueError('CBS initializer call differs')
    header = table + 40 * count
    if header + 40 > min(s[3] for s in sections) or any(original[header:header + 40]):
        raise ValueError('No unused section header')
    if len(original) != max(s[3] + s[2] for s in sections):
        raise ValueError('Unexpected PE overlay')
    section_alignment, file_alignment = struct.unpack_from('<II', original, optional + 32)
    align = lambda value, unit: (value + unit - 1) // unit * unit
    rva = align(max(s[1] + max(s[0], s[2]) for s in sections), section_alignment)
    raw_offset = align(len(original), file_alignment)
    hook = trampoline(rva)
    raw_size = align(len(hook), file_alignment)
    result = bytearray(original)
    result.extend(b'\0' * (raw_offset - len(original)))
    result.extend(hook + b'\0' * (raw_size - len(hook)))
    result[header:header + 40] = struct.pack('<8sIIIIIIHHI', b'.cbsslow', len(hook), rva,
                                           raw_size, raw_offset, 0, 0, 0, 0, 0x60000020)
    struct.pack_into('<H', result, pe + 6, count + 1)
    old_code_size = struct.unpack_from('<I', original, optional + 4)[0]
    struct.pack_into('<I', result, optional + 4, old_code_size + raw_size)
    struct.pack_into('<I', result, optional + 56, align(rva + len(hook), section_alignment))
    result[at:at + 5] = b'\xe8' + struct.pack('<i', rva - INIT_CALL_RVA - 5)
    return bytes(result)


def particle_targets(env):
    """Follow only the unique CBS 3D prefab, never scan-and-change all particles."""
    # Read the bundle's own container directly. Environment.container can load
    # unrelated dependency bundles while iterating its CAB dictionary.
    matches = [info.asset for obj in list(env.objects) if obj.type.name == 'AssetBundle'
               for name, info in obj.read().m_Container if name == PREFAB]
    if len(matches) != 1:
        raise ValueError('Expected the unique CBS shield_deflector prefab')
    root = matches[0].read().object_reader
    objects = root.assets_file.objects
    result, visited = {}, set()
    def visit(gameobject):
        if gameobject.path_id in visited:
            raise ValueError('Unexpected cyclic prefab hierarchy')
        visited.add(gameobject.path_id)
        tree = gameobject.read_typetree()
        for item in tree['m_Component']:
            pointer = item['component']
            if pointer['m_FileID']:
                raise ValueError('Expected embedded CBS components')
            component = objects[pointer['m_PathID']]
            if component.type.name == 'ParticleSystem':
                result[component.path_id] = component
            elif component.type.name == 'Transform':
                for child in component.read_typetree()['m_Children']:
                    if child['m_FileID']:
                        raise ValueError('Expected embedded CBS transform')
                    child_transform = objects[child['m_PathID']].read_typetree()
                    visit(objects[child_transform['m_GameObject']['m_PathID']])
    visit(root)
    if set(result) != PARTICLE_IDS:
        raise ValueError('CBS particle hierarchy differs')
    return result


def patch_particles(original):
    import UnityPy
    env = UnityPy.load(original)
    for obj in particle_targets(env).values():
        tree = obj.read_typetree()
        if tree['simulationSpeed'] != 1.0 or tree['lengthInSec'] != 1.0 or not tree['looping']:
            raise ValueError('CBS particle timing differs')
        tree['simulationSpeed'] = RATE
        obj.save_typetree(tree)
    return env.file.save(packer='original')


def patch_bytes(original, kind):
    if kind not in ORIGINAL_SHA256 or digest(original) != ORIGINAL_SHA256[kind]:
        raise ValueError('Unsupported ' + str(kind) + ' fingerprint')
    return patch_native(original) if kind == 'native' else patch_particles(original)


def native_client_running():
    if os.name == 'nt':
        lines = subprocess.check_output(['tasklist', '/FO', 'CSV', '/NH'], text=True)
        return any(line.split(',')[0].strip('"').casefold() == 'darkorbit.exe' for line in lines.splitlines())
    lines = subprocess.check_output(['ps', '-axo', 'comm='], text=True)
    return any(line.strip().replace('\\', '/').rsplit('/', 1)[-1].casefold() == 'darkorbit.exe'
               for line in lines.splitlines())


def backup_path(path):
    return Path(str(path) + '.cbs-shield-speed.original')


def manifest_path(path):
    return Path(str(path) + '.cbs-shield-speed.json')


def atomic_write(path, raw):
    path, temporary = Path(path), None
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


def verified_manifest(path, kind):
    manifest = json.loads(manifest_path(path).read_text())
    if manifest.get('kind') != kind or manifest.get('rate') != RATE or manifest.get('original_sha256') != ORIGINAL_SHA256[kind]:
        raise ValueError('Unknown shield-speed manifest')
    if digest(backup_path(path).read_bytes()) != ORIGINAL_SHA256[kind]:
        raise ValueError('Shield-speed backup fingerprint differs')
    return manifest


def apply(path, kind):
    if native_client_running():
        raise RuntimeError('Close DarkOrbit before changing shield artwork')
    path = Path(path)
    original = path.read_bytes()
    if digest(original) != ORIGINAL_SHA256[kind]:
        manifest = verified_manifest(path, kind)
        if digest(original) != manifest['modified_sha256']:
            raise ValueError('Current shield-speed fingerprint differs')
        return manifest
    modified = patch_bytes(original, kind)
    backup = backup_path(path)
    if backup.exists() and digest(backup.read_bytes()) != ORIGINAL_SHA256[kind]:
        raise ValueError('Existing shield-speed backup fingerprint differs')
    if not backup.exists():
        with backup.open('xb') as stream:
            stream.write(original)
    manifest = {'kind': kind, 'rate': RATE, 'original_sha256': ORIGINAL_SHA256[kind],
                'modified_sha256': digest(modified), 'scope': 'CBS shield animation only; no gameplay time changes'}
    atomic_write(manifest_path(path), (json.dumps(manifest, indent=2) + '\n').encode())
    atomic_write(path, modified)
    return manifest


def restore(path, kind):
    if native_client_running():
        raise RuntimeError('Close DarkOrbit before restoring shield artwork')
    path = Path(path)
    current = path.read_bytes()
    if digest(current) == ORIGINAL_SHA256[kind]:
        return {'status': 'original', 'kind': kind, 'sha256': ORIGINAL_SHA256[kind]}
    manifest = verified_manifest(path, kind)
    if digest(current) != manifest['modified_sha256']:
        raise ValueError('Current shield-speed fingerprint differs; refusing other changes')
    atomic_write(path, backup_path(path).read_bytes())
    return {'status': 'restored', 'kind': kind, 'sha256': ORIGINAL_SHA256[kind]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('kind', choices=ORIGINAL_SHA256)
    parser.add_argument('path', type=Path)
    action = parser.add_mutually_exclusive_group()
    action.add_argument('--apply', action='store_true')
    action.add_argument('--restore', action='store_true')
    args = parser.parse_args()
    if args.apply:
        result = apply(args.path, args.kind)
    elif args.restore:
        result = restore(args.path, args.kind)
    else:
        result = {'kind': args.kind, 'rate': RATE, 'read_only': True,
                  'current_sha256': digest(args.path.read_bytes()), 'original_sha256': ORIGINAL_SHA256[args.kind]}
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
