"""Build a native bundle and ZIP on the current host. Does not publish releases."""
from pathlib import Path
import argparse
import platform
import shutil
import subprocess
import sys
from setup import frontend_fingerprint,write_json

ROOT=Path(__file__).resolve().parents[1]


def command(arguments,cwd=ROOT):
    print('Running: '+' '.join(map(str,arguments)),flush=True)
    subprocess.run(list(map(str,arguments)),cwd=cwd,check=True)


def main(argv=None):
    parser=argparse.ArgumentParser(description='Build a KokoSpeak desktop bundle for this computer.')
    parser.add_argument('--skip-install',action='store_true',help='Use already-installed Python build dependencies.')
    args=parser.parse_args(argv)
    if sys.version_info[:2] not in ((3,11),(3,12)):
        raise SystemExit('Activate a Python 3.11 or 3.12 build environment first.')
    node=shutil.which('node')
    if not node:
        raise SystemExit('The builder needs Node.js 22.12+ or 24. End users of the resulting app do not.')
    version=subprocess.check_output([node,'--version'],text=True).strip().lstrip('v').split('.')
    major,minor=map(int,version[:2])
    if major<22 or (major==22 and minor<12):raise SystemExit('Node.js 22.12+ is required.')
    if not args.skip_install:
        command([sys.executable,'-m','pip','install','--timeout','120','--retries','5','-r',ROOT/'server'/'requirements-build.txt'])
    # Invoke npm's JavaScript entry point directly; no cmd/shell quoting is needed.
    node_directory=Path(node).resolve().parent
    npm=shutil.which('npm')
    candidates=[node_directory/'node_modules'/'npm'/'bin'/'npm-cli.js',
                node_directory.parent/'lib'/'node_modules'/'npm'/'bin'/'npm-cli.js']
    if npm:candidates.append(Path(npm).resolve())
    npm_cli=next((path for path in candidates if path.is_file() and path.suffix=='.js'),None)
    if npm_cli is None:raise SystemExit('npm-cli.js was not found. Install a standard Node.js distribution for this build.')
    def npm_command(*arguments):
        command([node,npm_cli,*arguments],ROOT/'client')
    npm_command('install','--include=dev','--no-fund','--no-audit')
    npm_command('run','build')
    write_json(ROOT/'client'/'dist'/'.kokospeak-build.json',{'sourceFingerprint':frontend_fingerprint()})
    output=ROOT/'release'/'native'
    command([sys.executable,'-m','PyInstaller','--noconfirm','--clean','--distpath',output,
             '--workpath',ROOT/'build'/'pyinstaller',ROOT/'packaging'/'KokoSpeak.spec'])
    name=f'KokoSpeak-{sys.platform}-{platform.machine()}'
    release=ROOT/'release';release.mkdir(exist_ok=True)
    if sys.platform=='darwin':
        archive=release/f'{name}.zip'
        command(['ditto','-c','-k','--sequesterRsrc','--keepParent',output/'KokoSpeak.app',archive])
    else:
        archive=shutil.make_archive(str(release/name),'zip',root_dir=output,base_dir='KokoSpeak')
    print(f'\nCreated: {archive}\nThis bundle must be launch-tested on a clean machine before publishing.')
    return 0

if __name__=='__main__':
    try:sys.exit(main())
    except subprocess.CalledProcessError as error:
        print(f'Build stopped (exit {error.returncode}).',file=sys.stderr);sys.exit(error.returncode)
