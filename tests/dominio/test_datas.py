"""Datas, vencimentos e fuso horário. Issue #77.

Regras de domínio; a camada de aplicação está em tests/aplicacao/test_datas_na_aplicacao.py.
Vencimento, atraso e proximidade do vencimento dependem de "hoje". Um erro de borda de dia ou de fuso muda o
estado dos títulos. A data de referência é sempre recebida de fora (parâmetro ou Relogio), nunca lida do
relógio da máquina. Catálogo em docs/qualidade/datas-e-fuso.md.
"""

import ast
import os
import pathlib
import time
import unittest
from datetime import date, timedelta
from decimal import Decimal

from remindme.dominio.titulo import EstadoTitulo, Titulo

HOJE = date(2026, 10, 3)
RAIZ_DO_CODIGO = pathlib.Path(__file__).resolve().parents[2] / "src" / "remindme"


def titulo(vencimento):
    return Titulo.cadastrar_manual("t1", "c1", Decimal("100.00"), vencimento)


class DataDeReferenciaInjetavel(unittest.TestCase):
    def test_RF_24_codigo_de_producao_nao_le_o_relogio_da_maquina(self):
        """Exceção única: `infraestrutura/relogio.py`, a implementação da porta `Relogio` usada em produção."""
        achados = []
        for caminho in sorted(RAIZ_DO_CODIGO.rglob("*.py")):
            if caminho == RAIZ_DO_CODIGO / "infraestrutura" / "relogio.py":
                continue
            for no in ast.walk(ast.parse(caminho.read_text(encoding="utf-8"))):
                if isinstance(no, ast.Attribute) and no.attr in ("today", "now", "utcnow", "fromtimestamp"):
                    achados.append(f"{caminho.name}:{no.lineno} {no.attr}")
        self.assertEqual(achados, [])

    def test_RF_24_o_resultado_nao_depende_da_data_da_maquina(self):
        for referencia in (date(2000, 1, 1), HOJE, date(2999, 12, 31)):
            with self.subTest(referencia=referencia):
                t = titulo(referencia - timedelta(days=1))
                self.assertTrue(t.marcar_vencido(referencia))


class VencimentoNaBordaDoDia(unittest.TestCase):
    def test_RF_24_titulo_que_vence_hoje_ainda_nao_esta_vencido(self):
        t = titulo(HOJE)
        self.assertFalse(t.marcar_vencido(HOJE))
        self.assertIs(t.estado, EstadoTitulo.ABERTO)

    def test_RF_24_titulo_que_venceu_ontem_passa_a_vencido(self):
        t = titulo(HOJE - timedelta(days=1))
        self.assertTrue(t.marcar_vencido(HOJE))
        self.assertIs(t.estado, EstadoTitulo.VENCIDO)

    def test_RF_24_titulo_que_vence_amanha_continua_aberto(self):
        t = titulo(HOJE + timedelta(days=1))
        self.assertFalse(t.marcar_vencido(HOJE))
        self.assertIs(t.estado, EstadoTitulo.ABERTO)

    def test_RF_24_o_dia_seguinte_ao_vencimento_vence_o_titulo(self):
        t = titulo(HOJE)
        self.assertFalse(t.marcar_vencido(HOJE))
        self.assertTrue(t.marcar_vencido(HOJE + timedelta(days=1)))

    def test_RF_24_verificar_duas_vezes_no_mesmo_dia_muda_o_estado_uma_vez(self):
        t = titulo(HOJE - timedelta(days=1))
        self.assertEqual([t.marcar_vencido(HOJE), t.marcar_vencido(HOJE)], [True, False])

    def test_RF_24_virada_de_mes_ano_e_bissexto(self):
        for vencimento, referencia in (
            (date(2026, 10, 31), date(2026, 11, 1)),
            (date(2026, 12, 31), date(2027, 1, 1)),
            (date(2028, 2, 29), date(2028, 3, 1)),
            (date(2027, 2, 28), date(2027, 3, 1)),
        ):
            with self.subTest(vencimento=vencimento):
                t = titulo(vencimento)
                self.assertFalse(t.marcar_vencido(vencimento))
                self.assertTrue(t.marcar_vencido(referencia))

    def test_RF_23_proximidade_do_vencimento_inclui_hoje_e_o_ultimo_dia_da_antecedencia(self):
        t = titulo(HOJE + timedelta(days=5))
        self.assertTrue(t.proximo_do_vencimento(HOJE, 5))
        self.assertFalse(t.proximo_do_vencimento(HOJE, 4))
        self.assertTrue(titulo(HOJE).proximo_do_vencimento(HOJE, 5))
        self.assertFalse(titulo(HOJE - timedelta(days=1)).proximo_do_vencimento(HOJE, 5))

    def test_RF_30_estorno_no_dia_do_vencimento_volta_a_aberto_e_no_dia_seguinte_a_vencido(self):
        for referencia, esperado in (
            (HOJE, EstadoTitulo.ABERTO),
            (HOJE + timedelta(days=1), EstadoTitulo.VENCIDO),
        ):
            with self.subTest(referencia=referencia):
                t = titulo(HOJE)
                t.registrar_pagamento("p1", Decimal("100.00"), HOJE)
                t.estornar_pagamento("p1", "motivo", referencia)
                self.assertIs(t.estado, esperado)


class FusoHorarioDaMaquina(unittest.TestCase):
    """O resultado não muda quando o fuso da máquina muda (Rock in Rio 2019: servidores em fusos diferentes)."""

    @unittest.skipUnless(hasattr(time, "tzset"), "time.tzset não existe neste sistema operacional")
    def test_RF_24_vencimento_e_o_mesmo_em_fusos_extremos(self):
        anterior = os.environ.get("TZ")
        resultados = {}
        try:
            for fuso in ("Pacific/Kiritimati", "UTC", "Pacific/Pago_Pago", "America/Sao_Paulo"):
                os.environ["TZ"] = fuso
                time.tzset()
                t = titulo(HOJE)
                resultados[fuso] = (t.marcar_vencido(HOJE), t.marcar_vencido(HOJE + timedelta(days=1)))
        finally:
            if anterior is None:
                os.environ.pop("TZ", None)
            else:
                os.environ["TZ"] = anterior
            time.tzset()
        self.assertEqual(set(resultados.values()), {(False, True)})


class DataDePagamento(unittest.TestCase):
    """OPEN-17 está aberta: a baseline não diz se a data do pagamento pode ser passada ou futura."""

    def test_OPEN_17_provisorio_pagamento_com_data_futura_e_aceito_hoje(self):
        """Caracteriza o comportamento atual, sem decidi-lo. Se a equipe decidir recusar data futura (sugestão
        de OPEN-17), este teste muda para exigir a recusa, no mesmo PR da decisão."""
        t = titulo(HOJE)
        pagamento = t.registrar_pagamento("p1", Decimal("40.00"), HOJE + timedelta(days=365))
        self.assertEqual(pagamento.data, HOJE + timedelta(days=365))
        self.assertEqual(t.saldo, Decimal("60.00"))

    def test_OPEN_17_provisorio_pagamento_com_data_passada_e_aceito(self):
        t = titulo(HOJE)
        t.registrar_pagamento("p1", Decimal("40.00"), HOJE - timedelta(days=400))
        self.assertEqual(t.saldo, Decimal("60.00"))

    def test_OPEN_17_a_data_do_pagamento_nao_define_o_estado_do_titulo(self):
        """Pagamento parcial datado de depois do vencimento não vence o título: o estado vem de RF-24."""
        t = titulo(HOJE)
        t.registrar_pagamento("p1", Decimal("40.00"), HOJE + timedelta(days=30))
        self.assertIs(t.estado, EstadoTitulo.ABERTO)


if __name__ == "__main__":
    unittest.main()
