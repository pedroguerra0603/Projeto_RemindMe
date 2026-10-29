"""Monta a aplicação a partir da configuração. Único ponto que conhece a infraestrutura.

A configuração vem dos argumentos da linha de comando; o código não lê variável de ambiente (Spec 001, CA-13).
"""

import logging
import threading
from dataclasses import dataclass

from remindme.aplicacao.sistema import Sistema
from remindme.apresentacao.web import AplicacaoWeb
from remindme.infraestrutura.relogio import RelogioDoSistema
from remindme.infraestrutura.sqlite import BancoSQLite, UnidadeDeTrabalhoSQLite

log = logging.getLogger("remindme")


@dataclass(frozen=True)
class Configuracao:
    banco: str = "remindme.db"
    host: str = "127.0.0.1"
    porta: int = 8000
    https: bool = False
    antecedencia_dias: int = 5
    intervalo_agendador_minutos: int = 60


@dataclass(frozen=True)
class Montagem:
    sistema: Sistema
    banco: BancoSQLite


def montar(configuracao: Configuracao) -> Montagem:
    banco = BancoSQLite(configuracao.banco)
    sistema = Sistema(
        UnidadeDeTrabalhoSQLite(banco), RelogioDoSistema(), antecedencia_dias=configuracao.antecedencia_dias
    )
    return Montagem(sistema, banco)


def montar_web(montagem: Montagem, configuracao: Configuracao) -> AplicacaoWeb:
    return AplicacaoWeb(montagem.sistema, segredo=montagem.banco.segredo(), cookies_seguros=configuracao.https)


class Agendador:
    """Entrada automática (DT-07; OPEN-13: tarefa periódica no próprio processo). Fora do caminho interativo."""

    def __init__(self, sistema: Sistema, intervalo_minutos: int):
        self._sistema = sistema
        self._intervalo = max(1, intervalo_minutos) * 60
        self._parar = threading.Event()
        self._thread = threading.Thread(target=self._executar, name="agendador", daemon=True)

    def iniciar(self) -> None:
        self._thread.start()

    def parar(self) -> None:
        self._parar.set()

    def _executar(self) -> None:
        while not self._parar.is_set():
            try:
                vencidos = self._sistema.verificar_vencimentos_automaticamente()
                if vencidos:
                    log.info("Verificação de vencimento: %d título(s) passaram a Vencido.", len(vencidos))
            except Exception:
                log.exception("Falha na verificação automática de vencimentos.")
            self._parar.wait(self._intervalo)
