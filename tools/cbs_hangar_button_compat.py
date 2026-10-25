#!/usr/bin/env python3
"""Reversible .115 CBS Hangar service bubbles using shipped geometry-free assets.

Only type48 IDs159500001..159500023 with userName=refinery_invisible_0 use
an existing empty prefab. Their blue Hangar artwork and click action remain
native. This expects the prior drone, resonator and CBS shield corrections.
Default operation is read-only. Close DarkOrbit before --apply/--restore.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import struct
import subprocess
import tempfile

ORIGINAL_SHA256='a462319b994b3f592786a3433e61a2a0330d78fe367b1fe67371e50396b7b38f'
HELPER_IDS=tuple(range(159500001,159500024))
PATTERN_NAME='refinery_invisible_0'
PATTERN_ENTRY_RVA=0x2b8700
ICON_CALL_RETURN_RVA=0xf1c450
PREFAB_JOIN_RVA=0x2cb057
EMPTY_PREFAB_GLOBAL_RVA=0x33cb838
ANIMATION_CALL_RVA=0x2fa943
SET_ANIMATION_RVA=0x6eb270
EXPECTED={PATTERN_ENTRY_RVA:bytes.fromhex('55 8b ec 83 ec 10'),
          PREFAB_JOIN_RVA:bytes.fromhex('8b 45 08 8b 7d dc'),
          ANIMATION_CALL_RVA:b'\xe8'+struct.pack('<i',SET_ANIMATION_RVA-ANIMATION_CALL_RVA-5)}


def digest(raw):return hashlib.sha256(raw).hexdigest()


class Code:
    def __init__(self,rva):self.rva=rva;self.raw=bytearray();self.labels={};self.refs=[]
    def emit(self,hex_bytes):self.raw.extend(bytes.fromhex(hex_bytes))
    def u32(self,value):self.raw.extend(struct.pack('<I',value))
    def branch(self,op,label):
        self.emit(op);self.refs.append((len(self.raw),label,'relative'));self.u32(0)
    def base(self):
        self.emit('e8 00 00 00 00');eip=self.rva+len(self.raw)
        self.emit('5b 81 eb');self.u32(eip)
    def helper(self,fallback):
        # EAX=original AssetCreateCommand, EBX=image base. Never mutate the item.
        self.emit('85 c0');self.branch('0f 84',fallback)
        self.emit('8b 50 1c 85 d2');self.branch('0f 84',fallback)
        self.emit('83 7a 08 30');self.branch('0f 85',fallback)
        self.emit('8b 50 28 81 ea');self.u32(HELPER_IDS[0])
        self.emit('83 fa 16');self.branch('0f 87',fallback)
        self.emit('8b 70 0c 85 f6');self.branch('0f 84',fallback)
        self.emit('83 7e 08');self.raw.append(len(PATTERN_NAME));self.branch('0f 85',fallback)
        self.emit('8d bb');self.refs.append((len(self.raw),'pattern','rva'));self.u32(0)
        self.emit('b9');self.u32(len(PATTERN_NAME));self.emit('8d 76 0c fc f3 66 a7')
        self.branch('0f 85',fallback)
    def finish(self):
        self.labels['pattern']=len(self.raw);self.raw.extend(PATTERN_NAME.encode('utf-16le'))
        for at,label,kind in self.refs:
            target=self.rva+self.labels[label] if isinstance(label,str) else label
            struct.pack_into('<I' if kind=='rva' else '<i',self.raw,at,target if kind=='rva' else target-(self.rva+at+4))
        return bytes(self.raw)


def pattern_trampoline(rva):
    c=Code(rva);c.emit('9c 60');c.base()
    # GetClickIcon must retain the original Hangar pattern and buttonHangar.
    c.emit('8d 83');c.u32(ICON_CALL_RETURN_RVA);c.emit('39 44 24 24');c.branch('0f 84','original')
    c.emit('8b 44 24 28');c.helper('original')
    c.emit('8b 40 0c 89 44 24 1c 61 9d c3')
    c.labels['original']=len(c.raw);c.emit('61 9d');c.raw.extend(EXPECTED[PATTERN_ENTRY_RVA]);c.branch('e9',PATTERN_ENTRY_RVA+6)
    return c.finish()


def prefab_trampoline(rva):
    c=Code(rva);c.emit('9c 60');c.base()
    c.emit('8b 45 08 85 c0');c.branch('0f 84','original')
    c.emit('8b 40 08');c.helper('original')
    c.emit('8b 83');c.u32(EMPTY_PREFAB_GLOBAL_RVA)
    c.emit('85 c0');c.branch('0f 84','original')
    c.emit('a8 01');c.branch('0f 85','original')
    # Preserve ESI's intended new resource and the state-machine local copy.
    c.emit('89 44 24 04 89 45 e8')
    c.labels['original']=len(c.raw);c.emit('61 9d');c.raw.extend(EXPECTED[PREFAB_JOIN_RVA]);c.branch('e9',PREFAB_JOIN_RVA+6)
    return c.finish()


def animation_trampoline(rva):
    # Ordinary Hangars require non-null background animation data; an empty
    # refinery pattern deliberately has none. Skip that call only for helpers.
    c=Code(rva);c.emit('9c 60');c.base()
    c.emit('85 ff');c.branch('0f 84','original')
    c.emit('8b 47 0c');c.helper('original')
    c.emit('61 9d c3')
    c.labels['original']=len(c.raw);c.emit('61 9d');c.branch('e9',SET_ANIMATION_RVA)
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
    for rva,raw in EXPECTED.items():
        if original[offset(rva):offset(rva)+len(raw)]!=raw:raise ValueError('Native hook differs')
    header=table+40*count
    if header+40>min(s[3] for s in sections) or any(original[header:header+40]):raise ValueError('No unused section header')
    if len(original)!=max(s[3]+s[2] for s in sections):raise ValueError('Unexpected PE overlay')
    sa,fa=struct.unpack_from('<II',original,optional+32)
    align=lambda v,n:(v+n-1)//n*n
    new_rva=align(max(s[1]+max(s[0],s[2]) for s in sections),sa);new_offset=align(len(original),fa)
    payload=bytearray();destinations={}
    for site,builder in [(PATTERN_ENTRY_RVA,pattern_trampoline),(PREFAB_JOIN_RVA,prefab_trampoline),(ANIMATION_CALL_RVA,animation_trampoline)]:
        destinations[site]=new_rva+len(payload);payload.extend(builder(destinations[site]))
    raw_size=align(len(payload),fa);result=bytearray(original)
    result.extend(b'\0'*(new_offset-len(result)));result.extend(payload);result.extend(b'\0'*(raw_size-len(payload)))
    result[header:header+40]=struct.pack('<8sIIIIIIHHI',b'.cbshgr',len(payload),new_rva,raw_size,new_offset,0,0,0,0,0x60000020)
    struct.pack_into('<H',result,pe+6,count+1)
    struct.pack_into('<I',result,optional+4,struct.unpack_from('<I',original,optional+4)[0]+raw_size)
    struct.pack_into('<I',result,optional+56,align(new_rva+len(payload),sa))
    for site,destination in destinations.items():
        call=site==ANIMATION_CALL_RVA
        result[offset(site):offset(site)+len(EXPECTED[site])]=(b'\xe8' if call else b'\xe9')+struct.pack('<i',destination-site-5)+(b'' if call else b'\x90')
    return bytes(result)


def native_client_running():
    if os.name=='nt':
        output=subprocess.check_output(['tasklist','/FO','CSV','/NH'],text=True)
        return any(line.split(',')[0].strip('"').casefold()=='darkorbit.exe' for line in output.splitlines())
    output=subprocess.check_output(['ps','-axo','comm='],text=True)
    return any(line.strip().replace('\\','/').rsplit('/',1)[-1].casefold()=='darkorbit.exe' for line in output.splitlines())


def backup_path(path):return Path(str(path)+'.cbs-hangar.original')
def manifest_path(path):return Path(str(path)+'.cbs-hangar.json')


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
    if manifest.get('original_sha256')!=ORIGINAL_SHA256 or manifest.get('helper_ids')!=list(HELPER_IDS) or manifest.get('pattern_name')!=PATTERN_NAME:
        raise ValueError('Unknown native Hangar manifest')
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
    manifest=dict(original_sha256=ORIGINAL_SHA256,modified_sha256=digest(modified),helper_ids=list(HELPER_IDS),pattern_name=PATTERN_NAME)
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
    result=apply(args.dll) if args.apply else restore(args.dll) if args.restore else dict(current_sha256=digest(args.dll.read_bytes()),expected_original_sha256=ORIGINAL_SHA256,helper_ids=HELPER_IDS,read_only=True)
    print(json.dumps(result,indent=2))

if __name__=='__main__':main()
