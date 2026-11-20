"""Página da empresa que usa o sistema (OPEN-54, Spec 017). Só monta o que os serviços devolvem (INV-1)."""

from decimal import Decimal
from typing import Optional

from remindme.apresentacao.web import formatos as f
from remindme.apresentacao.web.html import Html, h, juntar
from remindme.apresentacao.web.paginas import (
    Contexto,
    Erros,
    Valores,
    cabecalho,
    caixa_de_aviso,
    campo,
    erro_geral,
    layout,
    protecao,
)
from remindme.dominio.operacoes import Operacao
from remindme.dominio.titulo import EstadoTitulo


def pagina_empresa(ctx: Contexto, empresa, visoes: Optional[list], clientes: Optional[int], valores: Valores, erros: Erros, aviso=None) -> Html:
    partes = [cabecalho(empresa.nome_fantasia or empresa.razao_social if empresa else "Empresa", "Dados da sua empresa no RemindMe.")]
    if empresa:
        partes.append(
            h(
                """<section class="cartao"><dl class="dados">
<div><dt>Razão social</dt><dd>{razao}</dd></div>
<div><dt>CNPJ</dt><dd>{cnpj}</dd></div>
<div><dt>Telefone</dt><dd>{telefone}</dd></div>
<div><dt>E-mail</dt><dd>{email}</dd></div>
<div><dt>Endereço</dt><dd>{endereco}</dd></div>
</dl></section>""",
                razao=empresa.razao_social,
                cnpj=f.documento(empresa.cnpj),
                telefone=f.contato(empresa.telefone) if empresa.telefone else "Não informado",
                email=empresa.email or "Não informado",
                endereco=empresa.endereco or "Não informado",
            )
        )
    elif not ctx.pode(Operacao.MANTER_EMPRESA):
        partes.append(caixa_de_aviso("info", "Os dados da empresa ainda não foram preenchidos. Peça ao Dono para preenchê-los."))
    indicadores = []
    if clientes is not None:
        indicadores.append(h('<div class="indicador"><div class="rotulo">Clientes</div><div class="numero">{n}</div></div>', n=clientes))
    if visoes is not None:
        em_aberto = [v for v in visoes if v.estado in (EstadoTitulo.ABERTO, EstadoTitulo.VENCIDO)]
        indicadores.append(h('<div class="indicador"><div class="rotulo">Títulos em aberto</div><div class="numero">{n}</div></div>', n=len(em_aberto)))
        indicadores.append(
            h(
                '<div class="indicador"><div class="rotulo">A receber</div><div class="numero">{v}</div></div>',
                v=f.moeda(sum((v.saldo for v in em_aberto), Decimal("0.00"))),
            )
        )
    if indicadores:
        partes.append(h('<div class="indicadores">{i}</div>', i=juntar(indicadores)))
    if ctx.pode(Operacao.MANTER_EMPRESA):
        formulario = h(
            """<form class="formulario" method="post" action="/empresa" novalidate>
{protecao}{geral}
{razao}{fantasia}
<div class="linha-campos">{cnpj}{telefone}</div>
{email}{endereco}
<div class="acoes"><button type="submit">Salvar dados da empresa</button></div>
</form>""",
            protecao=protecao(ctx),
            geral=erro_geral(erros),
            razao=campo("razao_social", "Razão social", valores, erros),
            fantasia=campo("nome_fantasia", "Nome fantasia", valores, erros, obrigatorio=False),
            cnpj=campo("cnpj", "CNPJ", valores, erros, extra='inputmode="numeric"'),
            telefone=campo("telefone", "Telefone", valores, erros, tipo="text", obrigatorio=False, extra='inputmode="tel"'),
            email=campo("email", "E-mail", valores, erros, tipo="email", obrigatorio=False),
            endereco=campo("endereco", "Endereço", valores, erros, obrigatorio=False),
        )
        titulo = "Alterar dados" if empresa else "Preencher dados da empresa"
        partes.append(h('<section class="cartao"><h2>{t}</h2>{f}</section>', t=titulo, f=formulario))
    return layout("Empresa", juntar(partes), ctx, "empresa", aviso)
