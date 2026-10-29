"""Acurácia dos valores monetários (ISO/IEC 25010, Funcionalidade). Issue #78.

Saldo, soma de pagamentos e estorno não podem perder centavos por arredondamento ou ponto flutuante
(RF-25, RF-26, RB-22, RB-23). Casos de desconto (RB-15) e de apuração do resultado (UC-11) dependem
das Specs 004 e 012 e estão pendentes. Catálogo em docs/qualidade/acuracia-monetaria.md.
"""

import ast
import pathlib
import unittest
from datetime import date, timedelta
from decimal import Decimal

from remindme.dominio.erros import OperacaoRecusada
from remindme.dominio.titulo import EstadoTitulo, Titulo

HOJE = date(2026, 10, 3)
FUTURO = HOJE + timedelta(days=30)
RAIZ_DO_CODIGO = pathlib.Path(__file__).resolve().parents[2] / "src" / "remindme"


def titulo(valor):
    return Titulo.cadastrar_manual("t1", "c1", Decimal(valor), FUTURO)


class SemPontoFlutuante(unittest.TestCase):
    """Revisão automatizada do código da Spec 006: nenhum valor monetário usa `float`."""

    def arvores(self):
        for caminho in sorted(RAIZ_DO_CODIGO.rglob("*.py")):
            yield caminho, ast.parse(caminho.read_text(encoding="utf-8"))

    @staticmethod
    def linhas_de_exit(arvore):
        return {
            arg.lineno
            for no in ast.walk(arvore)
            if isinstance(no, (ast.FunctionDef, ast.AsyncFunctionDef)) and no.name == "__exit__"
            for arg in no.args.args
        }

    def test_RF_25_codigo_de_producao_nao_usa_float(self):
        achados = []
        for caminho, arvore in self.arvores():
            for no in ast.walk(arvore):
                if isinstance(no, ast.Constant) and isinstance(no.value, float):
                    achados.append(f"{caminho.name}:{no.lineno} literal float")
                if isinstance(no, ast.Name) and no.id == "float":
                    achados.append(f"{caminho.name}:{no.lineno} uso de float")
                if isinstance(no, ast.Div):
                    achados.append(f"{caminho.name}:{no.lineno} divisão com /")
        self.assertEqual(achados, [])

    def test_RF_25_valor_monetario_e_anotado_como_decimal(self):
        """Todo campo ou parâmetro chamado `valor` ou `saldo` declara `Decimal`. (O `valor` de
        `__exit__` é a exceção em curso, e não dinheiro.)"""
        sem_decimal = []
        for caminho, arvore in self.arvores():
            for no in ast.walk(arvore):
                if isinstance(no, ast.arg) and no.arg in ("valor", "saldo") and no.annotation is None and \
                        no.lineno in self.linhas_de_exit(arvore):
                    continue
                if isinstance(no, ast.arg) and no.arg in ("valor", "saldo"):
                    if no.annotation is None or "Decimal" not in ast.unparse(no.annotation):
                        sem_decimal.append(f"{caminho.name}:{no.lineno} parâmetro {no.arg}")
                if isinstance(no, ast.AnnAssign) and isinstance(no.target, ast.Name):
                    if no.target.id in ("valor", "saldo") and "Decimal" not in ast.unparse(no.annotation):
                        sem_decimal.append(f"{caminho.name}:{no.lineno} campo {no.target.id}")
        self.assertEqual(sem_decimal, [])

    def test_RF_25_float_nao_entra_pelas_portas_do_dominio(self):
        for valor in (100.0, 0.1, 33.33):
            with self.subTest(valor=valor):
                with self.assertRaises(OperacaoRecusada):
                    Titulo.cadastrar_manual("t1", "c1", valor, FUTURO)
                t = titulo("100.00")
                with self.assertRaises(OperacaoRecusada):
                    t.registrar_pagamento("p1", valor, HOJE)
                self.assertEqual(t.pagamentos, [])


class PagamentosFracionados(unittest.TestCase):
    def test_RB_23_tres_pagamentos_de_33_33_sobre_100_00_deixam_saldo_de_um_centavo(self):
        t = titulo("100.00")
        for n in range(1, 4):
            t.registrar_pagamento(f"p{n}", Decimal("33.33"), HOJE)
        self.assertEqual(t.saldo, Decimal("0.01"))
        self.assertIs(t.estado, EstadoTitulo.ABERTO)

    def test_RB_22_o_centavo_restante_baixa_o_titulo_exatamente(self):
        t = titulo("100.00")
        for n in range(1, 4):
            t.registrar_pagamento(f"p{n}", Decimal("33.33"), HOJE)
        t.registrar_pagamento("p4", Decimal("0.01"), HOJE)
        self.assertEqual(t.saldo, Decimal("0.00"))
        self.assertIs(t.estado, EstadoTitulo.BAIXADO)

    def test_RB_23_o_saldo_de_um_centavo_recusa_dois_centavos(self):
        t = titulo("100.00")
        for n in range(1, 4):
            t.registrar_pagamento(f"p{n}", Decimal("33.33"), HOJE)
        with self.assertRaises(OperacaoRecusada):
            t.registrar_pagamento("p4", Decimal("0.02"), HOJE)
        self.assertEqual(t.saldo, Decimal("0.01"))

    def test_RF_25_cem_pagamentos_de_um_centavo_somam_um_real_sem_erro_de_ponto_flutuante(self):
        """Com float, 100 × 0,01 não dá 1,00 exato; com Decimal, dá."""
        t = titulo("1.00")
        for n in range(100):
            t.registrar_pagamento(f"p{n}", Decimal("0.01"), HOJE)
        self.assertEqual(t.saldo, Decimal("0.00"))
        self.assertIs(t.estado, EstadoTitulo.BAIXADO)

    def test_RB_23_dez_pagamentos_de_0_10_sobre_1_00_baixam_o_titulo(self):
        """Caso clássico: 0,1 × 10 em float é 0,9999999999999999."""
        t = titulo("1.00")
        for n in range(10):
            t.registrar_pagamento(f"p{n}", Decimal("0.10"), HOJE)
        self.assertIs(t.estado, EstadoTitulo.BAIXADO)

    def test_RF_30_estorno_devolve_o_valor_exato_ao_saldo(self):
        t = titulo("100.00")
        for n in range(1, 4):
            t.registrar_pagamento(f"p{n}", Decimal("33.33"), HOJE)
        t.estornar_pagamento("p2", "valor lançado errado", HOJE)
        self.assertEqual(t.saldo, Decimal("33.34"))
        t.registrar_pagamento("p5", Decimal("33.34"), HOJE)
        self.assertIs(t.estado, EstadoTitulo.BAIXADO)

    def test_RF_25_ordem_dos_pagamentos_nao_muda_o_saldo(self):
        valores = [Decimal(v) for v in ("19.99", "0.01", "33.33", "7.77", "0.10")]
        saldos = set()
        for ordem in (valores, list(reversed(valores)), sorted(valores)):
            t = titulo("100.00")
            for n, valor in enumerate(ordem):
                t.registrar_pagamento(f"p{n}", valor, HOJE)
            saldos.add(t.saldo)
        self.assertEqual(saldos, {Decimal("38.80")})


class ValoresComMuitosDigitos(unittest.TestCase):
    """OPEN-24, decidida em 2026-10-23: no máximo 15 dígitos inteiros. Corrige o defeito D-06."""

    MAIOR = "9" * 15 + ".99"

    def test_OPEN_24_maior_valor_aceito_mantem_o_centavo(self):
        t = titulo(self.MAIOR)
        t.registrar_pagamento("p1", Decimal("0.01"), HOJE)
        self.assertEqual(t.saldo, Decimal("9" * 15 + ".98"))

    def test_OPEN_24_RB_22_maior_valor_aceito_e_baixado_pelo_pagamento_integral(self):
        t = titulo(self.MAIOR)
        t.registrar_pagamento("p1", Decimal("9" * 15 + ".98"), HOJE)
        self.assertEqual(t.saldo, Decimal("0.01"))
        t.registrar_pagamento("p2", Decimal("0.01"), HOJE)
        self.assertIs(t.estado, EstadoTitulo.BAIXADO)

    def test_OPEN_24_titulo_com_mais_de_15_digitos_inteiros_e_recusado(self):
        for valor in ("1" + "0" * 15, "9" * 20 + ".99", "1" + "0" * 30 + ".01"):
            with self.subTest(valor=valor):
                with self.assertRaisesRegex(OperacaoRecusada, "15 dígitos inteiros"):
                    titulo(valor)

    def test_OPEN_24_pagamento_com_mais_de_15_digitos_inteiros_e_recusado(self):
        t = titulo(self.MAIOR)
        with self.assertRaisesRegex(OperacaoRecusada, "15 dígitos inteiros"):
            t.registrar_pagamento("p1", Decimal("1" + "0" * 15), HOJE)
        self.assertEqual(t.saldo, t.valor)
        self.assertEqual(t.pagamentos, [])

    def test_D_06_corrigido_o_saldo_nasce_igual_ao_valor_em_todo_valor_aceito(self):
        t = titulo(self.MAIOR)
        self.assertEqual(t.saldo, t.valor)


class PendentesDeOutrasSpecs(unittest.TestCase):
    """Casos que dependem de specs ainda não aprovadas. Nenhum código é escrito antes (regra 1 do CLAUDE.md)."""

    @unittest.skip("Pendente da Spec 004: desconto percentual sobre o valor do orçamento (RB-15). "
                   "Casos: 10% de R$ 33,33; desconto igual à alçada; um centavo acima da alçada.")
    def test_RB_15_desconto_percentual_nao_perde_centavos(self):
        pass

    @unittest.skip("Pendente da Spec 012: apuração do resultado (RF-51, RF-55, UC-11). "
                   "Casos: soma de recebimentos e despesas ao centavo; estorno refletido sem resíduo.")
    def test_RF_51_apuracao_do_resultado_soma_ao_centavo(self):
        pass


if __name__ == "__main__":
    unittest.main()
