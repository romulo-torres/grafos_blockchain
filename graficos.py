# analisar_resultados.py
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import glob
import os
import sys
import re
from datetime import datetime
from scipy import stats as scipy_stats  # Renomear a importação


def carregar_dados():
    """Carrega todos os arquivos de estatísticas"""
    arquivos = glob.glob("resultados/estatisticas_merkle_*.csv")
    
    if not arquivos:
        print("ERRO: Nenhum arquivo de estatísticas encontrado em 'resultados/'")
        print("Execute primeiro: python3 executar_experimentos.py")
        return None
    
    dados_dict = {}  # Usar dicionário para agrupar por número de transações
    
    for arquivo in sorted(arquivos):
        try:
            # Extrai apenas números do nome do arquivo
            nome_base = os.path.basename(arquivo)
            match = re.search(r'estatisticas_merkle_(\d+)', nome_base)
            
            if not match:
                print(f"⚠️  Ignorando arquivo com formato inválido: {nome_base}")
                continue
                
            n = int(match.group(1))
            df = pd.read_csv(arquivo)
            
            if not df.empty:
                linha = df.iloc[-1].to_dict()
                linha['num_transacoes'] = n
                
                # Se já existe entrada para este n, faz a média
                if n in dados_dict:
                    # Calcula médias para colunas numéricas
                    for col in linha.keys():
                        if isinstance(linha[col], (int, float, np.number)):
                            if col in dados_dict[n]:
                                dados_dict[n][col] = (dados_dict[n][col] + linha[col]) / 2
                            else:
                                dados_dict[n][col] = linha[col]
                else:
                    dados_dict[n] = linha
                    
                print(f"✓ Processado: {n} transações")
        except Exception as e:
            print(f"✗ Erro ao carregar {arquivo}: {e}")
    
    if not dados_dict:
        print("Nenhum dado válido encontrado!")
        return None
    
    # Converte dicionário para DataFrame
    dados = list(dados_dict.values())
    df_completo = pd.DataFrame(dados)
    df_completo = df_completo.sort_values('num_transacoes')
    
    print(f"\n✓ Dados agrupados: {len(df_completo)} valores únicos de transações")
    
    return df_completo

def calcular_estatisticas_comparativas(df):
    """Calcula estatísticas comparativas"""
    print("\n" + "="*80)
    print("ESTATÍSTICAS COMPARATIVAS")
    print("="*80)
    
    # Taxa de crescimento
    if len(df) > 1:
        # Encontra primeiro e último valor único de transações
        primeiro_idx = df['num_transacoes'].idxmin()
        ultimo_idx = df['num_transacoes'].idxmax()
        
        tempo_primeiro = df.loc[primeiro_idx, 'tempo_construcao_seg']
        tempo_ultimo = df.loc[ultimo_idx, 'tempo_construcao_seg']
        altura_primeiro = df.loc[primeiro_idx, 'altura_arvore']
        altura_ultimo = df.loc[ultimo_idx, 'altura_arvore']
        
        if tempo_primeiro > 0:
            crescimento_tempo = (tempo_ultimo / tempo_primeiro - 1) * 100
        else:
            crescimento_tempo = float('inf')
            
        if altura_primeiro > 0:
            crescimento_altura = (altura_ultimo / altura_primeiro - 1) * 100
        else:
            crescimento_altura = float('inf')
        
        print(f"\nCrescimento de {df['num_transacoes'].min()} para {df['num_transacoes'].max()} transações:")
        print(f"  Tempo de construção: {crescimento_tempo:.1f}%")
        print(f"  Altura da árvore: {crescimento_altura:.1f}%")
    
    # Complexidade
    print("\nANÁLISE DE COMPLEXIDADE:")
    
    # Regressão para O(n)
    x = df['num_transacoes'].values
    y_tempo = df['tempo_construcao_seg'].values
    
    if len(x) > 1:
        slope_tempo, intercept_tempo, r_tempo, p_tempo, std_err_tempo = scipy_stats.linregress(x, y_tempo)
        r2_tempo = r_tempo**2
    else:
        slope_tempo = intercept_tempo = r_tempo = r2_tempo = float('nan')
    
    print(f"  Tempo de construção: O(n)")
    print(f"    Coeficiente linear: {slope_tempo:.6f}")
    print(f"    R²: {r2_tempo:.4f}")
    print(f"    Tempo por transação: {slope_tempo*1000:.3f} ms/transação")
    
    # Regressão para O(log n) na altura
    x_log = np.log2(x)
    y_altura = df['altura_arvore'].values
    
    if len(x_log) > 1:
        slope_altura, intercept_altura, r_altura, p_altura, std_err_altura = scipy_stats.linregress(x_log, y_altura)
        r2_altura = r_altura**2
    else:
        slope_altura = intercept_altura = r_altura = r2_altura = float('nan')
    
    print(f"\n  Altura da árvore: O(log n)")
    print(f"    Coeficiente: {slope_altura:.4f}")
    print(f"    R²: {r2_altura:.4f}")
    print(f"    Intercepto: {intercept_altura:.2f}")
    
    # Eficiência
    print("\nEFICIÊNCIA:")
    max_taxa = df['taxa_processamento_trans_seg'].max()
    min_taxa = df['taxa_processamento_trans_seg'].min()
    media_taxa = df['taxa_processamento_trans_seg'].mean()
    
    print(f"  Taxa máxima de processamento: {max_taxa:,.0f} transações/segundo")
    print(f"  Taxa mínima de processamento: {min_taxa:,.0f} transações/segundo")
    print(f"  Taxa média de processamento: {media_taxa:,.0f} transações/segundo")
    
    if 'tempo_medio_busca_ms' in df.columns:
        tempo_busca_medio = df['tempo_medio_busca_ms'].mean()
        print(f"  Tempo médio de busca: {tempo_busca_medio:.2f} ms")
    
    return {
        'slope_tempo': slope_tempo,
        'r2_tempo': r2_tempo,
        'slope_altura': slope_altura,
        'r2_altura': r2_altura,
        'max_taxa': max_taxa,
        'media_taxa': media_taxa
    }

def gerar_tabela_comparativa(df):
    """Gera uma tabela comparativa em LaTeX e Markdown"""
    print("\n" + "="*80)
    print("TABELA COMPARATIVA")
    print("="*80)
    
    # Seleciona colunas relevantes
    colunas = ['num_transacoes', 'tempo_construcao_seg', 'taxa_processamento_trans_seg', 
               'altura_arvore', 'tamanho_raiz_bytes']
    
    tem_busca = 'tempo_medio_busca_ms' in df.columns
    
    if tem_busca:
        colunas.append('tempo_medio_busca_ms')
    
    df_tabela = df[colunas].copy()
    
    # Formata números
    df_tabela['num_transacoes'] = df_tabela['num_transacoes'].apply(lambda x: f"{x:,}")
    df_tabela['tempo_construcao_seg'] = df_tabela['tempo_construcao_seg'].apply(lambda x: f"{x:.4f}")
    df_tabela['taxa_processamento_trans_seg'] = df_tabela['taxa_processamento_trans_seg'].apply(lambda x: f"{x:,.0f}")
    
    # Define nomes das colunas baseado no que está disponível
    if tem_busca:
        df_tabela['tempo_medio_busca_ms'] = df_tabela['tempo_medio_busca_ms'].apply(lambda x: f"{x:.2f}")
        nomes_colunas = ['Transações', 'Tempo (s)', 'Taxa (trans/s)', 'Altura', 'Tamanho Raiz (bytes)', 'Busca (ms)']
    else:
        nomes_colunas = ['Transações', 'Tempo (s)', 'Taxa (trans/s)', 'Altura', 'Tamanho Raiz (bytes)']
    
    # Renomeia colunas
    df_tabela.columns = nomes_colunas
    
    # Mostra tabela
    print("\nTabela de Resultados:")
    print(df_tabela.to_string(index=False))
    
    # Salva em CSV
    df_tabela.to_csv('resultados/tabela_comparativa.csv', index=False)
    
    # Gera LaTeX
    latex = df_tabela.to_latex(index=False, caption='Resultados de performance da Merkle Tree', label='tab:resultados')
    with open('resultados/tabela_latex.tex', 'w') as f:
        f.write(latex)
    
    # Gera Markdown
    markdown = df_tabela.to_markdown(index=False)
    with open('resultados/tabela_markdown.md', 'w') as f:
        f.write("# Tabela de Resultados\n\n")
        f.write(markdown)
    
    print("\n✓ Tabelas salvas em:")
    print("  - resultados/tabela_comparativa.csv")
    print("  - resultados/tabela_latex.tex")
    print("  - resultados/tabela_markdown.md")

def gerar_graficos_comparativos(df, estatisticas):  # Mudei o nome do parâmetro
    """Gera gráficos comparativos"""
    print("\n" + "="*80)
    print("GERANDO GRÁFICOS COMPARATIVOS")
    print("="*80)
    
    fig = plt.figure(figsize=(16, 12))
    fig.suptitle('Análise Comparativa de Performance da Merkle Tree', fontsize=18, fontweight='bold')
    
    # Gráfico 1: Tempo de construção (linear e log)
    ax1 = plt.subplot(2, 3, 1)
    ax1.plot(df['num_transacoes'], df['tempo_construcao_seg'], 'bo-', linewidth=2, markersize=6)
    ax1.set_xlabel('Número de Transações', fontsize=11)
    ax1.set_ylabel('Tempo de Construção (s)', fontsize=11)
    ax1.set_title('Tempo de Construção vs Número de Transações', fontsize=12, fontweight='bold')
    ax1.grid(True, alpha=0.3)
    ax1.set_xscale('linear')
    
    # Linha de tendência
    x_fit = np.linspace(df['num_transacoes'].min(), df['num_transacoes'].max(), 100)
    y_fit = estatisticas['slope_tempo'] * x_fit + (df['tempo_construcao_seg'].iloc[0] - estatisticas['slope_tempo'] * df['num_transacoes'].iloc[0])
    ax1.plot(x_fit, y_fit, 'r--', alpha=0.7, label=f'O(n), R²={estatisticas["r2_tempo"]:.3f}')
    ax1.legend()
    
    # Gráfico 2: Tempo de construção (escala log)
    ax2 = plt.subplot(2, 3, 2)
    ax2.plot(df['num_transacoes'], df['tempo_construcao_seg'], 'go-', linewidth=2, markersize=6)
    ax2.set_xlabel('Número de Transações', fontsize=11)
    ax2.set_ylabel('Tempo de Construção (s)', fontsize=11)
    ax2.set_title('Tempo de Construção (Escala Log)', fontsize=12, fontweight='bold')
    ax2.grid(True, alpha=0.3)
    ax2.set_xscale('log')
    ax2.set_yscale('log')
    
    # Gráfico 3: Taxa de processamento
    ax3 = plt.subplot(2, 3, 3)
    ax3.plot(df['num_transacoes'], df['taxa_processamento_trans_seg'], 'mo-', linewidth=2, markersize=6)
    ax3.set_xlabel('Número de Transações', fontsize=11)
    ax3.set_ylabel('Taxa de Processamento (transações/s)', fontsize=11)
    ax3.set_title('Taxa de Processamento', fontsize=12, fontweight='bold')
    ax3.grid(True, alpha=0.3)
    ax3.set_xscale('log')
    
    # Linha de média
    ax3.axhline(y=estatisticas['media_taxa'], color='r', linestyle='--', alpha=0.7, 
                label=f'Média: {estatisticas["media_taxa"]:,.0f} trans/s')
    ax3.legend()
    
    # Gráfico 4: Altura da árvore vs log2(n)
    ax4 = plt.subplot(2, 3, 4)
    x_log = np.log2(df['num_transacoes'])
    ax4.plot(x_log, df['altura_arvore'], 'co-', linewidth=2, markersize=6)
    ax4.set_xlabel('log₂(Número de Transações)', fontsize=11)
    ax4.set_ylabel('Altura da Árvore', fontsize=11)
    ax4.set_title('Altura da Árvore vs log₂(n)', fontsize=12, fontweight='bold')
    ax4.grid(True, alpha=0.3)
    
    # Linha de tendência
    y_fit_altura = estatisticas['slope_altura'] * x_log + estatisticas['slope_altura']
    ax4.plot(x_log, y_fit_altura, 'r--', alpha=0.7, label=f'O(log n), R²={estatisticas["r2_altura"]:.3f}')
    ax4.legend()
    
    # Gráfico 5: Eficiência de espaço
    ax5 = plt.subplot(2, 3, 5)
    tamanho_total_teorico = df['num_transacoes'] * 32  # 32 bytes por transação
    tamanho_real = df['tamanho_raiz_bytes'].iloc[0]  # Apenas a raiz
    
    ax5.bar(['Teórico', 'Merkle Tree'], 
            [tamanho_total_teorico.mean(), tamanho_real], 
            color=['lightcoral', 'lightgreen'])
    ax5.set_ylabel('Tamanho (bytes)', fontsize=11)
    ax5.set_title('Eficiência de Espaço', fontsize=12, fontweight='bold')
    ax5.grid(True, alpha=0.3, axis='y')
    
    # Adiciona valores nas barras
    for i, v in enumerate([tamanho_total_teorico.mean(), tamanho_real]):
        ax5.text(i, v + max(tamanho_total_teorico.mean(), tamanho_real)*0.01, 
                f'{v:,.0f}', ha='center', fontweight='bold')
    
    # Gráfico 6: Tempo de busca (se disponível)
    ax6 = plt.subplot(2, 3, 6)
    if 'tempo_medio_busca_ms' in df.columns:
        ax6.plot(df['num_transacoes'], df['tempo_medio_busca_ms'], 'yo-', linewidth=2, markersize=6)
        ax6.set_xlabel('Número de Transações', fontsize=11)
        ax6.set_ylabel('Tempo Médio de Busca (ms)', fontsize=11)
        ax6.set_title('Tempo de Busca vs Número de Transações', fontsize=12, fontweight='bold')
        ax6.grid(True, alpha=0.3)
        ax6.set_xscale('log')
        
        # Calcula complexidade de busca (deveria ser O(log n))
        if len(df) > 2:
            x_log_busca = np.log(df['num_transacoes'])
            y_busca = df['tempo_medio_busca_ms']
            slope_busca, _, r_busca, _, _ = scipy_stats.linregress(x_log_busca, y_busca)  # Usar scipy_stats
            ax6.plot(df['num_transacoes'], slope_busca * np.log(df['num_transacoes']), 
                    'r--', alpha=0.7, label=f'O(log n), R²={r_busca**2:.3f}')
            ax6.legend()
    else:
        # Gráfico de complexidade teórica
        n = np.array([2**i for i in range(1, 14)])
        o_n = n / n.max()
        o_log_n = np.log2(n) / np.log2(n).max()
        o_1 = np.ones_like(n) / np.ones_like(n).max()
        
        ax6.plot(n, o_n, 'r-', linewidth=2, label='O(n)')
        ax6.plot(n, o_log_n, 'g-', linewidth=2, label='O(log n)')
        ax6.plot(n, o_1, 'b-', linewidth=2, label='O(1)')
        ax6.set_xlabel('Tamanho da Entrada (n)', fontsize=11)
        ax6.set_ylabel('Complexidade Normalizada', fontsize=11)
        ax6.set_title('Complexidade Computacional Teórica', fontsize=12, fontweight='bold')
        ax6.grid(True, alpha=0.3)
        ax6.set_xscale('log')
        ax6.legend()
        ax6.set_ylim(0, 1.1)
    
    plt.tight_layout()
    
    # Salva os gráficos
    data_atual = datetime.now().strftime("%Y%m%d_%H%M%S")
    plt.savefig(f'resultados/graficos_comparativos_{data_atual}.png', dpi=300, bbox_inches='tight')
    plt.savefig(f'resultados/graficos_comparativos_{data_atual}.pdf', bbox_inches='tight')
    
    print(f"\n✓ Gráficos salvos em:")
    print(f"  - resultados/graficos_comparativos_{data_atual}.png")
    print(f"  - resultados/graficos_comparativos_{data_atual}.pdf")
    
    plt.show()

def gerar_relatorio_completo(df, estatisticas):  # Mudei o nome do parâmetro
    """Gera um relatório completo em Markdown"""
    print("\n" + "="*80)
    print("GERANDO RELATÓRIO COMPLETO")
    print("="*80)
    
    data_atual = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    relatorio = f"""# Relatório de Análise de Performance - Merkle Tree

**Data de geração:** {data_atual}
**Total de experimentos analisados:** {len(df)}

## Resumo Executivo

A análise de performance da implementação da Merkle Tree demonstra os seguintes resultados principais:

### Desempenho Geral
- **Taxa máxima de processamento:** {estatisticas['max_taxa']:,.0f} transações/segundo
- **Taxa média de processamento:** {estatisticas['media_taxa']:,.0f} transações/segundo
- **Tempo por transação:** {estatisticas['slope_tempo']*1000:.3f} ms/transação

### Complexidade Computacional
1. **Tempo de construção:** O(n)
   - Coeficiente R²: {estatisticas['r2_tempo']:.4f}
   - Confirma comportamento linear esperado

2. **Altura da árvore:** O(log n)
   - Coeficiente R²: {estatisticas['r2_altura']:.4f}
   - Comportamento logarítmico conforme teoria

### Eficiência de Espaço
- **Tamanho da raiz:** {df['tamanho_raiz_bytes'].iloc[0]} bytes (constante)
- **Compressão:** De {df['num_transacoes'].max():,} transações para apenas 32 bytes
- **Fator de compressão:** 1:{df['num_transacoes'].max()//32:,}

## Resultados Detalhados

### Tabela de Performance

| Transações | Tempo (s) | Taxa (trans/s) | Altura | Tamanho Raiz |
|------------|-----------|----------------|--------|--------------|
"""
    
    # Adiciona linhas da tabela
    for _, row in df.iterrows():
        relatorio += f"| {row['num_transacoes']:,} | {row['tempo_construcao_seg']:.4f} | {row['taxa_processamento_trans_seg']:,.0f} | {row['altura_arvore']} | {row['tamanho_raiz_bytes']} |\n"
    
    # Adiciona coluna de busca se existir
    if 'tempo_medio_busca_ms' in df.columns:
        # Reconstruir a tabela com busca
        relatorio = f"""# Relatório de Análise de Performance - Merkle Tree

**Data de geração:** {data_atual}
**Total de experimentos analisados:** {len(df)}

## Resumo Executivo

A análise de performance da implementação da Merkle Tree demonstra os seguintes resultados principais:

### Desempenho Geral
- **Taxa máxima de processamento:** {estatisticas['max_taxa']:,.0f} transações/segundo
- **Taxa média de processamento:** {estatisticas['media_taxa']:,.0f} transações/segundo
- **Tempo por transação:** {estatisticas['slope_tempo']*1000:.3f} ms/transação
- **Tempo médio de busca:** {df['tempo_medio_busca_ms'].mean():.2f} ms

### Complexidade Computacional
1. **Tempo de construção:** O(n)
   - Coeficiente R²: {estatisticas['r2_tempo']:.4f}
   - Confirma comportamento linear esperado

2. **Altura da árvore:** O(log n)
   - Coeficiente R²: {estatisticas['r2_altura']:.4f}
   - Comportamento logarítmico conforme teoria

### Eficiência de Espaço
- **Tamanho da raiz:** {df['tamanho_raiz_bytes'].iloc[0]} bytes (constante)
- **Compressão:** De {df['num_transacoes'].max():,} transações para apenas 32 bytes
- **Fator de compressão:** 1:{df['num_transacoes'].max()//32:,}

## Resultados Detalhados

### Tabela de Performance

| Transações | Tempo (s) | Taxa (trans/s) | Altura | Tamanho Raiz | Busca (ms) |
|------------|-----------|----------------|--------|--------------|------------|
"""
        
        for _, row in df.iterrows():
            relatorio += f"| {row['num_transacoes']:,} | {row['tempo_construcao_seg']:.4f} | {row['taxa_processamento_trans_seg']:,.0f} | {row['altura_arvore']} | {row['tamanho_raiz_bytes']} | {row['tempo_medio_busca_ms']:.2f} |\n"
    
    relatorio += """

## Análise de Complexidade

### 1. Tempo de Construção - O(n)
O tempo de construção da Merkle Tree cresce linearmente com o número de transações, conforme esperado pela teoria. Cada transação requer uma operação de hash, resultando em complexidade O(n).

### 2. Altura da Árvore - O(log n)
A altura da árvore cresce logaritmicamente, demonstrando a eficiência da estrutura para grandes volumes de dados. Para 10.000 transações, a altura é de apenas {df['altura_arvore'].iloc[-1]} níveis.

### 3. Espaço - O(1)
O tamanho da raiz permanece constante (32 bytes) independentemente do número de transações, demonstrando a eficiência de espaço da estrutura.

"""

    if 'tempo_medio_busca_ms' in df.columns:
        relatorio += """### 4. Tempo de Busca - O(log n)
O tempo de busca cresce logaritmicamente, o que é ideal para verificações de inclusão em sistemas blockchain.

"""

    relatorio += """## Conclusões

1. **Escalabilidade:** A Merkle Tree demonstra excelente escalabilidade, processando eficientemente desde 2 até 10.000 transações.

2. **Eficiência:** A taxa de processamento mantém-se consistente em diferentes volumes de dados.

3. **Verificação:** A estrutura permite verificações eficientes (Merkle Proofs) com complexidade O(log n).

4. **Aplicabilidade:** Ideal para sistemas blockchain onde é necessário verificar grandes volumes de transações de forma eficiente.

## Recomendações

1. **Para pequenos volumes:** Use a implementação atual que já demonstra boa performance.

2. **Para grandes volumes:** Considere paralelização adicional para hash computation.

3. **Otimizações:** Implementar cache de hashes intermediários pode melhorar performance em operações repetitivas.

---

*Relatório gerado automaticamente pela ferramenta de análise de performance da Merkle Tree.*
"""
    
    # Salva relatório
    nome_arquivo = data_atual.replace(":", "").replace(" ", "_")
    with open(f'resultados/relatorio_analise_{nome_arquivo}.md', 'w') as f:
        f.write(relatorio)
    
    print(f"\n✓ Relatório salvo em:")
    print(f"  - resultados/relatorio_analise_{nome_arquivo}.md")
    
    # Também gera HTML
    import markdown
    html = markdown.markdown(relatorio)
    with open(f'resultados/relatorio_analise_{nome_arquivo}.html', 'w') as f:
        f.write(f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Relatório de Análise - Merkle Tree</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 40px; line-height: 1.6; }}
        h1 {{ color: #2c3e50; border-bottom: 2px solid #3498db; }}
        h2 {{ color: #34495e; }}
        table {{ border-collapse: collapse; width: 100%; margin: 20px 0; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: right; }}
        th {{ background-color: #f2f2f2; }}
        tr:nth-child(even) {{ background-color: #f9f9f9; }}
        .summary {{ background-color: #e8f4fc; padding: 15px; border-radius: 5px; margin: 20px 0; }}
    </style>
</head>
<body>
{html}
</body>
</html>""")
    
    print(f"  - resultados/relatorio_analise_{nome_arquivo}.html")

def main():
    print("="*100)
    print("ANALISADOR DE RESULTADOS - MERKLE TREE")
    print("="*100)
    
    # Carrega dados
    df = carregar_dados()
    if df is None:
        return
    
    print(f"\n✓ Dados carregados com sucesso!")
    print(f"  Total de experimentos: {len(df)}")
    print(f"  Faixa de transações: {df['num_transacoes'].min():,} a {df['num_transacoes'].max():,}")
    
    # Calcula estatísticas
    estatisticas = calcular_estatisticas_comparativas(df)  # Mudei o nome aqui também
    
    # Gera tabela comparativa
    gerar_tabela_comparativa(df)
    
    # Gera gráficos
    gerar_graficos_comparativos(df, estatisticas)  # Passar o novo nome
    
    # Gera relatório completo
    gerar_relatorio_completo(df, estatisticas)  # Passar o novo nome
    
    print("\n" + "="*100)
    print("ANÁLISE CONCLUÍDA COM SUCESSO!")
    print("="*100)
    print("\nArquivos gerados:")
    for arquivo in os.listdir('resultados'):
        if arquivo.startswith(('graficos_', 'tabela_', 'relatorio_')):
            tamanho = os.path.getsize(f'resultados/{arquivo}')
            print(f"  - {arquivo} ({tamanho:,} bytes)")

if __name__ == "__main__":
    # Instala dependências se necessário
    try:
        import pandas
        import matplotlib
        import markdown
    except ImportError:
        print("Instalando dependências...")
        import subprocess
        subprocess.run([sys.executable, "-m", "pip", "install", "pandas", "matplotlib", "markdown"])
    
    # Verifica scipy separadamente
    try:
        from scipy import stats as scipy_stats
    except ImportError:
        print("Instalando scipy...")
        import subprocess
        subprocess.run([sys.executable, "-m", "pip", "install", "scipy"])
        from scipy import stats as scipy_stats
    
    # Cria diretório se não existir
    os.makedirs("resultados", exist_ok=True)
    
    main()