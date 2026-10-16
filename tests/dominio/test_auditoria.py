"""Unidade do registro de auditoria (Spec 001): INV-1, INV-3 e OPEN-30."""

import dataclasses
import unittest
from datetime import date, datetime

from remindme.dominio.auditoria import RegistroAuditoria

AGORA = datetime(2026, 10, 16, 9, 30)


class RegistroDeAuditoria(unittest.TestCase):
    def test_RF_62_registro_completo_de_operacao_de_usuario(self):
        r = RegistroAuditoria(
            "u1", AGORA, "estornar pagamento", "pagamento p1", "estornado", "não", "sim", "cheque devolvido"
        )
        self.assertEqual(
            dataclasses.astuple(r),
            ("u1", AGORA, "estornar pagamento", "pagamento p1", "estornado", "não", "sim",
             "cheque devolvido", False, None),
        )

    def test_INV_3_exige_data_e_hora_operacao_e_registro_afetado(self):
        for argumentos in (
            ("u1", None, "op", "titulo t1"),
            ("u1", date(2026, 10, 16), "op", "titulo t1"),
            ("u1", AGORA, "", "titulo t1"),
            ("u1", AGORA, "op", " "),
            ("u1", AGORA, None, "titulo t1"),
        ):
            with self.subTest(argumentos=argumentos), self.assertRaises(ValueError):
                RegistroAuditoria(*argumentos)

    def test_INV_3_exige_usuario_salvo_em_operacao_automatica(self):
        for usuario in (None, "", "  "):
            with self.subTest(usuario=usuario), self.assertRaises(ValueError):
                RegistroAuditoria(usuario, AGORA, "op", "titulo t1")

    def test_OPEN_30_operacao_automatica_tem_usuario_vazio_e_rotina(self):
        r = RegistroAuditoria(
            None, AGORA, "mudar estado", "titulo t1", "estado", "Aberto", "Vencido",
            automatica=True, rotina="verificação de vencimento",
        )
        self.assertIsNone(r.usuario_id)
        self.assertEqual(r.rotina, "verificação de vencimento")

    def test_OPEN_30_operacao_automatica_sem_rotina_ou_com_usuario_e_recusada(self):
        for usuario, rotina in ((None, None), (None, ""), ("u1", "verificação de vencimento")):
            with self.subTest(usuario=usuario, rotina=rotina), self.assertRaises(ValueError):
                RegistroAuditoria(usuario, AGORA, "op", "titulo t1", automatica=True, rotina=rotina)

    def test_OPEN_30_rotina_so_existe_em_operacao_automatica(self):
        with self.assertRaises(ValueError):
            RegistroAuditoria("u1", AGORA, "op", "titulo t1", rotina="verificação de vencimento")

    def test_RB_30_nenhum_campo_do_registro_muda(self):
        r = RegistroAuditoria("u1", AGORA, "op", "titulo t1")
        for campo in dataclasses.fields(RegistroAuditoria):
            with self.subTest(campo=campo.name), self.assertRaises(dataclasses.FrozenInstanceError):
                setattr(r, campo.name, None)


if __name__ == "__main__":
    unittest.main()
