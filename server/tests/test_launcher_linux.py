"""launcher.py on Linux: the user folder and start path with a Flatpak Steam, the game-closed grace period."""
import os
import sys
import tempfile
import time
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
import install  # noqa: E402
import launcher  # noqa: E402

FP = (".var", "app", "com.valvesoftware.Steam")


def touch(path, mtime=None):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    open(path, "w").close()
    if mtime is not None:
        os.utime(path, (mtime, mtime))




class GameClosed(unittest.TestCase):
    def test_a_restart_during_the_start_is_not_a_close(self):
        seen = iter([[1], [], [], [2], [2], []] + [[]] * 100)
        clock = [0.0]

        def sleep(s):
            clock[0] += s
        with mock.patch.object(launcher, "game_pids", lambda: next(seen)), \
                mock.patch.object(launcher, "game_connected", lambda: False), \
                mock.patch.object(launcher.time, "sleep", sleep), \
                mock.patch.object(launcher.time, "time", lambda: clock[0]):
            launcher.wait_for_game(None)
        # [1] found; gone twice (6 s), back ([2] x2, 6 s), then gone for good: closed after GAME_GONE_S of absence
        self.assertGreaterEqual(clock[0], 12 + launcher.GAME_GONE_S)


@unittest.skipIf(os.name == "nt", "Linux: ensure_ca_certs leaves Windows alone")
class CaCerts(unittest.TestCase):
    """The packaged app's OpenSSL looks in /usr/lib/ssl (Ubuntu's): elsewhere SSL_CERT_FILE points at a bundle."""
    NONE = mock.Mock(cafile="/usr/lib/ssl/cert.pem", capath="/nonexistent/certs")

    def run_it(self, bundles, env=None):
        with mock.patch.dict(os.environ, env or {}, clear=False), \
                mock.patch("ssl.get_default_verify_paths", return_value=self.NONE), \
                mock.patch.object(launcher, "CA_BUNDLES", bundles):
            if not env:
                os.environ.pop("SSL_CERT_FILE", None)
            launcher.ensure_ca_certs()
            return os.environ.get("SSL_CERT_FILE")

    def test_system_bundle(self):
        with tempfile.NamedTemporaryFile() as f:
            self.assertEqual(self.run_it(("/nonexistent/a.crt", f.name)), f.name)

    def test_certifi_fallback(self):
        import certifi
        self.assertEqual(self.run_it(("/nonexistent/a.crt",)), certifi.where())

    def test_kept_when_set(self):
        self.assertEqual(self.run_it((), {"SSL_CERT_FILE": "/mine.pem"}), "/mine.pem")



class CacheDirTest(unittest.TestCase):
    """--cache-dir: the download cache on another drive, remembered (GitHub #254)."""
    def test_remembered_and_forgotten(self):
        with tempfile.TemporaryDirectory() as dd:
            self.assertIsNone(launcher.cache_dir_arg(None, dd), "the server's default")
            where = os.path.join(dd, "other drive", "cache")
            self.assertEqual(launcher.cache_dir_arg(f' "{where}" ', dd), where)
            self.assertTrue(os.path.isdir(where), "made")
            self.assertEqual(launcher.cache_dir_arg(None, dd), where, "kept for the next start")
            self.assertIsNone(launcher.cache_dir_arg("default", dd))
            self.assertIsNone(launcher.cache_dir_arg(None, dd), "forgotten")


class GpuPlan(unittest.TestCase):
    """gpu_plan: the hybrid-graphics steering (the user's report, 2026-10-26: the game started directly rendered on
    the integrated GPU where Steam's start used the dedicated one)."""

    def test_nvidia_offload(self):
        env, note = launcher.gpu_plan("auto", scan=[("intel", True, 0), ("nvidia", False, 0, "nvidia")])
        self.assertEqual(env, {"__NV_PRIME_RENDER_OFFLOAD": "1", "__GLX_VENDOR_LIBRARY_NAME": "nvidia"})
        self.assertIn("NVIDIA", note)

    def test_nvidia_is_the_default_already(self):
        env, note = launcher.gpu_plan("auto", scan=[("nvidia", True, 0, "nvidia"), ("intel", False, 0, "")])
        self.assertIsNone(env)
        self.assertIn("already", note)

    def test_driverless_nvidia_goes_by_vram(self):
        # a nouveau-bound NVIDIA card: Mesa's offload only, and only while it reports the more VRAM
        env, note = launcher.gpu_plan("auto", scan=[("intel", True, 0), ("nvidia", False, 8 << 30, "nouveau")])
        self.assertEqual(env, {"DRI_PRIME": "1"})
        self.assertIn("nvidia", note)

    def test_mesa_pair(self):
        env, note = launcher.gpu_plan("auto", scan=[("amd", True, 512 << 20), ("amd", False, 8 << 30, "amdgpu")])
        self.assertEqual(env, {"DRI_PRIME": "1"})
        self.assertIn("DRI_PRIME=1", note)

    def test_mesa_pair_default_is_the_bigger_one(self):
        env, note = launcher.gpu_plan("auto", scan=[("amd", True, 12 << 30, "amdgpu"), ("amd", False, 512 << 20, "amdgpu")])
        self.assertIsNone(env)
        self.assertIn("most VRAM", note)

    def test_vram_unknown_gives_up(self):
        env, note = launcher.gpu_plan("auto", scan=[("intel", True, 0, "i915"), ("amd", False, 0, "amdgpu")])
        self.assertIsNone(env)
        self.assertIn("cannot tell", note)

    def test_discrete_guesses_when_unknown(self):
        env, note = launcher.gpu_plan("discrete", scan=[("intel", True, 0, "i915"), ("amd", False, 0, "amdgpu")])
        self.assertEqual(env, {"DRI_PRIME": "1"})

    def test_one_gpu_off_and_no_gpu(self):
        self.assertIsNone(launcher.gpu_plan("auto", scan=[("amd", True, 4 << 30, "amdgpu")])[0])
        self.assertIsNone(launcher.gpu_plan("off", scan=[("intel", True, 0, ""), ("nvidia", False, 0, "nvidia")])[0])
        self.assertIsNone(launcher.gpu_plan("off", scan=[])[0])
        self.assertIsNone(launcher.gpu_plan("auto", scan=[])[0])

    def test_no_boot_flag_takes_the_first_card(self):
        env, note = launcher.gpu_plan("auto", scan=[("other", False, 0, ""), ("other", False, 0, "")])
        self.assertIsNone(env)

    def test_player_vars_win(self):
        scan = [("intel", True, 0, "i915"), ("nvidia", False, 0, "nvidia")]
        for var, value in (("DRI_PRIME", "1"), ("__NV_PRIME_RENDER_OFFLOAD", "0"),
                           ("MESA_VK_DEVICE_SELECT", "1002:744c"), ("VK_DRIVER_FILES", "/mine.json")):
            env, note = launcher.gpu_plan("auto", environ={var: value}, scan=scan)
            self.assertIsNone(env)
            self.assertIn(var, note)












if __name__ == "__main__":
    unittest.main()


class WindowsTasklist(unittest.TestCase):
    """game_pids on Windows: tasklist's output in the console's code page (a German Windows, 2026-10-17: byte 0x81
    stopped the launcher with UnicodeDecodeError)."""

    def run_with(self, stdout):
        res = mock.Mock(stdout=stdout, returncode=0)
        with mock.patch.object(launcher, "IS_WIN", True), mock.patch.object(launcher.subprocess, "run", return_value=res):
            return launcher.game_pids()

    def test_localised_no_tasks_message(self):
        msg = "INFORMATION: Es werden keine Aufgaben mit den angegebenen Kriterien ausgeführt.\r\n".encode("cp850")
        self.assertIn(b"\x81", msg)
        self.assertEqual(self.run_with(msg), [])

    def test_game_found(self):
        exe = launcher.GAME_EXE_WIN
        out = f'"{exe}","4242","Console","1","1.234.567 K"\r\n'.encode("cp850")
        self.assertEqual(self.run_with(out), [4242])

    def test_no_output(self):
        self.assertEqual(self.run_with(None), [])


class FlatpakGameProcess(unittest.TestCase):
    """game_pids / game_alive on Linux when argv[0] does not name the game (a Flatpak Steam's container, a player's
    video 2026-10-17: the server stopped ~30 s after the game started)."""

    def fake_proc(self, procs):
        """procs: {pid: (argv list of bytes, exe path or None)}"""
        real_open, real_listdir, real_readlink = open, os.listdir, os.readlink

        def listdir(p):
            return [str(k) for k in procs] + ["self"] if p == "/proc" else real_listdir(p)

        def fopen(p, *a, **k):
            parts = str(p).split("/")
            if len(parts) == 4 and parts[1] == "proc" and parts[3] == "cmdline":
                import io
                return io.BytesIO(b"\0".join(procs[int(parts[2])][0]))
            return real_open(p, *a, **k)

        def readlink(p):
            parts = str(p).split("/")
            if len(parts) == 4 and parts[1] == "proc" and parts[3] == "exe":
                exe = procs[int(parts[2])][1]
                if exe is None:
                    raise PermissionError(p)
                return exe
            return real_readlink(p)
        return mock.patch.multiple(launcher.os, listdir=listdir, readlink=readlink), \
            mock.patch("builtins.open", fopen)

    def test_game_found_by_its_executable(self):
        game = "/home/u/.var/app/com.valvesoftware.Steam/.local/share/Steam/steamapps/common/BeamNG.drive/BinLinux/" + \
            os.path.basename(launcher.GAME_EXE_LINUX)
        procs = {
            10: ([b"/usr/lib/pressure-vessel/from-host/lib/ld-linux-x86-64.so.2", game.encode(), b"-forcecloud"], game),
            11: ([game.encode() + b" --type=renderer --enable-crash-reporter"], game),       # a CEF helper
            12: ([b"/usr/bin/bash", b"-c", b"x"], "/usr/bin/bash"),
            13: ([b"/usr/bin/other"], None),                                                     # not ours
        }
        p1, p2 = self.fake_proc(procs)
        with mock.patch.object(launcher, "IS_WIN", False), p1, p2:
            self.assertEqual(launcher.game_pids(), [10])

    def test_alive_while_the_mod_is_connected(self):
        port = format(launcher.SERVER_PORT, "04X")
        tcp = ("  sl  local_address rem_address   st\n"
               f"   0: 0100007F:{port} 0100007F:8A3C 01 00000000:00000000\n")
        with mock.patch.object(launcher, "IS_WIN", False), mock.patch.object(launcher, "game_pids", lambda: []), \
                mock.patch("builtins.open", mock.mock_open(read_data=tcp)):
            self.assertTrue(launcher.game_alive())
        listen = tcp.replace(" 01 ", " 0A ")
        with mock.patch.object(launcher, "IS_WIN", False), mock.patch.object(launcher, "game_pids", lambda: []), \
                mock.patch("builtins.open", mock.mock_open(read_data=listen)):
            self.assertFalse(launcher.game_alive())


class ConsoleEcho(unittest.TestCase):
    def test_only_warnings_errors_tracebacks_and_connected(self):
        log = ["2026-10-17 07:04:50,488 INFO earthd: session 1 kept\n",
               "earthd listening on 127.0.0.1:47613 session x\n",
               "2026-10-17 07:04:55,466 INFO earthd: client connected ('127.0.0.1', 34278)\n",
               "2026-10-17 07:05:01,000 WARNING earthd.net: net: host: circuit open for 60 s\n",
               "2026-10-17 07:05:02,000 ERROR earthd: tile failed\n",
               "Traceback (most recent call last):\n", '  File "dem.py", line 236\n', "dem.DemUnavailable: x\n",
               "2026-10-17 07:05:03,000 INFO earthd: anchor 1: land cover wait 3.11 s\n",
               "2026-10-17 07:05:04,000 INFO earthd: client connected ('127.0.0.1', 1)\n"]
        state = {}
        out = launcher.echo_lines(log[:4], state) + launcher.echo_lines(log[4:], state)
        self.assertEqual(out[0], "  Game          connected to the world server")
        self.assertTrue(out[1].startswith("  server: ") and "WARNING" in out[1])
        self.assertIn("ERROR", out[2])
        self.assertEqual([o.strip() for o in out[3:6]], ["server: Traceback (most recent call last):",
                                                         'server:   File "dem.py", line 236', "server: dem.DemUnavailable: x"])
        self.assertEqual(len(out), 6, "no INFO lines, 'connected' once")


class ModsOffAfterUpdateTest(unittest.TestCase):
    """A game update turns every mod off until the player turns them back on (BeamNG 0.40, 2026-10-19): the
    launcher reads the game's log and says what to do."""

    def test_the_line_is_reported(self):
        got = []
        old = launcher.problem
        launcher.problem = lambda msg, hint=None: got.append((msg, hint))
        self.addCleanup(setattr, launcher, "problem", old)
        with tempfile.TemporaryDirectory() as d:
            since = time.time() - 1
            launcher.watch_game_log(d, since)
            with open(os.path.join(d, "beamng.log"), "w") as f:
                f.write(" 1.2|I|getModsDisabledAfterUpdate| Mods will be disabled after updating from version: '0.39.4'\n")
            for _ in range(20):
                if got:
                    break
                time.sleep(0.25)
        self.assertEqual(len(got), 1)
        self.assertIn("turned all mods off", got[0][0])

    def test_last_runs_log_is_ignored(self):
        got = []
        old = launcher.problem
        launcher.problem = lambda msg, hint=None: got.append(msg)
        self.addCleanup(setattr, launcher, "problem", old)
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "beamng.log")
            with open(p, "w") as f:
                f.write("Mods will be disabled after updating from version: '0.39.4'\n")
            os.utime(p, (time.time() - 3600, time.time() - 3600))      # an old run's log
            launcher.watch_game_log(d, time.time())
            time.sleep(3)
        self.assertEqual(got, [])


class GfxArgTest(unittest.TestCase):
    def test_dx12_is_d3d12(self):
        """The game knows -gfx dx11 / vk but not dx12 ("no valid rendering device"): DirectX 12 is d3d12."""
        self.assertEqual(launcher.GFX_ARG, {"dx11": "dx11", "dx12": "d3d12", "vk": "vk"})




class WaitForGameTest(unittest.TestCase):
    def test_a_late_game_is_still_followed(self):
        """Started through Steam: no game for longer than GAME_START_S (the launch options window open), then the game
        runs and closes: wait_for_game returns once it is gone (it used to wait for good)."""
        clock = [0.0]
        seen = iter([False] * 5 + [True] * 3)        # game_pids: none for a while, then the game

        def fake_sleep(s):
            clock[0] += max(s, 100)
        alive = iter([True, True, False, False, False, False, False, False, False, False, False, False])
        with mock.patch.object(launcher.time, "time", side_effect=lambda: clock[0]), \
                mock.patch.object(launcher.time, "sleep", side_effect=fake_sleep), \
                mock.patch.object(launcher, "game_pids", side_effect=lambda: [1] if next(seen, True) else []), \
                mock.patch.object(launcher, "game_alive", side_effect=lambda: next(alive, False)), \
                mock.patch.object(launcher, "game_launcher_running", return_value=False), \
                mock.patch.object(launcher, "say") as say:
            launcher.wait_for_game(None)
            self.assertEqual(say.call_count, 1, "told once that the game has not started yet")

class StandaloneStartTest(unittest.TestCase):
    def test_windows_always_direct(self):
        for gfx in ("", "dx12"):
            with mock.patch.object(launcher, "IS_WIN", True), \
                    mock.patch.object(launcher, "windows_game_dir", return_value="C:/Games/BeamNG"), \
                    mock.patch.object(launcher.os, "startfile", create=True) as sf, \
                    mock.patch.object(launcher.subprocess, "Popen") as po, \
                    mock.patch.dict(os.environ, {"BNGE_GAME_ARGS": ""}):
                self.assertIs(launcher.start_game(False, gfx=gfx), po.return_value)
                sf.assert_not_called()
                self.assertEqual(po.call_args.args[0], ["C:/Games/BeamNG/BeamNG.drive.exe"] +
                                 (["-gfx", "d3d12"] if gfx else []))

    def test_missing_game_does_not_launch_client(self):
        with mock.patch.object(launcher, "IS_WIN", True), \
                mock.patch.object(launcher, "windows_game_dir", return_value=None), \
                mock.patch.object(launcher.subprocess, "Popen") as po:
            self.assertIsNone(launcher.start_game(False))
            po.assert_not_called()

    def test_explicit_game_dir(self):
        with tempfile.TemporaryDirectory() as root:
            touch(os.path.join(root, "BeamNG.drive.exe"))
            with mock.patch.dict(os.environ, {"BNGE_GAME_DIR": root}):
                self.assertEqual(launcher.windows_game_dir(), root)
            with mock.patch.dict(os.environ, {"BNGE_GAME_DIR": root + "/missing"}):
                self.assertIsNone(launcher.windows_game_dir())

    def test_linux_direct_without_client(self):
        with mock.patch.object(launcher, "IS_WIN", False), \
                mock.patch.object(launcher, "linux_game_exe", return_value="/game/BinLinux/BeamNG.drive.x64"), \
                mock.patch.object(launcher.subprocess, "Popen") as po, \
                mock.patch.dict(os.environ, {"BNGE_GAME_ARGS": ""}):
            launcher.start_game(False)
            self.assertEqual(po.call_args.args[0], ["/game/BinLinux/BeamNG.drive.x64"])
