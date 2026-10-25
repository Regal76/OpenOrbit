#!/usr/bin/env python3
"""Enable manual rockets for selected BuildUnit targets. Default is read-only.
Apply/restore require a stopped client and the exact prior compatibility chain.
"""
import argparse
import hashlib
import json
from pathlib import Path
import struct
from cbs_hangar_button_compat import atomic_write, native_client_running

ORIGINAL_SHA256='b6e9bdc465a72a5d369c601cf1d31b492863266c67e7e04a4df9e007f974f174'
MODIFIED_SHA256='42fc6f05cf86e75d94c4ec3be4669cd081d669661fb4ee41a27cef36317fbeec'
ENTRY_RVA=0x37fa15
ORIGINAL_BYTES=bytes.fromhex('57 8b 3a 8a 87 b8 00 00 00')
BUILD_CLASS_RVA=0x34050c4
BUILD_POSITION_RVA=0xf66930
SCOPE='Manual rocket accepts exact BuildUnit target using native position and existing request construction; preserve ship and unknown target paths'

def digest(raw):return hashlib.sha256(raw).hexdigest()

def trampoline(rva):
    code=bytearray();branches=[]
    def emit(raw):code.extend(bytes.fromhex(raw))
    def relative(op,target):
        emit(op);code.extend(struct.pack('<i',target-(rva+len(code)+4)))
    emit('57')                             # original PUSH EDI
    emit('e8 00 00 00 00 5f')              # EDI = current runtime address
    emit('81 ef');code.extend(struct.pack('<I',rva+6)) # EDI = module base
    emit('8b bf');code.extend(struct.pack('<I',BUILD_CLASS_RVA))
    emit('39 3a')                          # target exact class == BuildUnit?
    emit('0f 85');branches.append(len(code));code.extend(b'\0'*4)
    emit('8b 7a 30 8b c7 23 42 34 83 f8 ff') # Entity.Id; original invalid-ID test
    relative('0f 84',0x37fb6b)              # original POP EDI / return
    emit('6a 00 52 8d 45 e8 50')           # null MethodInfo, target, output
    relative('e8',BUILD_POSITION_RVA)       # native BuildUnit.get_RealPosition
    emit('8b 48 08 89 48 04')              # world x,z -> request targetX,targetY
    relative('e9',0x37fa5b)                # original allocation, delta and send
    fallback=len(code)
    code.extend(ORIGINAL_BYTES[1:])         # displaced original ship cast setup
    relative('e9',ENTRY_RVA+len(ORIGINAL_BYTES))
    for at in branches:struct.pack_into('<i',code,at,fallback-at-4)
    return bytes(code)

def patch_bytes(original):
    if digest(original)!=ORIGINAL_SHA256:raise ValueError('Unsupported native DLL fingerprint')
    pe=struct.unpack_from('<I',original,0x3c)[0];optional=pe+24
    if (original[pe:pe+4]!=b'PE\0\0' or struct.unpack_from('<H',original,pe+4)[0]!=0x14c or
            struct.unpack_from('<H',original,optional)[0]!=0x10b):raise ValueError('Expected x86 PE32 image')
    count=struct.unpack_from('<H',original,pe+6)[0]
    table=optional+struct.unpack_from('<H',original,pe+20)[0]
    sections=[struct.unpack_from('<IIII',original,table+40*i+8) for i in range(count)]
    def offset(rva):
        for _,start,size,raw in sections:
            if start<=rva<start+size:return raw+rva-start
        raise ValueError('Native hook outside section')
    site=offset(ENTRY_RVA)
    if original[site:site+len(ORIGINAL_BYTES)]!=ORIGINAL_BYTES:raise ValueError('Native rocket cast hook differs')
    header=table+40*(count-1);vsize,start,size,raw=sections[-1]
    if (original[header:header+8]!=b'.cbsloop' or struct.unpack_from('<I',original,header+36)[0]!=0x60000020 or
            raw+size!=len(original) or vsize>size):raise ValueError('Expected final executable compatibility section without overlay')
    sa,fa=struct.unpack_from('<II',original,optional+32)
    align=lambda value,unit:(value+unit-1)//unit*unit
    destination=start+size;hook=trampoline(destination);new_size=align(size+len(hook),fa)
    result=bytearray(original);result.extend(hook+b'\0'*(new_size-size-len(hook)))
    struct.pack_into('<I',result,header+8,size+len(hook));struct.pack_into('<I',result,header+16,new_size)
    struct.pack_into('<I',result,optional+4,struct.unpack_from('<I',original,optional+4)[0]+new_size-size)
    struct.pack_into('<I',result,optional+56,align(start+size+len(hook),sa))
    result[site:site+len(ORIGINAL_BYTES)]=b'\xe9'+struct.pack('<i',destination-ENTRY_RVA-5)+b'\x90'*4
    if digest(result)!=MODIFIED_SHA256:raise ValueError('Unexpected generated manual rocket fingerprint')
    return bytes(result)

def backup_path(path):return Path(str(path)+'.cbs-manual-rocket.original')
def manifest_path(path):return Path(str(path)+'.cbs-manual-rocket.json')

def verified_manifest(path):
    manifest=json.loads(manifest_path(path).read_text());backup=backup_path(path).read_bytes()
    if (manifest.get('original_sha256')!=ORIGINAL_SHA256 or digest(backup)!=ORIGINAL_SHA256 or
            manifest.get('modified_sha256')!=digest(patch_bytes(backup)) or manifest.get('scope')!=SCOPE):
        raise ValueError('Unknown manual rocket manifest or backup fingerprint')
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
        with backup.open('xb') as stream:stream.write(current)
    manifest=dict(original_sha256=ORIGINAL_SHA256,modified_sha256=digest(modified),scope=SCOPE,entry_rva=ENTRY_RVA)
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
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('dll',type=Path)
    action=parser.add_mutually_exclusive_group();action.add_argument('--apply',action='store_true');action.add_argument('--restore',action='store_true')
    args=parser.parse_args()
    if args.apply:result=apply(args.dll)
    elif args.restore:result=restore(args.dll)
    else:
        current=args.dll.read_bytes();result=dict(mode='read-only',sha256=digest(current),scope=SCOPE)
        if digest(current)==ORIGINAL_SHA256:result['prepared_sha256']=digest(patch_bytes(current))
        else:result['manifest']=verified_manifest(args.dll)
    print(json.dumps(result,indent=2))

if __name__=='__main__':main()
