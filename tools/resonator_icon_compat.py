#!/usr/bin/env python3
"""Reversible local artwork aliases for the 1.1.115 missing resonator icons.

These are reused native weapon/component illustrations, not recovered official
resonator artwork. Default operation is read-only. Requires UnityPy to apply.
"""
import argparse
import copy
import hashlib
import json
import os
from pathlib import Path
import subprocess
import tempfile

ORIGINAL_SHA256 = 'c7e86b2279376365b9aea263738a79cf0d313545d950475737ccf4b6cbec609b'
TIERS = ('c', 'uc', 'r', 'ep', 'ma', 'leg', 'ul')
SIZES = ('30x30', '100x100')
# The native cannon sets retain tier-specific colors and different silhouettes
# for Strike and Aegis. Loot identity, names, descriptions and effects are intact.
BASE_ALIASES = {tier + '-' + kind + '-resonator': tier + '-' + art
                for kind, art in (('strike', 'nidhogg'), ('aegis', 'helios'))
                for tier in TIERS}
BASE_ALIASES.update(dict(zip((
    'attack-expansion', 'attack-collapse', 'attack-evernight',
    'attack-aftershock', 'attack-stagnation', 'attack-adhesion',
    'defensive-grav-tolerance', 'defensive-entry-buffer',
    'defensive-zone-adaptation', 'defensive-slowing-resistance',
    'defensive-detachment',
), (
    'micro-transistors', 'nano-condenser', 'hybrid-processor',
    'plasmatic-stabilizer', 'high-frequency-cable', 'plasmatic-equalization-plate',
    'hydra-alloy', 'neptune-alloy', 'triskelion-alloy', 'ouroboros-alloy', 'beacon-crystal',
))))
ALIASES = {alias + '_' + size: source + '_' + size
           for alias, source in BASE_ALIASES.items() for size in SIZES}


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def native_client_running():
    if os.name == 'nt':
        lines = subprocess.check_output(['tasklist', '/FO', 'CSV', '/NH'], text=True)
        return any(line.split(',')[0].strip('"').casefold() == 'darkorbit.exe' for line in lines.splitlines())
    lines = subprocess.check_output(['ps', '-axo', 'comm='], text=True)
    return any(line.strip().replace('\\', '/').rsplit('/', 1)[-1].casefold() == 'darkorbit.exe'
               for line in lines.splitlines())


def item_atlas(env):
    matches = [o for o in env.objects if o.type.name == 'SpriteAtlas' and o.read().m_Name == 'Items']
    if len(matches) != 1:
        raise ValueError('Expected exactly one Items atlas')
    return matches[0], matches[0].read_typetree()


def patch_bytes(raw):
    if digest(raw) != ORIGINAL_SHA256:
        raise ValueError('Unsupported original bundle fingerprint')
    import UnityPy
    env = UnityPy.load(raw)
    atlas, tree = item_atlas(env)
    names, pointers = tree['m_PackedSpriteNamesToIndex'], tree['m_PackedSprites']
    if len(names) != len(pointers):
        raise ValueError('Atlas sprite/name count differs')
    for alias, source in ALIASES.items():
        if alias in names or names.count(source) != 1:
            raise ValueError('Ambiguous or existing alias/source: ' + alias)
    objects = atlas.assets_file.objects
    next_id = max(objects) + 1
    for alias, source in ALIASES.items():
        pointer = pointers[names.index(source)]
        if pointer['m_FileID'] != 0:
            raise ValueError('Expected embedded source sprite')
        original = objects[pointer['m_PathID']]
        if original.type.name != 'Sprite':
            raise ValueError('Alias source is not a Sprite')
        clone = copy.copy(original)
        clone.path_id = next_id
        clone.data = original.get_raw_data()
        data = original.read_typetree()
        data['m_Name'] = alias
        # Share native render keys/texture regions. Each alias is its own named
        # Sprite so both SpriteAtlas.GetSprite and Sprite.name agree.
        clone.save_typetree(data)
        objects[next_id] = clone
        names.append(alias)
        pointers.append({'m_FileID': 0, 'm_PathID': next_id})
        next_id += 1
    atlas.save_typetree(tree)
    return env.file.save()


def backup_path(bundle):
    return Path(str(bundle) + '.resonator-icons.original')


def manifest_path(bundle):
    return Path(str(bundle) + '.resonator-icons.json')


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


def verified_manifest(bundle):
    manifest = json.loads(manifest_path(bundle).read_text())
    if manifest.get('original_sha256') != ORIGINAL_SHA256 or manifest.get('aliases') != ALIASES:
        raise ValueError('Unknown compatibility manifest')
    if digest(backup_path(bundle).read_bytes()) != ORIGINAL_SHA256:
        raise ValueError('Backup fingerprint differs')
    return manifest


def apply(bundle):
    bundle = Path(bundle)
    if native_client_running():
        raise RuntimeError('Close DarkOrbit before changing its bundle')
    raw = bundle.read_bytes()
    if digest(raw) != ORIGINAL_SHA256:
        manifest = verified_manifest(bundle)
        if digest(raw) != manifest['modified_sha256']:
            raise ValueError('Current bundle fingerprint differs')
        return manifest
    patched = patch_bytes(raw)
    backup, sidecar = backup_path(bundle), manifest_path(bundle)
    if backup.exists() and digest(backup.read_bytes()) != ORIGINAL_SHA256:
        raise ValueError('Existing backup fingerprint differs')
    manifest = {'original_sha256': ORIGINAL_SHA256, 'modified_sha256': digest(patched),
                'aliases': ALIASES, 'artwork': 'Reused native cannon/component art; local compatibility only'}
    if not backup.exists():
        with backup.open('xb') as stream:
            stream.write(raw)
    atomic_write(sidecar, (json.dumps(manifest, indent=2) + '\n').encode())
    atomic_write(bundle, patched)
    return manifest


def restore(bundle):
    bundle = Path(bundle)
    if native_client_running():
        raise RuntimeError('Close DarkOrbit before restoring its bundle')
    raw = bundle.read_bytes()
    if digest(raw) == ORIGINAL_SHA256:
        return {'status': 'original', 'sha256': ORIGINAL_SHA256}
    manifest = verified_manifest(bundle)
    if digest(raw) != manifest['modified_sha256']:
        raise ValueError('Current bundle fingerprint differs; refusing to overwrite other changes')
    atomic_write(bundle, backup_path(bundle).read_bytes())
    return {'status': 'restored', 'sha256': ORIGINAL_SHA256}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('bundle', type=Path)
    action = parser.add_mutually_exclusive_group()
    action.add_argument('--apply', action='store_true')
    action.add_argument('--restore', action='store_true')
    args = parser.parse_args()
    if args.apply:
        result = apply(args.bundle)
    elif args.restore:
        result = restore(args.bundle)
    else:
        result = {'current_sha256': digest(args.bundle.read_bytes()), 'expected_original_sha256': ORIGINAL_SHA256,
                  'aliases': ALIASES, 'read_only': True, 'artwork': 'Reused native cannon/component art; local compatibility only'}
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
