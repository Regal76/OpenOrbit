# Client compatibility contribution notes

These changes support the **Windows x86 IL2CPP client 1.1.115** used with OpenOrbit. They are local, fingerprint-checked compatibility scripts, with a proposed source-level integration path. They are **not implemented in the upstream BepInEx plugin**. Server gameplay corrections should be reviewed separately from these client presentation and input changes.

No client DLL, Unity bundle, extracted texture, video, account save or proprietary asset is part of this contribution. The scripts operate on a user's existing client and reuse its shipped assets.

## Changes and boundaries

| Area | Current behavior | Implementation |
| --- | --- | --- |
| Drone angle wrap | Small turns across 0°/360° take the intended short direction instead of almost a full spin. | `tools/drone_turn_compat.py` |
| Drone facing synchronization | High-quality 2D drone orientation updates with the owning ship; sprite heading uses the owner's displayed rotation. Formation translation easing remains. | `tools/drone_sync_native_compat.py` |
| Resonator icons | Fourteen resonators and eleven source items resolve distinct existing illustrations in 30px and 100px views. A narrow allowlist bypasses unknown-item icon fallback. | `tools/resonator_icon_compat.py`, `tools/resonator_icon_native_compat.py` |
| Resonator tooltips | Eleven known modifier descriptions substitute values and distinguish seconds from percentages. | Native resonator formatter guard in the preceding tool |
| Quick buy | Only `buy_*` items require the native double-click callback. An isolated single click sends no purchase; a double click purchases one configured batch. Ordinary item selection and activation retain their existing click behavior. | `tools/quick_buy_double_click_compat.py` |
| CBS Space / Ctrl | Space accepts a selected BuildUnit through the existing manual rocket request route. Ctrl accepts BuildUnit for laser start, stop and restart. Ordinary Unit paths remain intact. | `tools/cbs_manual_rocket_native_compat.py`, `tools/cbs_ctrl_native_compat.py` |
| CBS Hangar | The existing HUD Hangar entry, window lifetime and Activate callback accept peace-area access **or** docking through `InStation.Value`. Server authorization still applies. No floating map helper is produced by the current server behavior. | `tools/cbs_hangar_activate_compat.py`, `tools/cbs_hangar_hud_compat.py` |
| CBS module models | Existing map artwork is reassigned for the LR/HR laser and LA/MA rocket family mismatches so it agrees with inventory art. MR and booster/repair families are unchanged. Levels, stats and ranges are unchanged. | `tools/cbs_module_model_compat.py` |
| CBS shield | A CBS-only clone uses fixed shipped hex artwork with a smooth six-second opacity cycle. Ship invulnerability assets remain unchanged. | `tools/cbs_shield_loop_compat.py` establishes isolation; `tools/cbs_reference_pulse_compat.py` supplies the final animation |
| CBS construction | Modifier 37 activates the shipped mechanical-arm/spark animation. A native correction anchors BuildUnit construction to its **visible 2D** `BuildGameObjectComponent.GameObject`, preserving ordinary Unit behavior. | Server activation plus `tools/cbs_construction_anchor_compat.py` |
| Assembly previews | Optional H.264-to-VP8 compatibility enables sampled item previews under the tested Wine video path. Existing clip IDs, aliases, split-alpha and audio metadata are retained. | `tools/video_compat.py` |

Resonator illustrations are reused native cannon/component illustrations, **not recovered official resonator art**. The icon hook does not invent compiled item definitions or clear every unknown-item diagnostic. Resonator mechanics and original-server RNG equivalence are outside this client contribution.

The quick-buy guard is distinct from the server's category-selection correction: category `SELECT` requests change ammunition selection without starting combat; activation keeps its existing shortcut behavior. Selection is not made double-click-only.

## Historical stages versus final behavior

Two shield experiments preceded the recorded-reference comparison: CBS-only Animator speed 0.5, followed by a cyclic 64-frame interpolation of the original flipbook. The reference instead showed fixed geometry breathing over six seconds. The final pulse replaces the clone's flipbook with an opacity curve; it retains the earlier isolation and native speed hook as prerequisites. The final clip lasts three simulation seconds at Animator speed 0.5. Its opacity range 0.5–1 is a visual calibration, not an exact recovery of absolute opacity from a composited recording. The retained earlier speed layer also sets two CBS 3D particle systems to simulation speed 0.5; the final reference comparison validates the 2D pulse, not 3D parity.

The floating Hangar helper implementation is superseded by the HUD presentation. Its native compatibility layer remains in the recorded binary dependency chain, but the current server does not spawn those helpers. It should not be carried into a new source implementation merely to reproduce that historical chain.

The first construction candidate anchored to the hidden 3D representation and failed visual QA. The final candidate follows the visible 2D component used by native `BuildUnit.RealPosition`. Temporary logging patches were removed; they are not part of the final payload.

## Exact version and dependency order

These are transformations of specific bytes, **not a general patch installer for every 1.1.115 download**. The recorded baseline DLL SHA-256 is `1ae406f311cd38927f435e9335704e3adc84b92b4048b19bc6ec948cdcc6bec5`; metadata SHA-256 is `43f85183250207c196db4e355bd04bcc50b4f0f217dd208918e53c8c910f225f`. A changed build requires new analysis and verification.

The recorded native stack, earliest to latest, is:

1. Drone wrap correction.
2. Resonator native icon/formatter correction, revision 2.
3. CBS shield speed isolation.
4. Historical Hangar helper compatibility.
5. Hangar Activate callback.
6. Native Hangar HUD access/lifetime correction.
7. CBS shield clone/name hook, corrected relocation revision 2.
8. CBS module model lookup correction.
9. Quick-buy double-click guard.
10. CBS manual rocket / Space route.
11. CBS Ctrl laser route.
12. Drone facing synchronization.
13. Construction anchoring to the visible 2D model.

The corresponding scripts are the `tools/*compat.py` entries in the inventory table, plus historical `tools/cbs_hangar_button_compat.py` and `tools/cbs_shield_speed_compat.py`. The construction tool requires the preceding native hash `fc3f5f7c190ad62ddd0cab9013fc50150a0d4b5ce5ed11239ca376f52132389a`.

Final native DLL SHA-256:

`89cd1b6f08347affe36c21477f7fae256c30ac120b84b077932e313bba3b153a`

Bundle changes have separate dependencies. Resonator atlas aliases complement the native icon guard. The shield clone step modifies its effect bundle, two catalogs and catalog hash; the later reference-pulse step changes only the isolated clone's renderer/clip in that bundle. Final shield bundle SHA-256:

`18d5574aa3950ef80986685e0bfdffe1446d8e55d7ca14947eb93ccbfb8f0f6d`

VP8 video conversion is optional and independent of the native DLL stack. It selects an explicit bundle/clip or reuses a conversion only when original payload and retained metadata match.

Read each tool's `--help` and exact input contract before use; older tools use different command syntax. Close the client before applying or restoring. Retain the per-layer backups/manifests and restore native layers in reverse order. A later layer's DLL is not a valid fixture for an earlier layer. Preparation/read-only modes exist where documented; these scripts are not a transactional installer for the complete stack.

## Verification and limitations

Native UI and rendering acceptance used **macOS with CrossOver/Wine**, including the tested DXMT/video configuration, on disposable copies of an existing account. The final fixture-enabled integration run passed **347 tests with zero skips**. This does not establish native Windows, Linux/Wine, other graphics backends, other client builds, or complete 3D parity.

Observed acceptance includes single/double quick-buy gestures, ordinary category selection, CBS Ctrl start/stop/restart and Space rocket requests, Hangar activation through the HUD, drone facing, inventory/map module artwork, six-second shield breathing, and construction arms/sparks on entry, build, reload and completion. Original 3D construction reference images and the shipped 2D counterpart are not claimed to be pixel-identical. Preview playback was sampled; it was not an exhaustive visual review of every clip.

Portable checks run with:

```sh
python3 -m unittest discover -s tests -v
```

Native/asset tests require locally supplied exact fixtures and optional dependencies, including UnityPy, Pillow, pefile and Unicorn as applicable. Video conversion additionally requires ffmpeg; real-media tests use the `VIDEO_COMPAT_*` fixture variables documented by the video tests. Some native tests load explicit earlier-layer fixtures or validated backups. Missing fixtures/dependencies can skip tests; such a run must not be reported as equivalent to the zero-skip integration run. No proprietary fixture is included.

Native replay tests cover relevant branch outcomes, null/ordinary-target behavior, register/XMM/stack preservation, PE mutation scope and loader relocations where applicable. They stub Unity/runtime boundaries and do not replace live rendering. The construction regression specifically distinguishes a hidden 3D model from the visible 2D component; the original model-only test missed that boundary. Backups, tampering refusal, idempotency and exact restoration are tested on temporary files.

## Proposed upstream BepInEx integration

This section is a design proposal, not implemented integration. The upstream source plugin at `server/panel/eklenti/Yamalar.cs` is the appropriate review point for replacing the local byte-patch chain with supported, version-gated IL2CPP hooks where feasible.

Port by behavior: verify the generated type/method bindings for the installed client; implement narrow input predicates and the BuildUnit-specific branches; obtain the visible construction component through its typed API; reuse the native HUD docking state; and keep the CBS shield presentation isolated from ship effects. Separate optional video conversion and asset alias generation from plugin startup. Do not transplant historical helper behavior, hard-coded RVAs or intermediate binary hashes as a substitute for source-level integration.

Validate each behavior independently before combining it: ordinary Unit/unknown-item paths, category selection versus purchase, docking transitions, source destruction and reload, construction lifecycle, shield lifecycle and original ship effects. Repeat native UI acceptance on supported target platforms. If a hook cannot be expressed safely through the plugin's actual IL2CPP bindings, document that unsupported boundary rather than silently applying a guessed native patch. Publish source, tests and version requirements; require users to provide their own client assets.
