"""Leitura do formulário com arquivo (Spec 010), sem o módulo `cgi`, que saiu do Python 3.13."""

import unittest

from remindme.apresentacao.web.multipart import ArquivoEnviado, ler_multipart

LIMITE = "----limite123"
TIPO = f"multipart/form-data; boundary={LIMITE}"


def corpo(*partes: bytes) -> bytes:
    return b"".join(b"--" + LIMITE.encode() + b"\r\n" + p + b"\r\n" for p in partes) + b"--" + LIMITE.encode() + b"--\r\n"


def campo(nome: str, valor: str) -> bytes:
    return f'Content-Disposition: form-data; name="{nome}"\r\n\r\n{valor}'.encode("utf-8")


def arquivo(nome: str, cabecalho_do_nome: str, conteudo: bytes) -> bytes:
    return (
        f'Content-Disposition: form-data; name="{nome}"; {cabecalho_do_nome}\r\nContent-Type: application/pdf\r\n\r\n'
    ).encode("utf-8") + conteudo


class LeituraDoMultipart(unittest.TestCase):
    def test_campos_e_arquivo(self):
        conteudo = b"%PDF-1.4\r\n\x00\xff bin\r\n--quase"
        campos, arquivos = ler_multipart(
            corpo(campo("protecao", "abc"), campo("descricao", "Guia paga — março"), arquivo("arquivo", 'filename="das.pdf"', conteudo)),
            TIPO,
        )
        self.assertEqual(campos, {"protecao": "abc", "descricao": "Guia paga — março"})
        self.assertEqual(arquivos, {"arquivo": ArquivoEnviado("das.pdf", conteudo)})

    def test_nome_do_arquivo_em_utf_8_pelo_filename_estrela(self):
        _, arquivos = ler_multipart(
            corpo(arquivo("arquivo", "filename=\"x.pdf\"; filename*=UTF-8''DAS%20mar%C3%A7o.pdf", b"%PDF-1")), TIPO
        )
        self.assertEqual(arquivos["arquivo"].nome, "DAS março.pdf")

    def test_nome_com_acento_cru_do_navegador(self):
        _, arquivos = ler_multipart(corpo(arquivo("arquivo", 'filename="março.pdf"', b"%PDF-1")), TIPO)
        self.assertEqual(arquivos["arquivo"].nome, "março.pdf")

    def test_foco_2_parte_de_arquivo_vazia_nao_entra(self):
        campos, arquivos = ler_multipart(corpo(campo("data", "2026-11-20"), arquivo("arquivo", 'filename=""', b"")), TIPO)
        self.assertEqual((campos, arquivos), ({"data": "2026-11-20"}, {}))

    def test_corpo_mal_formado_devolve_vazio(self):
        for tipo, conteudo in (
            ("multipart/form-data", corpo(campo("a", "1"))),
            (TIPO, b"lixo sem limite"),
            (TIPO, corpo(campo("a", "1"))[:20]),
            (TIPO, b"--" + LIMITE.encode() + b"\r\nsem cabecalhos"),
        ):
            with self.subTest(tipo=tipo, inicio=conteudo[:20]):
                self.assertEqual(ler_multipart(conteudo, tipo), ({}, {}))

    def test_limite_entre_aspas(self):
        campos, _ = ler_multipart(corpo(campo("a", "1")), f'multipart/form-data; boundary="{LIMITE}"')
        self.assertEqual(campos, {"a": "1"})


if __name__ == "__main__":
    unittest.main()
