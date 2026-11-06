"""Regra da senha (OPEN-44) e cifrador (RNF-04), em unidade."""

import unittest

from remindme.aplicacao.senhas import CifradorScrypt, motivo_da_senha
from tests.apoio import CIFRADOR_DE_TESTE


class MotivoDaSenha(unittest.TestCase):
    def test_OPEN_44_limites_de_tamanho(self):
        self.assertEqual(motivo_da_senha("a" * 7), "A senha deve ter pelo menos 8 caracteres.")
        self.assertEqual(motivo_da_senha("a" * 8), "")
        self.assertEqual(motivo_da_senha("a" * 256), "")
        self.assertEqual(motivo_da_senha("a" * 257), "A senha deve ter no máximo 256 caracteres.")

    def test_senha_ausente_usa_a_mensagem_pedida(self):
        self.assertEqual(motivo_da_senha("", ausente="Informe a nova senha."), "Informe a nova senha.")
        self.assertEqual(motivo_da_senha(None), "Informe a senha provisória.")


class Cifrador(unittest.TestCase):
    def test_CifradorScrypt_gera_salt_novo_e_confere(self):
        primeiro, segundo = CIFRADOR_DE_TESTE.gerar("x" * 8), CIFRADOR_DE_TESTE.gerar("x" * 8)
        self.assertNotEqual(primeiro, segundo)
        self.assertTrue(CIFRADOR_DE_TESTE.conferir("x" * 8, primeiro))
        self.assertFalse(CIFRADOR_DE_TESTE.conferir("y" * 8, primeiro))
        self.assertIsInstance(CIFRADOR_DE_TESTE, CifradorScrypt)
