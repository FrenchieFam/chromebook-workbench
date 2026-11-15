import argparse
import contextlib
import hashlib
import io
import json
from pathlib import Path
import subprocess
import sys
import tarfile
import tempfile
import unittest
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
import setup_userspace as setup
import connect_worker as connect
import remote_browser

class SetupTests(unittest.TestCase):
    def package(self):
        data=io.BytesIO()
        with tarfile.open(fileobj=data,mode='w:gz') as archive:
            for name in ('tailscale','tailscaled'):
                payload=b'#!/bin/sh\nexit 0\n';entry=tarfile.TarInfo(f'tailscale_{setup.VERSION}_amd64/{name}');entry.size=len(payload)
                archive.addfile(entry,io.BytesIO(payload))
        return data.getvalue()
    def invoke(self,home,data,checksum=None):
        responses=[io.BytesIO(data),io.BytesIO((checksum or hashlib.sha256(data).hexdigest()).encode())]
        def run(args,**kwargs):return subprocess.CompletedProcess(args,3 if args[:2]==['systemctl','is-active'] else 0)
        with patch('sys.argv',['setup','--name','test-worker']),patch.object(setup.Path,'home',return_value=home),patch.object(setup.os,'geteuid',return_value=1000),patch.object(setup.platform,'machine',return_value='x86_64'),patch.object(setup.shutil,'which',return_value=None),patch.object(setup.urllib.request,'urlopen',side_effect=responses),patch.object(setup.subprocess,'run',side_effect=run),contextlib.redirect_stdout(io.StringIO()):setup.main()
    def test_checksum_failure_installs_nothing(self):
        with tempfile.TemporaryDirectory() as tmp:
            home=Path(tmp)
            with self.assertRaisesRegex(SystemExit,'checksum'):self.invoke(home,self.package(),'0'*64)
            self.assertFalse((home/'.local/share/tailscale-workbench').exists())
    def test_conflicting_unit_preserves_existing_executables(self):
        with tempfile.TemporaryDirectory() as tmp:
            home=Path(tmp);binary=home/'.local/share/tailscale-workbench/tailscale';binary.parent.mkdir(parents=True);binary.write_text('preserve')
            unit=home/'.config/systemd/user/workbench-tailscaled.service';unit.parent.mkdir(parents=True);unit.write_text('unrelated service')
            with self.assertRaisesRegex(SystemExit,'unit differs'):self.invoke(home,self.package())
            self.assertEqual(binary.read_text(),'preserve');self.assertEqual(unit.read_text(),'unrelated service')
    def test_isolated_userspace_install_with_spaces_and_private_state(self):
        with tempfile.TemporaryDirectory(prefix='workbench home ') as tmp:
            home=Path(tmp);self.invoke(home,self.package())
            self.assertEqual((home/'.local/state/tailscale-workbench').stat().st_mode & 0o777,0o700)
            unit=(home/'.config/systemd/user/workbench-tailscaled.service').read_text()
            self.assertIn('--tun=userspace-networking',unit);self.assertIn('RuntimeDirectoryMode=0700',unit)
            self.assertTrue((home/'bin/workbench-tailscale').stat().st_mode & 0o100)
            self.invoke(home,self.package())
            self.assertEqual((home/'.config/systemd/user/workbench-tailscaled.service').read_text(),unit)

class PairTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(prefix='ssh workbench ');self.addCleanup(self.tmp.cleanup)
        self.home=Path(self.tmp.name);self.key=self.home/'identity'
        subprocess.run(['ssh-keygen','-q','-t','ed25519','-N','','-f',str(self.key)],check=True)
        parts=self.key.with_suffix('.pub').read_text().split();self.offered=(parts[0],parts[1])
        self.fingerprint=subprocess.check_output(['ssh-keygen','-lf',str(self.key.with_suffix('.pub')),'-E','sha256'],text=True).split()[1]
        self.args=argparse.Namespace(host='worker.example.ts.net',alias='test-worker',user='testuser',port=2222,fingerprint=self.fingerprint,identity=self.key,tailscale=self.home/'tailscale',directory=self.home/'pins')
    def test_mismatch_never_creates_pin(self):
        self.args.fingerprint='SHA256:'+'A'*43
        with patch.object(connect,'collect_key',return_value=self.offered):
            with self.assertRaisesRegex(ValueError,'MISMATCH'):connect.pair(self.args)
        self.assertFalse(self.args.directory.exists())
    def test_changed_existing_pin_is_preserved(self):
        self.args.directory.mkdir();pin=self.args.directory/'test-worker.known_hosts';pin.write_text('existing pin')
        with patch.object(connect,'collect_key',return_value=self.offered):
            with self.assertRaisesRegex(ValueError,'Existing pin'):connect.pair(self.args)
        self.assertEqual(pin.read_text(),'existing pin')
    def test_verified_pin_creates_strict_dedicated_config(self):
        with patch.object(connect,'collect_key',return_value=self.offered),contextlib.redirect_stdout(io.StringIO()):config=connect.pair(self.args)
        result=subprocess.run(['ssh','-G','-F',str(config),'test-worker'],capture_output=True,text=True,check=True)
        self.assertIn('stricthostkeychecking true',result.stdout);self.assertIn('batchmode yes',result.stdout)
        self.assertEqual(config.stat().st_mode & 0o777,0o600)
        self.assertEqual((self.args.directory/'test-worker.known_hosts').stat().st_mode & 0o777,0o600)
    def test_injected_hostname_rejected_before_network(self):
        self.args.host='worker; echo invalid'
        with patch.object(connect,'collect_key') as network:
            with self.assertRaisesRegex(ValueError,'Invalid host'):connect.pair(self.args)
            network.assert_not_called()

class RemoteCommandTests(unittest.TestCase):
    def test_json_and_shell_metacharacters_arrive_as_literal_arguments(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);client=root/'.local/bin/chromebook-browser';client.parent.mkdir(parents=True)
            client.write_text('#!/usr/bin/env python3\nimport json,sys\nprint(json.dumps(sys.argv[1:]))\n');client.chmod(0o755)
            arguments=['type','--args',json.dumps({'selector':'#entry','text':"it's $(touch injected); echo wrong"})]
            remote=remote_browser.command(Path('config with spaces'),'worker',arguments)[-1]
            output=subprocess.check_output(['sh','-c',remote],cwd=root,text=True)
            self.assertEqual(json.loads(output),arguments);self.assertFalse((root/'injected').exists())

if __name__=='__main__':unittest.main()
