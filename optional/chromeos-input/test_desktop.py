import json
from pathlib import Path
import tempfile
import time
import unittest
from unittest.mock import patch
import desktop


class ScreenGuardTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.state = Path(self.directory.name) / 'screen.json'
        self.patch = patch.object(desktop, 'STATE', self.state)
        self.patch.start()
        self.addCleanup(self.patch.stop)

    def write(self, width=1366, height=768, age=0):
        self.state.write_text(json.dumps(dict(width=width, height=height, capturedAt=time.time()-age)))

    def test_missing_and_stale_capture_block_input(self):
        with self.assertRaisesRegex(RuntimeError, 'fresh'):
            desktop.check_screen()
        self.write(age=121)
        with self.assertRaisesRegex(RuntimeError, 'stale'):
            desktop.check_screen()

    def test_changed_resolution_blocks_input(self):
        self.write(width=1920, height=1080)
        with patch.object(desktop, 'geometry', return_value=dict(width=1366, height=768)):
            with self.assertRaisesRegex(RuntimeError, 'geometry changed'):
                desktop.check_screen()

    def test_fresh_matching_capture_allows_input(self):
        self.write()
        with patch.object(desktop, 'geometry', return_value=dict(width=1366, height=768)):
            self.assertEqual(desktop.check_screen()['width'],1366)

    def test_helper_reports_its_configured_geometry(self):
        with patch.object(desktop, 'send', return_value='OK width=1920 height=1080 version=0.2.0'):
            self.assertEqual(desktop.geometry()['width'],1920)

    def test_unsupported_mouse_actions_never_reach_host(self):
        for arguments in [('click','right'),('click','middle'),('scroll','-2')]:
            with patch('sys.argv',['desktop',*arguments]), patch.object(desktop,'send') as send:
                with self.assertRaises(SystemExit):
                    desktop.main()
                send.assert_not_called()


if __name__ == '__main__':
    unittest.main()
