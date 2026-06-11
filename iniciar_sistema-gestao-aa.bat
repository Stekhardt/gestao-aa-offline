@echo off
echo ==========================================
echo    Iniciando o Sistema de Gestao AA...
echo ==========================================
echo.

REM Desativa a coleta de dados do Streamlit para pular a pergunta de e-mail
set STREAMLIT_GATHER_USAGE_STATS=false

REM Aponta o comando direto para o executavel do Python portatil
SET PYTHON_EXE="python_portatil\python.exe"

if not exist %PYTHON_EXE% (
    echo [ERRO] Nao encontrei o motor do Python.
    pause
    exit
)

echo [1/2] Baixando bibliotecas e configurando o ambiente...
echo.

%PYTHON_EXE% -m ensurepip >nul 2>&1
%PYTHON_EXE% -m pip install --upgrade pip >nul 2>&1
%PYTHON_EXE% -m pip install streamlit pandas >nul 2>&1

echo.
echo ==========================================
echo Tudo pronto! O navegador sera aberto.
echo Para encerrar o sistema, feche esta janela.
echo ==========================================
echo.

REM Executa a sua aplicacao
%PYTHON_EXE% -m streamlit run projeto_aa_v1_14.py

pause