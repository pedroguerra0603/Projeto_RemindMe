"""Métricas de desempenho das operações da Spec 006 (RNF-11). Resultados em docs/qualidade/eficiencia.md.

Na raiz do repositório:

    python3 -m tests.desempenho.medir_eficiencia
"""

import statistics
import time
import tracemalloc
from datetime import date, datetime, timedelta
from decimal import Decimal

import tests  # noqa: F401  (inclui src/ no caminho de importação)
from remindme.aplicacao.servico_titulos import FiltroTitulos, ServicoTitulos
from remindme.dominio.usuario import Perfil, Usuario
from remindme.infraestrutura.memoria import (
    AuditoriaEmMemoria,
    ClientesEmMemoria,
    RelogioFixo,
    RepositorioTitulosEmMemoria,
    UnidadeDeTrabalhoEmMemoria,
)

HOJE = date(2026, 10, 3)
DONO = Usuario("dono", "Dono", Perfil.DONO)
OPERADOR = Usuario("operador", "Operador", Perfil.OPERADOR_FINANCEIRO)
VOLUMES = (100, 500, 2000)
REPETICOES = 20


def montar(volume):
    """Serviço com `volume` títulos de 50 clientes; metade vence ontem."""
    servico = ServicoTitulos(
        UnidadeDeTrabalhoEmMemoria(RepositorioTitulosEmMemoria(), AuditoriaEmMemoria()),
        ClientesEmMemoria({f"c{i}" for i in range(50)}),
        RelogioFixo(datetime(2026, 10, 3, 10, 0)),
    )
    ids = []
    for i in range(volume):
        vencimento = HOJE - timedelta(days=1) if i % 2 else HOJE + timedelta(days=i % 60)
        ids.append(servico.cadastrar_titulo(OPERADOR, f"c{i % 50}", Decimal("1000.00"), vencimento).id)
    return servico, ids


def operacoes(servico, ids):
    """Cada operação recebe o número da repetição e escolhe um título diferente."""
    pagamentos = {}

    def registrar(n):
        pagamentos[n] = servico.registrar_pagamento(OPERADOR, ids[n], Decimal("1.00"), HOJE).pagamentos[0].id

    return {
        "cadastrar título": lambda n: servico.cadastrar_titulo(OPERADOR, "c1", Decimal("10.00"), HOJE),
        "registrar pagamento": registrar,
        "estornar pagamento": lambda n: servico.estornar_pagamento(DONO, ids[n], pagamentos[n], "medição", HOJE),
        "cancelar título": lambda n: servico.cancelar_titulo(DONO, ids[-1 - n], "medição"),
        "consultar com filtro": lambda n: servico.consultar_titulos(FiltroTitulos(cliente_id="c1"), HOJE, 5),
        "verificar vencimentos (lote)": lambda n: servico.verificar_vencimentos(OPERADOR, HOJE),
    }


def medir(volume):
    servico, ids = montar(volume)
    resultado = {}
    for nome, operacao in operacoes(servico, ids).items():
        tempos = []
        for n in range(REPETICOES):
            inicio = time.perf_counter()
            operacao(n)
            tempos.append((time.perf_counter() - inicio) * 1000)
        tempos.sort()
        resultado[nome] = (statistics.median(tempos), tempos[int(0.95 * (len(tempos) - 1))])
    return resultado


def memoria(volume):
    tracemalloc.start()
    servico, ids = montar(volume)
    em_uso, _ = tracemalloc.get_traced_memory()
    tracemalloc.reset_peak()
    servico.registrar_pagamento(OPERADOR, ids[0], Decimal("1.00"), HOJE)
    _, pico = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    return em_uso / 1024 / 1024, (pico - em_uso) / 1024 / 1024


def main():
    tabela = {v: medir(v) for v in VOLUMES}
    print("| Operação | " + " | ".join(f"{v} títulos: P50 / P95 (ms)" for v in VOLUMES) + " |")
    print("|---|" + "---|" * len(VOLUMES))
    for nome in tabela[VOLUMES[0]]:
        celulas = " | ".join(f"{tabela[v][nome][0]:.2f} / {tabela[v][nome][1]:.2f}" for v in VOLUMES)
        print(f"| {nome} | {celulas} |")
    print()
    print("| Títulos | Memória do repositório (MiB) | Memória adicional de um pagamento (MiB) |")
    print("|---|---|---|")
    for v in VOLUMES:
        em_uso, adicional = memoria(v)
        print(f"| {v} | {em_uso:.1f} | {adicional:.1f} |")


if __name__ == "__main__":
    main()
