"""Regra de dependência entre camadas (ADR-001, regra 9 do CLAUDE.md) e uso só da biblioteca padrão (OPEN-01)."""

import ast
import sys
import unittest
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2] / "src" / "remindme"

# Camadas que cada camada pode importar.
PERMITIDAS = {
    "dominio": {"dominio"},
    "aplicacao": {"dominio", "aplicacao"},
    "infraestrutura": {"dominio", "aplicacao", "infraestrutura"},
}


def importacoes(arquivo):
    for no in ast.walk(ast.parse(arquivo.read_text(encoding="utf-8"))):
        if isinstance(no, ast.Import):
            yield from (nome.name for nome in no.names)
        elif isinstance(no, ast.ImportFrom) and no.level == 0:
            yield no.module


class Camadas(unittest.TestCase):
    def test_ADR_001_cada_camada_importa_somente_as_camadas_permitidas(self):
        for camada, permitidas in PERMITIDAS.items():
            for arquivo in (RAIZ / camada).rglob("*.py"):
                for modulo in importacoes(arquivo):
                    partes = modulo.split(".")
                    if partes[0] == "remindme":
                        with self.subTest(arquivo=arquivo.name, importa=modulo):
                            self.assertIn(partes[1], permitidas)

    def test_OPEN_01_codigo_usa_somente_a_biblioteca_padrao(self):
        for arquivo in RAIZ.rglob("*.py"):
            for modulo in importacoes(arquivo):
                raiz = modulo.split(".")[0]
                if raiz != "remindme":
                    with self.subTest(arquivo=arquivo.name, importa=modulo):
                        self.assertIn(raiz, sys.stdlib_module_names)

    def test_RNF_19_regras_do_titulo_ficam_somente_no_dominio(self):
        """As recusas de RB-21 e RB-23 só são levantadas em `dominio/titulo.py`."""
        for arquivo in RAIZ.rglob("*.py"):
            texto = arquivo.read_text(encoding="utf-8")
            if arquivo.name != "titulo.py":
                with self.subTest(arquivo=arquivo.name):
                    self.assertNotIn("(RB-21)", texto)
                    self.assertNotIn("(RB-23)", texto)


if __name__ == "__main__":
    unittest.main()
