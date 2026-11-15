#!/usr/bin/env python3
"""Read-only, on-demand health of two Linux/browser workbenches over pinned SSH."""
import argparse
from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
import re
import subprocess


def read(command):
    try:
        result=subprocess.run(command,capture_output=True,text=True,timeout=25)
        if result.returncode:return {'error':'Health command failed or worker is unreachable'}
        data=json.loads(result.stdout)
        return data if isinstance(data,dict) else {'error':'Health command did not return an object'}
    except (OSError,ValueError,subprocess.TimeoutExpired):
        return {'error':'Health command unavailable, timed out or returned invalid JSON'}


def assess(report,required):
    browser=report.get('browser',{})
    service=report.get('service')=='active' or report.get('bridgeService',{}).get('ok') is True
    reachable=browser.get('reachable',browser.get('serviceReachable',False)) is True
    connected=browser.get('connected') is True
    running=browser.get('extensionVersion')
    staged=browser.get('stagedExtensionVersion')
    target=staged or required
    if report.get('error') or not service or not reachable:state='unavailable'
    elif not connected:state='disconnected'
    elif running!=target:state='reload extension'
    else:state='ready'
    return {'state':state,'serviceActive':service,'browserReachable':reachable,
            'connected':connected,'runningVersion':running,'stagedVersion':staged,
            'expectedVersion':target}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config',type=Path,required=True,help='Dedicated pinned SSH configuration')
    parser.add_argument('--host',default='workbench-worker')
    parser.add_argument('--local-check',type=Path,default=Path.home()/'.local/bin/chromebook-bridge-check')
    parser.add_argument('--required-version',default='0.3.1')
    parser.add_argument('--json',action='store_true')
    args=parser.parse_args()
    if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.-]{0,252}',args.host):parser.error('Invalid SSH host alias')
    with ThreadPoolExecutor(max_workers=2) as pool:
        local=pool.submit(read,[str(args.local_check.expanduser())])
        worker=pool.submit(read,['ssh','-o','BatchMode=yes','-o','ConnectTimeout=10','-F',str(args.config.expanduser()),args.host,'.local/bin/chromebook-bridge-check'])
        report={'coordinator':assess(local.result(),args.required_version),
                'worker':assess(worker.result(),args.required_version)}
    ready=all(node['state']=='ready' for node in report.values())
    if args.json:print(json.dumps({'ready':ready,'machines':report},indent=2))
    else:
        for name,node in report.items():
            print(f"{name}: {node['state']} — browser {node['runningVersion'] or 'unknown'}, expected {node['expectedVersion']}")
    return 0 if ready else 1

if __name__=='__main__':raise SystemExit(main())
