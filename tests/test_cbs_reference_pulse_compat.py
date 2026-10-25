"""Reference CBS pulse changes only the isolated CBS renderer and clip."""
import importlib.util
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
BUNDLE=ROOT/'DarkOrbit_Version1.1.115/DarkOrbit_Data/StreamingAssets/aa/BuildTarget/effect_2d_assets_bundle_pack_effect_2d_047.bundle'

class ReferencePulse(unittest.TestCase):
    def module(self):
        path=ROOT/'tools/cbs_reference_pulse_compat.py'
        self.assertTrue(path.exists(), 'Reference pulse implementation missing')
        spec=importlib.util.spec_from_file_location('reference_pulse',path)
        m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m

    def fixture(self,m):
        explicit=os.environ.get('CBS_REFERENCE_PULSE_BUNDLE')
        path=Path(explicit) if explicit else BUNDLE
        if not explicit and not path.exists():
            self.skipTest('Optional bundle fixture absent; set CBS_REFERENCE_PULSE_BUNDLE')
        raw=path.read_bytes()  # Explicit missing or malformed fixtures must fail.
        if m.digest(raw)!=m.INPUT_SHA256 and not explicit:
            raw=Path(str(path)+'.cbs-reference-pulse.original').read_bytes()
        self.assertEqual(m.digest(raw),m.INPUT_SHA256,'Unsupported reference pulse fixture fingerprint')
        try:
            import UnityPy
            from PIL import Image
        except ImportError:
            self.skipTest('Optional reference pulse bundle tests require UnityPy and Pillow')
        return raw

    def test_apply_restore_process_guard_idempotency_and_tamper(self):
        m=self.module();original=self.fixture(m)
        with tempfile.TemporaryDirectory() as d:
            source=Path(d)/BUNDLE.name;source.write_bytes(original)
            with patch.object(m,'native_client_running',return_value=True):
                with self.assertRaisesRegex(RuntimeError,'Close'):m.apply(source)
            self.assertEqual(source.read_bytes(),original)
            with patch.object(m,'native_client_running',return_value=False):
                first=m.apply(source);modified=source.read_bytes()
                self.assertEqual(m.apply(source),first)
                self.assertEqual(m.backup_path(source).read_bytes(),original)
                source.write_bytes(modified+b'bad')
                with self.assertRaisesRegex(ValueError,'fingerprint'):m.restore(source)
                with self.assertRaisesRegex(ValueError,'fingerprint'):m.apply(source)
                source.write_bytes(modified)
                self.assertEqual(m.restore(source)['status'],'restored')
                self.assertEqual(source.read_bytes(),original)
                self.assertEqual(m.restore(source)['status'],'original')

    def test_pulse_period_range_and_ease_out(self):
        m=self.module()
        self.assertEqual([m.alpha_at(t) for t in [0,1.5,3,4.5,6]], [1,.625,.5,.875,1])
        self.assertEqual(m.alpha_at(12),1)
        self.assertAlmostEqual(m.alpha_at(6-1e-7),m.alpha_at(0),places=6)

    def test_bundle_preserves_every_unrelated_object_and_ish(self):
        m=self.module();raw=self.fixture(m);import UnityPy
        before={o.path_id:o for o in UnityPy.load(raw).objects}
        modified=m.patch_bundle(raw);after={o.path_id:o for o in UnityPy.load(modified).objects}
        self.assertEqual(set(before),set(after))
        changed={pid for pid in before if before[pid].get_raw_data()!=after[pid].get_raw_data()}
        self.assertEqual(changed,{m.CBS_CLIP_ID,m.CBS_RENDERER_ID})
        clip=after[m.CBS_CLIP_ID].read_typetree();data=clip['m_MuscleClip']['m_Clip']['data']
        self.assertEqual(clip['m_ClipBindingConstant']['pptrCurveMapping'],[])
        self.assertEqual(clip['m_ClipBindingConstant']['genericBindings'][0]['attribute'],304273561)
        self.assertEqual(data['m_DenseClip']['m_CurveCount'],1)
        self.assertEqual(len(data['m_DenseClip']['m_SampleArray']),182)
        self.assertEqual(clip['m_MuscleClip']['m_StopTime']/.5,6)
        self.assertEqual(after[m.CBS_RENDERER_ID].read_typetree()['m_Sprite']['m_PathID'],m.SOURCE_SPRITE_ID)
        with self.assertRaisesRegex(ValueError,'fingerprint'):m.patch_bundle(modified)

    def test_prepare_isolated_and_existing_destination_refused(self):
        m=self.module();original=self.fixture(m)
        with tempfile.TemporaryDirectory() as d:
            source=Path(d)/BUNDLE.name;source.write_bytes(original)
            out=Path(d)/'candidate';m.prepare(source,out)
            self.assertEqual(source.read_bytes(),original)
            self.assertTrue((out/BUNDLE.name).exists())
            self.assertEqual((out/'original.bundle').read_bytes(),original)
            with self.assertRaisesRegex(ValueError,'new'):m.prepare(source,out)

if __name__=='__main__':unittest.main()
