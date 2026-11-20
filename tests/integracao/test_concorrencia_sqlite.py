"""Concorrência real no SQLite (RNF-09, ADR-007, DA-03).

Cada operação é uma transação `BEGIN IMMEDIATE`, que serializa as escritas: dois pagamentos simultâneos sobre o
mesmo título não estouram o saldo. A unidade de trabalho em memória não é segura para threads, por isso este caso
usa o banco de verdade. Catálogo em docs/qualidade/concorrencia-e-idempotencia.md.
"""

import tempfile
import threading
import unittest
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path

from remindme.dominio.erros import OperacaoRecusada
from remindme.dominio.usuario import Perfil
from remindme.infraestrutura.memoria import RegistroErrosEmMemoria, RelogioFixo
from remindme.inicializacao import montar
from tests.apoio import CIFRADOR_DE_TESTE

HOJE = date(2026, 10, 3)


class ConcorrenciaNoBanco(unittest.TestCase):
    """RNF-09: duas transações ao mesmo tempo sobre o mesmo título, repetidas para aumentar a chance de sobreposição."""

    RODADAS = 10

    def test_RNF_09_duas_transacoes_simultaneas_no_mesmo_titulo_nao_estouram_o_saldo(self):
        with tempfile.TemporaryDirectory() as pasta:
            relogio = RelogioFixo(datetime(2026, 10, 3, 15, 0, tzinfo=timezone.utc))
            sistema = montar(str(Path(pasta, "remindme.db")), relogio, CIFRADOR_DE_TESTE, RegistroErrosEmMemoria())
            acesso, titulos = sistema.servicos.acesso, sistema.servicos.titulos
            acesso.criar_primeiro_administrador("Ana Admin", "admin@exemplo.com", "senha-de-teste")
            admin = acesso.entrar("admin@exemplo.com", "senha-de-teste").identificador
            acesso.cadastrar_usuario(admin, "Diego Ramos", "diego@exemplo.com", Perfil.OPERADOR_FINANCEIRO, "senha-de-teste")
            operador = acesso.entrar("diego@exemplo.com", "senha-de-teste").identificador
            cliente = sistema.servicos.clientes.cadastrar_cliente(operador, "Padaria Ltda", "11.222.333/0001-81", "p@padaria.com")
            for rodada in range(self.RODADAS):
                with self.subTest(rodada=rodada):
                    titulo = titulos.cadastrar_titulo(operador, cliente.id, Decimal("100.00"), HOJE + timedelta(days=10))
                    largada = threading.Barrier(2)
                    resultados = []

                    def pagar():
                        largada.wait()
                        try:
                            titulos.registrar_pagamento(operador, titulo.id, Decimal("60.00"), HOJE)
                            resultados.append("aceito")
                        except OperacaoRecusada:
                            resultados.append("recusado")

                    corredores = [threading.Thread(target=pagar) for _ in range(2)]
                    for corredor in corredores:
                        corredor.start()
                    for corredor in corredores:
                        corredor.join(timeout=30)
                    self.assertEqual(sorted(resultados), ["aceito", "recusado"])
                    salvo = titulos.obter_titulo(operador, titulo.id)
                    self.assertEqual(salvo.saldo, Decimal("40.00"))
                    self.assertEqual(len(salvo.pagamentos), 1)


if __name__ == "__main__":
    unittest.main()
