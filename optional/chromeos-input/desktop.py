#!/usr/bin/env python3
"""Operate ChromeOS host input over existing pinned-key SSH, without network listener."""
import argparse
import json
import os
import re
from pathlib import Path
import shlex
import shutil
import struct
import subprocess
import sys
import time

HOST_ALIAS='chromeos-host'
BINARY='/usr/local/libexec/workbench-input'
SOCKET='/run/chromeos-workbench-input/control.sock'
DOWNLOADS=next((p for p in (Path('/mnt/shared/MyFiles/Downloads'),Path('/mnt/chromeos/MyFiles/Downloads')) if p.is_dir()),Path('/mnt/shared/MyFiles/Downloads'))
STATE=Path.home()/'.config/chromeos-workbench-input/screen.json'

def send(command):
    remote=shlex.join([BINARY,'--send',SOCKET,command])
    result=subprocess.run(['ssh','-o','BatchMode=yes','-o','StrictHostKeyChecking=yes',HOST_ALIAS,remote],capture_output=True,text=True,timeout=35)
    if result.returncode or not result.stdout.startswith('OK'):
        raise RuntimeError('Host helper unavailable or rejected command. Start Linux and the manual host startup helper.')
    return result.stdout.strip()

def geometry():
    try:
        info=send('info')
    except RuntimeError:
        raise RuntimeError('The host must run a helper supporting info; no guessed geometry fallback')
    match=re.fullmatch(r'OK width=(\d+) height=(\d+) version=([\w.]+)', info)
    if not match:raise RuntimeError('Unexpected host geometry response')
    return dict(width=int(match[1]),height=int(match[2]),version=match[3],pointerBackend='absolute-touch')

def check_screen():
    try:observed=json.loads(STATE.read_text())
    except (OSError,ValueError):raise RuntimeError('Take and inspect a fresh full-desktop screenshot first')
    if not isinstance(observed,dict) or not all(type(observed.get(k)) is int for k in ('width','height')) or not isinstance(observed.get('capturedAt'),(int,float)):
        raise RuntimeError('Invalid screen state; take and inspect a fresh screenshot')
    if not 0 <= time.time()-observed.get('capturedAt',0) <= 120:
        raise RuntimeError('Desktop screenshot is stale; take and inspect a fresh one')
    configured=geometry()
    if (observed['width'],observed['height']) != (configured['width'],configured['height']):
        raise RuntimeError('Display geometry changed; recalibrate the host helper before pointer input')
    return configured

def screenshot(destination):
    before={p:p.stat().st_mtime_ns for p in DOWNLOADS.glob('Screenshot*.png')}
    send('key ctrl+overview')
    for _ in range(20):
        time.sleep(.3)
        candidates=[p for p in DOWNLOADS.glob('Screenshot*.png') if p.stat().st_mtime_ns!=before.get(p)]
        if candidates:
            source=max(candidates,key=lambda p:p.stat().st_mtime_ns)
            try:
                with source.open('rb') as stream: header=stream.read(24)
                if header[:8]!=b'\x89PNG\r\n\x1a\n' or len(header)<24:continue
                width,height=struct.unpack('>II',header[16:24])
                shutil.copyfile(source,destination)
                os.chmod(destination,0o600)
                STATE.parent.mkdir(mode=0o700,parents=True,exist_ok=True)
                STATE.write_text(json.dumps({'width':width,'height':height,'capturedAt':time.time()}))
                STATE.chmod(0o600)
                return {'path':str(destination),'width':width,'height':height}
            except OSError:continue
    raise RuntimeError('No fresh screenshot found in shared Downloads. Screenshot save location may differ.')

def main():
    global HOST_ALIAS,DOWNLOADS
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--ssh-host',default='chromeos-host',help='Existing pinned OpenSSH host alias')
    parser.add_argument('--downloads',type=Path,default=DOWNLOADS,help='ChromeOS shared screenshot folder')
    parser.add_argument('action',choices=['ping','key','text','move','click','scroll','screenshot','stop','info','drag'])
    parser.add_argument('values',nargs='*')
    parser.add_argument('--output',type=Path)
    args=parser.parse_args()
    HOST_ALIAS=args.ssh_host;DOWNLOADS=args.downloads
    if args.action=='screenshot':
        if not args.output:parser.error('screenshot requires --output /tmp/desktop.png')
        print(screenshot(args.output));return
    if args.action=='info':
        print(json.dumps(geometry()));return
    if args.action in ('ping','stop'):
        if args.values:parser.error('No extra arguments allowed')
        command=args.action
    elif args.action in ('key','text','click','scroll'):
        if len(args.values)!=1:parser.error('Supply exactly one value; quote text')
        value=args.values[0]
        if any(ord(c)<32 or ord(c)>126 for c in value):parser.error('Only printable ASCII is supported; no newline/Enter is implicit')
        if args.action=='text' and len(value)>1000:parser.error('Text is limited to 1000 characters')
        if args.action=='click' and value not in ('left','right','middle'):parser.error('Use left, right or middle')
        if args.action=='click' and value!='left':parser.error('The absolute-touch backend cannot emit real right/middle clicks. For a touch context menu, use drag X Y X Y 900 after inspecting the target.')
        if args.action=='scroll':parser.error('Wheel events are unsupported by the absolute-touch backend. Use a vertical drag gesture or key pageup/pagedown after inspecting focus.')
        if args.action=='scroll' and not -20<=int(value)<=20:parser.error('Scroll must be between -20 and 20')
        if args.action in ('click','scroll'):check_screen()
        command=args.action+' '+value
    elif args.action=='drag':
        if len(args.values)!=5:parser.error('drag requires X1 Y1 X2 Y2 MILLISECONDS')
        x1,y1,x2,y2,ms=map(int,args.values)
        screen=check_screen()
        if screen['version']=='legacy-0.1.0':parser.error('Install the prepared host helper 0.2.0 for drag support')
        if not (0<=x1<screen['width'] and 0<=x2<screen['width'] and 0<=y1<screen['height'] and 0<=y2<screen['height'] and 100<=ms<=2000):parser.error('Drag coordinates or duration outside bounds')
        command=f'drag {x1} {y1} {x2} {y2} {ms}'
    else:
        if len(args.values)!=2:parser.error('move requires X Y in desktop screenshot coordinates')
        x,y=map(int,args.values)
        screen=check_screen()
        if not 0<=x<screen['width'] or not 0<=y<screen['height']:parser.error('Pointer outside calibrated desktop')
        command=f'move {x} {y}'
    print(send(command))

if __name__=='__main__':
    try:main()
    except (OSError,ValueError,RuntimeError,subprocess.SubprocessError) as e:raise SystemExit(str(e))
