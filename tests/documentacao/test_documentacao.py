"""Verificação automática da documentação (OPEN-66).

Confere os links relativos dos `.md` (arquivo e seção) e se todo identificador citado nos `.md`, em `src/` e em
`tests/` (RF, RNF, RB, UC, OPEN, ADR, DA, DT e spec) existe na baseline. A falha lista `arquivo:linha → problema`,
para a correção ser direta. Roda sem rede e sem dependência, como o resto da suíte (RNF-23).
"""

import os
import re
import unittest
from pathlib import Path
from typing import Dict, Iterator, List, Set, Tuple

RAIZ = Path(__file__).resolve().parents[2]

# Pastas ocultas que fazem parte da documentação; as demais (.git, .claude…) ficam de fora.
OCULTAS_LIDAS = {".specify", ".github"}
IGNORADAS = {"__pycache__", "node_modules"}

_CERCA = re.compile(r"^\s*(```|~~~)")
_CODIGO_EM_LINHA = re.compile(r"`[^`]*`")
_LINK = re.compile(r"!?\[[^\]]*\]\(([^)\s]+)(?:\s+\"[^\"]*\")?\)")
_TITULO = re.compile(r"^(#{1,6})\s+(.*?)\s*#*\s*$")

# Identificador citado: `RB-02` no texto, `RB_02` em nomes de teste e funções.
_IDENTIFICADOR = re.compile(r"(?<![A-Za-z0-9])(RNF|RF|RB|UC|OPEN|ADR|DA|DT)[-_](\d+)(?!\d)")
_SPECS = re.compile(r"(?<![A-Za-z])[Ss]pecs?\s+(\d{3}(?:(?:\s*,\s*|\s+e\s+|\s+a\s+)\d{3})*)(?!\d)")

# Citações de identificadores que não existem, de propósito. Cada uma com o motivo.
EXCECOES = {
    ("RB", 25): "RB-25 nunca foi usado; requisitos.md e documentacao-final.md citam-no para dizer isso.",
}


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


def _ids(texto: str, padrao: str) -> Set[Tuple[str, int]]:
    return {(prefixo, int(numero)) for prefixo, numero in re.findall(padrao, texto, re.M)}


def baseline() -> Dict[str, Set]:
    """Onde cada identificador é definido. Os requisitos retirados continuam nas tabelas, marcados, e contam."""
    requisitos = (RAIZ / "docs" / "requisitos.md").read_text(encoding="utf-8")
    abertas = (RAIZ / ".specify" / "open.md").read_text(encoding="utf-8")
    arquitetura = (RAIZ / "docs" / "arquitetura.md").read_text(encoding="utf-8")
    mapa = (RAIZ / ".specify" / "specs" / "mapa-de-specs.md").read_text(encoding="utf-8")
    nomes = [p.name for p in (RAIZ / "docs" / "casos-de-uso").glob("UC-*.md")] + [
        p.name for p in (RAIZ / "docs" / "adr").glob("ADR-*.md")
    ]
    identificadores = (
        _ids(requisitos, r"^\| (RNF|RF|RB)-(\d+) \|")
        | _ids(abertas, r"^\| (OPEN)-(\d+) \|")
        | _ids(arquitetura, r"\b(DA|DT)-(\d+)\b")
        | _ids("\n".join(nomes), r"^(UC|ADR)-(\d+)")
    )
    specs = {int(n) for n in re.findall(r"^\| \[?(\d{3})\]?", mapa, re.M)}
    return {"identificadores": identificadores, "specs": specs}


def citacoes(caminho: Path) -> Iterator[Tuple[int, str, object, object]]:
    """(linha, texto citado, chave, tipo) de cada identificador e spec citados no arquivo."""
    for numero, linha in enumerate(caminho.read_text(encoding="utf-8").splitlines(), 1):
        for prefixo, valor in _IDENTIFICADOR.findall(linha):
            yield numero, f"{prefixo}-{valor}", (prefixo, int(valor)), "identificadores"
        for lista in _SPECS.findall(linha):
            for valor in re.findall(r"\d{3}", lista):
                yield numero, f"Spec {valor}", int(valor), "specs"


def problemas_de_identificadores(caminhos: List[Path]) -> Tuple[List[str], int]:
    definidos = baseline()
    problemas, total = [], 0
    for caminho in caminhos:
        for numero, texto, chave, tipo in citacoes(caminho):
            total += 1
            if chave not in definidos[tipo] and chave not in EXCECOES:
                problemas.append(f"{relativo(caminho)}:{numero} → {texto} não existe na baseline")
    return problemas, total


class Links(unittest.TestCase):
    def test_OPEN_66_links_relativos_dos_md_apontam_para_arquivos_e_secoes_que_existem(self):
        problemas = problemas_de_links()
        if problemas:
            self.fail(f"{len(problemas)} link(s) quebrado(s):\n" + "\n".join(problemas))

    def test_OPEN_66_ancora_segue_a_regra_do_github(self):
        self.assertEqual(ancora("2. Drivers → decisões → implementação"), "2-drivers--decisões--implementação")
        self.assertEqual(ancora("Onde ficam as `tarefas`"), "onde-ficam-as-tarefas")
        self.assertEqual(ancora("Ver [visão](visao.md)"), "ver-visão")



class Identificadores(unittest.TestCase):
    def verificar(self, caminhos: List[Path], minimo: int):
        problemas, total = problemas_de_identificadores(caminhos)
        self.assertGreaterEqual(total, minimo, "a busca não encontrou as citações esperadas")
        if problemas:
            self.fail(f"{len(problemas)} identificador(es) inexistente(s):\n" + "\n".join(problemas))

    def test_OPEN_66_identificadores_citados_nos_md_existem_na_baseline(self):
        self.verificar(arquivos(".md"), 1000)

    def test_OPEN_66_identificadores_citados_no_codigo_e_nos_testes_existem_na_baseline(self):
        self.verificar(arquivos(".py", "src", "tests"), 500)

    def test_OPEN_66_a_baseline_tem_todos_os_tipos_de_identificador(self):
        definidos = baseline()
        prefixos = {prefixo for prefixo, _ in definidos["identificadores"]}
        self.assertEqual(prefixos, {"RF", "RNF", "RB", "UC", "OPEN", "ADR", "DA", "DT"})
        self.assertIn(17, definidos["specs"])

    def test_OPEN_66_reconhece_as_formas_de_citar(self):
        self.assertEqual(
            [m.group(0) for m in _IDENTIFICADOR.finditer("RB-02, test_RB_15_x, ADR_001, RF-nn, XRF-1, RF-096")],
            ["RB-02", "RB_15", "ADR_001", "RF-096"],
        )
        self.assertEqual(_SPECS.findall("Specs 005, 008 e 009; spec 017; Specs 004 a 006"), ["005, 008 e 009", "017", "004 a 006"])


if __name__ == "__main__":
    unittest.main()
