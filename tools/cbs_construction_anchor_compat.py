#!/usr/bin/env python3
"""Anchor only CBS construction effects whose source is BuildUnit.
Default read-only. Apply/restore require all native DarkOrbit clients stopped.
"""
import argparse,hashlib,json,struct
from pathlib import Path
from cbs_hangar_button_compat import atomic_write,native_client_running
from drone_sync_native_compat import Code

ORIGINAL_SHA256='fc3f5f7c190ad62ddd0cab9013fc50150a0d4b5ce5ed11239ca376f52132389a'
ENTRY_RVA=0x762f9f
ORIGINAL_BYTES=bytes.fromhex('85 db 0f 84 b4 00 00 00')
SCOPE='Anchor ConstructingEffect2D BuildUnit source to its visible 2D component transform; preserve Unit behavior and every earlier native layer'

def digest(raw):return hashlib.sha256(raw).hexdigest()

def trampoline(rva):
    c=Code(rva);c.emit('9c 60 81 ec 80 00 00 00')
    for reg in range(8):
        c.emit('f3 0f 7f');c.raw.extend(bytes([0x84|(reg<<3),0x24]));c.imm(16*reg)
    c.emit('85 c0');c.branch('0f 85','done') # native Unit parent already resolved
    c.emit('8b 45 08 85 c0');c.branch('0f 84','done') # ConstructingEffect2D this
    c.emit('8b 40 08 85 c0');c.branch('0f 84','done') # ConstructingEffect
    c.emit('8b 78 34 85 ff');c.branch('0f 84','done') # source
    c.emit('e8 00 00 00 00');pc=rva+len(c.raw);c.emit('5e 81 ee');c.imm(pc)
    c.emit('8d 86');c.imm(0x34050c4);c.emit('50');c.relative('e8',0x1ef640);c.emit('83 c4 04')
    c.emit('8b 86');c.imm(0x34050c4);c.emit('39 07');c.branch('0f 85','done') # exact BuildUnit
    # Match BuildUnit.RealPosition: Entity.GetComponent<BuildGameObjectComponent>
    # method usage115884 at0x3420300, then its visible GameObject field+0x68.
    c.emit('8d 86');c.imm(0x3420300);c.emit('50');c.relative('e8',0x1ef640);c.emit('83 c4 04')
    c.emit('ff b6');c.imm(0x3420300);c.emit('57');c.relative('e8',0x17b13a0)
    c.emit('83 c4 08 85 c0');c.branch('0f 84','done')
    c.emit('8b 40 68 85 c0');c.branch('0f 84','done')
    c.emit('6a 00 50');c.relative('e8',0x2920880);c.emit('83 c4 08 89 84 24 9c 00 00 00')
    c.label('done')
    for reg in range(8):
        c.emit('f3 0f 6f');c.raw.extend(bytes([0x84|(reg<<3),0x24]));c.imm(16*reg)
    c.emit('81 c4 80 00 00 00 61 9d 85 db')
    c.relative('0f 84',0x76305b);c.relative('e9',0x762fa7)
    return c.finish()

def patch_bytes(original):
    if digest(original)!=ORIGINAL_SHA256:raise ValueError('Unsupported native DLL fingerprint')
    import pefile
    pe=pefile.PE(data=original,fast_load=True)
    if pe.FILE_HEADER.Machine!=0x14c or pe.OPTIONAL_HEADER.Magic!=0x10b:raise ValueError('Expected x86 PE32')
    site=pe.get_offset_from_rva(ENTRY_RVA)
    if original[site:site+len(ORIGINAL_BYTES)]!=ORIGINAL_BYTES:raise ValueError('Construction hook bytes differ')
    count=pe.FILE_HEADER.NumberOfSections;optional=pe.DOS_HEADER.e_lfanew+24;header=optional+pe.FILE_HEADER.SizeOfOptionalHeader+40*(count-1)
    sec=pe.sections[-1];start,size,at=sec.VirtualAddress,sec.SizeOfRawData,sec.PointerToRawData
    if sec.Name.rstrip(b'\0')!=b'.cbsloop' or sec.Characteristics!=0x60000020 or at+size!=len(original) or sec.Misc_VirtualSize>size:
        raise ValueError('Expected final executable compatibility section')
    sa,fa=pe.OPTIONAL_HEADER.SectionAlignment,pe.OPTIONAL_HEADER.FileAlignment
    align=lambda v,a:(v+a-1)//a*a
    target=start+size;hook=trampoline(target);new_size=align(size+len(hook),fa)
    result=bytearray(original);result.extend(hook+b'\0'*(new_size-size-len(hook)))
    struct.pack_into('<I',result,header+8,size+len(hook));struct.pack_into('<I',result,header+16,new_size)
    struct.pack_into('<I',result,optional+4,pe.OPTIONAL_HEADER.SizeOfCode+new_size-size)
    struct.pack_into('<I',result,optional+56,align(start+size+len(hook),sa))
    result[site:site+len(ORIGINAL_BYTES)]=b'\xe9'+struct.pack('<i',target-ENTRY_RVA-5)+b'\x90'*3
    # Hook replaces only TEST+relative JE; neither instruction has a HIGHLOW.
    # All absolute slot addresses are derived from the runtime module base.
    return bytes(result)

def backup_path(path):return Path(str(path)+'.cbs-construction-anchor.original')
def manifest_path(path):return Path(str(path)+'.cbs-construction-anchor.json')

def verified_manifest(path):
    manifest=json.loads(manifest_path(path).read_text());backup=backup_path(path).read_bytes()
    if (manifest.get('original_sha256')!=ORIGINAL_SHA256 or digest(backup)!=ORIGINAL_SHA256 or
            manifest.get('modified_sha256')!=digest(patch_bytes(backup)) or manifest.get('scope')!=SCOPE):
        raise ValueError('Unknown construction anchor manifest or backup fingerprint')
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

def prepare(path,destination):
    path=Path(path);destination=Path(destination)
    if destination.exists():raise ValueError('Destination must be new')
    original=path.read_bytes();modified=patch_bytes(original)
    manifest=dict(scope=SCOPE,original_sha256=digest(original),modified_sha256=digest(modified),entry_rva=ENTRY_RVA)
    destination.mkdir(parents=True);(destination/'GameAssembly.dll').write_bytes(modified)
    (destination/'prepared.json').write_text(json.dumps(manifest,indent=2)+'\n');return manifest

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('dll',type=Path)
    g=p.add_mutually_exclusive_group();g.add_argument('--prepare',type=Path);g.add_argument('--apply',action='store_true');g.add_argument('--restore',action='store_true');a=p.parse_args()
    if a.prepare:result=prepare(a.dll,a.prepare)
    elif a.apply:result=apply(a.dll)
    elif a.restore:result=restore(a.dll)
    else:result=dict(read_only=True,current_sha256=digest(a.dll.read_bytes()),supported_sha256=ORIGINAL_SHA256)
    print(json.dumps(result,indent=2))

if __name__=='__main__':main()
