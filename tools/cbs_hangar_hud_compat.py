#!/usr/bin/env python3
"""Expose the native Hangar HUD while docked outside a peace area.

Two Hangar-only visibility reads and one close-window guard accept InPeaceArea
OR InStation.Value. Neither global setting is changed; no helper building is
created. Requires the prior Activate callback correction on exact .115 input.
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

ORIGINAL_SHA256='de3a4e1fd8f80ae84a3fc182dbfaa7d3971a25b240d9f1a75030e8aeeadf24ed'
MODIFIED_SHA256='5ad4fd5f6fe24744a86187a6c25c7a966ad9fe0610631c7892d1b9de465d98e9'
VISIBILITY_RVAS=(0x53ffaf, 0xf0ee8b)
CLOSE_GUARD_RVA=0xf0ef56
CLOSE_RVA=0xf0ef5f
KEEP_OPEN_RVA=0xf0ef8a
EXPECTED={site:bytes.fromhex('0f b6 80 d0 00 00 00') for site in VISIBILITY_RVAS}
EXPECTED[CLOSE_GUARD_RVA]=bytes.fromhex('80 b8 d0 00 00 00 00 75 2b')
SCOPE='Native Hangar HUD visibility and open-window lifetime: InPeaceArea OR non-null InStation.Value'


def digest(raw):return hashlib.sha256(raw).hexdigest()


class Code:
    def __init__(self,rva):self.rva=rva;self.raw=bytearray();self.labels={};self.refs=[]
    def emit(self,hex_bytes):self.raw.extend(bytes.fromhex(hex_bytes))
    def branch(self,opcode,target):
        self.emit(opcode);self.refs.append((len(self.raw),target));self.raw.extend(b'\0'*4)
    def label(self,name):self.labels[name]=len(self.raw)
    def finish(self):
        for at,target in self.refs:
            destination=self.rva+self.labels[target] if isinstance(target,str) else target
            struct.pack_into('<i',self.raw,at,destination-(self.rva+at+4))
        return bytes(self.raw)


def visibility_trampoline(rva,site):
    """MOVZX replacement: preserve every input register/flag except EAX output.

    EAX points to Settings.static_fields. A null InStation BindableBoolean means
    false; no shared setting is written. The relative branches need no ASLR fixup.
    """
    if site not in VISIBILITY_RVAS:raise ValueError('Unknown visibility call site')
    c=Code(rva);c.emit('9c 51 0f b6 88 d0 00 00 00 85 c9')
    c.branch('0f 85','value')
    c.emit('8b 88 d4 00 00 00 85 c9');c.branch('0f 84','false')
    c.emit('0f b6 49 0c');c.branch('e9','value')
    c.label('false');c.emit('31 c9')
    c.label('value');c.emit('89 c8 59 9d');c.branch('e9',site+7)
    return c.finish()


def close_trampoline(rva):
    """Preserve original EAX/GPRs and original CMP flags on both continuations."""
    c=Code(rva);c.emit('9c 60 80 b8 d0 00 00 00 00');c.branch('0f 85','keep')
    c.emit('8b 88 d4 00 00 00 85 c9');c.branch('0f 84','close')
    c.emit('80 79 0c 00');c.branch('0f 85','keep')
    c.label('close');c.emit('61 9d 80 b8 d0 00 00 00 00');c.branch('e9',CLOSE_RVA)
    c.label('keep');c.emit('61 9d 80 b8 d0 00 00 00 00');c.branch('e9',KEEP_OPEN_RVA)
    return c.finish()


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
    for site,expected in EXPECTED.items():
        if original[offset(site):offset(site)+len(expected)]!=expected:raise ValueError('Native HUD guard differs')
    header=table+40*count
    if header+40>min(s[3] for s in sections) or any(original[header:header+40]):raise ValueError('No unused section header')
    if len(original)!=max(s[3]+s[2] for s in sections):raise ValueError('Unexpected PE overlay')
    sa,fa=struct.unpack_from('<II',original,optional+32)
    align=lambda v,n:(v+n-1)//n*n
    new_rva=align(max(s[1]+max(s[0],s[2]) for s in sections),sa);new_offset=align(len(original),fa)
    payload=bytearray();destinations={}
    for site in EXPECTED:
        destinations[site]=new_rva+len(payload)
        code=visibility_trampoline(destinations[site],site) if site in VISIBILITY_RVAS else close_trampoline(destinations[site])
        payload.extend(code)
    raw_size=align(len(payload),fa);result=bytearray(original)
    result.extend(b'\0'*(new_offset-len(result)));result.extend(payload);result.extend(b'\0'*(raw_size-len(payload)))
    result[header:header+40]=struct.pack('<8sIIIIIIHHI',b'.cbshud',len(payload),new_rva,raw_size,new_offset,0,0,0,0,0x60000020)
    struct.pack_into('<H',result,pe+6,count+1)
    struct.pack_into('<I',result,optional+4,struct.unpack_from('<I',original,optional+4)[0]+raw_size)
    struct.pack_into('<I',result,optional+56,align(new_rva+len(payload),sa))
    for site,expected in EXPECTED.items():
        result[offset(site):offset(site)+len(expected)]=b'\xe9'+struct.pack('<i',destinations[site]-site-5)+b'\x90'*(len(expected)-5)
    if digest(result)!=MODIFIED_SHA256:raise ValueError('Unexpected generated HUD fingerprint')
    return bytes(result)


def native_client_running():
    if os.name=='nt':
        output=subprocess.check_output(['tasklist','/FO','CSV','/NH'],text=True)
        return any(line.split(',')[0].strip('"').casefold()=='darkorbit.exe' for line in output.splitlines())
    output=subprocess.check_output(['ps','-axo','comm='],text=True)
    return any(line.strip().replace('\\','/').rsplit('/',1)[-1].casefold()=='darkorbit.exe' for line in output.splitlines())


def backup_path(path):return Path(str(path)+'.cbs-hangar-hud.original')
def manifest_path(path):return Path(str(path)+'.cbs-hangar-hud.json')


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
        raise ValueError('Unknown native HUD manifest')
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
