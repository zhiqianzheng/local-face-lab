"""Installed CLI and local web application launcher."""
import argparse
import json
import os
from pathlib import Path
import socket
import threading
import time
import urllib.request
import webbrowser

from . import __version__
from .config import data_dir, model_dir


def main(argv=None):
    parser=argparse.ArgumentParser(description='Local Face Lab / 本地表情实验室')
    parser.add_argument('--version',action='version',version=__version__)
    parser.add_argument('--port',type=int,default=8766)
    parser.add_argument('--model-dir',type=Path,help='Directory containing downloaded models')
    parser.add_argument('--data-dir',type=Path,help='Directory for local recordings')
    parser.add_argument('--download-models',action='store_true',help='Download/repair missing model files')
    parser.add_argument('--download-only',action='store_true',help='Download models and exit')
    parser.add_argument('--check-models',action='store_true',help='Verify all required model checksums and exit')
    parser.add_argument('--no-browser',action='store_true',help='Do not open the browser automatically')
    args=parser.parse_args(argv)
    if not 1<=args.port<=65535:parser.error('port must be between 1 and 65535')
    if args.model_dir:os.environ['FACE_LAB_MODEL_DIR']=str(args.model_dir.expanduser().resolve())
    if args.data_dir:os.environ['FACE_LAB_DATA_DIR']=str(args.data_dir.expanduser().resolve())
    from .download import check_models, download_models
    try:
        if args.download_models or args.download_only:
            download_models(model_dir())
        states=check_models(model_dir())
        if args.check_models:
            for name,ok in states.items():print(('OK   ' if ok else 'FAIL ')+name)
            return 0 if all(states.values()) else 1
        if not all(states.values()):
            print('Models missing or invalid. Run: face-lab --download-models --download-only')
            print('Model directory:',model_dir())
            return 1
        if args.download_only:return 0
        url=f'http://127.0.0.1:{args.port}'
        with socket.socket() as probe:
            listening=probe.connect_ex(('127.0.0.1',args.port))==0
        if listening:
            try:
                with urllib.request.urlopen(url+'/health',timeout=3) as response:info=json.load(response)
                if info.get('application')!='local-face-lab':raise ValueError()
            except (OSError,ValueError):
                print(f'Port {args.port} is occupied by another application. Choose --port PORT.');return 1
            print('Local Face Lab is already running:',url)
            if not args.no_browser:webbrowser.open(url)
            return 0
        print('Loading models. All inference stays on this computer.',flush=True)
        from .app import app
        from waitress import serve
        if not args.no_browser:
            def open_when_ready():
                for _ in range(100):
                    try:
                        with urllib.request.urlopen(url+'/health',timeout=1):pass
                        webbrowser.open(url);return
                    except OSError:time.sleep(.2)
            threading.Thread(target=open_when_ready,daemon=True).start()
        print('Open:',url,'\nRecordings:',data_dir()/'recordings',flush=True)
        try:
            serve(app,host='127.0.0.1',port=args.port,threads=4,max_request_body_size=200*1024*1024)
        finally:
            from .app import engines
            engines.landmarker.close()
        return 0
    except (OSError,RuntimeError,ValueError) as error:
        print('Startup/download failed:',error)
        return 1
