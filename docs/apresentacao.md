# Como apresentar o RemindMe

Três jeitos de abrir a demonstração, do mais simples ao que não exige instalar nada. Em todos, a demonstração tem um usuário de cada perfil, clientes e títulos em todos os estados, e a senha aparece na tela.

| Perfil | E-mail |
|---|---|
| Dono | `carla@demo.example` |
| Operador Financeiro | `diego@demo.example` |
| Contador | `helena@demo.example` |
| Administrador | `admin@demo.example` |

## 1. Windows com Python: dois cliques

1. Baixe o repositório (no GitHub: **Code → Download ZIP**) e extraia a pasta.
2. Dê dois cliques em **`RemindMe-demonstracao.bat`**.
3. A janela preta mostra os usuários e a senha, e o navegador abre sozinho no RemindMe.
4. **Não feche a janela preta** durante a apresentação: ela é o servidor.

O atalho cria dados novos a cada uso, com uma senha nova. Se o computador não tiver Python 3.11 ou mais recente, a janela avisa e indica o caminho 3.

## 2. Qualquer sistema, pelo terminal

```
python3 iniciar.py demonstracao
```

No Windows, troque `python3` por `py` ou `python`. O navegador abre sozinho. Rodar o comando de novo reaproveita a mesma demonstração; `--substituir` recria tudo, e `--senha minha-senha` escolhe a senha.

## 3. Sem instalar nada: GitHub Codespaces

Serve para computador de laboratório sem Python ou sem permissão para instalar programas. Só precisa de navegador e de uma conta no GitHub com acesso ao repositório.

1. No GitHub, abra o repositório e clique em **Code → Codespaces → Create codespace on main**.
2. Espere o editor abrir no navegador (1 a 2 minutos na primeira vez).
3. No terminal da parte de baixo, rode:
   ```
   python3 iniciar.py demonstracao
   ```
4. Aparece um aviso **"Open in Browser"**. Clique nele. Se o aviso sumir, abra a aba **Ports**, procure a porta 8000 (RemindMe) e clique no ícone de globo.
5. O endereço é algo como `https://nome-8000.app.github.dev`, já com HTTPS.

Por padrão, só você, logado no GitHub, abre esse endereço. Para o professor abrir no computador dele, na aba **Ports**, clique com o botão direito na porta 8000 → **Port Visibility → Public** e envie o endereço. Volte para **Private** ao terminar. O Codespaces desliga sozinho depois de 30 minutos parado; a conta pessoal gratuita tem uma cota mensal de horas.

## "Não é possível acessar esse site"

Esse erro do navegador quer dizer que nada respondeu no endereço. As causas mais comuns:

| Causa | Como resolver |
|---|---|
| O servidor não está rodando: a janela do terminal foi fechada, ou o comando terminou com erro | Rode o comando de novo e deixe a janela aberta. Leia a última mensagem do terminal |
| O endereço está em outro computador | `127.0.0.1` é sempre o próprio computador. O RemindMe precisa rodar na mesma máquina do navegador, ou use o Codespaces |
| A porta mudou | Se a 8000 estiver ocupada, o RemindMe usa a seguinte e avisa no terminal. Use o endereço que o terminal mostrar |
| O navegador trocou `http` por `https` | Digite o endereço completo, com `http://`: `http://127.0.0.1:8000` |
| O proxy da rede intercepta `localhost` | Use `127.0.0.1` em vez de `localhost`, como o terminal mostra |
| O Python não está instalado ou é antigo | `py --version` ou `python3 --version` precisa mostrar 3.11 ou mais. Sem Python, use o Codespaces |
