# Blockchain em Python

Este projeto é uma implementação educacional de Blockchain em Python, focando nos conceitos fundamentais de criptografia e estrutura de dados distribuídos. Não foi implementado um servidor de timestamp nem a conexão 2P2 em si, houve uma tentativa de simular com o uso de threads.

## Funcionalidades Principais

- **Árvore de Merkle**: Implementação completa para verificação eficiente e segura de transações
- **Provas de Trabalho (Proof of Work)**: Mecanismo de consenso para validação de blocos
- **Processamento Concorrente**: Uso de threads para simular múltiplas transações ocorrendo simultaneamente
- **Hash Duplo SHA-256**: Seguindo o padrão do Bitcoin para maior segurança

## Características Técnicas

### Árvore de Merkle
- Construção recursiva da árvore de hash
- Busca eficiente de transações
- Geração de provas de inclusão
- Hash duplo (SHA-256 duas vezes) como no Bitcoin

### Sistema de Transações
- Processamento concorrente com threads
- Mecanismos de lock para segurança das transações
- Leitura de transações a partir de arquivo
- Validação de presença na árvore

## Como Usar

### Pré-requisitos
- Python 3.6+
- Nenhuma dependência externa necessária

### Execução
(garanta que o arquivo de teste fique no mesmo reposiório ou então dê o caminho absoluto)
```bash
python3 blockchain.py
