"""Fail if release archives contain private data, caches or model binaries."""
from pathlib import Path, PurePosixPath
import sys
import tarfile
import zipfile

count=0
for path in Path(sys.argv[1] if len(sys.argv)>1 else 'dist').iterdir():
    if path.suffix in ('.whl','.zip'):
        with zipfile.ZipFile(path) as z: names=z.namelist()
    elif path.name.endswith('.tar.gz'):
        with tarfile.open(path) as t:names=t.getnames()
    else:continue
    for name in names:
        parts=PurePosixPath(name).parts
        assert not set(parts)&{'recordings','.venv','.git','backups','__pycache__','vendor'},(path,name)
        assert not name.lower().endswith(('.onnx','.task','.webm','.mp4','.avi','.y4m','.nupkg','.pyc')),(path,name)
        assert not any(part.startswith('.env') for part in parts),(path,name)
        assert not name.startswith('/') and '..' not in parts,(path,name)
    count+=1
    print('PASS release audit:',path.name,len(names),'entries')
assert count>0,'No release archives found'
