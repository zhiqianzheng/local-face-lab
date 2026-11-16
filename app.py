"""Compatibility launcher. Prefer: python -m face_lab."""
from face_lab.cli import main
if __name__ == '__main__':
    raise SystemExit(main())
