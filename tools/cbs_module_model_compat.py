#!/usr/bin/env python3
"""Match CBS on-map laser/rocket models to their installed inventory artwork.

Four native model dictionary key operands are exchanged. Server IDs, module
statistics, native avoidance ranges, and all upgrade tier selection stay intact.
Requires the verified HUD plus shield-anchor REV2 compatibility image.
Default operation is read-only. Close DarkOrbit before --apply or --restore.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import struct
import subprocess
import tempfile

ORIGINAL_SHA256='66daef688b8230bfeaa4f2a1d377de8ae73d4ff41569566965007795aca94328'
# Updated after deterministic preparation; four PUSH imm8 operands only.
MODIFIED_SHA256='44b3c32e22f637767900f762b4665fac990d0e8ff085a7d82448e5ad8e1c7a1f'
EXPECTED={0x2fa042:bytes.fromhex('6a 06'),0x2fa086:bytes.fromhex('6a 04'),
          0x2fa0a8:bytes.fromhex('6a 07'),0x2fa0ca:bytes.fromhex('6a 08')}
REPLACEMENT={0x2fa042:4,0x2fa086:6,0x2fa0a8:8,0x2fa0ca:7}
SCOPE='CBS map artwork matches installed inventory artwork; swap only LR/HR and LA/MA dictionary model keys; preserve IDs, stats and AI ranges'


def digest(raw):return hashlib.sha256(raw).hexdigest()


def patch_bytes(original):
    if digest(original)!=ORIGINAL_SHA256:raise ValueError('Unsupported native DLL fingerprint')
    pe=struct.unpack_from('<I',original,0x3c)[0];optional=pe+24
    if original[pe:pe+4]!=b'PE\0\0' or struct.unpack_from('<H',original,pe+4)[0]!=0x14c or struct.unpack_from('<H',original,optional)[0]!=0x10b:
        raise ValueError('Expected x86 PE32 image')
    count=struct.unpack_from('<H',original,pe+6)[0]
    table=optional+struct.unpack_from('<H',original,pe+20)[0]
    sections=[struct.unpack_from('<IIII',original,table+40*i+8) for i in range(count)]
    def offset(rva):
        for _,start,size,raw in sections:
            if start<=rva<start+size:return raw+rva-start
        raise ValueError('Hook outside original section')
    result=bytearray(original)
    for site,expected in EXPECTED.items():
        at=offset(site)
        if original[at:at+len(expected)]!=expected:raise ValueError('Native model key instruction differs')
        result[at+1]=REPLACEMENT[site]
    if digest(result)!=MODIFIED_SHA256:raise ValueError('Unexpected generated model fingerprint')
    return bytes(result)


def native_client_running():
    if os.name=='nt':
        output=subprocess.check_output(['tasklist','/FO','CSV','/NH'],text=True)
        return any(line.split(',')[0].strip('"').casefold()=='darkorbit.exe' for line in output.splitlines())
    output=subprocess.check_output(['ps','-axo','comm='],text=True)
    return any(line.strip().replace('\\','/').rsplit('/',1)[-1].casefold()=='darkorbit.exe' for line in output.splitlines())


def backup_path(path):return Path(str(path)+'.cbs-module-model.original')
def manifest_path(path):return Path(str(path)+'.cbs-module-model.json')


def atomic_write(path,raw):
    path=Path(path);temporary=None
    try:
        with tempfile.NamedTemporaryFile(dir=path.parent,prefix='.'+path.name+'.',delete=False) as stream:
            temporary=Path(stream.name);stream.write(raw);stream.flush();os.fsync(stream.fileno())
        os.replace(temporary,path)
    finally:
        if temporary is not None and temporary.exists():temporary.unlink()


def verified_manifest(path):
    manifest=json.loads(manifest_path(path).read_text())
    if (manifest.get('original_sha256')!=ORIGINAL_SHA256 or manifest.get('modified_sha256')!=MODIFIED_SHA256
            or manifest.get('scope')!=SCOPE):
        raise ValueError('Unknown native model manifest')
    if digest(backup_path(path).read_bytes())!=ORIGINAL_SHA256:raise ValueError('Native backup fingerprint differs')
    return manifest


def apply(path):
    path=Path(path)
    if native_client_running():raise RuntimeError('Close DarkOrbit before changing its native DLL')
    current=path.read_bytes()
    if digest(current)!=ORIGINAL_SHA256:
        manifest=verified_manifest(path)
        if digest(current)!=manifest['modified_sha256']:raise ValueError('Current native fingerprint differs')
        return manifest
    modified=patch_bytes(current);backup=backup_path(path)
    if backup.exists() and digest(backup.read_bytes())!=ORIGINAL_SHA256:raise ValueError('Existing backup fingerprint differs')
    if not backup.exists():
        with backup.open('xb') as stream:stream.write(current);stream.flush();os.fsync(stream.fileno())
    manifest=dict(original_sha256=ORIGINAL_SHA256,modified_sha256=digest(modified),scope=SCOPE)
    atomic_write(manifest_path(path),(json.dumps(manifest,indent=2)+'\n').encode())
    if native_client_running():raise RuntimeError('Close DarkOrbit before changing its native DLL')
    if path.read_bytes()!=current:raise ValueError('Native DLL changed during operation')
    atomic_write(path,modified);return manifest


def restore(path):
    path=Path(path)
    if native_client_running():raise RuntimeError('Close DarkOrbit before restoring its native DLL')
    current=path.read_bytes()
    if digest(current)==ORIGINAL_SHA256:return dict(status='original',sha256=ORIGINAL_SHA256)
    manifest=verified_manifest(path)
    if digest(current)!=manifest['modified_sha256']:raise ValueError('Current native fingerprint differs')
    if native_client_running():raise RuntimeError('Close DarkOrbit before restoring its native DLL')
    if path.read_bytes()!=current:raise ValueError('Native DLL changed during operation')
    atomic_write(path,backup_path(path).read_bytes());return dict(status='restored',sha256=ORIGINAL_SHA256)


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('dll',type=Path)
    group=p.add_mutually_exclusive_group();group.add_argument('--apply',action='store_true');group.add_argument('--restore',action='store_true')
    args=p.parse_args()
    result=apply(args.dll) if args.apply else restore(args.dll) if args.restore else dict(current_sha256=digest(args.dll.read_bytes()),expected_original_sha256=ORIGINAL_SHA256,read_only=True)
    print(json.dumps(result,indent=2))

if __name__=='__main__':main()
