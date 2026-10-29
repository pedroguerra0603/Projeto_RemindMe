"""Atalho para rodar o RemindMe sem instalar nada: `python executar.py [servir|criar-admin|demo]`."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from remindme.apresentacao.cli import main  # noqa: E402

if __name__ == "__main__":
    sys.exit(main())
