"""Fail if release archives contain private data, caches or model binaries."""
from pathlib import Path, PurePosixPath
import sys
import hashlib
import json
import tarfile
import zipfile

count=0
for path in Path(sys.argv[1] if len(sys.argv)>1 else 'dist').iterdir():
    if path.suffix in ('.whl','.zip'):
        with zipfile.ZipFile(path) as z: names=z.namelist()
    elif path.name.endswith('.tar.gz'):
        with tarfile.open(path) as t:names=t.getnames()
    else:continue
    portable='-portable.tar.gz' in path.name
    model_entries=[]
    for name in names:
        parts=PurePosixPath(name).parts
        assert not set(parts)&{'recordings','.venv','.git','backups','__pycache__','vendor'},(path,name)
        assert not name.lower().endswith(('.webm','.mp4','.avi','.y4m','.nupkg','.pyc')),(path,name)
        if name.lower().endswith(('.onnx','.task')):
            assert portable and '/_internal/bundled_models/' in name,(path,name)
            model_entries.append(name)
        assert not any(part.startswith('.env') for part in parts),(path,name)
        assert not name.startswith('/') and '..' not in parts,(path,name)
    if portable:
        manifest=json.loads((Path(__file__).resolve().parents[1]/'face_lab/resources/model-manifest.json').read_text())
        assert len(model_entries)==len(manifest['files']),(path,model_entries)
        with tarfile.open(path) as archive:
            for entry in manifest['files']:
                name='LocalFaceLab/_internal/bundled_models/'+entry['path']
                file=archive.extractfile(name);hash_value=hashlib.sha256()
                while chunk:=file.read(1024*1024):hash_value.update(chunk)
                assert hash_value.hexdigest()==entry['sha256'],name
            assert archive.getmember('LocalFaceLab/LocalFaceLab').mode & 0o111
    count+=1
    print('PASS release audit:',path.name,len(names),'entries')
assert count>0,'No release archives found'
