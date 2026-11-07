# MuJoCo migration proposal

This inventory is a proposal. Source artifacts remain in their original locations.
Every source file has a recorded SHA-256 and size in inventory.json.
Activity is not inferred from directory names. Unresolved entries remain in place.

| Original | Proposed destination | Evidence | Dependencies |
|---|---|---|---|
| simulation/mujoco/runs/arena-preview.stderr.log | Preserve pending classification | Origin unresolved; preserve in place pending content/dependency review | 0 artifact references; 0 source references |
| simulation/mujoco/runs/arena-preview.stdout.log | Preserve pending classification | Origin unresolved; preserve in place pending content/dependency review | 0 artifact references; 0 source references |
| simulation/mujoco/runs/baseline-c03d496728334e05b144159ad8ab4b45.json | Preserve pending classification | Origin unresolved; preserve in place pending content/dependency review | 0 artifact references; 0 source references |
| simulation/mujoco/runs/baseline-new-task-48868ea50fd24870812e9ca6a76bf831 | simulation/mujoco/training/camera-manipulation/runs/baseline-new-task-48868ea50fd24870812e9ca6a76bf831 | P038 environment configuration in run.json | 1 artifact references; 1 source references |
| simulation/mujoco/runs/baseline-new-task-8b6f9a9ed7c54e44887555d422d6522a | simulation/mujoco/training/camera-manipulation/runs/baseline-new-task-8b6f9a9ed7c54e44887555d422d6522a | P038 environment configuration in run.json | 1 artifact references; 1 source references |
| simulation/mujoco/runs/camera-baseline-4a9e3fe8cbe84318b47a454a553c544c | simulation/mujoco/training/camera-manipulation/runs/camera-baseline-4a9e3fe8cbe84318b47a454a553c544c | P038 environment configuration in run.json | 1 artifact references; 1 source references |
| simulation/mujoco/runs/camera-test-d047c79f013244879318a79707a46fa0 | simulation/mujoco/examples/validate_native_perception/runs/camera-test-d047c79f013244879318a79707a46fa0 | Native perception report | 9 artifact references; 1 source references |
| simulation/mujoco/runs/capture-0fe55b3eb3034940912e401aaa28c0f0 | simulation/mujoco/examples/prepare_capture_task/runs/capture-0fe55b3eb3034940912e401aaa28c0f0 | Two-piece capture fixture manifest | 0 artifact references; 1 source references |
| simulation/mujoco/runs/capture-119a539c99e84ac99626cddc6d212458 | simulation/mujoco/examples/prepare_capture_task/runs/capture-119a539c99e84ac99626cddc6d212458 | Two-piece capture fixture manifest | 0 artifact references; 1 source references |
| simulation/mujoco/runs/capture-450916a19fb944af8a2876d0f482a168 | simulation/mujoco/assets/bundles/capture-450916a19fb944af8a2876d0f482a168 | Has hashed model manifest; shared consumers require path review | 0 artifact references; 1 source references |
| simulation/mujoco/runs/capture-camera-inspection | simulation/mujoco/examples/prepare_capture_task/runs/capture-camera-inspection | Capture evidence report | 0 artifact references; 1 source references |
| simulation/mujoco/runs/capture-d44b40c3682a453ca92525ae77dd3751 | simulation/mujoco/examples/prepare_capture_task/runs/capture-d44b40c3682a453ca92525ae77dd3751 | Two-piece capture fixture manifest | 0 artifact references; 1 source references |
| simulation/mujoco/runs/chess-pieces-v3.ppm | Preserve pending classification | Origin unresolved; preserve in place pending content/dependency review | 0 artifact references; 0 source references |
| simulation/mujoco/runs/demo-426349c5f3a443cab148bd7a306bd700.json | Preserve pending classification | Origin unresolved; preserve in place pending content/dependency review | 0 artifact references; 0 source references |
| simulation/mujoco/runs/demo-48221f3abf114a8db38aea2f68a802ff.json | Preserve pending classification | Origin unresolved; preserve in place pending content/dependency review | 0 artifact references; 0 source references |
| simulation/mujoco/runs/demo-65c772e4c29140769752bbffb72dba74.json | Preserve pending classification | Origin unresolved; preserve in place pending content/dependency review | 0 artifact references; 0 source references |
| simulation/mujoco/runs/demo-9079990effa44a58875bd1c5af785eba.json | Preserve pending classification | Origin unresolved; preserve in place pending content/dependency review | 0 artifact references; 0 source references |
| simulation/mujoco/runs/demo-9094b2e33a6e4f9b81f1069463a453c2.json | Preserve pending classification | Origin unresolved; preserve in place pending content/dependency review | 0 artifact references; 0 source references |
| simulation/mujoco/runs/demo-a7c850ad149c4479893f90f483ccdfcc.json | Preserve pending classification | Origin unresolved; preserve in place pending content/dependency review | 0 artifact references; 0 source references |
| simulation/mujoco/runs/demo-ae3902cedd6c4319858b89e1a850797e.json | Preserve pending classification | Origin unresolved; preserve in place pending content/dependency review | 0 artifact references; 0 source references |
| simulation/mujoco/runs/demo-b5186a0807744b5daa7f39623bf4a96f.json | Preserve pending classification | Origin unresolved; preserve in place pending content/dependency review | 0 artifact references; 0 source references |
| simulation/mujoco/runs/demo-ffd939f5c1ae47aaa1af445cc8c8d130.json | Preserve pending classification | Origin unresolved; preserve in place pending content/dependency review | 0 artifact references; 0 source references |
| simulation/mujoco/runs/exercise-01.json | Preserve pending classification | Origin unresolved; preserve in place pending content/dependency review | 0 artifact references; 1 source references |
| simulation/mujoco/runs/exercise-02.json | Preserve pending classification | Origin unresolved; preserve in place pending content/dependency review | 0 artifact references; 0 source references |
| simulation/mujoco/runs/exercise-f470882154ca4b11a54b91678c82af29.json | Preserve pending classification | Origin unresolved; preserve in place pending content/dependency review | 0 artifact references; 0 source references |
| simulation/mujoco/runs/exercise-p038 | Preserve pending classification | Origin unresolved; preserve in place pending content/dependency review | 11 artifact references; 3 source references |
| simulation/mujoco/runs/grasp-fast-4-workers | simulation/mujoco/training/grasp-lift/runs/grasp-fast-4-workers | Legacy environment metadata in run.json | 2 artifact references; 1 source references |
| simulation/mujoco/runs/grasp-fast-4-workers.stderr.log | Preserve pending classification | Origin unresolved; preserve in place pending content/dependency review | 0 artifact references; 0 source references |
| simulation/mujoco/runs/grasp-fast-4-workers.stdout.log | Preserve pending classification | Origin unresolved; preserve in place pending content/dependency review | 0 artifact references; 0 source references |
| simulation/mujoco/runs/grasp-parallel-watch-smoke | simulation/mujoco/training/grasp-lift/runs/grasp-parallel-watch-smoke | Legacy environment metadata in run.json | 0 artifact references; 1 source references |
| simulation/mujoco/runs/graveyard-vision-8c4ff961d74e43e4a4e5c90ae02cea62 | simulation/mujoco/examples/prepare_capture_task/runs/graveyard-vision-8c4ff961d74e43e4a4e5c90ae02cea62 | Graveyard camera qualification report | 0 artifact references; 1 source references |
| simulation/mujoco/runs/graveyard-vision-c7e98321560d47209ca3bc2061315901 | simulation/mujoco/examples/prepare_capture_task/runs/graveyard-vision-c7e98321560d47209ca3bc2061315901 | Graveyard camera qualification report | 0 artifact references; 1 source references |
| simulation/mujoco/runs/integration-exercise-a126286685004da797430ea76c285e68.json | Preserve pending classification | Origin unresolved; preserve in place pending content/dependency review | 0 artifact references; 0 source references |
| simulation/mujoco/runs/interactive-chess-v4 | simulation/mujoco/assets/bundles/interactive-chess-v4 | Has hashed model manifest; shared consumers require path review | 0 artifact references; 2 source references |
| simulation/mujoco/runs/interactive-chess-v5 | simulation/mujoco/assets/bundles/interactive-chess-v5 | Has hashed model manifest; shared consumers require path review | 0 artifact references; 2 source references |
| simulation/mujoco/runs/interactive-chess-v6 | simulation/mujoco/assets/bundles/interactive-chess-v6 | Has hashed model manifest; shared consumers require path review | 0 artifact references; 5 source references |
| simulation/mujoco/runs/interactive-v4.ppm | Preserve pending classification | Origin unresolved; preserve in place pending content/dependency review | 0 artifact references; 0 source references |
| simulation/mujoco/runs/interactive-v5.ppm | Preserve pending classification | Origin unresolved; preserve in place pending content/dependency review | 0 artifact references; 0 source references |
| simulation/mujoco/runs/latest-visual-training.txt | Preserve pending classification | Origin unresolved; preserve in place pending content/dependency review | 0 artifact references; 0 source references |
| simulation/mujoco/runs/live-arena-smoke | simulation/mujoco/training/grasp-lift/runs/live-arena-smoke | Legacy environment metadata in run.json | 0 artifact references; 1 source references |
| simulation/mujoco/runs/n | Preserve pending classification | Origin unresolved; preserve in place pending content/dependency review | 0 artifact references; 1163 source references |
| simulation/mujoco/runs/official-piece-exports | Preserve pending classification | Origin unresolved; preserve in place pending content/dependency review | 0 artifact references; 2 source references |
| simulation/mujoco/runs/p015-54a4374eed55493ca59bc10e7d4bc907.json | Preserve pending classification | Origin unresolved; preserve in place pending content/dependency review | 0 artifact references; 0 source references |
| simulation/mujoco/runs/p032-contract-20261106 | simulation/mujoco/examples/validate_native_perception/runs/p032-contract-20261106 | Native perception report | 3 artifact references; 22 source references |
| simulation/mujoco/runs/p033-pattern-20261106 | simulation/mujoco/examples/validate_native_perception/runs/p033-pattern-20261106 | Native perception report | 3 artifact references; 1 source references |
| simulation/mujoco/runs/p033-viewpoint-sweep-20261106 | simulation/mujoco/examples/validate_native_perception/runs/p033-viewpoint-sweep-20261106 | Native perception report | 9 artifact references; 48 source references |
| simulation/mujoco/runs/p034-diagnostic | Preserve pending classification | Origin unresolved; preserve in place pending content/dependency review | 1 artifact references; 1 source references |
| simulation/mujoco/runs/p034-markers-final | simulation/mujoco/examples/validate_board_reference/runs/p034-markers-final | Marker-layout qualification report | 28 artifact references; 134 source references |
| simulation/mujoco/runs/p034-markers-v1 | Preserve pending classification | Origin unresolved; preserve in place pending content/dependency review | 1 artifact references; 1 source references |
| simulation/mujoco/runs/p034-markers-v2 | simulation/mujoco/examples/validate_board_reference/runs/p034-markers-v2 | Marker-layout qualification report | 28 artifact references; 1 source references |
| simulation/mujoco/runs/p034-markers-v3 | simulation/mujoco/examples/validate_board_reference/runs/p034-markers-v3 | Marker-layout qualification report | 28 artifact references; 1 source references |
| simulation/mujoco/runs/p034-markers-v4 | simulation/mujoco/examples/validate_board_reference/runs/p034-markers-v4 | Marker-layout qualification report | 28 artifact references; 1 source references |
| simulation/mujoco/runs/p034-markers-v5 | simulation/mujoco/examples/validate_board_reference/runs/p034-markers-v5 | Marker-layout qualification report | 28 artifact references; 1 source references |
| simulation/mujoco/runs/p034-markers-v6 | simulation/mujoco/examples/validate_board_reference/runs/p034-markers-v6 | Marker-layout qualification report | 28 artifact references; 1 source references |
| simulation/mujoco/runs/p034-markers-v7 | simulation/mujoco/examples/validate_board_reference/runs/p034-markers-v7 | Marker-layout qualification report | 28 artifact references; 1 source references |
| simulation/mujoco/runs/p034-markers-v8 | simulation/mujoco/examples/validate_board_reference/runs/p034-markers-v8 | Marker-layout qualification report | 28 artifact references; 1 source references |
| simulation/mujoco/runs/p034-residual | Preserve pending classification | Origin unresolved; preserve in place pending content/dependency review | 1 artifact references; 1 source references |
| simulation/mujoco/runs/p035-foreground | simulation/mujoco/examples/validate_board_reference/runs/p035-foreground | Marker-layout qualification report | 37 artifact references; 1 source references |
| simulation/mujoco/runs/p035-steep | simulation/mujoco/examples/validate_board_reference/runs/p035-steep | Marker-layout qualification report | 37 artifact references; 4 source references |
| simulation/mujoco/runs/p035-steep-layout.json | Preserve pending classification | Origin unresolved; preserve in place pending content/dependency review | 0 artifact references; 0 source references |
| simulation/mujoco/runs/p035-steep-relayout | simulation/mujoco/examples/validate_board_reference/runs/p035-steep-relayout | Marker-layout qualification report | 37 artifact references; 3 source references |
| simulation/mujoco/runs/p036 | Preserve pending classification | Origin unresolved; preserve in place pending content/dependency review | 210 artifact references; 737 source references |
| simulation/mujoco/runs/p037-folded-cli | Preserve pending classification | Origin unresolved; preserve in place pending content/dependency review | 1 artifact references; 1 source references |
| simulation/mujoco/runs/p037-native-background | simulation/mujoco/examples/preview_native_policy/runs/p037-native-background | Actor-input preview report | 0 artifact references; 1 source references |
| simulation/mujoco/runs/p037-native-folded | simulation/mujoco/examples/preview_native_policy/runs/p037-native-folded | Actor-input preview report | 0 artifact references; 1 source references |
| simulation/mujoco/runs/p037-native-preview | simulation/mujoco/examples/preview_native_policy/runs/p037-native-preview | Actor-input preview report | 0 artifact references; 1 source references |
| simulation/mujoco/runs/p037-native-visible | simulation/mujoco/examples/preview_native_policy/runs/p037-native-visible | Actor-input preview report | 0 artifact references; 1 source references |
| simulation/mujoco/runs/p037-observation-poses.json | Preserve pending classification | Origin unresolved; preserve in place pending content/dependency review | 0 artifact references; 0 source references |
| simulation/mujoco/runs/p038-evaluation-check | simulation/mujoco/training/camera-manipulation/runs/p038-evaluation-check | P038 environment configuration in run.json | 1 artifact references; 1 source references |
| simulation/mujoco/runs/p038-resume-check | simulation/mujoco/training/camera-manipulation/runs/p038-resume-check | P038 environment configuration in run.json | 1 artifact references; 1 source references |
| simulation/mujoco/runs/p038-single-piece | simulation/mujoco/assets/bundles/p038-single-piece | Has hashed model manifest; shared consumers require path review | 1 artifact references; 31 source references |
| simulation/mujoco/runs/p038-smoke-final | simulation/mujoco/training/camera-manipulation/runs/p038-smoke-final | P038 environment configuration in run.json | 1 artifact references; 2 source references |
| simulation/mujoco/runs/p038-smoke-v1 | simulation/mujoco/training/camera-manipulation/runs/p038-smoke-v1 | P038 environment configuration in run.json | 1 artifact references; 1 source references |
| simulation/mujoco/runs/p038-test-new-task | simulation/mujoco/assets/bundles/p038-test-new-task | Has hashed model manifest; shared consumers require path review | 1 artifact references; 1 source references |
| simulation/mujoco/runs/p038-watch-66533e4d6ee049e69fefd0a8868ea15f | simulation/mujoco/training/camera-manipulation/runs/p038-watch-66533e4d6ee049e69fefd0a8868ea15f | P038 environment configuration in run.json | 1 artifact references; 1 source references |
| simulation/mujoco/runs/p038-watch-8ac0f96afa204b4f89e47c6223ccd7d7 | simulation/mujoco/training/camera-manipulation/runs/p038-watch-8ac0f96afa204b4f89e47c6223ccd7d7 | P038 environment configuration in run.json | 1 artifact references; 1 source references |
| simulation/mujoco/runs/p038-watch-a78905bbeb434d98ba57510309149008 | simulation/mujoco/training/camera-manipulation/runs/p038-watch-a78905bbeb434d98ba57510309149008 | P038 environment configuration in run.json | 1 artifact references; 1 source references |
| simulation/mujoco/runs/perception-35db463470694710be253e9b3cda2a84 | simulation/mujoco/examples/validate_native_perception/runs/perception-35db463470694710be253e9b3cda2a84 | Native perception report | 0 artifact references; 1 source references |
| simulation/mujoco/runs/playground-002fe0ca9cf14946b3deb635f6ca3999.json | Preserve pending classification | Origin unresolved; preserve in place pending content/dependency review | 0 artifact references; 0 source references |
| simulation/mujoco/runs/playground-00fb3660ad984b969037a6173622c442.json | Preserve pending classification | Origin unresolved; preserve in place pending content/dependency review | 0 artifact references; 0 source references |
| simulation/mujoco/runs/playground-067862e6fb374578b9575870b90fd23c.json | Preserve pending classification | Origin unresolved; preserve in place pending content/dependency review | 0 artifact references; 0 source references |
| simulation/mujoco/runs/playground-0a420555771c484cbb9ff029b4557c77.json | Preserve pending classification | Origin unresolved; preserve in place pending content/dependency review | 0 artifact references; 0 source references |
| simulation/mujoco/runs/playground-0c091083a4ed4761af03de6b0ca46c99.json | Preserve pending classification | Origin unresolved; preserve in place pending content/dependency review | 0 artifact references; 0 source references |
| simulation/mujoco/runs/playground-11f595c7550a40f7b9bad8a4109086dd.json | Preserve pending classification | Origin unresolved; preserve in place pending content/dependency review | 0 artifact references; 0 source references |
| simulation/mujoco/runs/playground-131be079de194528a9eb41f83385becb.json | Preserve pending classification | Origin unresolved; preserve in place pending content/dependency review | 0 artifact references; 0 source references |
| simulation/mujoco/runs/playground-1f672fe564f4436eb3b19233bdb00d0e.json | Preserve pending classification | Origin unresolved; preserve in place pending content/dependency review | 0 artifact references; 0 source references |
| simulation/mujoco/runs/playground-23f32ad4262b411d8053ecc5e527c1cf.json | Preserve pending classification | Origin unresolved; preserve in place pending content/dependency review | 0 artifact references; 0 source references |
| simulation/mujoco/runs/playground-27030f4d5a3846388efe8b510920bd63.json | Preserve pending classification | Origin unresolved; preserve in place pending content/dependency review | 0 artifact references; 0 source references |
| simulation/mujoco/runs/playground-29629a40929640c2b18d6f452f941ac3.json | Preserve pending classification | Origin unresolved; preserve in place pending content/dependency review | 0 artifact references; 0 source references |
| simulation/mujoco/runs/playground-2bcc96973ac141288c07267fece26de3.json | Preserve pending classification | Origin unresolved; preserve in place pending content/dependency review | 0 artifact references; 0 source references |
| simulation/mujoco/runs/playground-2c58fc12b776416dba2d89dda1e2cd1b.json | Preserve pending classification | Origin unresolved; preserve in place pending content/dependency review | 0 artifact references; 0 source references |
| simulation/mujoco/runs/playground-2dc1fb3dc02f41c09785ee12c05ce7e7.json | Preserve pending classification | Origin unresolved; preserve in place pending content/dependency review | 0 artifact references; 0 source references |
| simulation/mujoco/runs/playground-2e092d729cab4dfda5ddb6e788240bc5.json | Preserve pending classification | Origin unresolved; preserve in place pending content/dependency review | 0 artifact references; 0 source references |
| simulation/mujoco/runs/playground-2f6ed3530faf4dc38062886861eb7ddb.json | Preserve pending classification | Origin unresolved; preserve in place pending content/dependency review | 0 artifact references; 0 source references |
| simulation/mujoco/runs/playground-30c7475fc54c46e1a230441566044973.json | Preserve pending classification | Origin unresolved; preserve in place pending content/dependency review | 0 artifact references; 0 source references |
| simulation/mujoco/runs/playground-322a070686bc4b02812153e7dc5f2ca8.json | Preserve pending classification | Origin unresolved; preserve in place pending content/dependency review | 0 artifact references; 0 source references |
| simulation/mujoco/runs/playground-32fe0f6c17464afda1005b27904f83ee.json | Preserve pending classification | Origin unresolved; preserve in place pending content/dependency review | 0 artifact references; 0 source references |
| simulation/mujoco/runs/playground-347c9c335c9e4b6695a469f1ab482594.json | Preserve pending classification | Origin unresolved; preserve in place pending content/dependency review | 0 artifact references; 0 source references |
| simulation/mujoco/runs/playground-38dd90daf16b490dbedc13962d7ed044.json | Preserve pending classification | Origin unresolved; preserve in place pending content/dependency review | 0 artifact references; 0 source references |
| simulation/mujoco/runs/playground-38e40ce02aea471cbc90e5a12ff179cd.json | Preserve pending classification | Origin unresolved; preserve in place pending content/dependency review | 0 artifact references; 0 source references |
| simulation/mujoco/runs/playground-39d415f38b654917a16fb01f27126554.json | Preserve pending classification | Origin unresolved; preserve in place pending content/dependency review | 0 artifact references; 0 source references |
| simulation/mujoco/runs/playground-3b3b5481e83c4da38119e2dab9d59648.json | Preserve pending classification | Origin unresolved; preserve in place pending content/dependency review | 0 artifact references; 0 source references |
| simulation/mujoco/runs/playground-3c545623db4a482e88195236befd4953.json | Preserve pending classification | Origin unresolved; preserve in place pending content/dependency review | 0 artifact references; 0 source references |
| simulation/mujoco/runs/playground-3e784f977d394bc6bc06a88f256ca309.json | Preserve pending classification | Origin unresolved; preserve in place pending content/dependency review | 0 artifact references; 0 source references |
| simulation/mujoco/runs/playground-3fafeb5b0f764b24ac2136907460a9af.json | Preserve pending classification | Origin unresolved; preserve in place pending content/dependency review | 0 artifact references; 0 source references |
| simulation/mujoco/runs/playground-411b750afa734b1588f4b90389cc9ef2.json | Preserve pending classification | Origin unresolved; preserve in place pending content/dependency review | 0 artifact references; 0 source references |
| simulation/mujoco/runs/playground-413ab05944bf48d9bd0c59c8c7dd2d70.json | Preserve pending classification | Origin unresolved; preserve in place pending content/dependency review | 0 artifact references; 0 source references |
| simulation/mujoco/runs/playground-41ae810d17b24625a35f0be06b3424c9.json | Preserve pending classification | Origin unresolved; preserve in place pending content/dependency review | 0 artifact references; 0 source references |
| simulation/mujoco/runs/playground-41bb9b0578bc43e38ac533ffcef664dd.json | Preserve pending classification | Origin unresolved; preserve in place pending content/dependency review | 0 artifact references; 0 source references |
| simulation/mujoco/runs/playground-435ec32d943e4a5a8885e709b6c703b5.json | Preserve pending classification | Origin unresolved; preserve in place pending content/dependency review | 0 artifact references; 0 source references |
| simulation/mujoco/runs/playground-45a6b36c0fe4456a9affdbff4b46ac45.json | Preserve pending classification | Origin unresolved; preserve in place pending content/dependency review | 0 artifact references; 0 source references |
| simulation/mujoco/runs/playground-4ce5282f87bb4a069dad72916f4c57fb.json | Preserve pending classification | Origin unresolved; preserve in place pending content/dependency review | 0 artifact references; 0 source references |
| simulation/mujoco/runs/playground-50f7cbb547464cffbb072e109c9b750c.json | Preserve pending classification | Origin unresolved; preserve in place pending content/dependency review | 0 artifact references; 0 source references |
| simulation/mujoco/runs/playground-5283247310534fdaa85adc0659ad164f.json | Preserve pending classification | Origin unresolved; preserve in place pending content/dependency review | 0 artifact references; 0 source references |
| simulation/mujoco/runs/playground-52a207d6cb1845789913fcbd7812fee3.json | Preserve pending classification | Origin unresolved; preserve in place pending content/dependency review | 0 artifact references; 0 source references |
| simulation/mujoco/runs/playground-53f688e326b14604a9ae52cbc77ff30c.json | Preserve pending classification | Origin unresolved; preserve in place pending content/dependency review | 0 artifact references; 0 source references |
| simulation/mujoco/runs/playground-55a5cb4b9bd54c8db3da7f687344579d.json | Preserve pending classification | Origin unresolved; preserve in place pending content/dependency review | 0 artifact references; 0 source references |
| simulation/mujoco/runs/playground-58f8416979f246018de22e9a0381bb7d.json | Preserve pending classification | Origin unresolved; preserve in place pending content/dependency review | 0 artifact references; 0 source references |
| simulation/mujoco/runs/playground-599539687932422ca01377f823f576e0.json | Preserve pending classification | Origin unresolved; preserve in place pending content/dependency review | 0 artifact references; 0 source references |
| simulation/mujoco/runs/playground-5b9095c2bd9448c7a790865717e3bcf4.json | Preserve pending classification | Origin unresolved; preserve in place pending content/dependency review | 0 artifact references; 0 source references |
| simulation/mujoco/runs/playground-5bfa67ca1f6a4eb4a4e000428ffa71f3.json | Preserve pending classification | Origin unresolved; preserve in place pending content/dependency review | 0 artifact references; 0 source references |
| simulation/mujoco/runs/playground-5ea5290afd08403a9da9f416737f92e5.json | Preserve pending classification | Origin unresolved; preserve in place pending content/dependency review | 0 artifact references; 0 source references |
| simulation/mujoco/runs/playground-6445a7433d824297bbbb3c9486a7e30a.json | Preserve pending classification | Origin unresolved; preserve in place pending content/dependency review | 0 artifact references; 0 source references |
| simulation/mujoco/runs/playground-6480220774974d979303c9bc198578d7.json | Preserve pending classification | Origin unresolved; preserve in place pending content/dependency review | 0 artifact references; 0 source references |
| simulation/mujoco/runs/playground-66ee6e1f1fc54726b68c71a98e80c776.json | Preserve pending classification | Origin unresolved; preserve in place pending content/dependency review | 0 artifact references; 0 source references |
| simulation/mujoco/runs/playground-67a7155035304c56a59f038310bf2408.json | Preserve pending classification | Origin unresolved; preserve in place pending content/dependency review | 0 artifact references; 0 source references |
| simulation/mujoco/runs/playground-70d12dc90f234e49936a3dd88ff324c3.json | Preserve pending classification | Origin unresolved; preserve in place pending content/dependency review | 0 artifact references; 0 source references |
| simulation/mujoco/runs/playground-70fa191bdb764763bf80dc4f6ca66f22.json | Preserve pending classification | Origin unresolved; preserve in place pending content/dependency review | 0 artifact references; 0 source references |
| simulation/mujoco/runs/playground-71a31b7cd7a94f37b41d99ad10221546.json | Preserve pending classification | Origin unresolved; preserve in place pending content/dependency review | 0 artifact references; 0 source references |
| simulation/mujoco/runs/playground-72331b086058488c81c35bb1ee490895.json | Preserve pending classification | Origin unresolved; preserve in place pending content/dependency review | 0 artifact references; 0 source references |
| simulation/mujoco/runs/playground-739c9740bef9497994a624db496ec273.json | Preserve pending classification | Origin unresolved; preserve in place pending content/dependency review | 0 artifact references; 0 source references |
| simulation/mujoco/runs/playground-7706b5b01f624dd29b8505a89c317415.json | Preserve pending classification | Origin unresolved; preserve in place pending content/dependency review | 0 artifact references; 0 source references |
| simulation/mujoco/runs/playground-8668acc394d148f8a4da7fb1ba2eabdb.json | Preserve pending classification | Origin unresolved; preserve in place pending content/dependency review | 0 artifact references; 0 source references |
| simulation/mujoco/runs/playground-86ea0329304844a7a995dd1a6839b9c7.json | Preserve pending classification | Origin unresolved; preserve in place pending content/dependency review | 0 artifact references; 0 source references |
| simulation/mujoco/runs/playground-872f2e84c6ce43458bf80d66388091ed.json | Preserve pending classification | Origin unresolved; preserve in place pending content/dependency review | 0 artifact references; 0 source references |
| simulation/mujoco/runs/playground-88974c818a1840eb9f0cceaf2dc51e7c.json | Preserve pending classification | Origin unresolved; preserve in place pending content/dependency review | 0 artifact references; 0 source references |
| simulation/mujoco/runs/playground-88dfcc6505224132bab3be3e9217efbb.json | Preserve pending classification | Origin unresolved; preserve in place pending content/dependency review | 0 artifact references; 0 source references |
| simulation/mujoco/runs/playground-8cd28e82770b4181b5d90cfc999e842a.json | Preserve pending classification | Origin unresolved; preserve in place pending content/dependency review | 0 artifact references; 0 source references |
| simulation/mujoco/runs/playground-8fc4c2bdbfa04ae5aca54dbc563fd207.json | Preserve pending classification | Origin unresolved; preserve in place pending content/dependency review | 0 artifact references; 0 source references |
| simulation/mujoco/runs/playground-923375f551fa4bee9e7e5f911d8c0a7d.json | Preserve pending classification | Origin unresolved; preserve in place pending content/dependency review | 0 artifact references; 0 source references |
| simulation/mujoco/runs/playground-946b6af151cc49ac993f13a839c41024.json | Preserve pending classification | Origin unresolved; preserve in place pending content/dependency review | 0 artifact references; 0 source references |
| simulation/mujoco/runs/playground-9883ceddf5f94b16b7cdde7edd13e523.json | Preserve pending classification | Origin unresolved; preserve in place pending content/dependency review | 0 artifact references; 0 source references |
| simulation/mujoco/runs/playground-98f6fd1a9fe040b299e96983b92bacc1.json | Preserve pending classification | Origin unresolved; preserve in place pending content/dependency review | 0 artifact references; 0 source references |
| simulation/mujoco/runs/playground-9a0a54a420fa42a6957bbcdfaf166d4a.json | Preserve pending classification | Origin unresolved; preserve in place pending content/dependency review | 0 artifact references; 0 source references |
| simulation/mujoco/runs/playground-9ab7f99f7aa14d9d909557066264d5f0.json | Preserve pending classification | Origin unresolved; preserve in place pending content/dependency review | 0 artifact references; 0 source references |
| simulation/mujoco/runs/playground-9cb8e43de3c34a45aaba21b919960935.json | Preserve pending classification | Origin unresolved; preserve in place pending content/dependency review | 0 artifact references; 0 source references |
| simulation/mujoco/runs/playground-9f1b0acf32ea42fa8414f1de73f9c9f7.json | Preserve pending classification | Origin unresolved; preserve in place pending content/dependency review | 0 artifact references; 0 source references |
| simulation/mujoco/runs/playground-a0eb24b1157d4805afec4d76153e56e4.json | Preserve pending classification | Origin unresolved; preserve in place pending content/dependency review | 0 artifact references; 0 source references |
| simulation/mujoco/runs/playground-a42c80efc0cb44ddbf146853bdd9e434.json | Preserve pending classification | Origin unresolved; preserve in place pending content/dependency review | 0 artifact references; 0 source references |
| simulation/mujoco/runs/playground-a4f2859b30494c50b17927e0640f4fa5.json | Preserve pending classification | Origin unresolved; preserve in place pending content/dependency review | 0 artifact references; 0 source references |
| simulation/mujoco/runs/playground-acd21fd323cd44398ad81f2ab8e03de7.json | Preserve pending classification | Origin unresolved; preserve in place pending content/dependency review | 0 artifact references; 0 source references |
| simulation/mujoco/runs/playground-ae09a330a0ad45faa87e77ab75712d9c.json | Preserve pending classification | Origin unresolved; preserve in place pending content/dependency review | 0 artifact references; 0 source references |
| simulation/mujoco/runs/playground-afbdb51059ee4b17ae030b77c87b718b.json | Preserve pending classification | Origin unresolved; preserve in place pending content/dependency review | 0 artifact references; 0 source references |
| simulation/mujoco/runs/playground-b1e94001d9c1417aa76804c18f08a56d.json | Preserve pending classification | Origin unresolved; preserve in place pending content/dependency review | 0 artifact references; 0 source references |
| simulation/mujoco/runs/playground-b4114d89a7a84d6e85d5e46dd1bf2b3e.json | Preserve pending classification | Origin unresolved; preserve in place pending content/dependency review | 0 artifact references; 0 source references |
| simulation/mujoco/runs/playground-bcba34e3f9044a83b3babb602bbf453f.json | Preserve pending classification | Origin unresolved; preserve in place pending content/dependency review | 0 artifact references; 0 source references |
| simulation/mujoco/runs/playground-be23c1d4581e4ba59a426a34b4b25eed.json | Preserve pending classification | Origin unresolved; preserve in place pending content/dependency review | 0 artifact references; 0 source references |
| simulation/mujoco/runs/playground-board-v1 | simulation/mujoco/assets/bundles/playground-board-v1 | Has hashed model manifest; shared consumers require path review | 0 artifact references; 5 source references |
| simulation/mujoco/runs/playground-c12555342ae149e2b9ce1bf8adf20644.json | Preserve pending classification | Origin unresolved; preserve in place pending content/dependency review | 0 artifact references; 0 source references |
| simulation/mujoco/runs/playground-c60e62a9b3ab4564b2ba4d894e94b3e0.json | Preserve pending classification | Origin unresolved; preserve in place pending content/dependency review | 0 artifact references; 0 source references |
| simulation/mujoco/runs/playground-c6a20edefc154d2aa4d29d6435641725.json | Preserve pending classification | Origin unresolved; preserve in place pending content/dependency review | 0 artifact references; 0 source references |
| simulation/mujoco/runs/playground-c6b2475f2e81428faad9766495fdc617.json | Preserve pending classification | Origin unresolved; preserve in place pending content/dependency review | 0 artifact references; 0 source references |
| simulation/mujoco/runs/playground-c7e24195ae6e49a7bfcedcaf347f554a.json | Preserve pending classification | Origin unresolved; preserve in place pending content/dependency review | 0 artifact references; 0 source references |
| simulation/mujoco/runs/playground-c7e56eea3962415eabece7b1cf7b5689.json | Preserve pending classification | Origin unresolved; preserve in place pending content/dependency review | 0 artifact references; 0 source references |
| simulation/mujoco/runs/playground-c8436f1fdd594fb5a9e750473119e3fb.json | Preserve pending classification | Origin unresolved; preserve in place pending content/dependency review | 0 artifact references; 0 source references |
| simulation/mujoco/runs/playground-cbb350ae410541cc8c0df1955962ef33.json | Preserve pending classification | Origin unresolved; preserve in place pending content/dependency review | 0 artifact references; 0 source references |
| simulation/mujoco/runs/playground-cbebfea309a74e1aaa25295541bb2411.json | Preserve pending classification | Origin unresolved; preserve in place pending content/dependency review | 0 artifact references; 0 source references |
| simulation/mujoco/runs/playground-d5d88f52dc3244499543d898cd77c763.json | Preserve pending classification | Origin unresolved; preserve in place pending content/dependency review | 0 artifact references; 0 source references |
| simulation/mujoco/runs/playground-d81fd6c245464b8295c1b4898cb0cb75.json | Preserve pending classification | Origin unresolved; preserve in place pending content/dependency review | 0 artifact references; 0 source references |
| simulation/mujoco/runs/playground-d96f6722e6fe46eeb10de35c23447204.json | Preserve pending classification | Origin unresolved; preserve in place pending content/dependency review | 0 artifact references; 0 source references |
| simulation/mujoco/runs/playground-dd0f34fae3d243db9852b1a298499742.json | Preserve pending classification | Origin unresolved; preserve in place pending content/dependency review | 0 artifact references; 0 source references |
| simulation/mujoco/runs/playground-deec2327d1684f6392dca03c91ac56ff.json | Preserve pending classification | Origin unresolved; preserve in place pending content/dependency review | 0 artifact references; 0 source references |
| simulation/mujoco/runs/playground-e240dbdc6c304685a4bc09ca84b9e9a7.json | Preserve pending classification | Origin unresolved; preserve in place pending content/dependency review | 0 artifact references; 0 source references |
| simulation/mujoco/runs/playground-e27b7b4fba5c4dbca37ccd9c31f2d027.json | Preserve pending classification | Origin unresolved; preserve in place pending content/dependency review | 0 artifact references; 0 source references |
| simulation/mujoco/runs/playground-e2d04e188d4f41b8b860b2369fa827de.json | Preserve pending classification | Origin unresolved; preserve in place pending content/dependency review | 0 artifact references; 0 source references |
| simulation/mujoco/runs/playground-e33d80b662254cce90f76c26f8a08e57.json | Preserve pending classification | Origin unresolved; preserve in place pending content/dependency review | 0 artifact references; 0 source references |
| simulation/mujoco/runs/playground-e5c576364b4f45188b05931443ede270.json | Preserve pending classification | Origin unresolved; preserve in place pending content/dependency review | 0 artifact references; 0 source references |
| simulation/mujoco/runs/playground-e677290dd580450793b6d733152d9f3f.json | Preserve pending classification | Origin unresolved; preserve in place pending content/dependency review | 0 artifact references; 0 source references |
| simulation/mujoco/runs/playground-e750f9bcdd7e40c8b0a3328ffa4bf557.json | Preserve pending classification | Origin unresolved; preserve in place pending content/dependency review | 0 artifact references; 0 source references |
| simulation/mujoco/runs/playground-e870938920e44c3ba982c14cb1de5749.json | Preserve pending classification | Origin unresolved; preserve in place pending content/dependency review | 0 artifact references; 0 source references |
| simulation/mujoco/runs/playground-e9c7f36469eb453492bbde9268ededad.json | Preserve pending classification | Origin unresolved; preserve in place pending content/dependency review | 0 artifact references; 0 source references |
| simulation/mujoco/runs/playground-ebf96127fd1242cbb73d3992926dd0ac.json | Preserve pending classification | Origin unresolved; preserve in place pending content/dependency review | 0 artifact references; 0 source references |
| simulation/mujoco/runs/playground-edb2a7e9646249f1be31dade08d70bed.json | Preserve pending classification | Origin unresolved; preserve in place pending content/dependency review | 0 artifact references; 0 source references |
| simulation/mujoco/runs/playground-f04566c538704969a4c211bc3a78274a.json | Preserve pending classification | Origin unresolved; preserve in place pending content/dependency review | 0 artifact references; 0 source references |
| simulation/mujoco/runs/playground-f1d0996bc860406bb3d46e2bb30c4604.json | Preserve pending classification | Origin unresolved; preserve in place pending content/dependency review | 0 artifact references; 0 source references |
| simulation/mujoco/runs/playground-f31758abd8ef4187966df8d89b3e1738.json | Preserve pending classification | Origin unresolved; preserve in place pending content/dependency review | 0 artifact references; 0 source references |
| simulation/mujoco/runs/playground-f52cc923dd4d4c818f7fcd37d7c324de.json | Preserve pending classification | Origin unresolved; preserve in place pending content/dependency review | 0 artifact references; 0 source references |
| simulation/mujoco/runs/playground-f58ebf3d9265440690c83e884cf520af.json | Preserve pending classification | Origin unresolved; preserve in place pending content/dependency review | 0 artifact references; 0 source references |
| simulation/mujoco/runs/playground-fc77c4599db543038d0b3c3a0df074de.json | Preserve pending classification | Origin unresolved; preserve in place pending content/dependency review | 0 artifact references; 0 source references |
| simulation/mujoco/runs/playground-fcee43a3e67345e5848de7d49e41086e.json | Preserve pending classification | Origin unresolved; preserve in place pending content/dependency review | 0 artifact references; 0 source references |
| simulation/mujoco/runs/playground-ffa6f8bda0754cc29bc896b53d46d8f3.json | Preserve pending classification | Origin unresolved; preserve in place pending content/dependency review | 0 artifact references; 0 source references |
| simulation/mujoco/runs/playground-fingertip-only-v1 | simulation/mujoco/assets/bundles/playground-fingertip-only-v1 | Has hashed model manifest; shared consumers require path review | 0 artifact references; 58 source references |
| simulation/mujoco/runs/playground-graveyard-grid-v1 | simulation/mujoco/assets/bundles/playground-graveyard-grid-v1 | Has hashed model manifest; shared consumers require path review | 0 artifact references; 1 source references |
| simulation/mujoco/runs/playground-graveyard-grid-v2 | simulation/mujoco/assets/bundles/playground-graveyard-grid-v2 | Has hashed model manifest; shared consumers require path review | 0 artifact references; 3 source references |
| simulation/mujoco/runs/playground-graveyard-v1 | simulation/mujoco/assets/bundles/playground-graveyard-v1 | Has hashed model manifest; shared consumers require path review | 0 artifact references; 1 source references |
| simulation/mujoco/runs/playground-gripper-hulls-v1 | simulation/mujoco/assets/bundles/playground-gripper-hulls-v1 | Has hashed model manifest; shared consumers require path review | 0 artifact references; 1 source references |
| simulation/mujoco/runs/playground-home-graveyards-v1 | simulation/mujoco/assets/bundles/playground-home-graveyards-v1 | Has hashed model manifest; shared consumers require path review | 0 artifact references; 1 source references |
| simulation/mujoco/runs/playground-official-visuals-lod-v1 | simulation/mujoco/assets/bundles/playground-official-visuals-lod-v1 | Has hashed model manifest; shared consumers require path review | 0 artifact references; 1 source references |
| simulation/mujoco/runs/playground-official-visuals-v1 | simulation/mujoco/assets/bundles/playground-official-visuals-v1 | Has hashed model manifest; shared consumers require path review | 0 artifact references; 1 source references |
| simulation/mujoco/runs/playground-reachable-board-v1 | simulation/mujoco/assets/bundles/playground-reachable-board-v1 | Has hashed model manifest; shared consumers require path review | 0 artifact references; 1 source references |
| simulation/mujoco/runs/preview-check-deffc967db9a458fb37ce269ee71d52e | simulation/mujoco/examples/prepare_capture_task/runs/preview-check-deffc967db9a458fb37ce269ee71d52e | Capture evidence report | 0 artifact references; 1 source references |
| simulation/mujoco/runs/prototype-v1 | simulation/mujoco/assets/bundles/prototype-v1 | Has hashed model manifest; shared consumers require path review | 0 artifact references; 3 source references |
| simulation/mujoco/runs/readme-check-18424bf448144c8ea2aa867dd8681869 | Preserve pending classification | Origin unresolved; preserve in place pending content/dependency review | 12 artifact references; 1 source references |
| simulation/mujoco/runs/rgb-capture-106dc930c19e4498a5e5d8f9087675a3 | simulation/mujoco/examples/prepare_capture_task/runs/rgb-capture-106dc930c19e4498a5e5d8f9087675a3 | Capture evidence report | 0 artifact references; 1 source references |
| simulation/mujoco/runs/rgb-capture-120d8b3537a04205b69adcf8caa74cd3 | simulation/mujoco/examples/prepare_capture_task/runs/rgb-capture-120d8b3537a04205b69adcf8caa74cd3 | Capture evidence report | 0 artifact references; 1 source references |
| simulation/mujoco/runs/rgb-capture-2bac522c0b5b4256a430767cf16be1eb | simulation/mujoco/examples/prepare_capture_task/runs/rgb-capture-2bac522c0b5b4256a430767cf16be1eb | Capture evidence report | 0 artifact references; 1 source references |
| simulation/mujoco/runs/rgb-capture-2d82f63ff1234d4abc3f339092bf91df | simulation/mujoco/examples/prepare_capture_task/runs/rgb-capture-2d82f63ff1234d4abc3f339092bf91df | Capture evidence report | 0 artifact references; 1 source references |
| simulation/mujoco/runs/rgb-capture-2e2b4bd3e9224f05a7333caf2c243430 | simulation/mujoco/examples/prepare_capture_task/runs/rgb-capture-2e2b4bd3e9224f05a7333caf2c243430 | Capture evidence report | 0 artifact references; 1 source references |
| simulation/mujoco/runs/rgb-capture-3d1163438ff44f51a789737d8edce99a | simulation/mujoco/examples/prepare_capture_task/runs/rgb-capture-3d1163438ff44f51a789737d8edce99a | Capture evidence report | 0 artifact references; 1 source references |
| simulation/mujoco/runs/rgb-capture-966977a780d24d88b60ba324f82f6e00 | Preserve pending classification | Origin unresolved; preserve in place pending content/dependency review | 0 artifact references; 1 source references |
| simulation/mujoco/runs/rgb-capture-9a4581f99ee24a2f8f2f12e21e31fcb7 | simulation/mujoco/examples/prepare_capture_task/runs/rgb-capture-9a4581f99ee24a2f8f2f12e21e31fcb7 | Capture evidence report | 0 artifact references; 1 source references |
| simulation/mujoco/runs/rgb-capture-b5a9b7926cf54c939b145f9bafb113b9 | simulation/mujoco/examples/prepare_capture_task/runs/rgb-capture-b5a9b7926cf54c939b145f9bafb113b9 | Capture evidence report | 0 artifact references; 1 source references |
| simulation/mujoco/runs/rgb-capture-da609c442e8a492da7b0ee4cc5f4fde8 | Preserve pending classification | Origin unresolved; preserve in place pending content/dependency review | 1 artifact references; 1 source references |
| simulation/mujoco/runs/scene-build-v2.json | Preserve pending classification | Origin unresolved; preserve in place pending content/dependency review | 0 artifact references; 0 source references |
| simulation/mujoco/runs/side-camera-1c28f13bb8a74dbcbcf185fb5c0817d4 | Preserve pending classification | Origin unresolved; preserve in place pending content/dependency review | 10 artifact references; 1 source references |
| simulation/mujoco/runs/side-camera-check-5abbbe6f104b4ed5a7b2f8d86516449c | Preserve pending classification | Origin unresolved; preserve in place pending content/dependency review | 4 artifact references; 1 source references |
| simulation/mujoco/runs/upright-chess-v2 | simulation/mujoco/assets/bundles/upright-chess-v2 | Has hashed model manifest; shared consumers require path review | 0 artifact references; 1 source references |
| simulation/mujoco/runs/upright-chess-v2.ppm | Preserve pending classification | Origin unresolved; preserve in place pending content/dependency review | 0 artifact references; 0 source references |
| simulation/mujoco/runs/upright-chess-v3 | simulation/mujoco/assets/bundles/upright-chess-v3 | Has hashed model manifest; shared consumers require path review | 0 artifact references; 5 source references |
| simulation/mujoco/runs/vision-high-41d8f4f5c4914899bef1bcd9374b286e | simulation/mujoco/examples/validate_board_reference/runs/vision-high-41d8f4f5c4914899bef1bcd9374b286e | Marker-layout qualification report | 37 artifact references; 1 source references |
| simulation/mujoco/runs/vision-test-0655f2e72c004224985e56809995af46 | simulation/mujoco/examples/validate_board_reference/runs/vision-test-0655f2e72c004224985e56809995af46 | Marker-layout qualification report | 37 artifact references; 1 source references |
| simulation/mujoco/runs/visual-grasp-0a3e3435c49f4f238095f0e536726941 | simulation/mujoco/training/grasp-lift/runs/visual-grasp-0a3e3435c49f4f238095f0e536726941 | Legacy environment metadata in run.json | 0 artifact references; 1 source references |
| simulation/mujoco/runs/visual-grasp-48864f82642c4f8a9333d7cac14a22a2 | simulation/mujoco/training/grasp-lift/runs/visual-grasp-48864f82642c4f8a9333d7cac14a22a2 | Legacy environment metadata in run.json | 0 artifact references; 1 source references |
| simulation/mujoco/runs/visual-grasp-7b93fb512ad144b3ac930bed0f580a5d | simulation/mujoco/training/grasp-lift/runs/visual-grasp-7b93fb512ad144b3ac930bed0f580a5d | Legacy environment metadata in run.json | 0 artifact references; 1 source references |
| simulation/mujoco/runs/visual-grasp-camera-v3-first | simulation/mujoco/training/grasp-lift/runs/visual-grasp-camera-v3-first | Legacy environment metadata in run.json | 0 artifact references; 1 source references |
| simulation/mujoco/runs/visual-grasp-camera-v3-first.stderr.log | Preserve pending classification | Origin unresolved; preserve in place pending content/dependency review | 0 artifact references; 0 source references |
| simulation/mujoco/runs/visual-grasp-camera-v3-first.stdout.log | Preserve pending classification | Origin unresolved; preserve in place pending content/dependency review | 0 artifact references; 0 source references |
| simulation/mujoco/runs/visual-grasp-db957681cbb34710ad5fa15104c0c271 | simulation/mujoco/training/grasp-lift/runs/visual-grasp-db957681cbb34710ad5fa15104c0c271 | Legacy environment metadata in run.json | 0 artifact references; 1 source references |
| simulation/mujoco/runs/visual-grasp-ddd95ff620b843ea8f06f4a10956760d | simulation/mujoco/training/grasp-lift/runs/visual-grasp-ddd95ff620b843ea8f06f4a10956760d | Legacy environment metadata in run.json | 0 artifact references; 1 source references |
| simulation/mujoco/runs/visual-grasp-features-v1 | simulation/mujoco/training/grasp-lift/runs/visual-grasp-features-v1 | Legacy environment metadata in run.json | 2 artifact references; 1 source references |
| simulation/mujoco/runs/visual-grasp-features-v1.stderr.log | Preserve pending classification | Origin unresolved; preserve in place pending content/dependency review | 0 artifact references; 0 source references |
| simulation/mujoco/runs/visual-grasp-features-v1.stdout.log | Preserve pending classification | Origin unresolved; preserve in place pending content/dependency review | 0 artifact references; 0 source references |
| simulation/mujoco/runs/visual-grasp-ffc485a0ff4a438895f748d2561f4ea8 | simulation/mujoco/training/grasp-lift/runs/visual-grasp-ffc485a0ff4a438895f748d2561f4ea8 | Legacy environment metadata in run.json | 0 artifact references; 1 source references |
| simulation/mujoco/runs/visual-grasp-first | Preserve pending classification | Origin unresolved; preserve in place pending content/dependency review | 0 artifact references; 1 source references |
| simulation/mujoco/runs/visual-grasp-warm-full-open-v1 | simulation/mujoco/training/grasp-lift/runs/visual-grasp-warm-full-open-v1 | Legacy environment metadata in run.json | 2 artifact references; 1 source references |
| simulation/mujoco/runs/visual-grasp-warm-full-open-v1.stderr.log | Preserve pending classification | Origin unresolved; preserve in place pending content/dependency review | 0 artifact references; 0 source references |
| simulation/mujoco/runs/visual-grasp-warm-full-open-v1.stdout.log | Preserve pending classification | Origin unresolved; preserve in place pending content/dependency review | 0 artifact references; 0 source references |
| simulation/mujoco/runs/visual-grasp-warm-v3 | simulation/mujoco/training/grasp-lift/runs/visual-grasp-warm-v3 | Legacy environment metadata in run.json | 2 artifact references; 1 source references |
| simulation/mujoco/runs/visual-grasp-warm-v3.stderr.log | Preserve pending classification | Origin unresolved; preserve in place pending content/dependency review | 0 artifact references; 0 source references |
| simulation/mujoco/runs/visual-grasp-warm-v3.stdout.log | Preserve pending classification | Origin unresolved; preserve in place pending content/dependency review | 0 artifact references; 0 source references |
| simulation/mujoco/runs/visual-lift-21628dc49b1c460b8301be585ec232aa | simulation/mujoco/training/grasp-lift/runs/visual-lift-21628dc49b1c460b8301be585ec232aa | Legacy environment metadata in run.json | 0 artifact references; 1 source references |
| simulation/mujoco/runs/visual-lift-camera-v3-20000 | simulation/mujoco/training/grasp-lift/runs/visual-lift-camera-v3-20000 | Legacy environment metadata in run.json | 1 artifact references; 2 source references |
| simulation/mujoco/runs/visual-lift-camera-v3-20000.stderr.log | Preserve pending classification | Origin unresolved; preserve in place pending content/dependency review | 0 artifact references; 0 source references |
| simulation/mujoco/runs/visual-lift-camera-v3-20000.stdout.log | Preserve pending classification | Origin unresolved; preserve in place pending content/dependency review | 0 artifact references; 0 source references |
| simulation/mujoco/runs/visual-lift-controls-v2 | simulation/mujoco/training/grasp-lift/runs/visual-lift-controls-v2 | Legacy environment metadata in run.json | 0 artifact references; 1 source references |
| simulation/mujoco/runs/visual-lift-cuda-smoke-v2 | simulation/mujoco/training/grasp-lift/runs/visual-lift-cuda-smoke-v2 | Legacy environment metadata in run.json | 0 artifact references; 2 source references |
| simulation/mujoco/runs/visual-lift-cuda-smoke-v2b | simulation/mujoco/training/grasp-lift/runs/visual-lift-cuda-smoke-v2b | Legacy environment metadata in run.json | 0 artifact references; 1 source references |
| simulation/mujoco/runs/visual-lift-cuda-v3-smoke | simulation/mujoco/training/grasp-lift/runs/visual-lift-cuda-v3-smoke | Legacy environment metadata in run.json | 0 artifact references; 1 source references |
| simulation/mujoco/runs/visual-lift-v3-stop-test | simulation/mujoco/training/grasp-lift/runs/visual-lift-v3-stop-test | Legacy environment metadata in run.json | 1 artifact references; 1 source references |
| simulation/mujoco/runs/visual-lift-visible-smoke-v2 | simulation/mujoco/training/grasp-lift/runs/visual-lift-visible-smoke-v2 | Legacy environment metadata in run.json | 0 artifact references; 1 source references |
| simulation/mujoco/runs/visual-lift-visible-v2b | simulation/mujoco/training/grasp-lift/runs/visual-lift-visible-v2b | Legacy environment metadata in run.json | 0 artifact references; 1 source references |
| simulation/mujoco/runs/wrist-3bae6a467403465bb84b56e1306409e6 | simulation/mujoco/assets/bundles/wrist-3bae6a467403465bb84b56e1306409e6 | Has hashed model manifest; shared consumers require path review | 0 artifact references; 1 source references |

## Checkpoints

Optimizer presence alone does not prove resumability. Original environment,
configuration, libraries, source signatures and policy spaces must agree.
The current wrist profile adds a commanded joint while P038 still declares
four policy actions and five commanded joints. No recorded policy is qualified
for wrist control by this inventory.

| Checkpoint | Optimizer present | Resume status |
|---|---|---|
| simulation/mujoco/runs/grasp-fast-4-workers/checkpoint-100352.zip | True | pending full environment/provenance validation |
| simulation/mujoco/runs/grasp-fast-4-workers/checkpoint-102400.zip | True | pending full environment/provenance validation |
| simulation/mujoco/runs/grasp-fast-4-workers/checkpoint-104448.zip | True | pending full environment/provenance validation |
| simulation/mujoco/runs/grasp-fast-4-workers/checkpoint-106496.zip | True | pending full environment/provenance validation |
| simulation/mujoco/runs/grasp-fast-4-workers/checkpoint-108544.zip | True | pending full environment/provenance validation |
| simulation/mujoco/runs/grasp-fast-4-workers/checkpoint-110592.zip | True | pending full environment/provenance validation |
| simulation/mujoco/runs/grasp-fast-4-workers/checkpoint-112640.zip | True | pending full environment/provenance validation |
| simulation/mujoco/runs/grasp-fast-4-workers/checkpoint-114688.zip | True | pending full environment/provenance validation |
| simulation/mujoco/runs/grasp-fast-4-workers/checkpoint-116736.zip | True | pending full environment/provenance validation |
| simulation/mujoco/runs/grasp-fast-4-workers/checkpoint-118784.zip | True | pending full environment/provenance validation |
| simulation/mujoco/runs/grasp-fast-4-workers/checkpoint-120832.zip | True | pending full environment/provenance validation |
| simulation/mujoco/runs/grasp-fast-4-workers/checkpoint-122880.zip | True | pending full environment/provenance validation |
| simulation/mujoco/runs/grasp-fast-4-workers/checkpoint-24576.zip | True | pending full environment/provenance validation |
| simulation/mujoco/runs/grasp-fast-4-workers/checkpoint-26624.zip | True | pending full environment/provenance validation |
| simulation/mujoco/runs/grasp-fast-4-workers/checkpoint-28672.zip | True | pending full environment/provenance validation |
| simulation/mujoco/runs/grasp-fast-4-workers/checkpoint-30720.zip | True | pending full environment/provenance validation |
| simulation/mujoco/runs/grasp-fast-4-workers/checkpoint-32768.zip | True | pending full environment/provenance validation |
| simulation/mujoco/runs/grasp-fast-4-workers/checkpoint-34816.zip | True | pending full environment/provenance validation |
| simulation/mujoco/runs/grasp-fast-4-workers/checkpoint-36864.zip | True | pending full environment/provenance validation |
| simulation/mujoco/runs/grasp-fast-4-workers/checkpoint-38912.zip | True | pending full environment/provenance validation |
| simulation/mujoco/runs/grasp-fast-4-workers/checkpoint-40960.zip | True | pending full environment/provenance validation |
| simulation/mujoco/runs/grasp-fast-4-workers/checkpoint-43008.zip | True | pending full environment/provenance validation |
| simulation/mujoco/runs/grasp-fast-4-workers/checkpoint-45056.zip | True | pending full environment/provenance validation |
| simulation/mujoco/runs/grasp-fast-4-workers/checkpoint-47104.zip | True | pending full environment/provenance validation |
| simulation/mujoco/runs/grasp-fast-4-workers/checkpoint-49152.zip | True | pending full environment/provenance validation |
| simulation/mujoco/runs/grasp-fast-4-workers/checkpoint-51200.zip | True | pending full environment/provenance validation |
| simulation/mujoco/runs/grasp-fast-4-workers/checkpoint-53248.zip | True | pending full environment/provenance validation |
| simulation/mujoco/runs/grasp-fast-4-workers/checkpoint-55296.zip | True | pending full environment/provenance validation |
| simulation/mujoco/runs/grasp-fast-4-workers/checkpoint-57344.zip | True | pending full environment/provenance validation |
| simulation/mujoco/runs/grasp-fast-4-workers/checkpoint-59392.zip | True | pending full environment/provenance validation |
| simulation/mujoco/runs/grasp-fast-4-workers/checkpoint-61440.zip | True | pending full environment/provenance validation |
| simulation/mujoco/runs/grasp-fast-4-workers/checkpoint-63488.zip | True | pending full environment/provenance validation |
| simulation/mujoco/runs/grasp-fast-4-workers/checkpoint-65536.zip | True | pending full environment/provenance validation |
| simulation/mujoco/runs/grasp-fast-4-workers/checkpoint-67584.zip | True | pending full environment/provenance validation |
| simulation/mujoco/runs/grasp-fast-4-workers/checkpoint-69632.zip | True | pending full environment/provenance validation |
| simulation/mujoco/runs/grasp-fast-4-workers/checkpoint-71680.zip | True | pending full environment/provenance validation |
| simulation/mujoco/runs/grasp-fast-4-workers/checkpoint-73728.zip | True | pending full environment/provenance validation |
| simulation/mujoco/runs/grasp-fast-4-workers/checkpoint-75776.zip | True | pending full environment/provenance validation |
| simulation/mujoco/runs/grasp-fast-4-workers/checkpoint-77824.zip | True | pending full environment/provenance validation |
| simulation/mujoco/runs/grasp-fast-4-workers/checkpoint-79872.zip | True | pending full environment/provenance validation |
| simulation/mujoco/runs/grasp-fast-4-workers/checkpoint-81920.zip | True | pending full environment/provenance validation |
| simulation/mujoco/runs/grasp-fast-4-workers/checkpoint-83968.zip | True | pending full environment/provenance validation |
| simulation/mujoco/runs/grasp-fast-4-workers/checkpoint-86016.zip | True | pending full environment/provenance validation |
| simulation/mujoco/runs/grasp-fast-4-workers/checkpoint-88064.zip | True | pending full environment/provenance validation |
| simulation/mujoco/runs/grasp-fast-4-workers/checkpoint-90112.zip | True | pending full environment/provenance validation |
| simulation/mujoco/runs/grasp-fast-4-workers/checkpoint-92160.zip | True | pending full environment/provenance validation |
| simulation/mujoco/runs/grasp-fast-4-workers/checkpoint-94208.zip | True | pending full environment/provenance validation |
| simulation/mujoco/runs/grasp-fast-4-workers/checkpoint-96256.zip | True | pending full environment/provenance validation |
| simulation/mujoco/runs/grasp-fast-4-workers/checkpoint-98304.zip | True | pending full environment/provenance validation |
| simulation/mujoco/runs/grasp-fast-4-workers/policy.zip | True | pending full environment/provenance validation |
| simulation/mujoco/runs/grasp-parallel-watch-smoke/policy.zip | True | pending full environment/provenance validation |
| simulation/mujoco/runs/live-arena-smoke/policy.zip | True | pending full environment/provenance validation |
| simulation/mujoco/runs/p038-resume-check/policy.zip | True | pending full environment/provenance validation |
| simulation/mujoco/runs/p038-smoke-final/policy.zip | True | pending full environment/provenance validation |
| simulation/mujoco/runs/p038-smoke-v1/policy.zip | True | pending full environment/provenance validation |
| simulation/mujoco/runs/p038-watch-66533e4d6ee049e69fefd0a8868ea15f/policy.zip | True | pending full environment/provenance validation |
| simulation/mujoco/runs/readme-check-18424bf448144c8ea2aa867dd8681869/smoke/policy.zip | True | pending full environment/provenance validation |
| simulation/mujoco/runs/visual-grasp-0a3e3435c49f4f238095f0e536726941/checkpoint-2048.zip | True | pending full environment/provenance validation |
| simulation/mujoco/runs/visual-grasp-0a3e3435c49f4f238095f0e536726941/policy.zip | True | pending full environment/provenance validation |
| simulation/mujoco/runs/visual-grasp-48864f82642c4f8a9333d7cac14a22a2/checkpoint-10240.zip | True | pending full environment/provenance validation |
| simulation/mujoco/runs/visual-grasp-48864f82642c4f8a9333d7cac14a22a2/checkpoint-12288.zip | True | pending full environment/provenance validation |
| simulation/mujoco/runs/visual-grasp-48864f82642c4f8a9333d7cac14a22a2/checkpoint-14336.zip | True | pending full environment/provenance validation |
| simulation/mujoco/runs/visual-grasp-48864f82642c4f8a9333d7cac14a22a2/checkpoint-16384.zip | True | pending full environment/provenance validation |
| simulation/mujoco/runs/visual-grasp-48864f82642c4f8a9333d7cac14a22a2/checkpoint-18432.zip | True | pending full environment/provenance validation |
| simulation/mujoco/runs/visual-grasp-48864f82642c4f8a9333d7cac14a22a2/checkpoint-2048.zip | True | pending full environment/provenance validation |
| simulation/mujoco/runs/visual-grasp-48864f82642c4f8a9333d7cac14a22a2/checkpoint-20480.zip | True | pending full environment/provenance validation |
| simulation/mujoco/runs/visual-grasp-48864f82642c4f8a9333d7cac14a22a2/checkpoint-22528.zip | True | pending full environment/provenance validation |
| simulation/mujoco/runs/visual-grasp-48864f82642c4f8a9333d7cac14a22a2/checkpoint-24576.zip | True | pending full environment/provenance validation |
| simulation/mujoco/runs/visual-grasp-48864f82642c4f8a9333d7cac14a22a2/checkpoint-26624.zip | True | pending full environment/provenance validation |
| simulation/mujoco/runs/visual-grasp-48864f82642c4f8a9333d7cac14a22a2/checkpoint-28672.zip | True | pending full environment/provenance validation |
| simulation/mujoco/runs/visual-grasp-48864f82642c4f8a9333d7cac14a22a2/checkpoint-30720.zip | True | pending full environment/provenance validation |
| simulation/mujoco/runs/visual-grasp-48864f82642c4f8a9333d7cac14a22a2/checkpoint-32768.zip | True | pending full environment/provenance validation |
| simulation/mujoco/runs/visual-grasp-48864f82642c4f8a9333d7cac14a22a2/checkpoint-34816.zip | True | pending full environment/provenance validation |
| simulation/mujoco/runs/visual-grasp-48864f82642c4f8a9333d7cac14a22a2/checkpoint-36864.zip | True | pending full environment/provenance validation |
| simulation/mujoco/runs/visual-grasp-48864f82642c4f8a9333d7cac14a22a2/checkpoint-38912.zip | True | pending full environment/provenance validation |
| simulation/mujoco/runs/visual-grasp-48864f82642c4f8a9333d7cac14a22a2/checkpoint-4096.zip | True | pending full environment/provenance validation |
| simulation/mujoco/runs/visual-grasp-48864f82642c4f8a9333d7cac14a22a2/checkpoint-40960.zip | True | pending full environment/provenance validation |
| simulation/mujoco/runs/visual-grasp-48864f82642c4f8a9333d7cac14a22a2/checkpoint-43008.zip | True | pending full environment/provenance validation |
| simulation/mujoco/runs/visual-grasp-48864f82642c4f8a9333d7cac14a22a2/checkpoint-45056.zip | True | pending full environment/provenance validation |
| simulation/mujoco/runs/visual-grasp-48864f82642c4f8a9333d7cac14a22a2/checkpoint-47104.zip | True | pending full environment/provenance validation |
| simulation/mujoco/runs/visual-grasp-48864f82642c4f8a9333d7cac14a22a2/checkpoint-49152.zip | True | pending full environment/provenance validation |
| simulation/mujoco/runs/visual-grasp-48864f82642c4f8a9333d7cac14a22a2/checkpoint-51200.zip | True | pending full environment/provenance validation |
| simulation/mujoco/runs/visual-grasp-48864f82642c4f8a9333d7cac14a22a2/checkpoint-6144.zip | True | pending full environment/provenance validation |
| simulation/mujoco/runs/visual-grasp-48864f82642c4f8a9333d7cac14a22a2/checkpoint-8192.zip | True | pending full environment/provenance validation |
| simulation/mujoco/runs/visual-grasp-48864f82642c4f8a9333d7cac14a22a2/failed-policy.zip | True | pending full environment/provenance validation |
| simulation/mujoco/runs/visual-grasp-7b93fb512ad144b3ac930bed0f580a5d/policy.zip | True | pending full environment/provenance validation |
| simulation/mujoco/runs/visual-grasp-camera-v3-first/checkpoint-2048.zip | True | pending full environment/provenance validation |
| simulation/mujoco/runs/visual-grasp-camera-v3-first/policy.zip | True | pending full environment/provenance validation |
| simulation/mujoco/runs/visual-grasp-db957681cbb34710ad5fa15104c0c271/checkpoint-2048.zip | True | pending full environment/provenance validation |
| simulation/mujoco/runs/visual-grasp-db957681cbb34710ad5fa15104c0c271/checkpoint-4096.zip | True | pending full environment/provenance validation |
| simulation/mujoco/runs/visual-grasp-db957681cbb34710ad5fa15104c0c271/failed-policy.zip | True | pending full environment/provenance validation |
| simulation/mujoco/runs/visual-grasp-ddd95ff620b843ea8f06f4a10956760d/checkpoint-2048.zip | True | pending full environment/provenance validation |
| simulation/mujoco/runs/visual-grasp-ddd95ff620b843ea8f06f4a10956760d/checkpoint-4096.zip | True | pending full environment/provenance validation |
| simulation/mujoco/runs/visual-grasp-ddd95ff620b843ea8f06f4a10956760d/policy.zip | True | pending full environment/provenance validation |
| simulation/mujoco/runs/visual-grasp-features-v1/checkpoint-10240.zip | True | pending full environment/provenance validation |
| simulation/mujoco/runs/visual-grasp-features-v1/checkpoint-12288.zip | True | pending full environment/provenance validation |
| simulation/mujoco/runs/visual-grasp-features-v1/checkpoint-14336.zip | True | pending full environment/provenance validation |
| simulation/mujoco/runs/visual-grasp-features-v1/checkpoint-16384.zip | True | pending full environment/provenance validation |
| simulation/mujoco/runs/visual-grasp-features-v1/checkpoint-18432.zip | True | pending full environment/provenance validation |
| simulation/mujoco/runs/visual-grasp-features-v1/checkpoint-2048.zip | True | pending full environment/provenance validation |
| simulation/mujoco/runs/visual-grasp-features-v1/checkpoint-20480.zip | True | pending full environment/provenance validation |
| simulation/mujoco/runs/visual-grasp-features-v1/checkpoint-22528.zip | True | pending full environment/provenance validation |
| simulation/mujoco/runs/visual-grasp-features-v1/checkpoint-4096.zip | True | pending full environment/provenance validation |
| simulation/mujoco/runs/visual-grasp-features-v1/checkpoint-6144.zip | True | pending full environment/provenance validation |
| simulation/mujoco/runs/visual-grasp-features-v1/checkpoint-8192.zip | True | pending full environment/provenance validation |
| simulation/mujoco/runs/visual-grasp-features-v1/policy.zip | True | pending full environment/provenance validation |
| simulation/mujoco/runs/visual-grasp-ffc485a0ff4a438895f748d2561f4ea8/policy.zip | True | pending full environment/provenance validation |
| simulation/mujoco/runs/visual-grasp-warm-full-open-v1/policy.zip | True | pending full environment/provenance validation |
| simulation/mujoco/runs/visual-grasp-warm-v3/checkpoint-2048.zip | True | pending full environment/provenance validation |
| simulation/mujoco/runs/visual-grasp-warm-v3/policy.zip | True | pending full environment/provenance validation |
| simulation/mujoco/runs/visual-lift-21628dc49b1c460b8301be585ec232aa/policy.zip | True | pending full environment/provenance validation |
| simulation/mujoco/runs/visual-lift-camera-v3-20000/checkpoint-2048.zip | True | pending full environment/provenance validation |
| simulation/mujoco/runs/visual-lift-camera-v3-20000/checkpoint-4096.zip | True | pending full environment/provenance validation |
| simulation/mujoco/runs/visual-lift-camera-v3-20000/checkpoint-6144.zip | True | pending full environment/provenance validation |
| simulation/mujoco/runs/visual-lift-camera-v3-20000/checkpoint-8192.zip | True | pending full environment/provenance validation |
| simulation/mujoco/runs/visual-lift-camera-v3-20000/policy.zip | True | pending full environment/provenance validation |
| simulation/mujoco/runs/visual-lift-controls-v2/checkpoint-2048.zip | True | pending full environment/provenance validation |
| simulation/mujoco/runs/visual-lift-controls-v2/policy.zip | True | pending full environment/provenance validation |
| simulation/mujoco/runs/visual-lift-cuda-smoke-v2b/failed-policy.zip | True | pending full environment/provenance validation |
| simulation/mujoco/runs/visual-lift-cuda-v3-smoke/policy.zip | True | pending full environment/provenance validation |
| simulation/mujoco/runs/visual-lift-v3-stop-test/policy.zip | True | pending full environment/provenance validation |
| simulation/mujoco/runs/visual-lift-visible-v2b/policy.zip | True | pending full environment/provenance validation |
