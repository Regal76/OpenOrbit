"""Local artwork aliases preserve native loot IDs, textures and rollback bytes."""
import hashlib
import importlib.util
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]


class ResonatorIconCompatTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        spec = importlib.util.spec_from_file_location('resonator_icon_compat', ROOT / 'tools/resonator_icon_compat.py')
        cls.mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.mod)

    def test_covers_all_recipes_and_resources_at_both_sizes(self):
        import json
        data = json.loads((ROOT / 'server/data/esyalar_o6.json').read_text())['rezonator']
        expected = {loot.rsplit('_', 1)[-1] + '_' + size
                    for loot in (*data['esyalar'], *data['kaynaklar'])
                    for size in ('30x30', '100x100')}
        self.assertEqual(set(self.mod.ALIASES), expected)
        for size in ('30x30', '100x100'):
            sources = [self.mod.ALIASES[t + '-' + kind + '-resonator_' + size]
                       for kind in ('strike', 'aegis') for t in self.mod.TIERS]
            self.assertEqual(len(set(sources)), 14)

    def test_unknown_image_is_rejected_before_parsing(self):
        with self.assertRaisesRegex(ValueError, 'fingerprint'):
            self.mod.patch_bytes(b'unknown bundle')

    @unittest.skipUnless(os.environ.get('RESONATOR_COMPAT_BUNDLE'), 'Set RESONATOR_COMPAT_BUNDLE for exact native fixture')
    def test_native_roundtrip_clones_sprites_retains_originals_and_guards_restore(self):
        import UnityPy
        m = self.mod
        original = Path(os.environ['RESONATOR_COMPAT_BUNDLE']).read_bytes()
        modified = m.patch_bytes(original)
        old = UnityPy.load(original)
        new = UnityPy.load(modified)
        old_atlas, old_tree = m.item_atlas(old)
        new_atlas, new_tree = m.item_atlas(new)
        old_objects = old_atlas.assets_file.objects
        new_objects = new_atlas.assets_file.objects
        self.assertEqual(len(new_objects), len(old_objects) + len(m.ALIASES))
        for iid, obj in old_objects.items():
            if iid != old_atlas.path_id:
                self.assertEqual(obj.get_raw_data(), new_objects[iid].get_raw_data())
        self.assertEqual(old_tree['m_RenderDataMap'], new_tree['m_RenderDataMap'])
        lookup = dict(zip(new_tree['m_PackedSpriteNamesToIndex'], new_tree['m_PackedSprites']))
        for alias, source in m.ALIASES.items():
            clone = new_objects[lookup[alias]['m_PathID']].read_typetree()
            native = new_objects[lookup[source]['m_PathID']].read_typetree()
            self.assertEqual(clone['m_Name'], alias)
            clone['m_Name'] = source
            self.assertEqual(clone, native)
            cloned_image = new_objects[lookup[alias]['m_PathID']].read().image
            source_image = new_objects[lookup[source]['m_PathID']].read().image
            self.assertEqual(cloned_image.size, source_image.size)
            self.assertEqual(cloned_image.tobytes(), source_image.tobytes())
        with tempfile.TemporaryDirectory() as td:
            bundle = Path(td) / 'atlas_assets_all.bundle'
            bundle.write_bytes(original)
            with patch.object(m, 'native_client_running', return_value=True):
                with self.assertRaises(RuntimeError):
                    m.apply(bundle)
            self.assertEqual(bundle.read_bytes(), original)
            with patch.object(m, 'native_client_running', return_value=False):
                m.apply(bundle)
                applied = bundle.read_bytes()
                m.apply(bundle)
                self.assertEqual(bundle.read_bytes(), applied)
                self.assertEqual(m.backup_path(bundle).read_bytes(), original)
                damaged = bytearray(applied)
                damaged[-1] ^= 1
                bundle.write_bytes(damaged)
                with self.assertRaises(ValueError):
                    m.restore(bundle)
                self.assertEqual(bundle.read_bytes(), damaged)
                bundle.write_bytes(applied)
                m.restore(bundle)
                m.restore(bundle)
                self.assertEqual(hashlib.sha256(bundle.read_bytes()).hexdigest(), m.ORIGINAL_SHA256)


if __name__ == '__main__':
    unittest.main()
