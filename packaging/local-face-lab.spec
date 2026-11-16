# Build on each target operating system; PyInstaller is not a cross compiler.
from pathlib import Path
import importlib.metadata
from PyInstaller.utils.hooks import collect_data_files, collect_dynamic_libs, copy_metadata

root=Path(SPECPATH).parent
manifest=__import__('json').loads((root/'face_lab/resources/model-manifest.json').read_text())
datas=[(str(root/'face_lab/templates'),'face_lab/templates'),
       (str(root/'face_lab/static'),'face_lab/static'),
       (str(root/'face_lab/resources'),'face_lab/resources'),
       (str(root/'LICENSE'),'licenses'),(str(root/'THIRD_PARTY_NOTICES.md'),'licenses')]
for entry in manifest['files']:
    source=root/'models'/entry['path']
    if not source.is_file():raise RuntimeError(f'Missing model: {source}')
    datas.append((str(source),str(Path('bundled_models')/Path(entry['path']).parent)))
datas+=collect_data_files('mediapipe')
datas+=copy_metadata('mediapipe')+copy_metadata('onnxruntime')
# Keep runtime dependency notices alongside the executable.
for dist in importlib.metadata.distributions():
    for file in dist.files or []:
        name=str(file).lower()
        if '.dist-info/' in name and ('license' in name or 'copying' in name or 'notice' in name):
            source=dist.locate_file(file)
            if source.is_file():datas.append((str(source),'licenses/runtime/'+dist.metadata['Name']))
binaries=collect_dynamic_libs('mediapipe')+collect_dynamic_libs('onnxruntime')
# MediaPipe's Linux shared library links EGL/GLES even in CPU mode.
# PyInstaller normally excludes these system graphics libraries; bundle them explicitly.
import sys
if sys.platform.startswith('linux'):
    for name in ['libEGL.so.1','libGLESv2.so.2','libGLdispatch.so.0']:
        candidates=[Path('/lib/x86_64-linux-gnu')/name,Path('/usr/lib/x86_64-linux-gnu')/name]
        source=next((p for p in candidates if p.exists()),None)
        if source is None:raise RuntimeError(f'Missing build-host library: {name}')
        binaries.append((str(source),'.'))
    notice=Path('/usr/share/doc/libglvnd0/copyright')
    if notice.exists():datas.append((str(notice),'licenses/runtime/libglvnd'))
a=Analysis([str(root/'packaging/portable_entry.py')],pathex=[str(root)],
    binaries=binaries,datas=datas,hiddenimports=['mediapipe.tasks.c'],
    hookspath=[],runtime_hooks=[],excludes=['playwright','pytest','torch','tensorflow','IPython','notebook','tkinter','PyQt5','PyQt6','PySide6'],noarchive=False)
pyz=PYZ(a.pure)
exe=EXE(pyz,a.scripts,[],exclude_binaries=True,name='LocalFaceLab',debug=False,
    bootloader_ignore_signals=False,strip=False,upx=False,console=True)
coll=COLLECT(exe,a.binaries,a.datas,strip=False,upx=False,name='LocalFaceLab')
