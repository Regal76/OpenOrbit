# Regression tests

Run from the repository root with Python 3.10 or newer:

```sh
python -m pip install -e '.[test]'
python -m unittest discover -s tests -v
```

Server tests create temporary profiles and exercise actual damage, reward, packet and lifecycle methods. They do not connect to official servers or require an account. Optional native and media tests skip with an explicit reason when their local fixtures are absent. A skipped native test is not a rendering pass. An explicitly supplied but incompatible fixture must fail rather than silently skip.

The proprietary client, asset bundles and original backups are never distributed with these tests. Tools accept only their exact supported fingerprints; see [client compatibility](../docs/contribution-client-compatibility.md) for layer order. Never feed the final patched DLL to every layer's original-image test. Provide the appropriate original backup for each layer.

Optional environment variables used by existing test modules include `DRONE_COMPAT_ORIGINAL`, `DRONE_UNICORN_PATH`, `HELLSTORM_NATIVE_DLL`, `HELLSTORM_UNICORN_PATH`, `RESONATOR_NATIVE_DLL`, `RESONATOR_COMPAT_BUNDLE`, `CBS_HANGAR_NATIVE_DLL`, `CBS_ACTIVATE_NATIVE_DLL`, `CBS_HUD_NATIVE_DLL`, `CBS_SHIELD_NATIVE_DLL`, `CBS_SHIELD_PARTICLE_BUNDLE`, `CBS_MODELS_NATIVE_DLL`, `QUICK_BUY_NATIVE_DLL`, `CBS_LOOP_CLIENT_DIR`, `VIDEO_COMPAT_SOURCE_ORIGINAL`, `VIDEO_COMPAT_SOURCE_COMPATIBLE`, and `VIDEO_COMPAT_FFMPEG`. The shield-loop directory must contain all five exact original artifacts expected by that tool. Optional artwork tests use a locally supplied `DarkOrbit_Version1.1.115` directory and validated layer backups.

Historical local acceptance covered the exact 1.1.115 client on macOS/CrossOver/DXMT. It did not establish Windows, Linux, multiplayer, every ship/equipment combination, or every 3D rendering path. The current contribution test result and upstream integration notes are in [the contribution summary](../docs/contribution-summary.md).

New optional fixture selectors: `CBS_CONSTRUCTION_NATIVE_DLL` (exact pre-construction DLL), `CBS_REFERENCE_PULSE_BUNDLE` (exact pre-pulse bundle), and `CBS_HANGAR_BUNDLE` (building bundle for the blank-prefab structural check).
