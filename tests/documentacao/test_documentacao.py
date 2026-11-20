"""Verificação automática da documentação (OPEN-66).

Confere os links relativos dos `.md` (arquivo e seção). A falha lista `arquivo:linha → problema`, para a correção
ser direta. Roda sem rede e sem dependência, como o resto da suíte (RNF-23).
"""

import os
import re
import unittest
from pathlib import Path
from typing import Iterator, List, Set, Tuple

RAIZ = Path(__file__).resolve().parents[2]

# Pastas ocultas que fazem parte da documentação; as demais (.git, .claude…) ficam de fora.
OCULTAS_LIDAS = {".specify", ".github"}
IGNORADAS = {"__pycache__", "node_modules"}

_CERCA = re.compile(r"^\s*(```|~~~)")
_CODIGO_EM_LINHA = re.compile(r"`[^`]*`")
_LINK = re.compile(r"!?\[[^\]]*\]\(([^)\s]+)(?:\s+\"[^\"]*\")?\)")
_TITULO = re.compile(r"^(#{1,6})\s+(.*?)\s*#*\s*$")


def arquivos(sufixo: str, *pastas: str) -> List[Path]:
    """Arquivos com o sufixo, em ordem estável, sem pastas ocultas (exceto as lidas) nem caches."""
    encontrados = []
    for pasta in pastas or (".",):
        for raiz, dirs, nomes in os.walk(RAIZ / pasta):
            dirs[:] = sorted(d for d in dirs if d not in IGNORADAS and (not d.startswith(".") or d in OCULTAS_LIDAS))
            encontrados.extend(Path(raiz) / n for n in sorted(nomes) if n.endswith(sufixo))
    return encontrados


def linhas_de_texto(caminho: Path) -> Iterator[Tuple[int, str]]:
    """Linhas de um `.md` fora de blocos de código, com o código em linha apagado."""
    dentro = False
    for numero, linha in enumerate(caminho.read_text(encoding="utf-8").splitlines(), 1):
        if _CERCA.match(linha):
            dentro = not dentro
            continue
        if not dentro:
            yield numero, _CODIGO_EM_LINHA.sub("", linha)


def ancora(titulo: str) -> str:
    """A âncora que o GitHub gera para um título: texto sem formatação, minúsculas, sem pontuação, espaço vira hífen."""
    texto = re.sub(r"!?\[([^\]]*)\]\([^)]*\)", r"\1", titulo)
    texto = texto.replace("`", "").replace("*", "").strip().lower()
    texto = re.sub(r"[^\w\- ]", "", texto)
    return texto.replace(" ", "-")


def ancoras(caminho: Path) -> Set[str]:
    vistas, resultado = {}, set()
    dentro = False
    for linha in caminho.read_text(encoding="utf-8").splitlines():
        if _CERCA.match(linha):
            dentro = not dentro
            continue
        casamento = None if dentro else _TITULO.match(linha)
        if casamento:
            base = ancora(casamento.group(2))
            n = vistas.get(base, 0)
            vistas[base] = n + 1
            resultado.add(base if n == 0 else f"{base}-{n}")
    return resultado


def relativo(caminho: Path) -> str:
    return caminho.relative_to(RAIZ).as_posix()


def problemas_de_links() -> List[str]:
    problemas, cache = [], {}
    for md in arquivos(".md"):
        for numero, linha in linhas_de_texto(md):
            for alvo in _LINK.findall(linha):
                if re.match(r"^[a-zA-Z][a-zA-Z0-9+.-]*:", alvo) or alvo.startswith("<"):
                    continue  # http:, https:, mailto: e afins não são relativos
                caminho, _, secao = alvo.partition("#")
                destino = (md.parent / caminho).resolve() if caminho else md
                onde = f"{relativo(md)}:{numero}"
                if not destino.exists():
                    problemas.append(f"{onde} → arquivo não existe: {alvo}")
                elif secao and destino.suffix == ".md":
                    if destino not in cache:
                        cache[destino] = ancoras(destino)
                    if secao.lower() not in cache[destino]:
                        problemas.append(f"{onde} → seção não existe: {alvo}")
    return problemas


class Links(unittest.TestCase):
    def test_OPEN_66_links_relativos_dos_md_apontam_para_arquivos_e_secoes_que_existem(self):
        problemas = problemas_de_links()
        if problemas:
            self.fail(f"{len(problemas)} link(s) quebrado(s):\n" + "\n".join(problemas))

    def test_OPEN_66_ancora_segue_a_regra_do_github(self):
        self.assertEqual(ancora("2. Drivers → decisões → implementação"), "2-drivers--decisões--implementação")
        self.assertEqual(ancora("Onde ficam as `tarefas`"), "onde-ficam-as-tarefas")
        self.assertEqual(ancora("Ver [visão](visao.md)"), "ver-visão")


if __name__ == "__main__":
    unittest.main()
