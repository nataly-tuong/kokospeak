"""Launch the built browser UI and a local server; also the desktop bundle entry point."""
from pathlib import Path
import argparse
import json
import logging
import os
import secrets
import socket
import sys
import threading
import time
import urllib.error
import urllib.request
import webbrowser

ROOT = Path(__file__).resolve().parent
if not getattr(sys,'frozen',False):
    sys.path.insert(0,str(ROOT/'server'))
from src.runtime import client_dist, user_data_dir


def bind_local_socket(port):
    sock=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
    if os.name=='nt':
        sock.setsockopt(socket.SOL_SOCKET,socket.SO_EXCLUSIVEADDRUSE,1)
    try:
        sock.bind(('127.0.0.1',port))
    except OSError:
        if port==0:
            sock.close();raise
        sock.bind(('127.0.0.1',0))
    sock.listen(128)
    return sock


def health(port):
    try:
        # Local loopback must not be sent through a configured corporate HTTP proxy.
        opener=urllib.request.build_opener(urllib.request.ProxyHandler({}))
        with opener.open(f'http://127.0.0.1:{int(port)}/api/health',timeout=1) as response:
            return json.load(response)
    except (OSError,ValueError,urllib.error.URLError):
        return {}


def read_instance(path):
    try:
        data=json.loads(path.read_text())
        if (isinstance(data.get('port'),int) and 0<data['port']<65536
                and isinstance(data.get('token'),str) and data['token']
                and health(data['port']).get('appId')=='kokospeak'):
            return data
    except (OSError,ValueError,KeyError,TypeError):
        pass
    return None


def browser_url(port,token):
    return f'http://127.0.0.1:{port}/#session={token}'


def main(argv=None):
    parser=argparse.ArgumentParser(description='Start KokoSpeak in your browser.')
    parser.add_argument('--port',type=int,default=8000)
    parser.add_argument('--no-browser',action='store_true')
    args=parser.parse_args(argv)
    if not 0<=args.port<=65535:
        parser.error('Port must be between 0 and 65535.')
    data=user_data_dir();data.mkdir(parents=True,exist_ok=True)
    log=data/'launcher.log'
    if sys.stdout is None:
        sys.stdout=open(log,'a',encoding='utf-8',buffering=1)
    if sys.stderr is None:
        sys.stderr=sys.stdout
    logging.basicConfig(level=logging.INFO,filename=log,encoding='utf-8')
    if not (client_dist()/'index.html').is_file():
        raise RuntimeError('The interface is not built. Run the installation script from the project folder first.')
    if getattr(sys,'frozen',False):
        os.environ.setdefault('HF_HOME',str(data/'models'))
    instance=data/'launcher.json'
    existing=read_instance(instance)
    if existing:
        print(f'KokoSpeak is already running at http://127.0.0.1:{existing["port"]}')
        if not args.no_browser:
            webbrowser.open(browser_url(existing['port'],existing['token']))
        return 0
    token=secrets.token_urlsafe(32)
    os.environ['KOKOSPEAK_MANAGED_TOKEN']=token
    import uvicorn
    from src.main import app
    server=uvicorn.Server(uvicorn.Config(app,host='127.0.0.1',port=args.port,workers=1,log_level='info'))
    app.state.shutdown_callback=lambda:setattr(server,'should_exit',True)
    sock=bind_local_socket(args.port)
    port=sock.getsockname()[1]
    fd=os.open(instance,os.O_WRONLY|os.O_CREAT|os.O_TRUNC,0o600)
    with os.fdopen(fd,'w',encoding='utf-8') as output:
        json.dump(dict(port=port,token=token,pid=os.getpid()),output)
    ready=threading.Event()
    def open_when_ready():
        deadline=time.monotonic()+60
        while not ready.is_set() and time.monotonic()<deadline:
            if health(port).get('appId')=='kokospeak':
                if not args.no_browser:
                    webbrowser.open(browser_url(port,token))
                return
            ready.wait(.25)
        if not ready.is_set():
            logging.error('Server did not become ready within 60 seconds.')
    thread=threading.Thread(target=open_when_ready,daemon=True)
    thread.start()
    print(f'KokoSpeak: http://127.0.0.1:{port}')
    print('Use Quit KokoSpeak in the toolbar to stop it, or press Ctrl+C here.')
    try:
        server.run(sockets=[sock])
    finally:
        ready.set();sock.close()
        try:
            record=json.loads(instance.read_text())
            if record.get('pid')==os.getpid():instance.unlink(missing_ok=True)
        except (OSError,ValueError):pass
    return 0


def report_error(error):
    message=f'KokoSpeak could not start.\n\n{error}\n\nSee {user_data_dir()/"launcher.log"} for details.'
    logging.exception('Launcher failed')
    if getattr(sys,'frozen',False) and sys.platform=='win32':
        import ctypes
        ctypes.windll.user32.MessageBoxW(None,message,'KokoSpeak',0x10)
    elif getattr(sys,'frozen',False) and sys.platform=='darwin':
        import subprocess
        # Send dialog content as argv, never as AppleScript source interpolation.
        script='on run argv\n display alert "KokoSpeak could not start" message (item 1 of argv)\nend run'
        subprocess.run(['osascript','-e',script,message],check=False)
    else:
        print(message,file=sys.stderr)


if __name__=='__main__':
    import multiprocessing
    multiprocessing.freeze_support()
    try:sys.exit(main())
    except KeyboardInterrupt:sys.exit(0)
    except Exception as error:
        report_error(error);sys.exit(1)
