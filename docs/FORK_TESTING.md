# Standalone fork validation

Upstream imported at f8e7a774042ea53832e570d6474da2af890d91cf.

Linux sandbox checks:
- Python compilation of launcher.py and install.py: passed.
- launcher.py --help: passed, includes --game-dir.
- 10 unit tests: StandaloneStartTest, WindowsTasklist, GameClosed, GfxArgTest,
  WaitForGameTest: passed (mocked Windows process launch, missing/explicit game
  folder, native Linux launch, renderer selection and lifecycle).
- Full test_launcher_linux module: 18 tests, one error (certifi not installed in
  sandbox) and one failure in existing system CA discovery test (host has a
  working default CA directory). These CA tests do not exercise the changed launch path.

Windows .exe build and real BeamNG.drive launch were not run: this sandbox is Linux
and has no game installation. build_windows.bat includes an executable server --help
smoke test to run on the target Windows system. An actual in-game test is still needed.

Historical research, changelog and upstream README retain their original platform
references; they do not describe the fork's removed store integration.

## 1.6.3-beta update

Updated to upstream release v1.6.3-beta (d230840b0c7548b2842d46bb1869c2bdf7753ff3).
Three-way merged upstream changes, retaining standalone direct game launch and
native-module build checks. Added upstream remembered game/cache folders, gas
stations, railways, revisit caching and fixes. Python compile/help and 10 selected
launcher lifecycle/direct-start tests passed in Linux. Windows CI builds and
smoke-tests the packaged server; real game/network access still requires testing.

## 1.7.1-beta update

Three-way updated from upstream v1.6.3-beta to v1.7.1-beta. Preserved direct
launch, no store library/config/overlay integration, explicit/saved game folder,
and mandatory earthfast version checks (now MIN_VERSION 100). Kept upstream
Linux GPU selection without importing Steam launch options. Included native
Windows certificate-store support and parent-process cleanup improvements.
Compile/help checks and 32 selected launcher, settings and GPU unit tests passed.
Windows CI packages the rebuilt native module and smoke-tests --server --help.
Actual gameplay and access to external data providers need user-side testing.

## 1.7.3-beta update

Updated from upstream v1.7.1-beta to stable beta tag v1.7.3-beta (includes 1.7.2).
Direct launcher and removal of store integration retained without merge conflicts.
New upstream native module minimum is 116; native-version and 32 launcher/settings/
GPU regression checks now also run in Windows CI before packaging. The bundled
USGS lidar index is included by upstream packaging. Local compilation/help and
32 selected regression tests passed. Windows smoke test only checks packaged
server --help; real gameplay and provider connectivity still need user testing.
Upstream compatibility target: BeamNG.drive 0.40.4.
