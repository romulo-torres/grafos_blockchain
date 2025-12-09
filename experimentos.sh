#!/bin/bash

# Script: experimentos.sh
# Descrição: Roda todos os experimentos automaticamente

echo "================================================="
echo "INICIANDO EXPERIMENTOS DE MERKLE TREE"
echo "================================================="

# Verifica se o arquivo de transações existe
if [ ! -f "teste.txt" ]; then
    echo "ERRO: Arquivo 'teste.txt' não encontrado!"
    echo "Crie um arquivo com transações primeiro."
    exit 1
fi

# Verifica se o script Python existe
if [ ! -f "blockchain.py" ]; then
    echo "ERRO: Arquivo 'blockchain.py' não encontrado!"
    exit 1
fi

# Renomeia o arquivo para o que o Python espera
cp teste.txt transacoes.txt

# Cria diretório para resultados
mkdir -p resultados

echo "Executando todos os experimentos..."
echo "Isso pode levar alguns minutos..."
echo ""

# Executa todos os experimentos
python3 blockchain.py --todos-experimentos

echo ""
echo "================================================="
echo "EXPERIMENTOS CONCLUÍDOS!"
echo "================================================="
echo ""

# Verifica se arquivos foram criados
if [ -d "resultados" ]; then
    echo "Arquivos gerados em 'resultados/':"
    ls -lh resultados/
    
    echo ""
    echo "Resumo dos arquivos CSV:"
    for csv in resultados/*.csv; do
        if [ -f "$csv" ]; then
            lines=$(wc -l < "$csv" 2>/dev/null || echo "0")
            size=$(du -h "$csv" 2>/dev/null | cut -f1)
            echo "  $(basename "$csv"): $lines linhas, $size"
        fi
    done
    
    # Conta quantos arquivos foram criados
    total_csv=$(ls -1 resultados/*.csv 2>/dev/null | wc -l)
    echo ""
    echo "Total de arquivos CSV criados: $total_csv"
else
    echo "ERRO: Diretório 'resultados' não foi criado!"
fi
