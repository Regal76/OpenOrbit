"""Serialization safeguards using optional real, locally installed media fixtures.

Set VIDEO_COMPAT_SOURCE_ORIGINAL and VIDEO_COMPAT_SOURCE_COMPATIBLE to the
previous conversion's original and compatible bundles. VIDEO_COMPAT_TARGET can
select an explicit baseline; otherwise prefer the installed original backup.
No media is committed.
These tests check source identity and serialization, not native playback.
"""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from types import SimpleNamespace
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
INSTALLED_BUNDLE = ROOT / 'DarkOrbit_Version1.1.115/DarkOrbit_Data/StreamingAssets/aa/BuildTarget/video_assets_all.bundle'
INSTALLED_ORIGINAL = Path(str(INSTALLED_BUNDLE) + '.vp8.original')
BUNDLE = Path(os.environ['VIDEO_COMPAT_TARGET']) if 'VIDEO_COMPAT_TARGET' in os.environ else (
    INSTALLED_ORIGINAL if INSTALLED_ORIGINAL.exists() else INSTALLED_BUNDLE)
ORIGINAL = Path(os.environ.get('VIDEO_COMPAT_SOURCE_ORIGINAL', '/nonexistent/video-original'))
COMPATIBLE = Path(os.environ.get('VIDEO_COMPAT_SOURCE_COMPATIBLE', '/nonexistent/video-compatible'))
AVAILABLE = BUNDLE.exists() and ORIGINAL.exists() and COMPATIBLE.exists() and importlib.util.find_spec('UnityPy') is not None
FFMPEG = Path(os.environ.get('VIDEO_COMPAT_FFMPEG') or shutil.which('ffmpeg') or '/nonexistent/ffmpeg')


def tool():
    path = ROOT / 'tools/video_compat.py'
    if not path.exists():
        return None
    spec = importlib.util.spec_from_file_location('video_compat_under_test', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class VideoCompatibilityCLI(unittest.TestCase):
    def test_fresh_conversion_does_not_require_reference_bundles(self):
        result = subprocess.run([sys.executable, str(ROOT / 'tools/video_compat.py'), '--bundle', '/absent/video.bundle',
                                 '--convert-clip', 'pet-a-elite-dusklight', '--ffmpeg', str(FFMPEG)], capture_output=True, text=True)
        self.assertNotIn('unrecognized arguments', result.stderr)
        self.assertNotIn('--source-original, --source-compatible', result.stderr)
        self.assertNotEqual(result.returncode, 0)

    def test_tool_requires_an_explicit_bundle(self):
        self.assertTrue((ROOT / 'tools/video_compat.py').exists(), 'Missing reversible video compatibility tool')
        result = subprocess.run([sys.executable, str(ROOT / 'tools/video_compat.py'), '--restore'], capture_output=True, text=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('--bundle', result.stderr)

    def test_restore_refuses_changed_bundle_and_round_trips_exact_bytes(self):
        v = tool()
        self.assertIsNotNone(v, 'Missing reversible video compatibility tool')
        import json
        with tempfile.TemporaryDirectory() as folder, patch.object(v, 'native_client_running', return_value=False):
            bundle = Path(folder) / 'video.bundle'
            backup = Path(str(bundle) + '.vp8.original')
            manifest = Path(str(bundle) + '.vp8.json')
            bundle.write_bytes(b'patched bundle')
            backup.write_bytes(b'original bundle')
            record = {'sha256': v.sha(bundle), 'original_sha256': v.sha(backup)}
            manifest.write_text(json.dumps(record))
            bundle.write_bytes(b'external change')
            with self.assertRaisesRegex(ValueError, 'changed'):
                v.restore(bundle)
            self.assertEqual(bundle.read_bytes(), b'external change')
            self.assertTrue(backup.exists())
            bundle.write_bytes(b'patched bundle')
            v.restore(bundle)
            self.assertEqual(bundle.read_bytes(), b'original bundle')
            self.assertFalse(backup.exists())
            self.assertFalse(manifest.exists())

    def test_restore_retry_recovers_from_manifest_or_backup_unlink_failure(self):
        v = tool()
        for failing_file in ('manifest', 'backup'):
            with self.subTest(failing_file=failing_file), tempfile.TemporaryDirectory() as folder, patch.object(v, 'native_client_running', return_value=False):
                bundle = Path(folder) / 'video.bundle'
                backup, manifest = v.backup_paths(bundle)
                bundle.write_bytes(b'patched bundle')
                backup.write_bytes(b'original bundle')
                manifest.write_text(json.dumps({'sha256': v.sha(bundle), 'original_sha256': v.sha(backup)}))
                failing_path = manifest if failing_file == 'manifest' else backup
                real_unlink = Path.unlink

                def fail_unlink(path, *args, **kwargs):
                    if path == failing_path:
                        raise OSError('Injected unlink failure')
                    return real_unlink(path, *args, **kwargs)

                with patch.object(Path, 'unlink', fail_unlink):
                    with self.assertRaisesRegex(OSError, 'unlink failure'):
                        v.restore(bundle)
                self.assertEqual(bundle.read_bytes(), b'original bundle')
                self.assertEqual(backup.read_bytes(), b'original bundle')
                try:
                    result = v.restore(bundle)
                except ValueError as error:
                    self.fail('Restore retry must recover its cleanup: ' + str(error))
                self.assertEqual(result['status'], 'restored')
                self.assertEqual(bundle.read_bytes(), b'original bundle')
                self.assertFalse(backup.exists())
                self.assertFalse(manifest.exists())
                self.assertEqual(list(Path(folder).iterdir()), [bundle])

    def test_restore_retry_refuses_external_edits_after_partial_cleanup(self):
        v = tool()
        for changed_file in ('bundle', 'backup', 'manifest'):
            with self.subTest(changed_file=changed_file), tempfile.TemporaryDirectory() as folder, patch.object(v, 'native_client_running', return_value=False):
                bundle = Path(folder) / 'video.bundle'
                backup, manifest = v.backup_paths(bundle)
                bundle.write_bytes(b'patched bundle')
                backup.write_bytes(b'original bundle')
                manifest.write_text(json.dumps({'sha256': v.sha(bundle), 'original_sha256': v.sha(backup)}))
                real_unlink = Path.unlink

                def fail_manifest(path, *args, **kwargs):
                    if path == manifest:
                        raise OSError('Injected cleanup failure')
                    return real_unlink(path, *args, **kwargs)

                with patch.object(Path, 'unlink', fail_manifest):
                    with self.assertRaisesRegex(OSError, 'cleanup failure'):
                        v.restore(bundle)
                changed = {'bundle': bundle, 'backup': backup, 'manifest': manifest}[changed_file]
                changed.write_text('{"external": "edit"}')
                before = {path.name: path.read_bytes() for path in Path(folder).iterdir()}
                with self.assertRaisesRegex(ValueError, 'changed'):
                    v.restore(bundle)
                self.assertEqual({path.name: path.read_bytes() for path in Path(folder).iterdir()}, before)

    def test_apply_refuses_a_running_client_before_reading_bundle(self):
        v = tool()
        self.assertIsNotNone(v, 'Missing reversible video compatibility tool')
        with patch.object(v, 'native_client_running', return_value=True):
            with self.assertRaisesRegex(ValueError, 'Close DarkOrbit'):
                v.apply(Path('/absent/current'), Path('/absent/original'), Path('/absent/compatible'), ['berserker-phantasm'])

    def test_pending_transaction_refuses_external_bundle_changes(self):
        v = tool()
        with tempfile.TemporaryDirectory() as folder, patch.object(v, 'native_client_running', return_value=False):
            bundle = Path(folder) / 'video.bundle'
            backup, manifest = v.backup_paths(bundle)
            backup.write_bytes(b'original')
            bundle.write_bytes(b'prepared')
            proposed = {'sha256': v.sha(bundle), 'original_sha256': v.sha(backup), 'clips': ['fixture']}
            pending = Path(str(manifest) + '.pending')
            pending.write_text(json.dumps({'before_sha256': v.sha(backup), 'previous_record': None, 'record': proposed}))
            bundle.write_bytes(b'unrelated external edit')
            with self.assertRaisesRegex(ValueError, 'changed'):
                v.restore(bundle)
            self.assertEqual(bundle.read_bytes(), b'unrelated external edit')
            self.assertEqual(backup.read_bytes(), b'original')
            self.assertTrue(pending.exists())


@unittest.skipUnless(FFMPEG.exists(), 'Set VIDEO_COMPAT_FFMPEG to an explicit encoder')
class FreshConversionAudio(unittest.TestCase):
    def test_all_audio_streams_survive_conversion_as_vorbis(self):
        v = tool()
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder) / 'source.m4v'
            subprocess.run([str(FFMPEG), '-hide_banner', '-nostdin', '-v', 'error',
                            '-f', 'lavfi', '-i', 'testsrc2=size=64x32:rate=12',
                            '-f', 'lavfi', '-i', 'sine=frequency=440:sample_rate=44100',
                            '-f', 'lavfi', '-i', 'sine=frequency=880:sample_rate=44100',
                            '-t', '0.5', '-map', '0:v:0', '-map', '1:a:0', '-map', '2:a:0',
                            '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-f', 'matroska', str(source)],
                           check=True, capture_output=True)
            data = SimpleNamespace(m_Name='fixture', m_Format=1, m_OriginalPath='fixture.m4v',
                                   m_FrameCount=6, m_FrameRate=12.0, m_AudioChannelCount=[1, 1],
                                   m_AudioSampleRate=[44100, 44100], m_HasSplitAlpha=True, Width=80, Height=48)
            env = SimpleNamespace(objects=[SimpleNamespace(type=SimpleNamespace(name='VideoClip'), read=lambda: data)])
            # Replace only the bundle resource read; real FFmpeg encodes and decodes all media.
            with patch.object(v, 'payload', return_value=source.read_bytes()):
                raw, report = v.convert_one(env, 'fixture', FFMPEG)
            self.assertEqual([row['codec'] for row in report['source']['audio']], ['aac', 'aac'])
            self.assertEqual([row['codec'] for row in report['converted']['audio']], ['vorbis', 'vorbis'])
            self.assertEqual([row['sample_rate'] for row in report['converted']['audio']], [44100, 44100])
            self.assertEqual((report['converted']['width'], report['converted']['height']), (64, 32))
            self.assertEqual(report['converted']['frames'], 6)
            self.assertEqual(report['converted']['frame_rate'], '12/1')
            self.assertTrue(data.m_HasSplitAlpha)
            self.assertEqual((data.Width, data.Height), (80, 48))
            self.assertIn(b'V_VP8', raw[:16384])


@unittest.skipUnless(AVAILABLE, 'Set video compatibility reference fixture environment variables')
class RealVideoCompatibility(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import UnityPy
        cls.UnityPy = UnityPy
        cls.v = tool()
        cls.current_bytes = BUNDLE.read_bytes()
        cls.original = UnityPy.load(str(ORIGINAL))
        cls.compatible = UnityPy.load(str(COMPATIBLE))

    def setUp(self):
        self.assertIsNotNone(self.v, 'Missing reversible video compatibility tool')
        self.env = self.UnityPy.load(self.current_bytes)

    def test_selected_clip_preserves_all_other_objects_resources_and_metadata(self):
        v = self.v
        payloads, report = v.select_reusable(self.env, self.original, self.compatible, ['berserker-phantasm'])
        self.assertEqual(report['matched'], ['berserker-phantasm'])
        self.assertEqual(report['unmatched'], {})
        self.assertEqual(hashlib.sha256(payloads['berserker-phantasm']).hexdigest(), 'c487239a7a1d15e8e865d446006b4d9c9565985d3006d9f85b8c43e4d74476f2')
        objects = {o.path_id: o.get_raw_data() for o in self.env.objects}
        target = v.videos(self.env)['berserker-phantasm']
        before = target.read_typetree()
        key = before['m_ExternalResources']['m_Source'].rsplit('/', 1)[-1]
        resources = {name: entry.bytes for name, entry in self.env.file.files.items() if name.endswith('.resource')}
        self.assertEqual(v.patch_environment(self.env, payloads), ['berserker-phantasm'])
        reloaded = self.UnityPy.load(self.env.file.save(packer='none'))
        after_obj = v.videos(reloaded)['berserker-phantasm']
        after = after_obj.read_typetree()
        self.assertEqual(target.path_id, after_obj.path_id)
        allowed = {'m_Format', 'm_OriginalPath', 'm_ExternalResources'}
        self.assertEqual({k: x for k, x in before.items() if k not in allowed}, {k: x for k, x in after.items() if k not in allowed})
        self.assertEqual(after['m_Format'], 4)
        self.assertTrue(after['m_OriginalPath'].endswith('.webm'))
        self.assertEqual(v.payload(after_obj), payloads['berserker-phantasm'])
        for name, raw in resources.items():
            self.assertEqual(reloaded.file.files[name].bytes, raw + payloads['berserker-phantasm'] if name == key else raw)
        for obj in reloaded.objects:
            if obj.path_id != target.path_id:
                self.assertEqual(obj.get_raw_data(), objects[obj.path_id], str(obj.path_id))
        self.assertEqual(v.patch_environment(reloaded, payloads), [])
        second, report = v.select_reusable(reloaded, self.original, self.compatible, ['berserker-phantasm'])
        self.assertEqual(second, {})
        self.assertEqual(report['already_compatible'], ['berserker-phantasm'])

    def test_mismatched_source_or_metadata_is_reported_without_mutation(self):
        target = self.v.videos(self.env)['berserker-phantasm']
        data = target.read()
        data.m_FrameCount += 1
        data.save()
        # UnityPy reads its original stream until the serialized bundle reloads.
        self.env = self.UnityPy.load(self.env.file.save(packer='none'))
        target = self.v.videos(self.env)['berserker-phantasm']
        before = {o.path_id: o.get_raw_data() for o in self.env.objects}
        payloads, report = self.v.select_reusable(self.env, self.original, self.compatible, ['berserker-phantasm'])
        self.assertEqual(payloads, {})
        self.assertIn('metadata', report['unmatched']['berserker-phantasm'])
        self.assertEqual({o.path_id: o.get_raw_data() for o in self.env.objects}, before)
        data = target.read()
        data.m_FrameCount -= 1
        data.m_ExternalResources.m_Size -= 1
        data.save()
        self.env = self.UnityPy.load(self.env.file.save(packer='none'))
        payloads, report = self.v.select_reusable(self.env, self.original, self.compatible, ['berserker-phantasm'])
        self.assertEqual(payloads, {})
        self.assertIn('source', report['unmatched']['berserker-phantasm'])

    def test_invalid_payload_or_unknown_clip_fails_before_any_mutation(self):
        payloads, _ = self.v.select_reusable(self.env, self.original, self.compatible, ['berserker-phantasm'])
        for bad in ({'missing': next(iter(payloads.values()))}, {'berserker-phantasm': b'not a media file'}, {**payloads, 'battle-repair-bot': b'bad'}):
            before = {o.path_id: o.get_raw_data() for o in self.env.objects}
            with self.assertRaises(ValueError):
                self.v.patch_environment(self.env, bad)
            self.assertEqual({o.path_id: o.get_raw_data() for o in self.env.objects}, before)

    def test_all_matching_retains_audio_metadata_and_reports_new_clips(self):
        payloads, report = self.v.select_reusable(self.env, self.original, self.compatible)
        self.assertIn('berserker-phantasm', payloads)
        self.assertGreater(len(payloads), 1500)
        targets = self.v.videos(self.env)
        audio = [name for name in payloads if targets[name].read().m_AudioChannelCount]
        self.assertTrue(audio)
        name = audio[0]
        before = self.v.videos(self.env)[name].read_typetree()
        self.v.patch_environment(self.env, {name: payloads[name]})
        self.env = self.UnityPy.load(self.env.file.save(packer='none'))
        after = self.v.videos(self.env)[name].read_typetree()
        for field in ('m_AudioChannelCount', 'm_AudioSampleRate', 'm_AudioLanguage', 'm_HasSplitAlpha'):
            self.assertEqual(after[field], before[field])
        self.assertIn(b'A_VORBIS', payloads[name][:16384])
        self.assertTrue(report['unmatched'], 'The current version has new clips absent from the old conversion')

    def test_temporary_bundle_apply_idempotence_and_exact_restore(self):
        with tempfile.TemporaryDirectory() as folder, patch.object(self.v, 'native_client_running', return_value=False):
            bundle = Path(folder) / 'video.bundle'
            bundle.write_bytes(self.current_bytes)
            original_hash = self.v.sha(bundle)
            result = self.v.apply(bundle, ORIGINAL, COMPATIBLE, ['berserker-phantasm'])
            self.assertEqual(result['status'], 'patched')
            self.assertEqual(result['clips'], ['berserker-phantasm'])
            backup = Path(result['backup'])
            self.assertEqual(self.v.sha(backup), original_hash)
            changed_hash = self.v.sha(bundle)
            self.assertNotEqual(changed_hash, original_hash)
            second = self.v.apply(bundle, ORIGINAL, COMPATIBLE, ['berserker-phantasm'])
            self.assertEqual(second['status'], 'unchanged')
            self.assertEqual(self.v.sha(bundle), changed_hash)
            self.v.restore(bundle)
            self.assertEqual(self.v.sha(bundle), original_hash)
            self.assertFalse(backup.exists())
            self.assertFalse(Path(result['manifest']).exists())

    def test_manifest_replace_failure_keeps_backup_recoverable_after_first_and_later_patches(self):
        for prior_patch in (False, True):
            with self.subTest(prior_patch=prior_patch), tempfile.TemporaryDirectory() as folder, patch.object(self.v, 'native_client_running', return_value=False):
                bundle = Path(folder) / 'video.bundle'
                bundle.write_bytes(self.current_bytes)
                original_hash = self.v.sha(bundle)
                if prior_patch:
                    self.v.apply(bundle, ORIGINAL, COMPATIBLE, ['berserker-phantasm'])
                real_replace = os.replace
                calls = []

                def fail_manifest(source, destination):
                    calls.append(str(destination))
                    if len(calls) == 2:
                        raise OSError('Injected manifest replace failure')
                    return real_replace(source, destination)

                with patch.object(self.v.os, 'replace', side_effect=fail_manifest):
                    with self.assertRaisesRegex(OSError, 'manifest replace failure'):
                        self.v.apply(bundle, ORIGINAL, COMPATIBLE, ['battle-repair-bot' if prior_patch else 'berserker-phantasm'])
                backup, manifest = self.v.backup_paths(bundle)
                self.assertEqual(self.v.sha(backup), original_hash)
                self.v.restore(bundle)
                self.assertEqual(self.v.sha(bundle), original_hash)
                self.assertFalse(manifest.exists())
                self.assertFalse(backup.exists())

    @unittest.skipUnless(FFMPEG.exists(), 'Set VIDEO_COMPAT_FFMPEG to an explicit encoder')
    def test_fresh_pet_conversion_keeps_encoded_size_frame_rate_alpha_and_all_other_assets(self):
        name = 'pet-a-elite-dusklight'
        target = self.v.videos(self.env)[name]
        before = target.read_typetree()
        objects = {obj.path_id: obj.get_raw_data() for obj in self.env.objects}
        raw, report = self.v.convert_one(self.env, name, FFMPEG)
        self.assertEqual(report['source']['codec'], 'h264')
        self.assertEqual(report['converted']['codec'], 'vp8')
        for key, expected in (('width', 384), ('height', 192), ('frames', 120), ('frame_rate', '30/1')):
            self.assertEqual(report['source'][key], expected)
            self.assertEqual(report['converted'][key], expected)
        self.assertEqual(report['source']['audio'], [])
        self.assertEqual(report['converted']['audio'], [])
        self.v.patch_environment(self.env, {name: raw})
        reloaded = self.UnityPy.load(self.env.file.save(packer='none'))
        after_obj = self.v.videos(reloaded)[name]
        after = after_obj.read_typetree()
        self.assertEqual(self.v.metadata(after_obj), {key: value for key, value in before.items() if key not in self.v.CHANGED_FIELDS})
        self.assertEqual((after['Width'], after['Height']), (254, 206))
        self.assertTrue(after['m_HasSplitAlpha'])
        self.assertEqual(self.v.payload(after_obj), raw)
        for obj in reloaded.objects:
            if obj.path_id != target.path_id:
                self.assertEqual(obj.get_raw_data(), objects[obj.path_id])

    @unittest.skipUnless(FFMPEG.exists(), 'Set VIDEO_COMPAT_FFMPEG to an explicit encoder')
    def test_fresh_conversion_after_reuse_preserves_backup_and_is_idempotent(self):
        with tempfile.TemporaryDirectory() as folder, patch.object(self.v, 'native_client_running', return_value=False):
            bundle = Path(folder) / 'video.bundle'
            bundle.write_bytes(self.current_bytes)
            original_hash = self.v.sha(bundle)
            first = self.v.apply(bundle, ORIGINAL, COMPATIBLE, ['berserker-phantasm'])
            result = self.v.convert_clip(bundle, 'pet-a-elite-dusklight', FFMPEG, apply_change=True)
            self.assertEqual(result['status'], 'patched')
            self.assertEqual(result['clips'], ['berserker-phantasm', 'pet-a-elite-dusklight'])
            self.assertEqual(result['reference_original_sha256'], first['reference_original_sha256'])
            backup = Path(result['backup'])
            self.assertEqual(self.v.sha(backup), original_hash)
            patched_hash = self.v.sha(bundle)
            second = self.v.convert_clip(bundle, 'pet-a-elite-dusklight', FFMPEG, apply_change=True)
            self.assertEqual(second['status'], 'unchanged')
            self.assertEqual(self.v.sha(bundle), patched_hash)
            self.assertEqual(self.v.sha(backup), original_hash)
            self.v.restore(bundle)
            self.assertEqual(self.v.sha(bundle), original_hash)


if __name__ == '__main__':
    unittest.main()
