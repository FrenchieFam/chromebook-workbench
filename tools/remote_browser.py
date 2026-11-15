#!/usr/bin/env python3
"""Use an installed worker browser bridge through a pinned SSH configuration."""
import argparse
from pathlib import Path
import shlex
import re
import subprocess


def command(config,host,arguments):
    if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.-]{0,252}',host):raise ValueError('Invalid SSH host alias')
    return ['ssh','-F',str(config),host,shlex.join(['.local/bin/chromebook-browser',*arguments])]


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config',type=Path,required=True)
    parser.add_argument('--host',default='workbench-worker',help='Alias from the dedicated SSH config')
    parser.add_argument('arguments',nargs=argparse.REMAINDER)
    args=parser.parse_args();arguments=args.arguments
    if arguments and arguments[0]=='--':arguments=arguments[1:]
    if not arguments:parser.error('Supply a browser action, for example: -- status')
    raise SystemExit(subprocess.call(command(args.config.expanduser(),args.host,arguments)))
if __name__=='__main__':main()
