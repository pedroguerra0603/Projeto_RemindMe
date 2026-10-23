"""Matriz de permissões e regras de perfil da Spec 002, sem banco e sem interface (RNF-19)."""

import unittest

from remindme.dominio.erros import OperacaoNegada, OperacaoRecusada
from remindme.dominio.operacoes import Operacao
from remindme.dominio.permissoes import MatrizPermissoes
from remindme.dominio.usuario import Perfil, Usuario

D, O, C, Cl, A = (
    Perfil.DONO,
    Perfil.OPERADOR_FINANCEIRO,
    Perfil.CONTADOR,
    Perfil.CLIENTE,
    Perfil.ADMINISTRADOR,
)

# Seção 4 da Spec 002, linha a linha, com a consulta de clientes (OPEN-42).
TABELA_DA_SPEC = {
    Operacao.CADASTRAR_TITULO: {D, O},
    Operacao.REGISTRAR_PAGAMENTO: {D, O},
    Operacao.VERIFICAR_VENCIMENTOS: {D, O},
    Operacao.ESTORNAR_PAGAMENTO: {D},
    Operacao.CANCELAR_TITULO: {D},
    Operacao.CONSULTAR_TITULOS: {D, O, C},
    Operacao.MANTER_CLIENTES: {D, O},
    Operacao.CONSULTAR_CLIENTES: {D, O, C},
    Operacao.CONDUZIR_ORCAMENTO: {D, O},
    Operacao.APROVAR_DESCONTO: {D},
    Operacao.GERENCIAR_OBRIGACOES: {D, O},
    Operacao.CLASSIFICAR_LANCAMENTO: {D, O},
    Operacao.APURAR_RESULTADO: {D, O, C},
    Operacao.CONSULTAR_AUDITORIA: {D, C, A},
    Operacao.CONFIGURAR_REGRAS: {A},
    Operacao.IMPORTAR_CSV: {D, O},
    Operacao.EXPORTAR_CSV: {D, O, C},
    Operacao.ADMINISTRAR_USUARIOS: {A},
}


class MatrizInicial(unittest.TestCase):
    def test_OPEN_32_a_matriz_inicial_e_a_tabela_da_spec(self):
        matriz = MatrizPermissoes.inicial()
        for operacao in Operacao:
            for perfil in Perfil:
                with self.subTest(operacao=operacao.value, perfil=perfil.value):
                    self.assertEqual(matriz.permite(perfil, operacao), perfil in TABELA_DA_SPEC[operacao])

    def test_RNF_02_perfil_desconhecido_e_negado_em_tudo(self):
        matriz = MatrizPermissoes.inicial()
        for operacao in Operacao:
            with self.subTest(operacao=operacao.value), self.assertRaises(OperacaoNegada):
                matriz.exigir(object(), operacao)

    def test_RF_67_a_negacao_informa_o_motivo(self):
        with self.assertRaisesRegex(OperacaoNegada, "Administrador não tem permissão para cadastrar título"):
            MatrizPermissoes.inicial().exigir(A, Operacao.CADASTRAR_TITULO)


class PermissoesFixadas(unittest.TestCase):
    def test_RB_03_o_contador_nao_ganha_permissao_de_alterar_registros(self):
        matriz = MatrizPermissoes.inicial()
        for operacao in (
            Operacao.CADASTRAR_TITULO,
            Operacao.REGISTRAR_PAGAMENTO,
            Operacao.VERIFICAR_VENCIMENTOS,
            Operacao.MANTER_CLIENTES,
            Operacao.IMPORTAR_CSV,
        ):
            with self.subTest(operacao=operacao.value), self.assertRaisesRegex(OperacaoRecusada, "RB-03"):
                matriz.conceder(C, operacao)

    def test_RB_02_RB_15_OPEN_16_so_o_dono_e_isso_nao_muda(self):
        matriz = MatrizPermissoes.inicial()
        for operacao, regra in (
            (Operacao.ESTORNAR_PAGAMENTO, "RB-02"),
            (Operacao.APROVAR_DESCONTO, "RB-15"),
            (Operacao.CANCELAR_TITULO, "OPEN-16"),
        ):
            with self.subTest(operacao=operacao.value):
                with self.assertRaisesRegex(OperacaoRecusada, regra):
                    matriz.retirar(D, operacao)
                with self.assertRaisesRegex(OperacaoRecusada, regra):
                    matriz.conceder(O, operacao)

    def test_RB_26_o_cliente_nao_ganha_a_consulta_geral_de_titulos(self):
        with self.assertRaisesRegex(OperacaoRecusada, "RB-26"):
            MatrizPermissoes.inicial().conceder(Cl, Operacao.CONSULTAR_TITULOS)

    def test_RF_03_celula_configuravel_muda_e_volta(self):
        matriz = MatrizPermissoes.inicial().conceder(O, Operacao.CONSULTAR_AUDITORIA)
        self.assertTrue(matriz.permite(O, Operacao.CONSULTAR_AUDITORIA))
        self.assertFalse(matriz.retirar(O, Operacao.CONSULTAR_AUDITORIA).permite(O, Operacao.CONSULTAR_AUDITORIA))


class UsuarioDoDominio(unittest.TestCase):
    def test_RF_02_usuario_nasce_ativo_com_exatamente_um_perfil(self):
        usuario = Usuario.cadastrar("u1", " Diego Ramos ", " Diego@Exemplo.com ", O)
        self.assertEqual((usuario.nome, usuario.email, usuario.perfil, usuario.ativo), ("Diego Ramos", "diego@exemplo.com", O, True))

    def test_RNF_14_campos_invalidos_sao_indicados_de_uma_vez(self):
        with self.assertRaises(OperacaoRecusada) as ctx:
            Usuario.cadastrar("u1", "", "sem-arroba", "Dono")
        self.assertEqual(set(ctx.exception.campos), {"nome", "email", "perfil"})

    def test_A3_usuario_inativo_nao_e_inativado_de_novo(self):
        usuario = Usuario.cadastrar("u1", "Diego", "diego@exemplo.com", O).inativado()
        with self.assertRaises(OperacaoRecusada):
            usuario.inativado()


if __name__ == "__main__":
    unittest.main()
