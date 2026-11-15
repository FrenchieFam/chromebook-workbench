#!/usr/bin/env python3
"""Run fixed, trusted local test suites independently of the SSH client (Linux)."""
import argparse
from datetime import datetime, timezone
import fcntl
import json
import os
from pathlib import Path
import re
import resource
import secrets
import signal
import subprocess
import sys
import time

SUITES={
 'browser-bridge':('chromebook-browser-bridge',[[sys.executable,'-m','unittest','discover','-p','test_*.py'],['node','--test','test_worker.cjs','test_persistence.cjs','test_input_visibility.cjs']]),
 'workbench':('chromebook-workbench',[[sys.executable,'-m','unittest','discover','-s','tests']]),
}
ID=re.compile(r'\d{8}T\d{6}Z-[0-9a-f]{8}')

def now():return datetime.now(timezone.utc).isoformat()
def store(path,data):
    temp=path.with_suffix('.tmp')
    fd=os.open(temp,os.O_WRONLY|os.O_CREAT|os.O_TRUNC,0o600)
    with os.fdopen(fd,'w') as out:json.dump(data,out,indent=2);out.write('\n')
    temp.replace(path)
def identity(pid):
    try:
        ticks=(Path('/proc')/str(pid)/'stat').read_text().rsplit(')',1)[1].split()[19]
        return [Path('/proc/sys/kernel/random/boot_id').read_text().strip(),ticks]
    except (OSError,IndexError):return None
def job_path(root,job):
    if not ID.fullmatch(job):raise ValueError('Invalid job ID')
    return root/job

def clean_revision(repo):
    dirty=subprocess.check_output(['git','status','--porcelain'],cwd=repo,text=True,timeout=10)
    if dirty:raise ValueError('Working copy has changes; commit or use a separate clean checkout')
    return subprocess.check_output(['git','rev-parse','HEAD'],cwd=repo,text=True,timeout=10).strip()
def limits():resource.setrlimit(resource.RLIMIT_FSIZE,(2*1024*1024,2*1024*1024))
def terminate(child):
    try:os.killpg(child.pid,signal.SIGTERM)
    except ProcessLookupError:pass
    try:child.wait(timeout=2)
    except subprocess.TimeoutExpired:
        try:os.killpg(child.pid,signal.SIGKILL)
        except ProcessLookupError:pass
        child.wait()

def run_job(root,job,repo,commands):
    directory=job_path(root,job);meta=directory/'result.json';result=json.loads(meta.read_text());child=None
    lockfile=root/(result['suite']+'.lock')
    with lockfile.open('a') as lock:
        lockfile.chmod(0o600)
        try:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        except BlockingIOError:
            result.update(state='busy',finishedAt=now());store(meta,result);return
        try:
            if clean_revision(repo)!=result['commit']:raise ValueError('Checkout changed since submission')
            result.update(state='running',pid=os.getpid(),processIdentity=identity(os.getpid()),startedAt=now(),steps=[]);store(meta,result)
            def interrupted(signum,frame):raise InterruptedError('Runner interrupted')
            signal.signal(signal.SIGTERM,interrupted);signal.signal(signal.SIGHUP,interrupted)
            deadline=time.monotonic()+result['timeoutSeconds']
            for command in commands:
                if clean_revision(repo)!=result['commit']:raise ValueError('Checkout changed during job')
                step={'command':command,'startedAt':now()};result['steps'].append(step);store(meta,result)
                log=directory/'test.log';fd=os.open(log,os.O_WRONLY|os.O_CREAT|os.O_APPEND,0o600)
                with os.fdopen(fd,'ab') as output:
                    output.write(('\n'+json.dumps(command)+'\n').encode());output.flush()
                    child=subprocess.Popen(command,cwd=repo,stdin=subprocess.DEVNULL,stdout=output,stderr=subprocess.STDOUT,start_new_session=True,pass_fds=(lock.fileno(),),preexec_fn=limits)
                    try:code=child.wait(timeout=max(0,deadline-time.monotonic()))
                    except subprocess.TimeoutExpired:
                        terminate(child);step['exitCode']=child.returncode;result['state']='timed_out';break
                child=None;step.update(exitCode=code,finishedAt=now());store(meta,result)
                if code!=0:result['state']='failed';break
            else:result['state']='passed' if clean_revision(repo)==result['commit'] else 'checkout_changed'
        except (OSError,ValueError,subprocess.SubprocessError,InterruptedError) as error:
            if child is not None:terminate(child)
            result.update(state='interrupted' if isinstance(error,InterruptedError) else 'failed',error=str(error)[:300])
        finally:
            result['finishedAt']=now();store(meta,result)

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    sub=parser.add_subparsers(dest='action',required=True)
    start=sub.add_parser('start');start.add_argument('suite',choices=SUITES);start.add_argument('--timeout',type=int,default=600)
    status=sub.add_parser('status');status.add_argument('job')
    internal=sub.add_parser('_run',help=argparse.SUPPRESS);internal.add_argument('job')
    args=parser.parse_args();os.umask(0o077)
    root=Path.home()/'.local/state/chromebook-workbench/jobs';root.mkdir(parents=True,exist_ok=True,mode=0o700);root.chmod(0o700)
    if args.action=='start':
        if not 1<=args.timeout<=1800:parser.error('Timeout must be1–1800 seconds')
        folder,commands=SUITES[args.suite];repo=Path.home()/'projects'/folder
        revision=clean_revision(repo);job=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ-')+secrets.token_hex(4)
        directory=job_path(root,job);directory.mkdir(mode=0o700)
        data={'job':job,'suite':args.suite,'commit':revision,'timeoutSeconds':args.timeout,'createdAt':now(),'state':'queued'};store(directory/'result.json',data)
        with (directory/'runner.log').open('ab') as output:
            process=subprocess.Popen([sys.executable,str(Path(__file__).resolve()),'_run',job],stdin=subprocess.DEVNULL,stdout=output,stderr=subprocess.STDOUT,start_new_session=True)
        print(json.dumps({'job':job,'pid':process.pid,'state':'submitted'}));return
    directory=job_path(root,args.job);data=json.loads((directory/'result.json').read_text())
    if args.action=='status':
        if data['state']=='running' and identity(data.get('pid'))!=data.get('processIdentity'):
            data['state']='interrupted';data['note']='Runner is gone; inspect private logs and any remaining test processes. No job was restarted.'
        print(json.dumps(data,indent=2));return
    folder,commands=SUITES[data['suite']];repo=Path.home()/'projects'/folder
    if data['suite']=='browser-bridge':
        commands=[commands[0],[*commands[1],*[name for name in ('test_power.cjs','test_popup.cjs') if (repo/name).is_file()]]]
    run_job(root,args.job,repo,commands)

if __name__=='__main__':main()
