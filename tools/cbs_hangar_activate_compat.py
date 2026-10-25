#!/usr/bin/env python3
"""Allow the native Hangar Activate request when docked outside a peace area.

One .115 Hangar callback guard accepts InPeaceArea OR InStation.Value. Beacon
and global peace state remain unchanged. The server continues to authorize ship
activation. Requires the prior CBS Hangar service-bubble correction.
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

ORIGINAL_SHA256='cfbd0808bdd913c6a13770f03310f87cd1d3ddd19a0b79bff7df65f15bef4e6e'
GUARD_RVA=0x581520
ALLOWED_RVA=0x581529
DENIED_RVA=0x581590
EXPECTED=bytes.fromhex('80 b8 d0 00 00 00 00 74 67')
SCOPE='Hangar Activate callback: InPeaceArea OR non-null InStation.Value'


def digest(raw):return hashlib.sha256(raw).hexdigest()


def trampoline(rva):
    """Preserve GPR/XMM/stack and original comparison flags on both paths.

    EAX already points to Settings.static_fields. The docking BindableBoolean
    pointer is at +0xd4, with Value at +0xc. No helper calls or managed mutation.
    Both branches repeat the original CMP so their native continuation receives
    exactly the same flags it had before this compatibility change.
    """
    code=bytearray();labels={};refs=[]
    def emit(hex_bytes):code.extend(bytes.fromhex(hex_bytes))
    def branch(op,destination):
        emit(op);refs.append((len(code),destination));code.extend(b'\0'*4)
    emit('9c 60 80 b8 d0 00 00 00 00');branch('0f 85','allowed')
    emit('8b 88 d4 00 00 00 85 c9');branch('0f 84','denied')
    emit('80 79 0c 00');branch('0f 85','allowed')
    labels['denied']=len(code)
    emit('61 9d 80 b8 d0 00 00 00 00');branch('e9',DENIED_RVA)
    labels['allowed']=len(code)
    emit('61 9d 80 b8 d0 00 00 00 00');branch('e9',ALLOWED_RVA)
    for at,destination in refs:
        target=rva+labels[destination] if isinstance(destination,str) else destination
        struct.pack_into('<i',code,at,target-(rva+at+4))
    return bytes(code)


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
    at=offset(GUARD_RVA)
    if original[at:at+len(EXPECTED)]!=EXPECTED:raise ValueError('Native Activate guard differs')
    header=table+40*count
    if header+40>min(s[3] for s in sections) or any(original[header:header+40]):raise ValueError('No unused section header')
    if len(original)!=max(s[3]+s[2] for s in sections):raise ValueError('Unexpected PE overlay')
    sa,fa=struct.unpack_from('<II',original,optional+32)
    align=lambda v,n:(v+n-1)//n*n
    new_rva=align(max(s[1]+max(s[0],s[2]) for s in sections),sa);new_offset=align(len(original),fa)
    payload=trampoline(new_rva);raw_size=align(len(payload),fa);result=bytearray(original)
    result.extend(b'\0'*(new_offset-len(result)));result.extend(payload);result.extend(b'\0'*(raw_size-len(payload)))
    result[header:header+40]=struct.pack('<8sIIIIIIHHI',b'.cbsact',len(payload),new_rva,raw_size,new_offset,0,0,0,0,0x60000020)
    struct.pack_into('<H',result,pe+6,count+1)
    struct.pack_into('<I',result,optional+4,struct.unpack_from('<I',original,optional+4)[0]+raw_size)
    struct.pack_into('<I',result,optional+56,align(new_rva+len(payload),sa))
    result[at:at+len(EXPECTED)]=b'\xe9'+struct.pack('<i',new_rva-GUARD_RVA-5)+b'\x90'*(len(EXPECTED)-5)
    return bytes(result)


def native_client_running():
    if os.name=='nt':
        output=subprocess.check_output(['tasklist','/FO','CSV','/NH'],text=True)
        return any(line.split(',')[0].strip('"').casefold()=='darkorbit.exe' for line in output.splitlines())
    output=subprocess.check_output(['ps','-axo','comm='],text=True)
    return any(line.strip().replace('\\','/').rsplit('/',1)[-1].casefold()=='darkorbit.exe' for line in output.splitlines())


def backup_path(path):return Path(str(path)+'.cbs-hangar-activate.original')
def manifest_path(path):return Path(str(path)+'.cbs-hangar-activate.json')


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
    if manifest.get('original_sha256')!=ORIGINAL_SHA256 or manifest.get('scope')!=SCOPE:
        raise ValueError('Unknown native Activate manifest')
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
