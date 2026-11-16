"""Create a self-contained Linux x86_64 user download from a dedicated build venv."""
from pathlib import Path
import platform
import shutil
import subprocess
import sys
import tarfile

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from face_lab import __version__
from face_lab.download import check_models

if platform.system()!='Linux' or platform.machine() not in ('x86_64','AMD64'):
    raise SystemExit('This packaging script currently targets Linux x86_64 only.')
if not all(check_models(ROOT/'models').values()):
    raise SystemExit('Download/verify the models first: python -m face_lab --model-dir models --download-only')
subprocess.run([sys.executable,'-m','PyInstaller','--noconfirm','--clean','--distpath',str(ROOT/'portable-dist'),
                '--workpath',str(ROOT/'build/portable'),str(ROOT/'packaging/local-face-lab.spec')],check=True,cwd=ROOT)
bundle=ROOT/'portable-dist/LocalFaceLab'
shutil.copy2(ROOT/'packaging/PORTABLE_README.txt',bundle/'请先阅读_README.txt')
subprocess.run([str(bundle/'LocalFaceLab'),'--self-test'],check=True)
output=ROOT/'dist'/f'local-face-lab-v{__version__}-linux-x86_64-portable.tar.gz'
output.parent.mkdir(exist_ok=True)
with tarfile.open(output,'w:gz',compresslevel=6) as archive:
    archive.add(bundle,arcname='LocalFaceLab')
print('Portable download:',output)
