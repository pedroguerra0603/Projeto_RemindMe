"""Dados de demonstração para a apresentação (Spec 017, A8; OPEN-12).

Tudo é feito pelos serviços da aplicação, com as sessões dos próprios usuários: a auditoria da demonstração é a
de uma operação de verdade. A senha é informada por quem executa o comando e não fica em arquivo.
"""

from datetime import date, timedelta
from decimal import Decimal
from typing import List, Tuple

from remindme.aplicacao.tempo import data_local
from remindme.dominio.cliente import tipo_do_documento
from remindme.dominio.usuario import Perfil

USUARIOS = (
    ("Carla Menezes", "carla@demo.example", Perfil.DONO),
    ("Diego Ramos", "diego@demo.example", Perfil.OPERADOR_FINANCEIRO),
    ("Helena Prado", "helena@demo.example", Perfil.CONTADOR),
)
ADMINISTRADOR = ("Administração RemindMe", "admin@demo.example")


def _documento(base: str) -> str:
    """Completa a base com os dígitos verificadores que a tornam um CPF ou CNPJ válido (OPEN-40)."""
    for sufixo in range(100):
        candidato = f"{base}{sufixo:02d}"
        if tipo_do_documento(candidato):
            return candidato
    raise ValueError(f"Base sem documento válido: {base}")


CLIENTES = (
    ("Padaria Pão Quente Ltda", _documento("112223330001"), "financeiro@paoquente.example"),
    ("Sérgio Tavares", _documento("123456789"), "(11) 98765-4321"),
    ("Oficina Duas Rodas ME", _documento("456789010001"), "(11) 3456-7890"),
    ("Studio Bela Forma", _documento("12ABC34501DE"), "contato@belaforma.example"),
    ("Mercadinho São José Ltda", _documento("789012340001"), "(19) 99876-5432"),
)


def preparar_demonstracao(sistema, senha: str) -> List[Tuple[str, str, str]]:
    servicos = sistema.servicos
    hoje = data_local(sistema.relogio.agora())
    acesso = servicos.acesso
    acesso.criar_primeiro_administrador(ADMINISTRADOR[0], ADMINISTRADOR[1], senha)
    admin = acesso.entrar(ADMINISTRADOR[1], senha).identificador
    for nome, email, perfil in USUARIOS:
        acesso.cadastrar_usuario(admin, nome, email, perfil, senha)
    dona = acesso.entrar("carla@demo.example", senha).identificador
    operador = acesso.entrar("diego@demo.example", senha).identificador

    padaria, sergio, oficina, studio, mercadinho = (
        servicos.clientes.cadastrar_cliente(operador, nome, documento, contato) for nome, documento, contato in CLIENTES
    )
    titulos = servicos.titulos

    def titulo(cliente, reais: str, dias: int, condicao: str = ""):
        return titulos.cadastrar_titulo(operador, cliente.id, Decimal(reais), hoje + timedelta(days=dias), condicao)

    def pagar(t, reais: str, dias_atras: int = 0):
        return titulos.registrar_pagamento(operador, t.id, Decimal(reais), hoje - timedelta(days=dias_atras))

    titulo(padaria, "1250.00", 3, "Boleto, 30 dias")
    pagar(titulo(padaria, "980.00", -12, "Pix"), "300.00", 5)
    pagar(titulo(padaria, "2400.00", -40, "Boleto"), "2400.00", 38)
    titulo(sergio, "450.00", 20, "Pix")
    titulo(sergio, "320.00", -5, "Dinheiro")
    titulo(oficina, "3800.00", -2, "Boleto, 3 parcelas")
    titulo(oficina, "1150.00", 1, "Pix")
    estornado = pagar(titulo(studio, "720.00", 10, "Cheque"), "720.00", 1)
    titulos.estornar_pagamento(dona, estornado.id, estornado.pagamentos[0].id, "Cheque devolvido pelo banco", hoje)
    cancelado = titulo(mercadinho, "610.00", 15, "Boleto")
    titulos.cancelar_titulo(dona, cancelado.id, "Cobrança em duplicidade")
    pagar(titulo(mercadinho, "1890.00", -20, "Pix"), "1890.00", 18)

    titulos.verificar_vencimentos_automaticamente(hoje)

    # Orçamentos (Spec 004): todos os estados desta spec, com um desconto aguardando a Dona.
    orcamentos = servicos.orcamentos

    def orcamento(cliente, condicao: str, itens, desconto: str = ""):
        o = orcamentos.criar_orcamento(operador, cliente.id, condicao)
        for descricao, quantidade, unitario in itens:
            orcamentos.incluir_item(operador, o.id, descricao, Decimal(quantidade), Decimal(unitario))
        if desconto:
            o = orcamentos.informar_desconto(operador, o.id, Decimal(desconto))
        return o

    orcamento(
        studio, "50% na aprovação e 50% na entrega",
        [("Manutenção dos aparelhos de musculação", "1", "1800.00"), ("Visita técnica extra", "2", "150.00")], "5",
    )
    orcamento(padaria, "Boleto, 28 dias", [("Forno industrial, revisão completa", "1", "2600.00"), ("Peças de reposição", "4", "185.50")], "15")
    aprovado = orcamento(oficina, "Pix à vista", [("Consultoria financeira, horas", "12", "220.00")], "18")
    orcamentos.decidir_desconto(dona, aprovado.id, True, Decimal("12"))
    cancelado_o = orcamento(mercadinho, "Boleto", [("Sistema de etiquetas", "1", "980.00")])
    orcamentos.cancelar_orcamento(operador, cancelado_o.id, "Cliente desistiu da compra")
    orcamentos.criar_orcamento(operador, sergio.id, "A combinar")

    # Dados da empresa (OPEN-54), preenchidos pela Dona, e um pedido de conta esperando o Administrador (OPEN-55).
    servicos.empresa.salvar(
        dona, razao_social="Menezes Serviços Empresariais Ltda", nome_fantasia="Menezes Serviços",
        cnpj=_documento("334445550001"), telefone="(11) 3322-4455", email="contato@menezes.example",
        endereco="Rua das Palmeiras, 120, sala 4, São Paulo, SP",
    )
    acesso.criar_conta("Bruno Lima", "bruno@demo.example", Perfil.OPERADOR_FINANCEIRO, senha)

    for sessao in (admin, dona, operador):
        acesso.sair(sessao)
    pessoas = [(ADMINISTRADOR[0], ADMINISTRADOR[1], Perfil.ADMINISTRADOR.value)]
    return pessoas + [(nome, email, perfil.value) for nome, email, perfil in USUARIOS]
