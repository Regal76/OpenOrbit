#!/usr/bin/env python3
"""Synchronize 2D drone orientation with its ship; retain formation movement.
Default is read-only. Apply/restore require a stopped exact supported client.
"""
import argparse
import hashlib
import json
from pathlib import Path
import struct
from cbs_hangar_button_compat import atomic_write,native_client_running

ORIGINAL_SHA256='d498b0702ca1d725b69bad9633dde27dea22c8756be650cf69b5643330c26330'
MODIFIED_SHA256='fc3f5f7c190ad62ddd0cab9013fc50150a0d4b5ce5ed11239ca376f52132389a'
EXPECTED={0x35300f:bytes.fromhex('85 ff 0f 84 3e 01 00 00'),0x34fac0:bytes.fromhex('55 8b ec 83 ec 10')}
SCOPE='2D drone orientation is immediate and sprite heading follows owner ShipRotation; retain formation translations, parent damping, angle normalization and every prior compatibility layer'

def digest(raw):return hashlib.sha256(raw).hexdigest()

class Code:
    def __init__(self,rva):self.rva=rva;self.raw=bytearray();self.labels={};self.branches=[]
    def emit(self,text):self.raw.extend(bytes.fromhex(text))
    def imm(self,value):self.raw.extend(struct.pack('<I',value))
    def relative(self,op,target):
        self.emit(op);self.raw.extend(struct.pack('<i',target-(self.rva+len(self.raw)+4)))
    def branch(self,op,label):
        self.emit(op);self.branches.append((len(self.raw),label));self.raw.extend(b'\0'*4)
    def label(self,name):self.labels[name]=len(self.raw)
    def finish(self):
        for at,name in self.branches:struct.pack_into('<i',self.raw,at,self.labels[name]-at-4)
        return bytes(self.raw)

def rotation_trampoline(rva):
    # Enter after native metadata/component lookup, only when isRotation=true.
    c=Code(rva)
    c.emit('85 ff');c.branch('0f 84','apply')
    c.emit('8b 77 70 85 f6');c.branch('0f 84','apply')
    c.emit('6a 00 6a 00 56');c.relative('e8',0x170fe80) # Kill rotation tween, complete=false
    c.emit('83 c4 0c c7 47 70 00 00 00 00')
    c.label('apply')
    c.emit('6a 00 53');c.relative('e8',0xf7c780) # Unit.GameObject
    c.emit('83 c4 08 85 c0');c.relative('0f 84',0x35324e)
    c.emit('6a 00 50');c.relative('e8',0x2920880) # GameObject.transform
    c.emit('83 c4 08 85 c0');c.relative('0f 84',0x35324e)
    c.emit('6a 00 ff 75 14 ff 75 10 ff 75 0c 50') # original normalized Euler vector
    c.relative('e8',0x292f6b0) # Transform.localEulerAngles = endValue
    c.emit('83 c4 14');c.relative('e9',0x353231) # native epilogue
    return c.finish()

def sprite_trampoline(rva):
    c=Code(rva);c.raw.extend(EXPECTED[0x34fac0]);c.emit('9c 60')
    c.emit('8b 45 08 85 c0');c.branch('0f 84','done')
    c.emit('8b 58 40 85 db');c.branch('0f 84','done') # DroneComponent2D.OwnerUnit
    c.emit('e8 00 00 00 00');pc=c.rva+len(c.raw);c.emit('5e 81 ee');c.imm(pc)
    c.emit('8d 86');c.imm(0x33c5e70) # GetComponent<ShipComponent> metadata usage
    c.emit('50');c.relative('e8',0x1ef640);c.emit('83 c4 04')
    c.emit('ff b6');c.imm(0x33c5e70);c.emit('53');c.relative('e8',0x17b13a0)
    c.emit('83 c4 08 85 c0');c.branch('0f 84','done')
    c.emit('8b 40 7c 89 45 0c') # current ShipComponent.ShipRotation -> sprite angle
    c.label('done');c.emit('61 9d');c.relative('e9',0x34fac6)
    return c.finish()

def patch_bytes(original):
    if digest(original)!=ORIGINAL_SHA256:raise ValueError('Unsupported native DLL fingerprint')
    pe=struct.unpack_from('<I',original,0x3c)[0];optional=pe+24
    if (original[pe:pe+4]!=b'PE\0\0' or struct.unpack_from('<H',original,pe+4)[0]!=0x14c or
            struct.unpack_from('<H',original,optional)[0]!=0x10b):raise ValueError('Expected x86 PE32 image')
    count=struct.unpack_from('<H',original,pe+6)[0];table=optional+struct.unpack_from('<H',original,pe+20)[0]
    sections=[struct.unpack_from('<IIII',original,table+40*i+8) for i in range(count)]
    def offset(rva):
        for _,start,size,raw in sections:
            if start<=rva<start+size:return raw+rva-start
        raise ValueError('Native hook outside section')
    for rva,expected in EXPECTED.items():
        at=offset(rva)
        if original[at:at+len(expected)]!=expected:raise ValueError('Native drone orientation hook differs')
    header=table+40*(count-1);vsize,start,size,raw=sections[-1]
    if (original[header:header+8]!=b'.cbsloop' or struct.unpack_from('<I',original,header+36)[0]!=0x60000020 or
            raw+size!=len(original) or vsize>size):raise ValueError('Expected final executable compatibility section without overlay')
    sa,fa=struct.unpack_from('<II',original,optional+32);align=lambda value,unit:(value+unit-1)//unit*unit
    destination=start+size;rotation=rotation_trampoline(destination);sprite=sprite_trampoline(destination+len(rotation));hook=rotation+sprite
    destinations={0x35300f:destination,0x34fac0:destination+len(rotation)};new_size=align(size+len(hook),fa)
    result=bytearray(original);result.extend(hook+b'\0'*(new_size-size-len(hook)))
    struct.pack_into('<I',result,header+8,size+len(hook));struct.pack_into('<I',result,header+16,new_size)
    struct.pack_into('<I',result,optional+4,struct.unpack_from('<I',original,optional+4)[0]+new_size-size)
    struct.pack_into('<I',result,optional+56,align(start+size+len(hook),sa))
    for rva,target in destinations.items():
        at=offset(rva);length=len(EXPECTED[rva]);result[at:at+length]=b'\xe9'+struct.pack('<i',target-rva-5)+b'\x90'*(length-5)
    if digest(result)!=MODIFIED_SHA256:raise ValueError('Unexpected generated drone orientation fingerprint')
    return bytes(result)

def backup_path(path):return Path(str(path)+'.drone-sync.original')
def manifest_path(path):return Path(str(path)+'.drone-sync.json')

def verified_manifest(path):
    manifest=json.loads(manifest_path(path).read_text());backup=backup_path(path).read_bytes()
    if (manifest.get('original_sha256')!=ORIGINAL_SHA256 or digest(backup)!=ORIGINAL_SHA256 or
            manifest.get('modified_sha256')!=digest(patch_bytes(backup)) or manifest.get('scope')!=SCOPE):
        raise ValueError('Unknown drone orientation manifest or backup fingerprint')
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
    manifest=dict(original_sha256=ORIGINAL_SHA256,modified_sha256=digest(modified),scope=SCOPE,entry_rvas=list(EXPECTED))
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
