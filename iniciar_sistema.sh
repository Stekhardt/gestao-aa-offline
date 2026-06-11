#!/bin/bash

echo "=========================================="
echo "   Iniciando o Sistema de Gestão AA..."
echo "=========================================="
echo ""

# Verifica se a pasta venv existe. Se não, cria.
if [ ! -d "venv" ]; then
    echo "[1/3] Primeira execução detectada. Criando ambiente virtual isolado..."
    python3 -m venv venv
fi

# Ativa o ambiente virtual
echo "[2/3] Ativando ambiente virtual..."
source venv/bin/activate

# Atualiza o pip e instala as dependências
echo "[3/3] Verificando dependências essenciais..."
pip install --upgrade pip -q
pip install streamlit pandas -q

echo ""
echo "=========================================="
echo "Tudo pronto! O navegador será aberto."
echo "Para encerrar o sistema, pressione CTRL+C."
echo "=========================================="
echo ""

# Executa o aplicativo
streamlit run projeto_aa_v1_14.py