#!/usr/bin/env python3
"""Install a dedicated user-service Tailscale in userspace mode. No login or host changes."""
import argparse
import hashlib
import io
import os
import re
from pathlib import Path
import platform
import shlex
import shutil
import subprocess
import tarfile
import tempfile
import urllib.request

VERSION='1.104.7'
BASE='https://pkgs.tailscale.com/stable/'

def run(*args):
    return subprocess.run(args,check=True)

def unit_quote(value):
    return '"'+str(value).replace('\\','\\\\').replace('"','\\"').replace('%','%%').replace('$','$$')+'"'

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--name',required=True,help='Unique device name, e.g. workbench-coordinator')
    args=parser.parse_args()
    if not re.fullmatch(r'[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?',args.name):raise SystemExit('Use a lowercase hostname of 1–63 letters/digits/hyphens.')
    if os.geteuid()==0:raise SystemExit('Run as the normal Linux user, not sudo.')
    if platform.machine()!='x86_64':raise SystemExit('This prepared package is for x86_64 only.')
    home=Path.home();app=home/'.local/share/tailscale-workbench';state=home/'.local/state/tailscale-workbench'
    existing=shutil.which('tailscale')
    if existing and not Path(existing).resolve().is_relative_to(app):
        raise SystemExit('An existing Tailscale installation was found; inspect it before installing a second one.')
    active=subprocess.run(['systemctl','is-active','--quiet','tailscaled.service'],capture_output=True)
    if active.returncode==0:raise SystemExit('A system Tailscale service is active; inspect before proceeding.')
    filename=f'tailscale_{VERSION}_amd64.tgz'
    print('Downloading official stable package',VERSION,flush=True)
    with urllib.request.urlopen(BASE+filename,timeout=60) as response:data=response.read()
    with urllib.request.urlopen(BASE+filename+'.sha256',timeout=30) as response:expected=response.read().decode().split()[0]
    actual=hashlib.sha256(data).hexdigest()
    if actual!=expected:raise SystemExit('Official package checksum mismatch; nothing installed.')
    units=home/'.config/systemd/user';units.mkdir(parents=True,exist_ok=True)
    unit=units/'workbench-tailscaled.service'
    content='''[Unit]
Description=Workbench Tailscale (userspace, Linux user only)
After=network.target

[Service]
'''+f'ExecStart={unit_quote(app/"tailscaled")} --tun=userspace-networking --state={unit_quote(state/"tailscaled.state")} --socket=%t/workbench-tailscale/tailscaled.sock --port=0\n'+'''RuntimeDirectory=workbench-tailscale
RuntimeDirectoryMode=0700
UMask=0077
NoNewPrivileges=true
Restart=on-failure
RestartSec=3

[Install]
WantedBy=default.target
'''
    if unit.exists() and unit.read_text()!=content:raise SystemExit('Existing workbench unit differs; inspect before replacing.')
    bins=home/'bin';bins.mkdir(exist_ok=True)
    wrapper=bins/'workbench-tailscale'
    script='#!/bin/sh\nexec '+shlex.quote(str(app/'tailscale'))+' --socket="${XDG_RUNTIME_DIR:-/run/user/$(id -u)}/workbench-tailscale/tailscaled.sock" "$@"\n'
    if wrapper.exists() and wrapper.read_text()!=script:raise SystemExit('Existing wrapper differs; inspect before replacing.')
    app.mkdir(parents=True,exist_ok=True);state.mkdir(mode=0o700,parents=True,exist_ok=True);state.chmod(0o700)
    prefix=f'tailscale_{VERSION}_amd64/'
    with tarfile.open(fileobj=io.BytesIO(data),mode='r:gz') as archive:
        for name in ('tailscale','tailscaled'):
            member=archive.getmember(prefix+name)
            if not member.isfile():raise SystemExit('Unexpected archive member')
            with tempfile.NamedTemporaryFile(dir=app,delete=False) as temporary:
                temporary.write(archive.extractfile(member).read());temporary_path=Path(temporary.name)
            temporary_path.chmod(0o755);temporary_path.replace(app/name)
    run(str(app/'tailscale'),'version')
    unit.write_text(content)
    wrapper.write_text(script);wrapper.chmod(0o755)
    run('systemctl','--user','daemon-reload')
    run('systemctl','--user','enable','--now','workbench-tailscaled.service')
    print('Installed userspace service and',wrapper)
    print('No account login performed. Next, owner runs or approves:')
    print(str(wrapper)+f' up --hostname={args.name} --accept-dns=false --accept-routes=false --timeout=10s')
    print('Keep state private and local. Never copy tailscaled.state to Drive or Git.')
    print('Rollback: systemctl --user disable --now workbench-tailscaled.service')

if __name__=='__main__':main()
