#!/usr/bin/env python3
"""Prepare a CBS-only 50-fps cyclic shield loop without changing ship ISH.

Adds a dedicated prefab/controller/clip and interpolated atlas, a dedicated
Addressables alias, and a scoped native constructor-name hook. The existing
CBS-only Animator speed 0.5 remains intact: 64 frames at 100 Hz yield 50 real
frames/second and a 1.28-second period. Default operation is read-only.
"""
import argparse
import base64
import copy
import hashlib
import json
from pathlib import Path
import struct

SOURCE_ALIAS='invincibilityShield_2D'
ALIAS='cbsShieldSmooth_2D'
SOURCE_PATH='Assets/Res/Prefabs/2D/Effect_2D/Shield/'+SOURCE_ALIAS+'.prefab'
ALIAS_PATH='Assets/Res/Prefabs/2D/Effect_2D/Shield/'+ALIAS+'.prefab'
CLIP_ID=4253857719557661382
CONTROLLER_ID=4229465780702823626
ROOT_ID=7852722992530810838
SPRITE_RENDERER_ID=-4873544397819975722
ANIMATOR_ID=4747593718417090518
PREFAB_IDS=(ROOT_ID,6138660523558856662,-8269544462178031658,
            -5281111735850670122,597884265495947222,SPRITE_RENDERER_ID,ANIMATOR_ID)
INPUT_HASH={
 'native':'5ad4fd5f6fe24744a86187a6c25c7a966ad9fe0610631c7892d1b9de465d98e9',
 'bundle':'25e5916ac2156442da485376c1262e91f5a9a4da6f6d76e495c3a95e3fa31cef',
 'catalog':'178a06bf0ad663213561ca05d976ffd7e2394b683871ff4b5cb4c605637361c2',
 'hash':'1e1be022c348e1211c262c8a807684cc8ead44d630e22a8db7251e8ea978f528',
}


def digest(raw):return hashlib.sha256(raw).hexdigest()

def check(raw,kind):
    if digest(raw)!=INPUT_HASH[kind]:raise ValueError('Unsupported '+kind+' fingerprint')


def interpolate_frames(frames,substeps=4):
    """Convex premultiplied-alpha interpolation, including last→first.

    Original endpoint bytes are retained. Premultiplied interpolation preserves
    the linear combination of visible RGB on a black background; transparent
    RGB never creates a bright halo and no center content is introduced.
    """
    from PIL import Image
    if len(frames)<2 or substeps<1:raise ValueError('At least two frames and one substep required')
    if any(im.size!=frames[0].size or im.mode!='RGBA' for im in frames):
        raise ValueError('Consistent RGBA frames required')
    result=[]
    for i,frame in enumerate(frames):
        result.append(frame.copy())
        following=frames[(i+1)%len(frames)]
        for step in range(1,substeps):
            result.append(Image.blend(frame.convert('RGBa'),following.convert('RGBa'),step/substeps).convert('RGBA'))
    return result


def catalog_locations(catalog):
    keys=base64.b64decode(catalog['m_KeyDataString'])
    buckets=base64.b64decode(catalog['m_BucketDataString'])
    entries=base64.b64decode(catalog['m_EntryDataString']);pos=4;result={}
    for i in range(struct.unpack_from('<i',buckets)[0]):
        offset,count=struct.unpack_from('<ii',buckets,pos);pos+=8
        indices=struct.unpack_from('<%di'%count,buckets,pos);pos+=4*count
        if keys[offset]!=0:continue
        length=struct.unpack_from('<i',keys,offset+1)[0]
        key=keys[offset+5:offset+5+length].decode('ascii')
        locations=[]
        for j in indices:
            row=struct.unpack_from('<7i',entries,4+28*j)
            locations.append(dict(internalId=catalog['m_InternalIds'][row[0]],provider=row[1],
                                  dependency=row[2],dependencyHash=row[3],extra=row[4],resourceType=row[6]))
        result[key]=locations
    return result


def patch_catalog(raw):
    check(raw,'catalog');catalog=json.loads(raw)
    keys=bytearray(base64.b64decode(catalog['m_KeyDataString']))
    buckets=bytearray(base64.b64decode(catalog['m_BucketDataString']))
    entries=bytearray(base64.b64decode(catalog['m_EntryDataString']))
    nk=struct.unpack_from('<i',keys)[0];ne=struct.unpack_from('<i',entries)[0]
    if struct.unpack_from('<i',buckets)[0]!=nk:raise ValueError('Catalog key/bucket count differs')
    pos=4;source=[]
    for i in range(nk):
        offset,count=struct.unpack_from('<ii',buckets,pos);pos+=8
        ids=struct.unpack_from('<%di'%count,buckets,pos);pos+=4*count
        if keys[offset]==0:
            length=struct.unpack_from('<i',keys,offset+1)[0]
            key=keys[offset+5:offset+5+length].decode('ascii')
            if key==ALIAS:raise ValueError('Alias already exists')
            if key==SOURCE_ALIAS:source.extend(ids)
    if len(source)!=1:raise ValueError('Unique source addressable required')
    row=list(struct.unpack_from('<7i',entries,4+28*source[0]))
    if catalog['m_InternalIds'][row[0]]!=SOURCE_PATH:raise ValueError('Source addressable path differs')
    offset=len(keys);alias=ALIAS.encode('ascii');keys.extend(b'\0'+struct.pack('<i',len(alias))+alias)
    buckets.extend(struct.pack('<iii',offset,1,ne))
    row[0]=len(catalog['m_InternalIds']);row[5]=nk
    catalog['m_InternalIds'].append(ALIAS_PATH);entries.extend(struct.pack('<7i',*row))
    struct.pack_into('<i',keys,0,nk+1);struct.pack_into('<i',buckets,0,nk+1);struct.pack_into('<i',entries,0,ne+1)
    for name,value in (('m_KeyDataString',keys),('m_BucketDataString',buckets),('m_EntryDataString',entries)):
        catalog[name]=base64.b64encode(value).decode('ascii')
    return json.dumps(catalog,separators=(',',':')).encode()


def remap(tree,ids):
    if isinstance(tree,dict):
        if tree.get('m_FileID')==0 and tree.get('m_PathID') in ids:
            tree['m_PathID']=ids[tree['m_PathID']]
        for value in tree.values():remap(value,ids)
    elif isinstance(tree,(list,tuple)):
        for value in tree:remap(value,ids)


def patch_bundle(raw):
    check(raw,'bundle')
    import UnityPy
    from PIL import Image
    env=UnityPy.load(raw);objects={o.path_id:o for o in env.objects}
    source=objects[CLIP_ID].read_typetree()
    mapping=source['m_ClipBindingConstant']['pptrCurveMapping']
    if len(mapping)!=16 or source['m_SampleRate']!=25.:raise ValueError('Original shield frames differ')
    frames=interpolate_frames([objects[p['m_PathID']].read().image.convert('RGBA') for p in mapping])
    if any(im.size!=(350,350) for im in frames):raise ValueError('Original frame size differs')
    next_id=max(objects)+1;added=[]
    def clone(original,tree=None):
        nonlocal next_id
        obj=copy.copy(original);obj.path_id=next_id;next_id+=1
        obj.data=original.get_raw_data()
        if tree is not None:obj.save_typetree(tree)
        original.assets_file.objects[obj.path_id]=obj;objects[obj.path_id]=obj;added.append(obj.path_id)
        return obj
    # One shared atlas and one renderer: no double alpha-compositing or extra draw layer.
    width=2816;tile=352;atlas=Image.new('RGBA',(width,width))
    for i,frame in enumerate(frames):atlas.paste(frame,((i%8)*tile+1,(i//8)*tile+1))
    texture=clone(objects[-7803321577036476289]);tex=texture.read();tex.m_Name=ALIAS+' atlas'
    tex.set_image(atlas,target_format=4);tex.save()
    sprites=[]
    for i in range(64):
        # Each full-rect quad retains the original centered 350×350 dimensions.
        original=objects[mapping[i//4]['m_PathID']]
        data=original.read_typetree();data['m_Name']=ALIAS+'_%03d'%i
        x=(i%8)*tile+1;y=width-((i//8)*tile+1)-350
        rd=data['m_RD'];rd['texture']={'m_FileID':0,'m_PathID':texture.path_id}
        rd['textureRect']=dict(x=float(x),y=float(y),width=350.,height=350.)
        rd['textureRectOffset']=dict(x=0.,y=0.);rd['atlasRectOffset']=dict(x=0.,y=0.)
        rd['settingsRaw']=(rd['settingsRaw'] & ~127)|2
        vertices=[(-175.,-175.,0.),(175.,-175.,0.),(175.,175.,0.),(-175.,175.,0.)]
        uv=[(x/width,y/width),((x+350)/width,y/width),((x+350)/width,(y+350)/width),(x/width,(y+350)/width)]
        rd['m_VertexData']['m_VertexCount']=4
        rd['m_VertexData']['m_DataSize']=b''.join(struct.pack('<3f',*v) for v in vertices)+b''.join(struct.pack('<2f',*v) for v in uv)
        rd['m_IndexBuffer']=struct.pack('<6H',0,1,2,0,2,3)
        mesh=rd['m_SubMeshes'][0];mesh.update(firstByte=0,indexCount=6,firstVertex=0,vertexCount=4,baseVertex=0)
        rd['m_SubMeshes']=[mesh];rd['uvTransform']=dict(x=350.,y=175.,z=350.,w=175.)
        data['m_RenderDataKey']=(copy.deepcopy(data['m_RenderDataKey'][0]),next_id)
        sprites.append(clone(original,data).path_id)
    clip=copy.deepcopy(source);clip['m_Name']=ALIAS;clip['m_SampleRate']=100.
    clip['m_ClipBindingConstant']['pptrCurveMapping']=[dict(m_FileID=0,m_PathID=pid) for pid in sprites]
    streamed=clip['m_MuscleClip']['m_Clip']['data']['m_StreamedClip']
    old_size=len(streamed['data']);data=bytearray()
    for i in range(64):
        time=-3.4028234663852886e38 if i==0 else i/100.
        data.extend(struct.pack('<fii4f',time,1,0,0.,0.,0.,float(i)))
    data.extend(struct.pack('<fi',float('inf'),0))
    streamed['data']=list(struct.unpack('<%dI'%(len(data)//4),data))
    clip['m_MuscleClipSize']+=len(data)-old_size*4
    dense=clip['m_MuscleClip']['m_Clip']['data']['m_DenseClip'];dense['m_FrameCount']=66;dense['m_SampleRate']=100.
    # Stop time remains 0.64 simulation seconds; existing CBS-only speed remains 0.5.
    clone_clip=clone(objects[CLIP_ID],clip)
    controller=objects[CONTROLLER_ID].read_typetree();controller['m_Name']=ALIAS
    remap(controller,{CLIP_ID:clone_clip.path_id});clone_controller=clone(objects[CONTROLLER_ID],controller)
    ids={pid:next_id+i for i,pid in enumerate(PREFAB_IDS)}
    ids[CONTROLLER_ID]=clone_controller.path_id;ids[mapping[0]['m_PathID']]=sprites[0]
    for pid in PREFAB_IDS:
        tree=objects[pid].read_typetree();remap(tree,ids)
        if pid==ROOT_ID:tree['m_Name']=ALIAS
        cloned=clone(objects[pid],tree)
        if cloned.path_id!=ids[pid]:raise ValueError('Prefab clone allocation differs')
    ab=next(o for o in objects.values() if o.type.name=='AssetBundle');tree=ab.read_typetree()
    source_entry=next(info for name,info in tree['m_Container'] if name==SOURCE_PATH)
    preload=tree['m_PreloadTable'];start=len(preload)
    preload.extend(copy.deepcopy(preload[source_entry['preloadIndex']:source_entry['preloadIndex']+source_entry['preloadSize']]))
    preload.extend(dict(m_FileID=0,m_PathID=pid) for pid in added)
    tree['m_Container'].append((ALIAS_PATH,dict(preloadIndex=start,preloadSize=len(preload)-start,asset=dict(m_FileID=0,m_PathID=ids[ROOT_ID]))))
    ab.save_typetree(tree)
    return env.file.save(packer='original')


def native_trampoline(rva):
    """Return the dedicated managed alias string with MOV-compatible context."""
    code=bytearray(bytes.fromhex('9c 60 81 ec 80 00 00 00'))
    def emit(value):code.extend(bytes.fromhex(value))
    for reg in range(8):
        emit('f3 0f 7f');code.extend(bytes([0x84|(reg<<3),0x24]));code.extend(struct.pack('<I',16*reg))
    emit('e8 00 00 00 00');eip=rva+len(code)
    emit('58 2d');code.extend(struct.pack('<I',eip))
    emit('05');name_ref=len(code);code.extend(b'\0'*4)
    emit('50 e8');code.extend(struct.pack('<i',0x2002a0-(rva+len(code)+4)))
    emit('83 c4 04 89 84 24 9c 00 00 00')
    for reg in range(8):
        emit('f3 0f 6f');code.extend(bytes([0x84|(reg<<3),0x24]));code.extend(struct.pack('<I',16*reg))
    emit('81 c4 80 00 00 00 61 9d c3')
    struct.pack_into('<I',code,name_ref,rva+len(code))
    code.extend(ALIAS.encode('ascii')+b'\0')
    return bytes(code)


def patch_native(raw):
    check(raw,'native')
    import pefile
    pe=pefile.PE(data=raw,fast_load=True)
    if pe.FILE_HEADER.Machine!=0x14c or pe.OPTIONAL_HEADER.Magic!=0x10b:raise ValueError('Expected x86 PE32')
    hook=pe.get_offset_from_rva(0x7645e6);push=pe.get_offset_from_rva(0x7645f1)
    if raw[hook:hook+5]!=bytes.fromhex('a1 74 ef 3e 13'):
        # MOV EAX,[absolute string] is five bytes; next byte is following MOV.
        raise ValueError('CBS constructor literal load differs')
    # Hook only the original five-byte MOV. No following store byte is overwritten.
    if raw[push:push+6]!=bytes.fromhex('ff 35 74 ef 3e 13'):raise ValueError('CBS constructor barrier argument differs')
    optional=pe.DOS_HEADER.e_lfanew+24;table=optional+pe.FILE_HEADER.SizeOfOptionalHeader
    count=pe.FILE_HEADER.NumberOfSections;header=table+40*count
    if header+40>min(s.PointerToRawData for s in pe.sections) or any(raw[header:header+40]):
        raise ValueError('No unused PE section header')
    if len(raw)!=max(s.PointerToRawData+s.SizeOfRawData for s in pe.sections):raise ValueError('Unexpected PE overlay')
    align=lambda n,a:(n+a-1)//a*a
    rva=align(max(s.VirtualAddress+max(s.Misc_VirtualSize,s.SizeOfRawData) for s in pe.sections),pe.OPTIONAL_HEADER.SectionAlignment)
    at=align(len(raw),pe.OPTIONAL_HEADER.FileAlignment);payload=native_trampoline(rva)
    size=align(len(payload),pe.OPTIONAL_HEADER.FileAlignment);result=bytearray(raw)
    result.extend(b'\0'*(at-len(raw)));result.extend(payload+b'\0'*(size-len(payload)))
    result[header:header+40]=struct.pack('<8sIIIIIIHHI',b'.cbsloop',len(payload),rva,size,at,0,0,0,0,0x60000020)
    struct.pack_into('<H',result,pe.DOS_HEADER.e_lfanew+6,count+1)
    struct.pack_into('<I',result,optional+4,pe.OPTIONAL_HEADER.SizeOfCode+size)
    struct.pack_into('<I',result,optional+56,align(rva+len(payload),pe.OPTIONAL_HEADER.SectionAlignment))
    result[hook:hook+5]=b'\xe8'+struct.pack('<i',rva-0x7645e6-5)
    result[push:push+6]=bytes.fromhex('ff 76 0c 90 90 90')
    # Both replaced instructions originally contained absolute addresses. Their
    # HIGHLOW entries must become ABSOLUTE (no-op) entries: otherwise the loader
    # adds the image delta to our relative CALL and to the new PUSH/NOP bytes.
    # Keep the table/block sizes and every other relocation unchanged.
    directory=pe.OPTIONAL_HEADER.DATA_DIRECTORY[5]
    cursor=pe.get_offset_from_rva(directory.VirtualAddress);end=cursor+directory.Size
    targets={0x7645e7,0x7645f3};found=set()
    while cursor<end:
        page,block_size=struct.unpack_from('<II',raw,cursor)
        if block_size<8 or cursor+block_size>end:raise ValueError('Invalid PE relocation block')
        if page in {target&~0xfff for target in targets}:
            for position in range(cursor+8,cursor+block_size,2):
                entry=struct.unpack_from('<H',raw,position)[0];target=page+(entry&0xfff)
                if target in targets:
                    if entry>>12!=3 or target in found:raise ValueError('Expected unique HIGHLOW constructor relocation')
                    struct.pack_into('<H',result,position,entry&0xfff);found.add(target)
        cursor+=block_size
    if found!=targets:raise ValueError('Expected both constructor relocation entries')
    return bytes(result)


SCOPE='CBS-only cyclic 64-frame shield: 50 real frames/second at existing speed 0.5'


def artifact_paths(client):
    client=Path(client)
    aa=client/'DarkOrbit_Data/StreamingAssets/aa'
    return {
        'native':client/'GameAssembly.dll',
        'bundle':aa/'BuildTarget/effect_2d_assets_bundle_pack_effect_2d_047.bundle',
        'catalog':aa/'catalog.json',
        'remote_catalog':aa/'BuildTarget/catalog_2026.10.20.12.29.31.json',
        'hash':aa/'BuildTarget/catalog_2026.10.20.12.29.31.hash',
    }


def input_kind(kind):return 'catalog' if kind=='remote_catalog' else kind

def backups(path):return Path(str(path)+'.cbs-shield-loop.original')

def manifest_path(client):return Path(client)/'.cbs-shield-loop.json'


def build_artifacts(originals):
    for kind,raw in originals.items():check(raw,input_kind(kind))
    catalog=patch_catalog(originals['catalog'])
    # Addressables compares this opaque Hash128 with its cached catalog hash.
    # A new value forces the local modified catalog to be loaded after restart.
    return dict(native=patch_native(originals['native']),bundle=patch_bundle(originals['bundle']),
                catalog=catalog,remote_catalog=catalog,hash=digest(catalog)[:32].encode('ascii'))


def native_client_running():
    import os,subprocess
    if os.name=='nt':
        out=subprocess.check_output(['tasklist','/FO','CSV','/NH'],text=True)
        return any(line.split(',')[0].strip('"').casefold()=='darkorbit.exe' for line in out.splitlines())
    out=subprocess.check_output(['ps','-axo','comm='],text=True)
    return any(line.strip().replace('\\','/').rsplit('/',1)[-1].casefold()=='darkorbit.exe' for line in out.splitlines())


def atomic_write(path,raw):
    import os,tempfile
    path=Path(path);temporary=None
    try:
        with tempfile.NamedTemporaryFile(dir=path.parent,prefix='.'+path.name+'.',delete=False) as stream:
            temporary=Path(stream.name);stream.write(raw);stream.flush();os.fsync(stream.fileno())
        os.replace(temporary,path)
    finally:
        if temporary is not None and temporary.exists():temporary.unlink()


def describe(originals,modified):
    return dict(scope=SCOPE,revision=2,artifacts={kind:dict(original_sha256=digest(originals[kind]),
                                               modified_sha256=digest(modified[kind])) for kind in originals})


def prepare(client,destination):
    """Write reviewable candidate copies to a new directory; never alter client."""
    destination=Path(destination)
    if destination.exists():raise ValueError('Preparation directory must be new')
    paths=artifact_paths(client);originals={kind:path.read_bytes() for kind,path in paths.items()}
    modified=build_artifacts(originals);manifest=describe(originals,modified)
    destination.mkdir(parents=True)
    for kind,path in paths.items():
        target=destination/path.relative_to(client);target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(modified[kind])
    (destination/'prepared.json').write_text(json.dumps(manifest,indent=2)+'\n')
    return manifest


def verified_state(client):
    manifest=json.loads(manifest_path(client).read_text())
    paths=artifact_paths(client)
    if manifest.get('scope')!=SCOPE or manifest.get('revision',1) not in (1,2) or set(manifest.get('artifacts',{}))!=set(paths):raise ValueError('Unknown shield-loop manifest')
    originals={}
    for kind,path in paths.items():
        record=manifest['artifacts'][kind];raw=backups(path).read_bytes();check(raw,input_kind(kind))
        if record['original_sha256']!=INPUT_HASH[input_kind(kind)]:raise ValueError('Manifest input fingerprint differs')
        if digest(path.read_bytes()) not in (record['original_sha256'],record['modified_sha256']):
            raise ValueError('Current '+kind+' fingerprint differs')
        originals[kind]=raw
    return manifest,originals


def apply(client):
    if native_client_running():raise RuntimeError('Close DarkOrbit before changing shield artwork')
    paths=artifact_paths(client);captured={kind:path.read_bytes() for kind,path in paths.items()}
    if manifest_path(client).exists():
        manifest,originals=verified_state(client)
        if manifest.get('revision',1)==2 and all(digest(captured[kind])==record['modified_sha256'] for kind,record in manifest['artifacts'].items()):return manifest
    else:
        originals=captured
    modified=build_artifacts(originals);manifest=describe(originals,modified)
    for kind,path in paths.items():
        backup=backups(path)
        if backup.exists():
            if backup.read_bytes()!=originals[kind]:raise ValueError('Existing '+kind+' backup differs')
        else:
            with backup.open('xb') as stream:stream.write(originals[kind])
    atomic_write(manifest_path(client),(json.dumps(manifest,indent=2)+'\n').encode())
    for kind,path in paths.items():
        if native_client_running():raise RuntimeError('Close DarkOrbit before changing shield artwork')
        if path.read_bytes()!=captured[kind]:raise ValueError('Artifact changed during operation: '+kind)
        atomic_write(path,modified[kind])
    return manifest


def restore(client):
    if native_client_running():raise RuntimeError('Close DarkOrbit before restoring shield artwork')
    paths=artifact_paths(client);captured={kind:path.read_bytes() for kind,path in paths.items()}
    if all(digest(raw)==INPUT_HASH[input_kind(kind)] for kind,raw in captured.items()):return dict(status='original',scope=SCOPE)
    manifest,originals=verified_state(client)
    for kind,path in reversed(list(paths.items())):
        if native_client_running():raise RuntimeError('Close DarkOrbit before restoring shield artwork')
        if path.read_bytes()!=captured[kind]:raise ValueError('Artifact changed during restore: '+kind)
        atomic_write(path,originals[kind])
    return dict(status='restored',scope=SCOPE)


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('client',type=Path)
    group=parser.add_mutually_exclusive_group();group.add_argument('--prepare',type=Path);group.add_argument('--apply',action='store_true');group.add_argument('--restore',action='store_true')
    args=parser.parse_args()
    if args.prepare:result=prepare(args.client,args.prepare)
    elif args.apply:result=apply(args.client)
    elif args.restore:result=restore(args.client)
    else:
        result=dict(read_only=True,scope=SCOPE,artifacts={kind:dict(path=str(path),current_sha256=digest(path.read_bytes()),
                    expected_sha256=INPUT_HASH[input_kind(kind)]) for kind,path in artifact_paths(args.client).items()})
    print(json.dumps(result,indent=2))


if __name__=='__main__':main()
