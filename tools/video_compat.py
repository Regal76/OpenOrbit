#!/usr/bin/env python3
"""Reuse verified VP8 previews or explicitly convert one Wine preview video.

Default operation only reports matches. --apply appends compatible media to the
selected bundle without replacing native IDs, aliases, alpha or audio metadata.
No client path is assumed. Requires UnityPy for bundle operations.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import re
import tempfile
from fractions import Fraction


CHANGED_FIELDS = {'m_Format', 'm_OriginalPath', 'm_ExternalResources'}


def sha(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()


def native_client_running():
    if os.name == 'nt':
        commands = subprocess.check_output(['tasklist', '/FO', 'CSV', '/NH'], text=True)
        return any(line.split(',')[0].strip('"').casefold() == 'darkorbit.exe' for line in commands.splitlines())
    commands = subprocess.check_output(['ps', '-axo', 'comm='], text=True)
    return any(line.strip().replace('\\', '/').rsplit('/', 1)[-1].casefold() == 'darkorbit.exe' for line in commands.splitlines())


def videos(env):
    result = {}
    for obj in env.objects:
        if obj.type.name == 'VideoClip':
            name = obj.read().m_Name
            if name in result:
                raise ValueError('Ambiguous video name: ' + name)
            result[name] = obj
    return result


def payload(obj):
    from UnityPy.helpers.ResourceReader import get_resource_data
    data = obj.read()
    resource = data.m_ExternalResources
    if resource.m_Offset < 0 or resource.m_Size <= 0:
        raise ValueError('Invalid video resource bounds')
    raw = get_resource_data(resource.m_Source, data.object_reader.assets_file, resource.m_Offset, resource.m_Size)
    if len(raw) != resource.m_Size:
        raise ValueError('Truncated video resource')
    return raw


def metadata(obj):
    return {key: value for key, value in obj.read_typetree().items() if key not in CHANGED_FIELDS}


def validate_webm(raw, audio):
    # Container/codec identifiers reject wrong inputs. Native playback, rather
    # than these checks, establishes decoder and graphics interoperability.
    if not isinstance(raw, bytes) or not raw.startswith(b'\x1aE\xdf\xa3') or b'webm' not in raw[:128] or b'V_VP8' not in raw[:16384]:
        raise ValueError('Expected VP8 WebM payload')
    if audio and b'A_VORBIS' not in raw[:16384]:
        raise ValueError('Audio-bearing preview requires a Vorbis payload')


def select_reusable(current, source_original, source_compatible, names=None):
    """Return payloads only when original bytes and every retained field agree."""
    targets, originals, compatible = videos(current), videos(source_original), videos(source_compatible)
    selected = sorted(targets) if names is None else list(dict.fromkeys(names))
    result = {}
    report = {'matched': [], 'already_compatible': [], 'unmatched': {}}
    for name in selected:
        if name not in targets:
            report['unmatched'][name] = 'Current clip is absent'
            continue
        target = targets[name]
        data = target.read()
        if data.m_Format == 4 and data.m_OriginalPath.endswith('.webm'):
            try:
                validate_webm(payload(target), data.m_AudioChannelCount)
            except ValueError as error:
                report['unmatched'][name] = str(error)
            else:
                report['already_compatible'].append(name)
            continue
        if data.m_Format != 1 or not data.m_OriginalPath.endswith('.m4v'):
            report['unmatched'][name] = 'Unsupported current import format'
            continue
        if name not in originals or name not in compatible:
            report['unmatched'][name] = 'Reference clip is absent; conversion required'
            continue
        original, converted = originals[name], compatible[name]
        old, new = original.read(), converted.read()
        if old.m_Format != 1 or old.m_OriginalPath != data.m_OriginalPath or new.m_Format != 4 or new.m_OriginalPath != old.m_OriginalPath[:-4] + '.webm':
            report['unmatched'][name] = 'Reference import format/path differs'
            continue
        if metadata(target) != metadata(original) or metadata(original) != metadata(converted):
            report['unmatched'][name] = 'Clip metadata differs; conversion required'
            continue
        if hashlib.sha256(payload(target)).digest() != hashlib.sha256(payload(original)).digest():
            report['unmatched'][name] = 'Original source SHA256 differs; conversion required'
            continue
        raw = payload(converted)
        try:
            validate_webm(raw, data.m_AudioChannelCount)
        except ValueError as error:
            report['unmatched'][name] = str(error)
            continue
        result[name] = raw
        report['matched'].append(name)
    return result, report


def patch_environment(env, payloads):
    """Preflight every change, then append media and update only import pointers."""
    from UnityPy.streams import EndianBinaryReader
    targets = videos(env)
    changes = []
    for name, raw in payloads.items():
        if name not in targets:
            raise ValueError('Unknown video target: ' + name)
        obj = targets[name]
        data = obj.read()
        validate_webm(raw, data.m_AudioChannelCount)
        if data.m_Format == 4 and data.m_OriginalPath.endswith('.webm'):
            if payload(obj) != raw:
                raise ValueError('Compatible video differs: ' + name)
            continue
        if data.m_Format != 1 or not data.m_OriginalPath.endswith('.m4v'):
            raise ValueError('Unrecognized video import format: ' + name)
        resource = data.m_ExternalResources
        key = resource.m_Source.rsplit('/', 1)[-1]
        if key not in env.file.files:
            raise ValueError('Embedded video resource missing')
        if resource.m_Offset < 0 or resource.m_Size <= 0 or resource.m_Offset + resource.m_Size > len(env.file.files[key].bytes):
            raise ValueError('Invalid original video resource bounds')
        changes.append((name, data, key, raw))
    resources = {}
    for name, data, key, raw in changes:
        if key not in resources:
            resources[key] = bytearray(env.file.files[key].bytes)
        resource = data.m_ExternalResources
        resource.m_Offset = len(resources[key])
        resource.m_Size = len(raw)
        data.m_OriginalPath = data.m_OriginalPath[:-4] + '.webm'
        data.m_Format = 4
        data.save()
        resources[key].extend(raw)
    for key, raw in resources.items():
        replacement = EndianBinaryReader(bytes(raw))
        replacement.flags = env.file.files[key].flags
        env.file.files[key] = replacement
    return [change[0] for change in changes]


def backup_paths(bundle):
    return Path(str(bundle) + '.vp8.original'), Path(str(bundle) + '.vp8.json')


def read_record(bundle):
    backup, manifest = backup_paths(bundle)
    pending = Path(str(manifest) + '.pending')
    if pending.exists():
        transaction = json.loads(pending.read_text())
        proposed = transaction['record']
        current = sha(bundle)
        if (not backup.exists() or sha(backup) != proposed['original_sha256'] or
                current not in (transaction['before_sha256'], proposed['sha256'])):
            raise ValueError('Video bundle/backup changed during pending transaction; refusing overwrite')
        recovered = proposed if current == proposed['sha256'] else transaction['previous_record']
        if recovered is None:
            recovered = {'sha256': current, 'original_sha256': proposed['original_sha256'], 'clips': []}
        temporary = Path(str(manifest) + '.tmp')
        temporary.write_text(json.dumps(recovered, indent=2))
        os.replace(temporary, manifest)
        pending.unlink()
    if manifest.exists():
        record = json.loads(manifest.read_text())
        if not backup.exists() or sha(bundle) != record['sha256'] or sha(backup) != record['original_sha256']:
            raise ValueError('Video bundle/backup changed; refusing overwrite')
        return record
    if backup.exists():
        raise ValueError('Untracked backup; refusing overwrite')
    return None


def commit_prepared(bundle, temporary, manifest_tmp, record, before, changes, provenance):
    """Keep enough hashed state to finish a manifest after either replace fails."""
    backup, manifest = backup_paths(bundle)
    pending = Path(str(manifest) + '.pending')
    if sha(bundle) != before:
        raise ValueError('Video bundle changed while preparing patch')
    if native_client_running():
        raise ValueError('Close DarkOrbit.exe before changing video assets')
    previous = record
    record = dict(record or {'original_sha256': before, 'clips': []})
    record['clips'] = sorted(set(record['clips']) | set(changes))
    record['sha256'] = sha(temporary)
    record.update(provenance)
    manifest_tmp.write_text(json.dumps(record, indent=2))
    if previous is None:
        shutil.copy2(bundle, backup)
    with pending.open('x') as stream:
        json.dump({'before_sha256': before, 'previous_record': previous, 'record': record}, stream, indent=2)
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(temporary, bundle)
    os.replace(manifest_tmp, manifest)
    pending.unlink()
    return record


def inspect_media(path, ffmpeg):
    """Decode every frame and audio stream using the explicitly chosen binary."""
    process = subprocess.run([str(ffmpeg), '-hide_banner', '-nostdin', '-nostats', '-v', 'info', '-i', str(path),
                              '-map', '0:v:0', '-vf', 'showinfo', '-map', '0:a?', '-f', 'null', '-'],
                             capture_output=True, text=True)
    if process.returncode:
        raise ValueError('Video decoding failed: ' + process.stderr[-2000:])
    information = process.stderr.split('Stream mapping:')[0]
    codec = re.search(r'Video:\s*([^,\s(]+)', information)
    rate = re.search(r'config in time_base:.*?frame_rate:\s*(\d+/\d+)', process.stderr)
    frames = re.findall(r'\bn:\s*(\d+)\s+pts:.*?\bs:(\d+)x(\d+)\b', process.stderr)
    if not codec or not rate or not frames or len({(w, h) for _, w, h in frames}) != 1:
        raise ValueError('Cannot establish constant encoded dimensions, rate and decoded frame count')
    frequency = Fraction(rate.group(1))
    if frequency <= 0:
        raise ValueError('Invalid frame rate')
    audio = [{'codec': c.split()[0], 'sample_rate': int(hz), 'layout': layout.strip()}
             for c, hz, layout in re.findall(r'Stream #0:\d+[^\n]*?: Audio: ([^,]+), (\d+) Hz, ([^,\n]+)', information)]
    return {'codec': codec.group(1), 'width': int(frames[0][1]), 'height': int(frames[0][2]), 'frames': len(frames),
            'frame_rate': '%d/%d' % (frequency.numerator, frequency.denominator), 'audio': audio}


def convert_one(env, name, ffmpeg):
    """Convert encoded pixels as stored, including a packed split-alpha plane."""
    targets = videos(env)
    if name not in targets:
        raise ValueError('Unknown video target: ' + name)
    target = targets[name]
    data = target.read()
    if data.m_Format != 1 or not data.m_OriginalPath.endswith('.m4v'):
        raise ValueError('Fresh conversion requires an H264 imported clip: ' + name)
    source = payload(target)
    with tempfile.TemporaryDirectory(prefix='openorbit-video-') as folder:
        original, converted = Path(folder) / 'original.m4v', Path(folder) / 'converted.webm'
        original.write_bytes(source)
        before = inspect_media(original, ffmpeg)
        if (before['codec'] != 'h264' or before['frames'] != data.m_FrameCount or
                abs(float(Fraction(before['frame_rate'])) - data.m_FrameRate) > 0.000001 or
                len(before['audio']) != len(data.m_AudioChannelCount)):
            raise ValueError('Decoded source differs from clip frame/audio metadata')
        process = subprocess.run([str(ffmpeg), '-hide_banner', '-nostdin', '-nostats', '-v', 'error', '-i', str(original),
                                  '-map', '0:v:0', '-map', '0:a?', '-c:v', 'libvpx', '-pix_fmt', 'yuv420p',
                                  '-crf', '10', '-b:v', '0', '-deadline', 'good', '-cpu-used', '2',
                                  '-c:a', 'libvorbis', '-q:a', '5', '-fps_mode', 'passthrough', str(converted)],
                                 capture_output=True, text=True)
        if process.returncode:
            raise ValueError('VP8 conversion failed: ' + process.stderr[-2000:])
        raw = converted.read_bytes()
        validate_webm(raw, data.m_AudioChannelCount)
        after = inspect_media(converted, ffmpeg)
    if after['codec'] != 'vp8' or any(before[key] != after[key] for key in ('width', 'height', 'frames', 'frame_rate')):
        raise ValueError('Converted dimensions, frame rate or decoded frame count changed')
    if (len(before['audio']) != len(after['audio']) or
            any(new['codec'] != 'vorbis' or old['sample_rate'] != new['sample_rate'] or old['layout'] != new['layout']
                for old, new in zip(before['audio'], after['audio']))):
        raise ValueError('Converted audio streams differ from source')
    return raw, {'source_sha256': hashlib.sha256(source).hexdigest(), 'payload_sha256': hashlib.sha256(raw).hexdigest(),
                 'source': before, 'converted': after}


def convert_clip(bundle, name, ffmpeg, apply_change=False):
    import UnityPy
    bundle = Path(bundle)
    if apply_change and native_client_running():
        raise ValueError('Close DarkOrbit.exe before changing video assets')
    record = read_record(bundle) if apply_change else None
    before = sha(bundle)
    env = UnityPy.load(str(bundle))
    target = videos(env).get(name)
    if target is not None and target.read().m_Format == 4:
        validate_webm(payload(target), target.read().m_AudioChannelCount)
        return {'status': 'unchanged', 'already_compatible': [name], 'sha256': before}
    raw, conversion = convert_one(env, name, ffmpeg)
    if not apply_change:
        return {'status': 'report_only', 'clip': name, **conversion}
    changes = patch_environment(env, {name: raw})
    backup, manifest = backup_paths(bundle)
    temporary, manifest_tmp = Path(str(bundle) + '.vp8.tmp'), Path(str(manifest) + '.tmp')
    if temporary.exists() or manifest_tmp.exists():
        raise ValueError('Temporary video patch file already exists')
    try:
        temporary.write_bytes(env.file.save(packer='original'))
        checked = videos(UnityPy.load(str(temporary)))[name]
        if checked.read().m_Format != 4 or metadata(checked) != metadata(target) or payload(checked) != raw:
            raise ValueError('Saved preview verification failed: ' + name)
        conversions = dict((record or {}).get('conversions', {}))
        conversions[name] = conversion
        record = commit_prepared(bundle, temporary, manifest_tmp, record, before, changes, {'conversions': conversions})
    finally:
        temporary.unlink(missing_ok=True)
        manifest_tmp.unlink(missing_ok=True)
    return {'status': 'patched', 'backup': str(backup), 'manifest': str(manifest), **record}


def apply(bundle, source_original, source_compatible, names=None):
    if native_client_running():
        raise ValueError('Close DarkOrbit.exe before changing video assets')
    import UnityPy
    bundle, source_original, source_compatible = map(Path, (bundle, source_original, source_compatible))
    if bundle.resolve() in (source_original.resolve(), source_compatible.resolve()):
        raise ValueError('Target must differ from reference bundles')
    before = sha(bundle)
    record = read_record(bundle)
    env = UnityPy.load(str(bundle))
    payloads, report = select_reusable(env, UnityPy.load(str(source_original)), UnityPy.load(str(source_compatible)), names)
    changes = patch_environment(env, payloads)
    if not changes:
        return {'status': 'unchanged', 'sha256': before, **report}
    backup, manifest = backup_paths(bundle)
    temporary = Path(str(bundle) + '.vp8.tmp')
    manifest_tmp = Path(str(manifest) + '.tmp')
    if temporary.exists() or manifest_tmp.exists():
        raise ValueError('Temporary video patch file already exists')
    try:
        temporary.write_bytes(env.file.save(packer='original'))
        checked = videos(UnityPy.load(str(temporary)))
        prepared = videos(env)
        for name in changes:
            if checked[name].read().m_Format != 4 or metadata(checked[name]) != metadata(prepared[name]) or payload(checked[name]) != payloads[name]:
                raise ValueError('Saved preview verification failed: ' + name)
        record = commit_prepared(bundle, temporary, manifest_tmp, record, before, changes, {
            'reference_original_sha256': sha(source_original), 'reference_compatible_sha256': sha(source_compatible)})
    finally:
        temporary.unlink(missing_ok=True)
        manifest_tmp.unlink(missing_ok=True)
    return {'status': 'patched', 'backup': str(backup), 'manifest': str(manifest), **record, **report}


def restore(bundle):
    if native_client_running():
        raise ValueError('Close DarkOrbit.exe before changing video assets')
    bundle = Path(bundle)
    backup, manifest = backup_paths(bundle)
    temporary = Path(str(bundle) + '.restore.tmp')
    journal = Path(str(bundle) + '.restore.pending')
    if journal.exists():
        record = json.loads(journal.read_text())
    else:
        record = read_record(bundle)
        if record is None:
            raise ValueError('No video compatibility backup')
        if temporary.exists():
            raise ValueError('Temporary restore file already exists')
        with journal.open('x') as stream:
            json.dump(record, stream, indent=2)
            stream.flush()
            os.fsync(stream.fileno())
    current = sha(bundle)
    original = record['original_sha256']
    if (current not in (record['sha256'], original) or
            (backup.exists() and sha(backup) != original) or
            (not backup.exists() and current != original)):
        raise ValueError('Video bundle/backup changed during restore; refusing overwrite')
    if manifest.exists() and json.loads(manifest.read_text()) != record:
        raise ValueError('Video manifest changed during restore; refusing overwrite')
    try:
        if current != original:
            shutil.copy2(backup, temporary)
            os.replace(temporary, bundle)
        manifest.unlink(missing_ok=True)
        backup.unlink(missing_ok=True)
        journal.unlink()
    finally:
        temporary.unlink(missing_ok=True)
    return {'status': 'restored', 'sha256': sha(bundle)}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--bundle', type=Path, required=True)
    parser.add_argument('--source-original', type=Path)
    parser.add_argument('--source-compatible', type=Path)
    selection = parser.add_mutually_exclusive_group()
    selection.add_argument('--clip', action='append')
    selection.add_argument('--all-matching', action='store_true')
    selection.add_argument('--convert-clip')
    parser.add_argument('--ffmpeg', type=Path)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument('--apply', action='store_true')
    mode.add_argument('--restore', action='store_true')
    args = parser.parse_args(argv)
    if args.restore:
        result = restore(args.bundle)
    elif args.convert_clip:
        if not args.ffmpeg or not args.ffmpeg.is_file() or not os.access(args.ffmpeg, os.X_OK):
            parser.error('--convert-clip requires an explicit executable --ffmpeg')
        result = convert_clip(args.bundle, args.convert_clip, args.ffmpeg, args.apply)
    else:
        if not args.source_original or not args.source_compatible or not (args.clip or args.all_matching):
            parser.error('--source-original, --source-compatible and --clip/--all-matching are required')
        if args.apply:
            result = apply(args.bundle, args.source_original, args.source_compatible, args.clip)
        else:
            import UnityPy
            _, result = select_reusable(UnityPy.load(str(args.bundle)), UnityPy.load(str(args.source_original)), UnityPy.load(str(args.source_compatible)), args.clip)
            result = {'status': 'report_only', **result}
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
