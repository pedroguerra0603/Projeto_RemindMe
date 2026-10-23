"""Agendador: entrada automática separada da interface web, que chama os mesmos casos de uso (DT-07).

OPEN-13 e OPEN-48, decididas em 2026-10-23: tarefa periódica no próprio processo, na inicialização e a cada
hora. A verificação é idempotente: título já Vencido não muda de novo.
"""

import logging
import threading
from datetime import timedelta
from typing import List, Optional

from remindme.aplicacao.portas import Relogio
from remindme.aplicacao.servico_titulos import ServicoTitulos
from remindme.aplicacao.tempo import data_local

INTERVALO_PADRAO = timedelta(hours=1)


class AgendadorDeVencimentos:
    def __init__(self, titulos: ServicoTitulos, relogio: Relogio, intervalo: timedelta = INTERVALO_PADRAO):
        self._titulos = titulos
        self._relogio = relogio
        self._intervalo = intervalo
        self._parar = threading.Event()
        self._linha: Optional[threading.Thread] = None

    def executar_uma_vez(self) -> List[str]:
        """Marca como Vencidos os títulos Abertos com vencimento anterior à data de referência (RF-24)."""
        return self._titulos.verificar_vencimentos_automaticamente(data_local(self._relogio.agora()))

    def iniciar(self) -> None:
        self._parar.clear()
        self._linha = threading.Thread(target=self._repetir, name="agendador de vencimentos", daemon=True)
        self._linha.start()

    def parar(self) -> None:
        self._parar.set()
        if self._linha is not None:
            self._linha.join(timeout=5)

    def _repetir(self) -> None:
        while not self._parar.is_set():
            try:
                vencidos = self.executar_uma_vez()
                if vencidos:
                    logging.getLogger("remindme").info("Verificação de vencimento: %d título(s) vencido(s).", len(vencidos))
            except Exception:
                # O erro já foi registrado com o identificador de correlação (RNF-21); a rotina continua.
                pass
            self._parar.wait(self._intervalo.total_seconds())
