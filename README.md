# Blockchain e Análise de Merkle Tree em Python

Este projeto é uma implementação de Blockchain em Python focando no grafo por trás (Merkle Tree). O projeto inclui um módulo de análise de performance para validar a eficiência teórica da Merkle Tree.

## Funcionalidades Principais

- **Árvore de Merkle**: Implementação completa para verificação eficiente e segura de transações.
- **Análise de Performance**: Scripts para gerar gráficos comparativos (Tempo de Construção, Altura da Árvore, Taxa de Processamento).
- **Processamento Concorrente**: Uso de threads para simular múltiplas transações ocorrendo simultaneamente.
- **Hash Duplo SHA-256**: Seguindo o padrão do Bitcoin para maior segurança.

## Características Técnicas

### Árvore de Merkle
- Construção recursiva da árvore de hash.
- Busca eficiente de transações ($O(\log n)$).
- Geração de provas de inclusão.
- Hash duplo (SHA-256 duas vezes) como no Bitcoin.

### Sistema de Transações
- Processamento concorrente com threads.
- Mecanismos de lock para segurança das transações.
- Leitura de transações a partir de arquivo de texto.
- Validação de presença na árvore.

### Como funciona

Esse experimento é uma implementação de uma Merkle Tree em python, o script em shell 'experimentos.sh' executa o código 'blockchain.py' em configurações diferentes variando o número de transações usadas para formar a árvore. Como o objetivo era focar mais no grafo por trás do que no blockchain em si essa foi o foco dos experimentos, o número de transações foi variado de 2 até 8192 nas potências de 2 (2,4,8,..,8192) e depois foi para 10000. Foram usadas sempre 8 threads para simular diferentes transações chegando, as transações foram geradas usando geradores online de strings. O arquivo 'graficos.py' serve para fazer a análise dos csv's gerados pelo 'blockchain.py', esses arquivos são formados com o tempo para formar a árvore em si, tempo de busca médio, altura da árvore e etc.

## Como Usar

### Pré-requisitos

É necessário ter o **Python 3.6+** instalado.

Para rodar todo o código (incluindo a geração dos gráficos), você precisará da biblioteca `matplotlib`. Instale as dependências com o comando:

```bash
pip install matplotlib
``` 

Execute então os comandos:

```bash
chmod +x experimentos.sh
``` 

Isso torna o script executável que faz automaticamente todos os experimentos de uma vez.

```bash
./experimentos.sh
```

```bash
python3 analise_performance.py
``` 

Responsável por fazer as tabelas e gráficos usados no relatório.