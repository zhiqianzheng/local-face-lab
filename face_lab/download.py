"""Download upstream model artifacts atomically, with pinned integrity checks."""
import base64
import hashlib
import json
from pathlib import Path
import time
import urllib.request
import zipfile
from .config import PACKAGE_DIR

MANIFEST = json.loads((PACKAGE_DIR/'resources/model-manifest.json').read_text())

def digest(path, algorithm='sha256'):
    result=hashlib.new(algorithm)
    with Path(path).open('rb') as f:
        for chunk in iter(lambda:f.read(1024*1024),b''):
            result.update(chunk)
    return result

def valid(path, entry):
    path=Path(path)
    return path.is_file() and path.stat().st_size==entry['bytes'] and digest(path).hexdigest()==entry['sha256']

def check_models(directory):
    return {entry['path']:valid(Path(directory)/entry['path'],entry) for entry in MANIFEST['files']}

def fetch(url, destination):
    destination=Path(destination)
    destination.parent.mkdir(parents=True,exist_ok=True)
    temporary=destination.with_suffix(destination.suffix+'.part')
    for attempt in range(3):
        try:
            request=urllib.request.Request(url,headers={'User-Agent':'Local-Face-Lab/0.1.0'})
            with urllib.request.urlopen(request,timeout=90) as source,temporary.open('wb') as target:
                total=int(source.headers.get('Content-Length',0));received=0;reported=0
                while chunk:=source.read(1024*1024):
                    target.write(chunk);received+=len(chunk)
                    if received-reported>=8*1024*1024:
                        print(f'  {destination.name}: {received//1048576} / {total//1048576 if total else "?"} MiB',flush=True);reported=received
                if total and received!=total:
                    raise OSError('Incomplete download')
            temporary.replace(destination)
            return
        except (OSError,ValueError):
            temporary.unlink(missing_ok=True)
            if attempt==2:raise
            time.sleep(1+attempt)

def download_models(directory):
    directory=Path(directory);directory.mkdir(parents=True,exist_ok=True)
    missing=[]
    for entry in MANIFEST['files']:
        path=directory/entry['path']
        if valid(path,entry):
            print('OK:',entry['path'],flush=True);continue
        if 'archive_member' in entry:
            missing.append(entry);continue
        print('Downloading:',entry['url'],flush=True)
        fetch(entry['url'],path)
        if not valid(path,entry):
            path.unlink(missing_ok=True)
            raise RuntimeError(f'Checksum mismatch: {entry["path"]}. Upstream file may have changed.')
    if missing:
        package=MANIFEST['libreface_package'];archive=directory/'.downloads'/package['filename']
        def archive_valid():
            return archive.is_file() and base64.b64encode(digest(archive,'sha512').digest()).decode()==package['sha512_base64']
        if not archive_valid():
            print('Downloading official LibreFace package (USC Research License):',flush=True)
            fetch(package['url'],archive)
        if not archive_valid():
            archive.unlink(missing_ok=True);raise RuntimeError('LibreFace package checksum mismatch')
        with zipfile.ZipFile(archive) as z:
            for entry in missing:
                path=directory/entry['path'];path.parent.mkdir(parents=True,exist_ok=True)
                temporary=path.with_suffix('.part')
                temporary.write_bytes(z.read(entry['archive_member']))
                if not valid(temporary,entry):
                    temporary.unlink(missing_ok=True);raise RuntimeError('Checksum mismatch: '+entry['path'])
                temporary.replace(path);print('Extracted:',entry['path'],flush=True)
    if not all(check_models(directory).values()):
        raise RuntimeError('Model verification failed')
