# Gameplay and client compatibility contribution

This contribution collects reproducible fixes developed while playing OpenOrbit locally with the original Unity 1.1.115 client on macOS/CrossOver/DXMT. It separates ordinary Python server fixes from opt-in, exact-version client compatibility research. No game client, artwork, save, account record, credential, diagnostic DLL, or private capture is included.

## Why these changes matter

A player could own ammunition while its HUD counter still looked empty, select RSB and be switched to another laser during reload, or target a hostile battle station without being able to start fire with Ctrl or use rockets consistently. Some effects survived their owning target or map; station construction advanced its timer without showing the construction animation at the asteroid. These failures crossed server state, protocol presentation and native client behavior. The fixes and their tests identify those boundaries separately.

## Server changes

| Area | Before | Result and coverage |
| --- | --- | --- |
| Ammunition counters | Captured empty-account red styles persisted despite stock | Availability and counter presentation follow live stock during initialization, restock and depletion; templates remain unchanged |
| Quickslot selection | Category selection and activation semantics were conflated | Ordinary selection remains a selection; activation is handled separately; client quick-buy double-click is documented separately |
| RSB/RCB reload | Reload forced selection back to an earlier laser | Selected ammunition stays selected through cooldown for NPC and side-target combat; manual switching remains possible |
| Singularity/drive effects | Losing the primary target could leave a persistent zone | Expiry, map teardown and death deactivate visuals; iteration survives cancellation inside a damage callback |
| QFC and resonators | Stored equipment information was missing from tooltips; conversion presentation differed | Tooltip fields expose stored percentages and ship binding, and resonator presentation uses the correct item references; native missing icons are a separate compatibility fix |
| HUD bars | Saved premium/pro toolbar visibility flags did not refresh the displayed toolbar | Display settings refresh the menu initialization packet using the saved profile flags |
| CBS models and statistics | Hub levels and satellite design namespaces were mixed, some module capacities/weapons were incorrect | Pack hub levels as the native reader expects; use correct module design IDs, reviewed statistics and existing damage fractions when migrating synthetic rivals |
| CBS target/combat | Periodic info packets could reset target attack state; side-target attacks lacked normal hit feedback | Keep the selected target stable, report actual shield/HP damage and use valid target-type paths |
| CBS rockets | Ordinary/special rockets and launcher payloads had inconsistent building support | Resolve hostile building targets through the same validated attack paths, retaining ammunition use and cooldowns |
| CBS SAB/CBO | Shield-only and normal laser components were collapsed into one incorrect hit | Drain shield separately, restore only actually stolen shield up to the attacker's limit, then apply normal damage; four hero-path regressions reproduce the original failure |
| CBS/PET | PET and hostile stations did not consistently recognize or damage one another | Guard/combo support, recent-aggressor selection, independent PET defenses and module attack cooldowns work through real damage paths |
| CBS docking | Docking/hangar behavior and protection were conflated | Own/allied station docking is evaluated separately from combat immunity; the HUD client icon needs the optional native compatibility layer |
| CBS boosters | XP/honor chose the strongest station instead of stacking and omitted some reward paths | Clan ownership checks, independent 50% global XP/honor caps, station-map damage bonus, 20-hour ramp, and actual NPC/quest/gate reward crediting |
| CBS repair | A repair module could heal before its installation finished | Repair starts after installation; living installed modules can be repaired during combat; destroyed modules remain excluded |
| CBS construction | Building-state packets only updated UI/countdown | Send native modifier 37 immediately and include it in map-entry packets; completion replaces the asteroid with its hub and modules |
| Mines and Hellstorm | Radius/damage/visual and building-target paths differed | Reconcile supported mine effects and area behavior, retain persistent mine visuals, validate launcher packet semantics and CBS impacts |
| Safe areas and NPC movement | CBS overlap, navigation and spawn positions could produce crowding or unintended station intrusion | Preserve map exclusions, safe station behavior and approach paths while allowing provoked combat; retain upstream's map-specific rules |
| Shared player combat helpers | Some building/side-target handling had no reusable player target path | Isolate target lookup, damage and combat feedback; this is local implementation coverage, not a claim of full multiplayer balance |

## Client changes: source-only and opt-in

The Python server changes do not automatically apply native or asset modifications. The included local compatibility tools reproduce the historical fixes on exact known images and reject unsupported versions. They are not integrated into the panel and are not a replacement for upstream's BepInEx approach.

The client inventory covers drone angle wrapping and synchronized facing, missing resonator icons, normal selection versus double-click quick-buy, Ctrl/Space building-target support, CBS hangar HUD activation, satellite model mappings, reference-based CBS shield breathing, correct 2D construction placement, and Wine video preview compatibility. [The client compatibility guide](contribution-client-compatibility.md) documents dependencies, fingerprints, rollback order, limits and the proposed BepInEx port.

The shield investigation compared a 12-second original-game recording to the local client. The observed original had static hex geometry and an approximately six-second brightness cycle. The earlier 1.28-second geometry-changing interpolation was superseded. The final local pulse preserves the original sprite pixels and changes only the isolated CBS clone's renderer/clip. It is not claimed to match every reference pixel or absolute opacity under a different background.

Construction required both the server modifier and a client placement fix. The first native candidate used the hidden 3D building object and was rejected by runtime QA despite passing bounded instruction tests. Temporary diagnostics identified the separate visible `BuildGameObjectComponent.GameObject`; the final hook uses it. Mechanical arms were then observed on build, after map re-entry and removed at completion. Temporary diagnostics are not part of the contribution.

## Upstream integration

Integration base: `d8501e4b1c7084369c21890184930205ccc58994` on `kaanumay/OpenOrbit:main`. The running local installation is kept separate from this contribution checkout. Conflicts were resolved per behavior, retaining upstream changes rather than replacing entire files:

- Keep map-specific pirate safe zones, Black Light portal radii and wall-aware spawning/navigation alongside CBS exclusions.
- Keep the rotated satellite layout while preserving a tested clearance between native sprite footprints.
- Keep galaxy gate ring bitmasks derived from completion history instead of reintroducing the old numeric counter.
- Keep field-mine creation and respawn scheduling alongside the new mine visual/damage paths.
- Keep per-ship PET configuration and migration; adapt only obsolete test setup to the upstream API.
- Keep upstream BepInEx and macOS Wine support without enabling local binary patching through the panel.

## Evidence and limits

The historical exact-client fixture suite passed 347 tests before the contribution review. That review subsequently found and fixed the CBS SAB/CBO integration gap, adding four tests. Latest-upstream reconciliation added three map/CBS tests. The integrated tree passed **354 tests with no failures, errors or skips** using the exact local native/media fixtures. A separate source-only run discovered 348 tests: **275 passed and 73 skipped** because optional fixtures were absent. Native tests are optional and proprietary fixtures are not distributed. Test setup and fixture selectors are documented in [tests/README.md](../tests/README.md).

Tests create temporary profiles and do not edit the player's account. Native emulation executes selected x86 paths after PE relocations at multiple image bases, but stubs external Unity calls; it cannot replace rendering acceptance. Actual visual checks used disposable account copies. Windows/Linux, broad multiplayer and full 3D parity remain unverified. The original server RNG and every equipment formula have not been recovered; no such claim is made. Some timing/balance values remain documented single-player adaptations.

## References

- [Official French module statistics](https://board-fr.darkorbit.com/threads/lexique-2-0-station-de-combat-de-clan.133912/)
- [Official German CBS FAQ](https://board-de.darkorbit.com/threads/faq-clan-battlestations-cbs.2972/)
- [Official Russian CBS FAQ](https://board-ru.darkorbit.com/threads/klanovye-boevye-stancii-kbs-faq.1453/)
- [Official CBS FAQ](https://board-en.darkorbit.com/threads/clan-battle-station-faq.819/)
- [Official booster clarification](https://board-en.darkorbit.com/threads/battle-station-booster-modules.41277/)
- [CBS guide used for comparison](https://darkorbitwiki.com/guides/clan-battle-station/)
- [Mine/equipment guide used for comparison](https://darkorbitwiki.com/equipment/mines-and-fireworks/)

## Türkçe özet

Bu katkı; mühimmat çubuğu, RSB seçimi, kalıcı kalan efektler, ekipman açıklamaları, savaş istasyonları, PET, mayınlar ve bazı istemci hataları üzerinde yaptığımız çalışmaları toplar. Sunucu düzeltmeleri ile yalnız belirli istemci dosyalarında çalışan yerel uyumluluk araçları açıkça ayrılmıştır.

İstasyonlarda hedef seçimi ve saldırının sürmesi, roket/roketatar kullanımı, gerçek hasarın gösterilmesi, PET ile karşılıklı savaş, kendi veya müttefik istasyona kenetlenme, modül görselleri/istatistikleri, bonusların ödüllere uygulanması ve yapım başlangıcı ele alınmıştır. SAB/CBO'nun kalkan çalma ve normal hasar bileşenleri katkı öncesi ek incelemeyle ayrıca düzeltilmiştir. TP/şeref bonusları klan istasyonları arasında birikir ve CBS'ye ait %50 sınırını uygular; hasar bonusu yalnız istasyonun haritasında geçerlidir.

İstemci tarafında drone dönüşleri, Ctrl/Space ile istasyona saldırı, hangar HUD simgesi, çift tıklamayla hızlı satın alma, eksik rezonatör görselleri, kalkanın yumuşak parlaklık döngüsü, yapım kollarının doğru asteroide bağlanması ve Wine video önizlemeleri belgelenmiştir. Bunların BepInEx'e taşınması öneridir; henüz eklentiye uygulanmış gibi sunulmaz.

Katkı güncel ana sürüme uyarlanırken yeni harita kuralları, PET'in gemiye bağlı ekipmanı, kapı halkaları ve mayın alanlarının yeniden doğması korunmuştur. Oyun dosyaları, hesabın, kayıtların, özel günlükler ve geçici teşhis yamaları paylaşılmaz. Önceki NosGalaxy ve ayrı tarayıcı oyunu çalışmaları bu OpenOrbit katkısının kapsamı değildir.
