"""Hash de senha com salt por `scrypt`, da biblioteca padrão (RNF-04, OPEN-33). Senha mínima: OPEN-44."""

import base64
import hashlib
import hmac
import secrets

TAMANHO_MINIMO = 8
TAMANHO_MAXIMO = 256


class CifradorScrypt:
    """O custo `n` é o parâmetro adaptativo: cada potência de 2 dobra o trabalho e a memória.

    O padrão é o mínimo recomendado pela OWASP para `scrypt` (n = 2^17, r = 8, p = 1), cerca de 128 MiB e
    poucas centenas de milissegundos por senha. Os testes usam um custo menor, para a suíte ficar rápida.
    """

    def __init__(self, n: int = 2**17, r: int = 8, p: int = 1):
        self._n, self._r, self._p = n, r, p

    def gerar(self, senha: str) -> str:
        sal = secrets.token_bytes(16)
        resumo = self._derivar(senha, sal, self._n, self._r, self._p)
        return "$".join(["scrypt", str(self._n), str(self._r), str(self._p), _b64(sal), _b64(resumo)])

    def conferir(self, senha: str, guardado: str) -> bool:
        try:
            nome, n, r, p, sal, resumo = guardado.split("$")
            if nome != "scrypt":
                return False
            calculado = self._derivar(senha, base64.b64decode(sal), int(n), int(r), int(p))
        except (ValueError, TypeError):
            return False
        return hmac.compare_digest(calculado, base64.b64decode(resumo))

    @staticmethod
    def _derivar(senha: str, sal: bytes, n: int, r: int, p: int) -> bytes:
        return hashlib.scrypt(
            senha.encode("utf-8"), salt=sal, n=n, r=r, p=p, dklen=32, maxmem=128 * r * (n + p) + 16 * 1024 * 1024
        )


def motivo_da_senha(senha: object) -> str:
    """OPEN-44, decidida em 2026-10-23: pelo menos 8 caracteres, sem regra de composição."""
    if not isinstance(senha, str) or not senha:
        return "Informe a senha provisória."
    if len(senha) < TAMANHO_MINIMO:
        return f"A senha deve ter pelo menos {TAMANHO_MINIMO} caracteres."
    if len(senha) > TAMANHO_MAXIMO:
        return f"A senha deve ter no máximo {TAMANHO_MAXIMO} caracteres."
    return ""


def _b64(dados: bytes) -> str:
    return base64.b64encode(dados).decode("ascii")
