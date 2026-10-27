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
