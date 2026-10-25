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
