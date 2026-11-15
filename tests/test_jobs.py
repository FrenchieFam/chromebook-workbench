import fcntl
import importlib.util
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import tempfile
import time
import unittest
spec=importlib.util.spec_from_file_location('workbench_jobs',Path(__file__).resolve().parents[1]/'tools/job_runner.py')
jobs=importlib.util.module_from_spec(spec);spec.loader.exec_module(jobs)

class JobTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.base=Path(self.temp.name);self.repo=self.base/'repo';self.repo.mkdir();self.root=self.base/'jobs';self.root.mkdir()
        subprocess.run(['git','init','-q',str(self.repo)],check=True)
        (self.repo/'README').write_text('fixture\n');subprocess.run(['git','add','README'],cwd=self.repo,check=True)
        subprocess.run(['git','-c','user.name=Test','-c','user.email=test@example.invalid','commit','-qm','fixture'],cwd=self.repo,check=True)
        self.handlers={s:signal.getsignal(s) for s in (signal.SIGTERM,signal.SIGHUP)}
    def tearDown(self):
        for s,h in self.handlers.items():signal.signal(s,h)
        self.temp.cleanup()
    def make_job(self,number=1,timeout=10):
        job='20260101T000000Z-'+f'{number:08x}';directory=jobs.job_path(self.root,job);directory.mkdir()
        jobs.store(directory/'result.json',{'suite':'fixture','state':'queued','commit':jobs.clean_revision(self.repo),'timeoutSeconds':timeout})
        return job,directory
    def test_success_and_failure_are_persisted_with_private_logs(self):
        job,d=self.make_job();jobs.run_job(self.root,job,self.repo,[[sys.executable,'-c','print("passed fixture")']])
        self.assertEqual(json.loads((d/'result.json').read_text())['state'],'passed');self.assertIn('passed fixture',(d/'test.log').read_text())
        self.assertEqual((d/'test.log').stat().st_mode&0o777,0o600)
        job,d=self.make_job(2);jobs.run_job(self.root,job,self.repo,[[sys.executable,'-c','raise SystemExit(7)']])
        r=json.loads((d/'result.json').read_text());self.assertEqual(r['state'],'failed');self.assertEqual(r['steps'][0]['exitCode'],7)
    def test_busy_kernel_lock_refuses_without_waiting_then_releases(self):
        job,d=self.make_job()
        with (self.root/'fixture.lock').open('a') as lock:
            fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
            start=time.monotonic();jobs.run_job(self.root,job,self.repo,[])
            self.assertLess(time.monotonic()-start,1);self.assertEqual(json.loads((d/'result.json').read_text())['state'],'busy')
        job,d=self.make_job(2);jobs.run_job(self.root,job,self.repo,[]);self.assertEqual(json.loads((d/'result.json').read_text())['state'],'passed')
    def test_timeout_terminates_child_process_group(self):
        job,d=self.make_job(timeout=1);marker=self.base/'must-not-appear'
        grandchild='import time;from pathlib import Path;time.sleep(2);Path('+repr(str(marker))+').touch()'
        command='import subprocess,sys,time;subprocess.Popen([sys.executable,"-c",'+repr(grandchild)+']);time.sleep(30)'
        jobs.run_job(self.root,job,self.repo,[[sys.executable,'-c',command]])
        self.assertEqual(json.loads((d/'result.json').read_text())['state'],'timed_out');time.sleep(1.3);self.assertFalse(marker.exists())
    def test_changed_checkout_is_refused_and_path_traversal_rejected(self):
        job,d=self.make_job();(self.repo/'README').write_text('changed')
        jobs.run_job(self.root,job,self.repo,[[sys.executable,'-c','raise Exception("should never run")']])
        r=json.loads((d/'result.json').read_text());self.assertEqual(r['state'],'failed');self.assertNotIn('steps',r)
        with self.assertRaises(ValueError):jobs.job_path(self.root,'../../outside')
