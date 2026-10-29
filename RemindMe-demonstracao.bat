@echo off
rem Inicia a demonstracao do RemindMe no Windows com dois cliques.
rem Cria dados de exemplo novos, mostra os usuarios e a senha, e abre o navegador.
chcp 65001 >nul
cd /d "%~dp0"
title RemindMe

set "PY="
py -3 -c "import sys; sys.exit(0 if sys.version_info >= (3, 11) else 1)" >nul 2>nul && set "PY=py -3"
if not defined PY python -c "import sys; sys.exit(0 if sys.version_info >= (3, 11) else 1)" >nul 2>nul && set "PY=python"
if not defined PY goto sem_python

%PY% iniciar.py demonstracao --substituir
echo.
echo O RemindMe foi encerrado.
pause
exit /b 0

:sem_python
echo.
echo Nao encontrei o Python 3.11 ou mais recente neste computador.
echo.
echo Opcoes:
echo   1. Instale o Python em https://www.python.org/downloads/ (marque "Add python.exe to PATH")
echo      e rode este arquivo de novo.
echo   2. Sem instalar nada: abra o repositorio no GitHub, clique em Code, depois em
echo      Codespaces e em "Create codespace". Veja docs\apresentacao.md.
echo.
pause
exit /b 1
