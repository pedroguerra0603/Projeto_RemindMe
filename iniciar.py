"""Atalho para iniciar o RemindMe a partir da raiz do repositório, sem instalar nada.

    python3 iniciar.py demonstracao     # dados de demonstração e servidor em http://localhost:8000
    python3 iniciar.py --help           # todos os comandos
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.joinpath("src")))

from remindme.inicializacao import principal  # noqa: E402

sys.exit(principal())
