"""Idempotent project-local setup, executed by uv with Python 3.12."""
from pathlib import Path
import argparse
import hashlib
import json
import os
import platform
import shlex
import shutil
import stat
import subprocess
import sys
import tarfile
import tempfile
import time
import urllib.error
import urllib.request
import zipfile

ROOT=Path(__file__).resolve().parents[1]
RUNTIME=ROOT/'.runtime'


def file_digest(paths):
    digest=hashlib.sha256()
    for path in sorted(paths,key=lambda p:str(p)):
        if path.is_file():
            digest.update(str(path.relative_to(ROOT)).encode())
            digest.update(path.read_bytes())
    return digest.hexdigest()


def frontend_fingerprint():
    client=ROOT/'client'
    paths=[client/'package.json',client/'package-lock.json',client/'index.html',client/'vite.config.ts']
    paths+=list(client.glob('tsconfig*.json'))
    for directory in ('src','public'):
        paths+=list((client/directory).rglob('*'))
    return file_digest(paths)


def write_json(path,value):
    path.parent.mkdir(parents=True,exist_ok=True)
    temporary=path.with_suffix(path.suffix+'.tmp')
    temporary.write_text(json.dumps(value,indent=2)+'\n',encoding='utf-8')
    temporary.replace(path)


def load_json(path):
    try:return json.loads(path.read_text(encoding='utf-8'))
    except (OSError,ValueError):return {}


def run(command,cwd=ROOT,env=None):
    print('\n> '+shlex.join(map(str,command)),flush=True)
    RUNTIME.mkdir(parents=True,exist_ok=True)
    with (RUNTIME/'setup.log').open('a',encoding='utf-8') as log:
        log.write('\n> '+shlex.join(map(str,command))+'\n')
        with subprocess.Popen(list(map(str,command)),cwd=cwd,env=env,stdout=subprocess.PIPE,
                              stderr=subprocess.STDOUT,text=True,encoding='utf-8',errors='replace') as process:
            for line in process.stdout:
                print(line,end='',flush=True);log.write(line)
            code=process.wait()
            if code:
                raise RuntimeError(f'Command failed (exit {code}). See {RUNTIME/"setup.log"}. Run the installer again to retry.')


def download(url,destination,checksum=None):
    destination=Path(destination)
    destination.parent.mkdir(parents=True,exist_ok=True)
    partial=destination.with_name(destination.name+'.part')
    for attempt in range(3):
        try:
            print(f'Downloading {url}',flush=True)
            request=urllib.request.Request(url,headers={'User-Agent':'KokoSpeak-Installer/1.0'})
            digest=hashlib.sha256();read=0;last=-1
            with urllib.request.urlopen(request,timeout=120) as response,partial.open('wb') as output:
                total=int(response.headers.get('Content-Length','0'))
                while block:=response.read(1024*1024):
                    output.write(block);digest.update(block);read+=len(block)
                    bucket=int(read*10/total) if total else -1
                    if total and bucket>last:
                        print(f'  {min(100,bucket*10)}%',flush=True);last=bucket
                if total and read!=total:raise OSError('Download ended before all bytes arrived.')
            if checksum and digest.hexdigest()!=checksum:
                raise OSError('The downloaded file failed its SHA-256 checksum.')
            partial.replace(destination)
            return destination
        except (OSError,urllib.error.URLError):
            partial.unlink(missing_ok=True)
            if attempt==2:raise
            print('Download interrupted; retrying...',flush=True)
            time.sleep(2**attempt)


def node_target(system=None,machine=None):
    system=system or sys.platform
    machine=(machine or platform.machine()).lower()
    operating={'darwin':'darwin','win32':'win','linux':'linux'}.get(system)
    architecture={'arm64':'arm64','aarch64':'arm64','x86_64':'x64','amd64':'x64'}.get(machine)
    if not operating or not architecture:
        raise RuntimeError(f'Automatic Node setup is unavailable for {system}/{machine}. Build client/dist on a supported computer first.')
    return operating,architecture


def safe_extract(archive,destination):
    destination=Path(destination).resolve()
    if str(archive).endswith('.zip'):
        with zipfile.ZipFile(archive) as bundle:
            for item in bundle.infolist():
                resolved=(destination/item.filename).resolve()
                if not resolved.is_relative_to(destination) or stat.S_ISLNK(item.external_attr>>16):
                    raise ValueError('Unsafe path in downloaded ZIP archive.')
            bundle.extractall(destination)
    else:
        with tarfile.open(archive,'r:gz') as bundle:
            # Python 3.12's data filter rejects traversal and unsafe links.
            bundle.extractall(destination,filter='data')


def node_paths(directory):
    directory=Path(directory)
    if os.name=='nt':return directory/'node.exe',directory/'node_modules'/'npm'/'bin'/'npm-cli.js'
    return directory/'bin'/'node',directory/'lib'/'node_modules'/'npm'/'bin'/'npm-cli.js'


def ensure_node():
    node_root=RUNTIME/'node'
    for directory in sorted(node_root.glob('node-v24.*'),reverse=True):
        node,npm=node_paths(directory)
        if node.is_file() and npm.is_file():return node,npm
    operating,architecture=node_target()
    node_root.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='download-',dir=node_root) as scratch:
        scratch=Path(scratch)
        index=download('https://nodejs.org/dist/index.json',scratch/'index.json')
        releases=json.loads(index.read_text())
        selected=next((row for row in releases if row['version'].startswith('v24.') and row.get('lts')),None)
        if not selected:raise RuntimeError('No Node.js 24 LTS release was found.')
        version=selected['version']
        if not all(character in 'v0123456789.' for character in version):raise ValueError('Invalid Node release version.')
        directory=f'node-{version}-{operating}-{architecture}'
        filename=directory+('.zip' if operating=='win' else '.tar.gz')
        base=f'https://nodejs.org/dist/{version}/'
        sums=download(base+'SHASUMS256.txt',scratch/'SHASUMS256.txt')
        entries=[line.split() for line in sums.read_text().splitlines()]
        checksum=next((parts[0] for parts in entries if len(parts)==2 and parts[1].lstrip('*')==filename),None)
        if not checksum or len(checksum)!=64:raise RuntimeError('The Node archive checksum was not found.')
        archive=download(base+filename,scratch/filename,checksum)
        safe_extract(archive,scratch/'unpacked')
        (scratch/'unpacked'/directory).replace(node_root/directory)
    node,npm=node_paths(node_root/directory)
    if not node.is_file() or not npm.is_file():raise RuntimeError('The Node archive did not contain the expected executables.')
    return node,npm


def install_python(uv,all_languages,repair,record):
    environment=RUNTIME/'python312'
    python=environment/('Scripts/python.exe' if os.name=='nt' else 'bin/python')
    if not python.is_file():run([uv,'venv','--python','3.12',environment])
    actual=subprocess.check_output([str(python),'-c','import sys;print("%s.%s"%sys.version_info[:2])'],text=True).strip()
    if actual!='3.12':raise RuntimeError(f'{environment} contains Python {actual}; move that folder aside and rerun setup.')
    requirements=ROOT/'server'/'requirements.txt'
    extras=ROOT/'server'/'requirements-languages.txt'
    fingerprint=file_digest([requirements,*([extras] if all_languages else [])])+f'|3.12|{sys.platform}|{platform.machine()}'
    if repair or record.get('pythonFingerprint')!=fingerprint:
        env=os.environ.copy();env['UV_HTTP_TIMEOUT']='120';env['UV_HTTP_RETRIES']='5'
        run([uv,'pip','install','--python',python,'-r',extras if all_languages else requirements],env=env)
        if all_languages and (repair or not record.get('allLanguages')):
            run([python,'-m','unidic','download'])
        run([python,'-c','import fastapi, uvicorn, numpy, soundfile, kokoro, imageio_ffmpeg; '
                        'import en_core_web_sm; import subprocess; '
                        'subprocess.run([imageio_ffmpeg.get_ffmpeg_exe(),"-version"],check=True,stdout=subprocess.DEVNULL)'])
    return python,fingerprint


def install_frontend(repair=False):
    client=ROOT/'client';dist=client/'dist';manifest=dist/'.kokospeak-build.json'
    fingerprint=frontend_fingerprint()
    if not repair and (dist/'index.html').is_file() and load_json(manifest).get('sourceFingerprint')==fingerprint:
        return
    print('\nPreparing the interface (Node.js stays inside this project)...',flush=True)
    node,npm=ensure_node()
    env=os.environ.copy();env['PATH']=str(node.parent)+os.pathsep+env.get('PATH','')
    env['npm_config_fetch_retries']='5';env['npm_config_fetch_timeout']='120000'
    run([node,npm,'install','--include=dev','--no-fund','--no-audit'],cwd=client,env=env)
    run([node,npm,'run','build'],cwd=client,env=env)
    if not (dist/'index.html').is_file():raise RuntimeError('The frontend build did not create index.html.')
    write_json(manifest,{'sourceFingerprint':frontend_fingerprint()})


def main(argv=None):
    parser=argparse.ArgumentParser(description='Install and launch KokoSpeak locally.')
    parser.add_argument('--uv',required=True)
    parser.add_argument('--repair',action='store_true')
    parser.add_argument('--all-languages',action='store_true')
    parser.add_argument('--no-launch',action='store_true')
    args=parser.parse_args(argv)
    if sys.version_info[:2]!=(3,12):raise RuntimeError('Run install.sh or install.ps1 so Python 3.12 is selected automatically.')
    RUNTIME.mkdir(parents=True,exist_ok=True)
    receipt=RUNTIME/'installed.json'
    record=load_json(receipt)
    all_languages=args.all_languages or bool(record.get('allLanguages'))
    print('KokoSpeak setup\nPython, dependencies, and build tools stay separate from your existing environments.',flush=True)
    python,fingerprint=install_python(args.uv,all_languages,args.repair,record)
    # Keep completed backend work if a network failure interrupts the frontend build.
    write_json(receipt,dict(pythonFingerprint=fingerprint,allLanguages=all_languages))
    install_frontend(args.repair)
    print('\nKokoSpeak is ready. The first generation may download model and voice files.',flush=True)
    if not args.no_launch:
        return subprocess.call([str(python),str(ROOT/'launch.py')],cwd=ROOT)
    print('Launch later with start.sh or the Start KokoSpeak file.')
    return 0

if __name__=='__main__':
    try:sys.exit(main())
    except KeyboardInterrupt:
        print('\nSetup interrupted. Run it again to continue.');sys.exit(130)
    except Exception as error:
        print(f'\nKokoSpeak setup stopped: {error}',file=sys.stderr);sys.exit(1)
