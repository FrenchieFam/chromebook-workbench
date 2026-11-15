#!/usr/bin/env python3
"""Pin an independently verified SSH host key over Tailscale userspace networking."""
import argparse
from pathlib import Path
import re
import shlex
import socket
import subprocess
import tempfile
import threading


def collect_key(client,host,port):
    listener=socket.socket();listener.bind(('127.0.0.1',0));listener.listen(5);listener.settimeout(.3)
    local_port=listener.getsockname()[1];stop=threading.Event();children=[]
    def accept():
        while not stop.is_set():
            try:connection,_=listener.accept()
            except socket.timeout:continue
            except OSError:break
            with connection:
                children.append(subprocess.Popen([str(client),'nc',host,str(port)],stdin=connection,stdout=connection,stderr=subprocess.DEVNULL))
    thread=threading.Thread(target=accept,daemon=True);thread.start()
    try:
        result=subprocess.run(['ssh-keyscan','-T','12','-p',str(local_port),'-t','ed25519','127.0.0.1'],capture_output=True,text=True,timeout=20)
    finally:
        stop.set();listener.close();thread.join(2)
        for child in children:
            if child.poll() is None:child.terminate()
        for child in children:
            try:child.wait(timeout=2)
            except subprocess.TimeoutExpired:child.kill();child.wait()
    entries=[line.split() for line in result.stdout.splitlines() if line and not line.startswith('#')]
    unique={(parts[1],parts[2]) for parts in entries if len(parts)==3 and parts[1]=='ssh-ed25519'}
    if len(unique)!=1:raise ValueError('No unique ED25519 key received. Nothing pinned; no login attempted.')
    return unique.pop()


def ssh_path(path):
    text=str(path)
    if any(ord(c)<32 for c in text):raise ValueError('Control characters in path')
    return '"'+text.replace('\\','\\\\').replace('"','\\"').replace('%','%%')+'"'


def pair(args):
    if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9.:-]{0,252}',args.host):raise ValueError('Invalid host')
    if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_-]{0,62}',args.alias):raise ValueError('Invalid SSH alias')
    if not re.fullmatch(r'[a-z_][a-z0-9_-]{0,31}',args.user):raise ValueError('Invalid Linux user')
    if not 1<=args.port<=65535:raise ValueError('Invalid port')
    if not re.fullmatch(r'SHA256:[A-Za-z0-9+/]{43}',args.fingerprint):raise ValueError('Supply the independently obtained SHA256 ED25519 fingerprint')
    identity=args.identity.expanduser().resolve();client=args.tailscale.expanduser().resolve()
    if not identity.is_file() or identity.stat().st_mode & 0o077:raise ValueError('Private identity must exist with no group/other permissions')
    directory=args.directory.expanduser().resolve()
    known=directory/(args.alias+'.known_hosts');config=directory/(args.alias+'.conf')
    algorithm,key=collect_key(client,args.host,args.port)
    pinned=f'{args.alias} {algorithm} {key}\n'
    with tempfile.NamedTemporaryFile(mode='w') as temporary:
        temporary.write(pinned);temporary.flush()
        actual=subprocess.check_output(['ssh-keygen','-lf',temporary.name,'-E','sha256'],text=True).split()[1]
    if actual!=args.fingerprint:raise ValueError('HOST KEY MISMATCH. Nothing pinned; no login attempted.')
    proxy=shlex.quote(str(client)).replace('%','%%')+' nc %h %p'
    content=f'''Host {args.alias}
    HostName {args.host}
    User {args.user}
    Port {args.port}
    IdentityFile {ssh_path(identity)}
    IdentitiesOnly yes
    BatchMode yes
    PasswordAuthentication no
    KbdInteractiveAuthentication no
    StrictHostKeyChecking yes
    UserKnownHostsFile {ssh_path(known)}
    HostKeyAlias {args.alias}
    HostKeyAlgorithms ssh-ed25519
    ConnectTimeout 15
    ServerAliveInterval 20
    ServerAliveCountMax 2
    ForwardAgent no
    ProxyCommand {proxy}
'''
    if known.exists() and known.read_text()!=pinned:raise ValueError('Existing pin differs; inspect instead of replacing it')
    if config.exists() and config.read_text()!=content:raise ValueError('Existing SSH config differs; inspect instead of replacing it')
    directory.mkdir(parents=True,exist_ok=True,mode=0o700);directory.chmod(0o700)
    for path,text in ((known,pinned),(config,content)):
        path.write_text(text);path.chmod(0o600)
    print('Public host fingerprint verified. Dedicated SSH config:',config)
    print('Use:',shlex.join(['ssh','-F',str(config),args.alias]))
    return config


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--host',required=True,help='Worker Tailscale IP or DNS name')
    parser.add_argument('--user',required=True,help='Worker Linux user')
    parser.add_argument('--port',type=int,default=2222)
    parser.add_argument('--fingerprint',required=True)
    parser.add_argument('--identity',type=Path,required=True)
    parser.add_argument('--alias',default='workbench-worker')
    parser.add_argument('--tailscale',type=Path,default=Path.home()/'bin/workbench-tailscale')
    parser.add_argument('--directory',type=Path,default=Path.home()/'.ssh')
    args=parser.parse_args()
    try:pair(args)
    except (OSError,ValueError,subprocess.SubprocessError) as error:parser.exit(1,str(error)+'\n')
if __name__=='__main__':main()
