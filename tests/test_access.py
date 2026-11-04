import base64
import gzip
import hashlib
import shutil
import subprocess
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from tv import check_identity, decode_pull, private_path, script_command, PROFILE


class AccessTests(unittest.TestCase):
    @unittest.skipUnless(shutil.which("sh") and shutil.which("base64"), "POSIX shell and base64 required")
    def test_script_executes_with_windows_newlines_and_literal_arguments(self):
        script = b'set -eu\r\nprintf "%s\\n" "$1" "$2"\r\n'
        arguments = ["a spaced 'argument'", "$(printf should-not-run); *"]
        result = subprocess.run(["sh", "-c", script_command(script, arguments)],
                                check=True, capture_output=True, text=True)
        self.assertEqual(result.stdout.splitlines(), arguments)

    @unittest.skipUnless(shutil.which("sh") and shutil.which("base64"), "POSIX shell and base64 required")
    def test_script_failure_is_propagated(self):
        result = subprocess.run(["sh", "-c", script_command(b"exit 17\n", [])],
                                capture_output=True)
        self.assertEqual(result.returncode, 17)

    def test_script_size_is_bounded(self):
        with self.assertRaises(ValueError):
            script_command(b"x" * 45001, [])

    def test_target_identity_gate(self):
        check_identity(PROFILE["model"], PROFILE["firmware"])
        with self.assertRaises(ValueError):
            check_identity("ANOTHER_MODEL", PROFILE["firmware"])
        with self.assertRaises(ValueError):
            check_identity(PROFILE["model"], "ANOTHER_FIRMWARE")
        with self.assertRaises(ValueError):
            check_identity(PROFILE["model"], None)

    def test_transfer_integrity(self):
        payload = b"synthetic contents only" * 100
        digest = hashlib.sha256(payload).hexdigest()
        body = base64.encodebytes(gzip.compress(payload)).decode()
        self.assertEqual(decode_pull(digest + "\n" + body), payload)
        with self.assertRaises(ValueError):
            decode_pull("0" * 64 + "\n" + body)
        with self.assertRaises(Exception):
            decode_pull(digest + "\n" + body[:-12])

    def test_private_outputs_cannot_escape_checkout_private_directory(self):
        with self.assertRaises(ValueError):
            private_path(ROOT / "public-backup.json")
        with self.assertRaises(ValueError):
            private_path(ROOT / ".local/../public-backup.json")

    def test_runtime_fallback_is_narrow(self):
        from samsung_tv_root.archive_root import _check_target, ArchiveRootError
        from unittest.mock import Mock
        client = Mock()
        capabilities = ("/usr/bin/dotnet cap_setgid,cap_sys_admin=ep\n"
                        "/usr/sbin/sdbd-tarlauncher cap_setgid,cap_setuid=ep")
        with patch("samsung_tv_root.archive_root._capture", side_effect=[
            capabilities, ArchiveRootError("Unknown option --list-runtimes"),
            "Microsoft.NETCore.App 6.0.9 [/usr/share/runtime/6.0.9]",
            "--to-command=COMMAND", "synthetic hash",
        ]) as capture:
            self.assertEqual(_check_target(client).runtime, "6.0")
            self.assertIn("System.Private.CoreLib.dll", capture.call_args_list[2].args[1])
        with patch("samsung_tv_root.archive_root._capture", side_effect=[
            capabilities, ArchiveRootError("permission denied"),
        ]):
            with self.assertRaises(ArchiveRootError):
                _check_target(client)


if __name__ == "__main__":
    unittest.main()
