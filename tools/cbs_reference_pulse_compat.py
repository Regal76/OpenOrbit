#!/usr/bin/env python3
"""Prepare a CBS-only static-artwork, six-second breathing candidate.

Defaults to read-only. Apply/restore write only the selected effect bundle.
It never changes native DLLs, catalogs or profiles.
Amplitude .5–1 is a visually plausible candidate; footage establishes cadence
and static geometry, but does not uniquely recover absolute alpha/background.
"""
import argparse
import hashlib
import json
from pathlib import Path

INPUT_SHA256='c79f59e6436b2a973b1a32c352d5a9463f331ca81bf0c99146e4613a8b30103d'
CBS_CLIP_ID=9208249630577230910
CBS_RENDERER_ID=9208249630577230917
SOURCE_SPRITE_ID=4267730706580210684


def digest(raw):return hashlib.sha256(raw).hexdigest()


def alpha_at(real_seconds):
    """Three seconds down then three up, quadratic ease-out each half."""
    phase=real_seconds%6
    if phase<3:return .5+.5*(1-phase/3)**2
    return 1-.5*(1-(phase-3)/3)**2


def patch_bundle(raw):
    if digest(raw)!=INPUT_SHA256:raise ValueError('Unsupported input fingerprint')
    import UnityPy
    env=UnityPy.load(raw);objects={o.path_id:o for o in env.objects}
    clip=objects[CBS_CLIP_ID].read_typetree()
    if clip['m_Name']!='cbsShieldSmooth_2D' or len(clip['m_ClipBindingConstant']['pptrCurveMapping'])!=64:
        raise ValueError('Expected isolated CBS smooth clone')
    old=clip['m_MuscleClip']['m_Clip']['data'];old_stream_bytes=4*len(old['m_StreamedClip']['data'])
    old_dense_bytes=4*len(old['m_DenseClip']['m_SampleArray'])
    clip['m_SampleRate']=60.
    # Unity's own protection clip has the identical SpriteRenderer alpha binding:
    # typeID212, customType0, attribute CRC32("m_Color.a")=304273561.
    clip['m_ClipBindingConstant']={
        'genericBindings':[dict(path=0,attribute=304273561,script=dict(m_FileID=0,m_PathID=0),
            typeID=212,customType=0,isPPtrCurve=0,isIntCurve=0,isSerializeReferenceCurve=0)],
        'pptrCurveMapping':[]}
    old['m_StreamedClip']=dict(data=[4286578687,0,2139095040,0],curveCount=0,discreteCurveCount=0)
    # Existing CBS Animator speed=.5. Three simulation seconds are six wall
    # seconds. Dense float curves interpolate per rendered frame; no flipbook.
    samples=[alpha_at(min(i/60,3)*2) for i in range(182)]
    old['m_DenseClip']=dict(m_FrameCount=182,m_CurveCount=1,m_SampleRate=60.,m_BeginTime=0.,m_SampleArray=samples)
    old['m_ConstantClip']={'data':[]}
    clip['m_MuscleClipSize']+=16-old_stream_bytes+4*len(samples)-old_dense_bytes
    clip['m_MuscleClip']['m_StopTime']=3.
    clip['m_MuscleClip']['m_ValueArrayDelta']=[dict(m_Start=1.,m_Stop=1.)]
    objects[CBS_CLIP_ID].save_typetree(clip)
    renderer=objects[CBS_RENDERER_ID].read_typetree()
    renderer['m_Sprite']=dict(m_FileID=0,m_PathID=SOURCE_SPRITE_ID)
    objects[CBS_RENDERER_ID].save_typetree(renderer)
    return env.file.save(packer='original')


def prepare(bundle,destination):
    bundle=Path(bundle);destination=Path(destination)
    if destination.exists():raise ValueError('Destination must be new')
    original=bundle.read_bytes();modified=patch_bundle(original)
    manifest=dict(scope='CBS-only fixed shipped sprite zero and six-second opacity breathing',
        status='candidate-requires-native-QA',input_sha256=digest(original),output_sha256=digest(modified),
        changed_objects=[CBS_CLIP_ID,CBS_RENDERER_ID],real_period_seconds=6.,alpha_range=[.5,1.],
        amplitude='provisional; absolute opacity cannot be uniquely recovered from composited reference',
        native_changed=False,catalog_changed=False,profile_changed=False)
    destination.mkdir(parents=True)
    (destination/bundle.name).write_bytes(modified)
    (destination/'original.bundle').write_bytes(original)
    (destination/'prepared.json').write_text(json.dumps(manifest,indent=2)+'\n')
    return manifest


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


def backup_path(bundle):return Path(str(bundle)+'.cbs-reference-pulse.original')
def manifest_path(bundle):return Path(str(bundle)+'.cbs-reference-pulse.json')


def original_and_manifest(bundle,current):
    manifest=json.loads(manifest_path(bundle).read_text())
    original=backup_path(bundle).read_bytes()
    if digest(original)!=INPUT_SHA256 or manifest.get('input_sha256')!=INPUT_SHA256:
        raise ValueError('Original backup fingerprint differs')
    expected=digest(patch_bundle(original))
    if manifest.get('output_sha256')!=expected or digest(current) not in (INPUT_SHA256,expected):
        raise ValueError('Current bundle or manifest fingerprint differs')
    return original,manifest


def apply(bundle):
    if native_client_running():raise RuntimeError('Close DarkOrbit before changing CBS pulse')
    bundle=Path(bundle);captured=bundle.read_bytes()
    if manifest_path(bundle).exists():
        original,manifest=original_and_manifest(bundle,captured)
        if digest(captured)==manifest['output_sha256']:return manifest
    else:
        original=captured
    modified=patch_bundle(original)
    manifest=dict(scope='CBS reference pulse',revision=1,input_sha256=digest(original),output_sha256=digest(modified))
    backup=backup_path(bundle)
    if backup.exists():
        if backup.read_bytes()!=original:raise ValueError('Existing backup fingerprint differs')
    else:
        with backup.open('xb') as stream:stream.write(original)
    atomic_write(manifest_path(bundle),(json.dumps(manifest,indent=2)+'\n').encode())
    if native_client_running():raise RuntimeError('Close DarkOrbit before changing CBS pulse')
    if bundle.read_bytes()!=captured:raise ValueError('Bundle fingerprint changed during apply')
    atomic_write(bundle,modified)
    return manifest


def restore(bundle):
    if native_client_running():raise RuntimeError('Close DarkOrbit before restoring CBS pulse')
    bundle=Path(bundle);captured=bundle.read_bytes()
    if digest(captured)==INPUT_SHA256:return dict(status='original')
    original,manifest=original_and_manifest(bundle,captured)
    if native_client_running():raise RuntimeError('Close DarkOrbit before restoring CBS pulse')
    if bundle.read_bytes()!=captured:raise ValueError('Bundle fingerprint changed during restore')
    atomic_write(bundle,original)
    return dict(status='restored')


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('bundle',type=Path)
    group=p.add_mutually_exclusive_group();group.add_argument('--prepare',type=Path)
    group.add_argument('--apply',action='store_true');group.add_argument('--restore',action='store_true')
    a=p.parse_args()
    if a.prepare:result=prepare(a.bundle,a.prepare)
    elif a.apply:result=apply(a.bundle)
    elif a.restore:result=restore(a.bundle)
    else:result=dict(read_only=True,current_sha256=digest(a.bundle.read_bytes()),supported_sha256=INPUT_SHA256)
    print(json.dumps(result,indent=2))

if __name__=='__main__':main()
