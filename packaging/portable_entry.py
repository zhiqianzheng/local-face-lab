"""Frozen entrypoint; dependencies and models are embedded by PyInstaller."""
import os
from pathlib import Path
import sys
import traceback

# Do not inherit a developer's external Python installation settings.
os.environ.pop('PYTHONHOME',None)
os.environ.pop('PYTHONPATH',None)

try:
    from face_lab.cli import main
    raise SystemExit(main())
except Exception:
    root=Path(os.environ.get('LOCALAPPDATA',Path.home()/'.local'/'share'))/'local-face-lab'
    root.mkdir(parents=True,exist_ok=True)
    log=root/'startup-error.log'
    log.write_text(traceback.format_exc(),encoding='utf-8')
    print(f'启动失败。详细日志：{log}',file=sys.stderr)
    if os.name=='nt':
        import ctypes
        ctypes.windll.user32.MessageBoxW(None,f'软件启动失败，日志保存在：\n{log}','Local Face Lab',0x10)
    raise SystemExit(1)
