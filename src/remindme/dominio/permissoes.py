"""Matriz de permissões por perfil (Spec 002, OPEN-32). Operação que não está na matriz é negada (RNF-02)."""

from dataclasses import dataclass
from typing import Dict, FrozenSet, Optional, Tuple

from remindme.dominio.erros import OperacaoNegada, OperacaoRecusada
from remindme.dominio.operacoes import Operacao
from remindme.dominio.regras import PermissaoFixada, permissao_fixada
from remindme.dominio.usuario import Perfil

_D, _O, _C, _A = Perfil.DONO, Perfil.OPERADOR_FINANCEIRO, Perfil.CONTADOR, Perfil.ADMINISTRADOR

# Seção 4 da Spec 002, com a consulta de clientes (OPEN-42). As células fixadas ficam em `regras`.
MATRIZ_INICIAL: Dict[Operacao, FrozenSet[Perfil]] = {
    Operacao.CADASTRAR_TITULO: frozenset({_D, _O}),
    Operacao.REGISTRAR_PAGAMENTO: frozenset({_D, _O}),
    Operacao.VERIFICAR_VENCIMENTOS: frozenset({_D, _O}),
    Operacao.ESTORNAR_PAGAMENTO: frozenset({_D}),
    Operacao.CANCELAR_TITULO: frozenset({_D}),
    Operacao.CONSULTAR_TITULOS: frozenset({_D, _O, _C}),
    Operacao.MANTER_CLIENTES: frozenset({_D, _O}),
    Operacao.CONSULTAR_CLIENTES: frozenset({_D, _O, _C}),
    Operacao.CONDUZIR_ORCAMENTO: frozenset({_D, _O}),
    Operacao.APROVAR_DESCONTO: frozenset({_D}),
    Operacao.GERENCIAR_OBRIGACOES: frozenset({_D, _O}),
    Operacao.CLASSIFICAR_LANCAMENTO: frozenset({_D, _O}),
    Operacao.APURAR_RESULTADO: frozenset({_D, _O, _C}),
    Operacao.CONSULTAR_AUDITORIA: frozenset({_D, _C, _A}),
    Operacao.CONFIGURAR_REGRAS: frozenset({_A}),
    Operacao.IMPORTAR_CSV: frozenset({_D, _O}),
    Operacao.EXPORTAR_CSV: frozenset({_D, _O, _C}),
    Operacao.ADMINISTRAR_USUARIOS: frozenset({_A}),
    Operacao.MANTER_EMPRESA: frozenset({_D}),  # OPEN-54
    # Spec 018: como clientes e títulos; estorno e cancelamento só pelo Dono (RB-33).
    Operacao.MANTER_FORNECEDORES: frozenset({_D, _O}),
    Operacao.CONSULTAR_FORNECEDORES: frozenset({_D, _O, _C}),
    Operacao.CADASTRAR_CONTA_PAGAR: frozenset({_D, _O}),
    Operacao.PAGAR_CONTA: frozenset({_D, _O}),
    Operacao.ESTORNAR_PAGAMENTO_CONTA: frozenset({_D}),
    Operacao.CANCELAR_CONTA_PAGAR: frozenset({_D}),
    Operacao.CONSULTAR_CONTAS_PAGAR: frozenset({_D, _O, _C}),
}


@dataclass(frozen=True)
class Celula:
    permitido: bool
    fixada: Optional[PermissaoFixada]


@dataclass(frozen=True)
class MatrizPermissoes:
    """O que cada perfil pode fazer. As células fixadas por regra prevalecem sobre a configuração (INV-4)."""

    concedidas: FrozenSet[Tuple[Operacao, Perfil]]

    @classmethod
    def inicial(cls) -> "MatrizPermissoes":
        return cls(frozenset((op, p) for op, perfis in MATRIZ_INICIAL.items() for p in perfis))

    def celula(self, operacao: Operacao, perfil: Perfil) -> Celula:
        fixada = permissao_fixada(operacao, perfil)
        if fixada is not None:
            return Celula(fixada.permitido, fixada)
        return Celula((operacao, perfil) in self.concedidas, None)

    def permite(self, perfil: Perfil, operacao: Operacao) -> bool:
        return self.celula(operacao, perfil).permitido

    def exigir(self, perfil: Perfil, operacao: Operacao) -> None:
        """RF-67, RNF-02: nega o que não está explicitamente permitido, informando o motivo."""
        celula = self.celula(operacao, perfil)
        if celula.permitido:
            return
        if celula.fixada is not None:
            raise OperacaoNegada(celula.fixada.motivo)
        nome = perfil.value if isinstance(perfil, Perfil) else "informado"
        raise OperacaoNegada(f"O perfil {nome} não tem permissão para {operacao.descricao}.")

    def operacoes(self, perfil: Perfil) -> FrozenSet[Operacao]:
        """RF-65: as funcionalidades que o perfil vê."""
        return frozenset(op for op in Operacao if self.permite(perfil, op))

    def conceder(self, perfil: Perfil, operacao: Operacao) -> "MatrizPermissoes":
        """A4, RF-03. E5: célula fixada por regra não muda."""
        celula = self._alteravel(operacao, perfil)
        if celula.permitido:
            raise OperacaoRecusada("O perfil já tem essa permissão.")
        return MatrizPermissoes(self.concedidas | {(operacao, perfil)})

    def retirar(self, perfil: Perfil, operacao: Operacao) -> "MatrizPermissoes":
        celula = self._alteravel(operacao, perfil)
        if not celula.permitido:
            raise OperacaoRecusada("O perfil não tem essa permissão.")
        return MatrizPermissoes(self.concedidas - {(operacao, perfil)})

    def _alteravel(self, operacao: Operacao, perfil: Perfil) -> Celula:
        celula = self.celula(operacao, perfil)
        if celula.fixada is not None:
            raise OperacaoRecusada(
                f"Essa permissão é fixada por regra de negócio e não muda por configuração: {celula.fixada.motivo}"
            )
        return celula
