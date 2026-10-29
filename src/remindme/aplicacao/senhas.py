"""Hash de senha com salt por `scrypt` (RNF-04, OPEN-33). A senha em claro nunca é guardada (INV-3)."""

import hashlib
import hmac
import secrets

_N, _R, _P = 2**14, 8, 1
_TAMANHO = 32


def gerar_hash(senha: str) -> str:
    salt = secrets.token_bytes(16)
    resumo = hashlib.scrypt(senha.encode("utf-8"), salt=salt, n=_N, r=_R, p=_P, dklen=_TAMANHO)
    return f"scrypt${_N}${_R}${_P}${salt.hex()}${resumo.hex()}"


def conferir(senha: str, hash_guardado: str) -> bool:
    try:
        algoritmo, n, r, p, salt, resumo = hash_guardado.split("$")
        if algoritmo != "scrypt":
            return False
        calculado = hashlib.scrypt(
            senha.encode("utf-8"),
            salt=bytes.fromhex(salt),
            n=int(n),
            r=int(r),
            p=int(p),
            dklen=len(bytes.fromhex(resumo)),
        )
    except (ValueError, TypeError):
        return False
    return hmac.compare_digest(calculado.hex(), resumo)


# Usado quando o e-mail não existe, para que a recusa leve o mesmo tempo (RF-66).
HASH_FICTICIO = gerar_hash(secrets.token_urlsafe(16))
