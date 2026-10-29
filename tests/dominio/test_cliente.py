import unittest

from remindme.dominio.cliente import Cliente, documento_valido
from remindme.dominio.erros import EntradaInvalida


class DocumentoDoCliente(unittest.TestCase):
    def test_cpf_e_cnpj_validos(self):
        for documento in ("52998224725", "11222333000181"):
            self.assertTrue(documento_valido(documento))

    def test_digito_verificador_errado_ou_repetido(self):
        for documento in ("52998224724", "11222333000182", "11111111111", "123"):
            with self.subTest(documento=documento):
                self.assertFalse(documento_valido(documento))

    def test_formatacao(self):
        self.assertEqual(Cliente.criar("1", "A", "52998224725").documento_formatado, "529.982.247-25")
        self.assertEqual(Cliente.criar("1", "A", "11222333000181").documento_formatado, "11.222.333/0001-81")

    def test_contato_invalido_informa_o_campo(self):
        with self.assertRaises(EntradaInvalida) as erro:
            Cliente.criar("1", "A", "52998224725", email="sem-arroba", telefone="12")
        self.assertEqual(set(erro.exception.campos), {"e-mail", "telefone"})


if __name__ == "__main__":
    unittest.main()
