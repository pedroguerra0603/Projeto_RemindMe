"""Eficiência: as operações interativas da Spec 006 respondem dentro do limite de RNF-11.

As métricas completas, com mais volumes, saem de `python3 -m tests.desempenho.medir_eficiencia`
e estão em docs/qualidade/eficiencia.md.
"""

import time
import unittest
from decimal import Decimal

from remindme.aplicacao.servico_titulos import FiltroTitulos
from tests.desempenho.medir_eficiencia import DONO, HOJE, OPERADOR, montar

LIMITE_RNF_11 = 2.0  # segundos, para 95% das operações de consulta e cadastro
VOLUME = 300
REPETICOES = 20


def p95(operacao):
    tempos = []
    for n in range(REPETICOES):
        inicio = time.perf_counter()
        operacao(n)
        tempos.append(time.perf_counter() - inicio)
    tempos.sort()
    return tempos[int(0.95 * (len(tempos) - 1))]


class Eficiencia(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.servico, cls.ids = montar(VOLUME)

    def test_RNF_11_cadastro_responde_em_menos_de_2_segundos(self):
        tempo = p95(lambda n: self.servico.cadastrar_titulo(OPERADOR, "c1", Decimal("10.00"), HOJE))
        self.assertLess(tempo, LIMITE_RNF_11)

    def test_RNF_11_consulta_responde_em_menos_de_2_segundos(self):
        tempo = p95(lambda n: self.servico.consultar_titulos(FiltroTitulos(cliente_id="c1"), HOJE, 5))
        self.assertLess(tempo, LIMITE_RNF_11)

    def test_RNF_11_pagamento_e_cancelamento_respondem_em_menos_de_2_segundos(self):
        pagamento = p95(
            lambda n: self.servico.registrar_pagamento(OPERADOR, self.ids[n], Decimal("1.00"), HOJE)
        )
        cancelamento = p95(lambda n: self.servico.cancelar_titulo(DONO, self.ids[-1 - n], "medição"))
        self.assertLess(pagamento, LIMITE_RNF_11)
        self.assertLess(cancelamento, LIMITE_RNF_11)


if __name__ == "__main__":
    unittest.main()
