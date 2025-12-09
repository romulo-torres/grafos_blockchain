import hashlib  # para poder usar o sha-256
import os # para abrir arquivos
import threading # para simular várias operações vindo em tempos diferentes
import random
import sys
import time
import csv
from datetime import datetime

# lock para acessar e salvar as transações feitas
lock_feitas = threading.Lock()

# lock para acessar e salvar as transações não feitas
lock_nao_feitas = threading.Lock()


def sha_256(dados):
    if isinstance(dados, str):
        dados = dados.encode('utf-8')
    return hashlib.sha256(dados).hexdigest()

class No:
    def __init__(self, valor_hash, esq=None, dir=None):
        self.hash = valor_hash
        self.esq = esq
        self.dir = dir

class Merkle_tree:
    def __init__(self,nome_arquivo, num_threads=4,transacoes_por_thread=None):
        self.folhas = []
        self.raiz = None
        self.num_threads=num_threads
        self.transacoes_por_thread=transacoes_por_thread
        self.tempo_construcao=0
        self.transacoes_originais = []  # Para armazenar as transações originais
        self.transacoes_selecionadas = []  # Transações realmente selecionadas para a árvore
        self.estatisticas = {}  # Dicionário para armazenar estatísticas
        self.tempos_busca = []  # Lista para armazenar tempos de busca
        self.nome_arquivo = nome_arquivo

        if not os.path.exists(nome_arquivo):
            print(f"Erro: Arquivo '{nome_arquivo}' não encontrado!")
            return

        transacoes_nao_feitas = self.leitura_arquivo(nome_arquivo)
        if not transacoes_nao_feitas:
            print("Problema na leitura das transacoes")
            return

        total_transacoes = len(transacoes_nao_feitas)
        print(f"Total de transações no arquivo: {total_transacoes}")

        # Salva todas as transações originais
        self.transacoes_originais = transacoes_nao_feitas.copy()
        
        # Seleciona transações aleatórias para processamento
        if self.transacoes_por_thread and self.transacoes_por_thread < total_transacoes:
            # Seleciona transações aleatórias
            self.transacoes_selecionadas = random.sample(transacoes_nao_feitas, self.transacoes_por_thread)
            print(f"Selecionadas {self.transacoes_por_thread} transações aleatoriamente")
        else:
            # Usa todas as transações
            self.transacoes_selecionadas = transacoes_nao_feitas.copy()
            print(f"Processando todas as {len(self.transacoes_selecionadas)} transações")
        
        # Cria cópia para processamento em threads
        transacoes_para_processar = self.transacoes_selecionadas.copy()
        
        inicio = time.time()
        print(f"\nIniciando o processo de criar as folhas com {self.num_threads} threads")
        threads = []

        for i in range(self.num_threads):
            t = threading.Thread(target=self.salva_transacao, args=(transacoes_para_processar,))
            t.start()
            threads.append(t)
        
        for t in threads:
            t.join()
        
        print(f"Folhas criadas: {len(self.folhas)}")
        print("Terminou o processo de criar as folhas")

        if not self.folhas:
            print("Problema ao criar as folhas")
            return

        print("Iniciando o processo de montar a árvore com o hash dos filhos e vizinhos")
        self.raiz = self.monta_tudo(self.folhas)
        fim = time.time()
        self.tempo_construcao = fim - inicio 
        
        print("Terminou o processo de montar a árvore com o hash dos filhos e vizinhos")
        print(f"Tempo total de construção: {self.tempo_construcao:.4f} segundos")
        
        # Calcula estatísticas
        altura = self.calcular_altura(self.raiz)
        print(f"Altura da árvore: {altura}")
        print(f"Raiz da árvore: {self.raiz.hash[:32]}...")
        
        # Armazena estatísticas
        self.estatisticas = {
            'nome_arquivo': nome_arquivo,
            'data_execucao': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'total_transacoes_arquivo': total_transacoes,
            'transacoes_processadas': len(self.transacoes_selecionadas),
            'num_threads': num_threads,
            'folhas_criadas': len(self.folhas),
            'altura_arvore': altura,
            'tempo_construcao': self.tempo_construcao,
            'taxa_processamento': len(self.folhas) / self.tempo_construcao if self.tempo_construcao > 0 else 0,
            'tamanho_raiz_bytes': len(self.raiz.hash) // 2 if self.raiz else 0,
            'hash_raiz': self.raiz.hash[:32] + '...' if self.raiz else '',
        }

    def calcular_altura(self, no):
        if no is None:
            return 0
        return 1 + max(self.calcular_altura(no.esq), self.calcular_altura(no.dir))
        
    def leitura_arquivo(self,nome_arquivo):
        transacoes_nao_feitas = []

        if not os.path.exists(nome_arquivo):
            print("Erro ao abrir o arquivo")
            return transacoes_nao_feitas

        with open(nome_arquivo, "r", encoding="utf-8") as f:
            for linha in f:
                dado = linha.strip()
                if dado:
                    transacoes_nao_feitas.append(dado)
        
        return transacoes_nao_feitas

    # funcao que irá ser chamada por todas as threads para criar todas as folhas
    def salva_transacao(self, transacoes_para_processar):
        contador = 0
        thread_id = threading.get_ident()  # Obtém ID único da thread
        
        while True:
            with lock_nao_feitas:
                if not transacoes_para_processar:
                    break
                transacao = random.choice(transacoes_para_processar)
                transacoes_para_processar.remove(transacao)
            
            # nesse caso na hora de salvar a folha será aplicada duas vezes a funcao de hash sha-256 isso é feito no bitcoin pois
            # serve para proteção contra ataques e é uma herança do hashcash
            dado_hash = sha_256(sha_256(transacao))

            with lock_feitas:
                self.folhas.append(No(valor_hash=dado_hash))
                contador += 1
                
                # Mostra progresso a cada 500 transações (para não poluir muito)
                if contador % 500 == 0:
                    print(f"Thread {thread_id % 1000}: Processadas {contador} transações")
        
        print(f"Thread {thread_id % 1000} finalizou: processou {contador} transações")

    def monta_tudo(self, nos):
        if not nos:
            return None

        if len(nos) == 1:
            return nos[0]
        
        altura_atual = []
        for i in range(0, len(nos), 2):
            esq = nos[i]
            if i+1 < len(nos):
                dir = nos[i+1]
            else:
                dir = nos[i]

            pai = sha_256(sha_256(esq.hash + dir.hash))
            altura_atual.append(No(pai, esq, dir))

        return self.monta_tudo(altura_atual)
    
    def busca_transacao(self, transacao):
        # para buscar uma transação
        if not self.raiz:
            print("Árvore não foi construída!")
            return None
        
        # Calcula o hash da transação (mesmo processo usado na criação)
        hash_procurado = sha_256(sha_256(transacao))
        
        inicio = time.time()
        resultado = self._busca_no(self.raiz, hash_procurado)
        fim = time.time()
        
        tempo_busca = fim - inicio
        self.tempos_busca.append(tempo_busca)  # Armazena tempo de busca
        
        if resultado:
            print(f"✓ Transação encontrada na árvore")
            print(f"  Tempo de busca: {tempo_busca*1000:.2f} ms")
            return resultado, tempo_busca
        else:
            print(f"✗ Transação não encontrada na árvore")
            print(f"  Tempo de busca: {tempo_busca*1000:.2f} ms")
            return None, tempo_busca
    
    def _busca_no(self, no, hash_procura):
        # buscar um no pelo hash
        if no is None:
            return None
        
        # verifica se esse nó é o procurado
        if no.hash == hash_procura:
            return no
        
        # senão busca nos filhos
        achou_esq = self._busca_no(no.esq, hash_procura)
        if achou_esq:
            return achou_esq
        
        return self._busca_no(no.dir, hash_procura)
    
    def buscar_transacao_aleatoria(self):
        """Busca uma transação aleatória da lista de transações selecionadas"""
        if not self.transacoes_selecionadas:
            print("Nenhuma transação selecionada para busca!")
            return None, 0
        
        # Seleciona uma transação aleatória
        transacao_aleatoria = random.choice(self.transacoes_selecionadas)
        print(f"\nBuscando transação aleatória: {transacao_aleatoria[:50]}...")
        
        resultado, tempo = self.busca_transacao(transacao_aleatoria)
        return resultado, tempo
    
    def gerar_prova_inclusao(self, transacao):
        # gera a prova de inclusão
        if not self.raiz:
            print("Árvore não foi construída!")
            return None
        
        hash_transacao = sha_256(sha_256(transacao))
        caminho = []
        
        inicio = time.time()
        if self._encontrar_caminho(self.raiz, hash_transacao, caminho):
            fim = time.time()
            tempo_geracao = fim - inicio
            
            print(f"\n=== Prova de inclusão para: {transacao[:50]}... ===")
            print(f"Hash da transação: {hash_transacao[:32]}...")
            print(f"Tempo de geração da prova: {tempo_geracao*1000:.2f} ms")
            print(f"Elementos na prova: {len(caminho)}")
            print("\nCaminho até a raiz:")
            
            for i, (hash_irmao, direcao) in enumerate(caminho):
                print(f"  Nível {i+1}: {direcao} -> {hash_irmao[:16]}...")
            
            print(f"\nHash raiz: {self.raiz.hash[:32]}...")
            
            # Verifica a prova
            if self.verificar_prova(transacao, caminho):
                print("✓ Prova verificada com sucesso!")
            else:
                print("✗ Falha na verificação da prova!")
            
            return caminho
        else:
            print("Transação não encontrada para gerar prova")
            return None
    
    # encontra o caminho da folha até a raiz para uma transação
    def _encontrar_caminho(self, no, hash_procura, caminho):
        
        if no is None:
            return False
        
        # se encontrou o nó com o hash procurado
        if no.hash == hash_procura:
            return True
        
        # procura no filho esquerdo
        if self._encontrar_caminho(no.esq, hash_procura, caminho):
            # adiciona o hash do irmão direito (se existir)
            if no.dir:
                caminho.append((no.dir.hash, "direita"))
            else:
                # se não tem irmão direito, duplica o hash do filho esquerdo
                caminho.append((no.esq.hash, "direita"))
            return True
        
        # procura no filho direito
        if self._encontrar_caminho(no.dir, hash_procura, caminho):
            # adiciona o hash do irmão esquerdo (se existir)
            if no.esq:
                caminho.append((no.esq.hash, "esquerda"))
            else:
                # se não tem irmão esquerdo, duplica o hash do filho direito
                caminho.append((no.dir.hash, "esquerda"))
            return True
        
        return False
    
    # verifica se a prova de inclusão é válida
    def verificar_prova(self, transacao, caminho):
        
        current_hash = sha_256(sha_256(transacao))
        
        # percorre o caminho da folha até a raiz
        for hash_irmao, direcao in caminho:
            if direcao == "esquerda":
                # o irmão está à esquerda: hash_irmao + current_hash
                current_hash = sha_256(sha_256(hash_irmao + current_hash))
            else:  # "direita"
                # o irmão está à direita: current_hash + hash_irmao
                current_hash = sha_256(sha_256(current_hash + hash_irmao))
        
        return current_hash == self.raiz.hash
    
    # mostra estatísticas da árvore
    def mostrar_estatisticas(self):
        print("\n" + "="*60)
        print("ESTATÍSTICAS DA MERKLE TREE")
        print("="*60)
        
        print(f"Arquivo de origem: {self.estatisticas.get('nome_arquivo', 'N/A')}")
        print(f"Data de execução: {self.estatisticas.get('data_execucao', 'N/A')}")
        print(f"Total de transações no arquivo: {self.estatisticas.get('total_transacoes_arquivo', 0):,}")
        print(f"Transações processadas: {self.estatisticas.get('transacoes_processadas', 0):,}")
        print(f"Número de threads: {self.estatisticas.get('num_threads', 0)}")
        print(f"Folhas criadas: {self.estatisticas.get('folhas_criadas', 0):,}")
        print(f"Altura da árvore: {self.estatisticas.get('altura_arvore', 0)}")
        print(f"Tempo de construção: {self.estatisticas.get('tempo_construcao', 0):.4f} segundos")
        print(f"Taxa de processamento: {self.estatisticas.get('taxa_processamento', 0):.1f} transações/segundo")
        print(f"Tamanho da raiz: {self.estatisticas.get('tamanho_raiz_bytes', 0)} bytes")
        print(f"Hash raiz: {self.estatisticas.get('hash_raiz', 'N/A')}")
        
        # Estatísticas de busca
        if self.tempos_busca:
            tempo_medio_busca = sum(self.tempos_busca) / len(self.tempos_busca)
            print(f"\nESTATÍSTICAS DE BUSCA:")
            print(f"  Total de buscas realizadas: {len(self.tempos_busca)}")
            print(f"  Tempo médio de busca: {tempo_medio_busca*1000:.2f} ms")
            print(f"  Buscas por segundo: {1/tempo_medio_busca:.0f}")
            print(f"  Tempo mínimo de busca: {min(self.tempos_busca)*1000:.2f} ms")
            print(f"  Tempo máximo de busca: {max(self.tempos_busca)*1000:.2f} ms")
        else:
            print(f"\nESTATÍSTICAS DE BUSCA: Nenhuma busca realizada ainda")
    
    # testa performance de busca com transações reais
    def testar_performance_busca(self):
        if not self.transacoes_selecionadas:
            print("Nenhuma transação selecionada para teste!")
            return
        
        print("\n" + "="*60)
        print("TESTE DE PERFORMANCE - BUSCA")
        print("="*60)
        
        num_testes = min(20, len(self.transacoes_selecionadas))
        tempos_busca = []
        
        print(f"Realizando {num_testes} buscas aleatórias...")
        
        for i in range(num_testes):
            transacao_teste = random.choice(self.transacoes_selecionadas)
            print(f"  Teste {i+1}/{num_testes}: {transacao_teste[:30]}...")
            
            inicio = time.time()
            resultado = self._busca_no(self.raiz, sha_256(sha_256(transacao_teste)))
            fim = time.time()
            
            if resultado:
                tempos_busca.append(fim - inicio)
        
        if tempos_busca:
            tempo_medio = sum(tempos_busca) / len(tempos_busca)
            print(f"\nRESULTADOS DO TESTE DE PERFORMANCE:")
            print(f"  Buscas realizadas: {len(tempos_busca)}")
            print(f"  Buscas bem-sucedidas: {len(tempos_busca)}")
            print(f"  Tempo médio de busca: {tempo_medio*1000:.2f} ms")
            print(f"  Tempo mínimo de busca: {min(tempos_busca)*1000:.2f} ms")
            print(f"  Tempo máximo de busca: {max(tempos_busca)*1000:.2f} ms")
            print(f"  Buscas por segundo: {1/tempo_medio:.0f}")
            
            # Adiciona ao histórico de tempos de busca
            self.tempos_busca.extend(tempos_busca)
        else:
            print("Nenhuma busca bem-sucedida para calcular estatísticas.")
    
    def salvar_estatisticas_csv(self, nome_arquivo="estatisticas_merkle.csv"):
        """Salva as estatísticas em um arquivo CSV"""
        try:
            # Determina se o arquivo já existe para adicionar cabeçalho
            arquivo_existe = os.path.exists(nome_arquivo)
            
            with open(nome_arquivo, 'a', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                
                # Escreve cabeçalho se o arquivo não existe
                if not arquivo_existe:
                    writer.writerow([
                        'data_execucao',
                        'nome_arquivo',
                        'total_transacoes_arquivo',
                        'transacoes_processadas',
                        'num_threads',
                        'folhas_criadas',
                        'altura_arvore',
                        'tempo_construcao_seg',
                        'taxa_processamento_trans_seg',
                        'tamanho_raiz_bytes',
                        'hash_raiz_32chars',
                        'total_buscas_realizadas',
                        'tempo_medio_busca_ms',
                        'tempo_min_busca_ms',
                        'tempo_max_busca_ms',
                        'buscas_por_segundo'
                    ])
                
                # Calcula estatísticas de busca
                if self.tempos_busca:
                    tempo_medio_busca = sum(self.tempos_busca) / len(self.tempos_busca) * 1000
                    tempo_min_busca = min(self.tempos_busca) * 1000
                    tempo_max_busca = max(self.tempos_busca) * 1000
                    buscas_por_segundo = 1 / (tempo_medio_busca / 1000) if tempo_medio_busca > 0 else 0
                else:
                    tempo_medio_busca = 0
                    tempo_min_busca = 0
                    tempo_max_busca = 0
                    buscas_por_segundo = 0
                
                # Escreve linha de dados
                writer.writerow([
                    self.estatisticas.get('data_execucao', ''),
                    self.estatisticas.get('nome_arquivo', ''),
                    self.estatisticas.get('total_transacoes_arquivo', 0),
                    self.estatisticas.get('transacoes_processadas', 0),
                    self.estatisticas.get('num_threads', 0),
                    self.estatisticas.get('folhas_criadas', 0),
                    self.estatisticas.get('altura_arvore', 0),
                    round(self.estatisticas.get('tempo_construcao', 0), 4),
                    round(self.estatisticas.get('taxa_processamento', 0), 1),
                    self.estatisticas.get('tamanho_raiz_bytes', 0),
                    self.estatisticas.get('hash_raiz', ''),
                    len(self.tempos_busca),
                    round(tempo_medio_busca, 2),
                    round(tempo_min_busca, 2),
                    round(tempo_max_busca, 2),
                    round(buscas_por_segundo, 0)
                ])
            
            print(f"\n✓ Estatísticas salvas em CSV: {nome_arquivo}")
            
            # Também salva os tempos de busca individuais em um arquivo separado
            if self.tempos_busca:
                nome_arquivo_tempos = nome_arquivo.replace('.csv', '_tempos_busca.csv')
                with open(nome_arquivo_tempos, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    writer.writerow(['numero_busca', 'tempo_busca_ms'])
                    for i, tempo in enumerate(self.tempos_busca):
                        writer.writerow([i+1, round(tempo*1000, 3)])
                print(f"✓ Tempos de busca individuais salvos em: {nome_arquivo_tempos}")
            
            return True
            
        except Exception as e:
            print(f"✗ Erro ao salvar estatísticas CSV: {e}")
            return False
    
    def salvar_transacoes_selecionadas_csv(self, nome_arquivo="transacoes_selecionadas.csv"):
        """Salva as transações selecionadas em um arquivo CSV"""
        try:
            with open(nome_arquivo, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(['indice', 'transacao'])
                for i, transacao in enumerate(self.transacoes_selecionadas):
                    writer.writerow([i+1, transacao])
            
            print(f"\n✓ Transações selecionadas salvas em CSV: {nome_arquivo}")
            return True
            
        except Exception as e:
            print(f"✗ Erro ao salvar transações selecionadas: {e}")
            return False
    
    def mostrar_transacoes_selecionadas(self, limite=10):
        """Mostra as transações selecionadas para a árvore"""
        if not self.transacoes_selecionadas:
            print("Nenhuma transação selecionada!")
            return
        
        print(f"\n" + "="*60)
        print(f"TRANSAÇÕES SELECIONADAS PARA A ÁRVORE")
        print(f"Total: {len(self.transacoes_selecionadas):,} transações")
        print("="*60)
        
        if len(self.transacoes_selecionadas) <= limite:
            mostrar = self.transacoes_selecionadas
        else:
            mostrar = self.transacoes_selecionadas[:limite]
            print(f"(Mostrando apenas as primeiras {limite} transações)")
        
        for i, transacao in enumerate(mostrar):
            print(f"{i+1:3}. {transacao}")
        
        if len(self.transacoes_selecionadas) > limite:
            print(f"... e mais {len(self.transacoes_selecionadas) - limite} transações")

# parte principal
def main():
    print("="*70)
    print("IMPLEMENTAÇÃO DE MERKLE TREE PARA BLOCKCHAIN")
    print("="*70)
    print("Sistema de análise de performance com estatísticas em CSV")
    print("="*70)
    
    # Verifica argumentos da linha de comando
    if len(sys.argv) > 1:
        nome_arquivo = sys.argv[1]
        num_threads = int(sys.argv[2]) if len(sys.argv) > 2 else 4
        num_transacoes = int(sys.argv[3]) if len(sys.argv) > 3 else 10000
    else:
        # Interface interativa
        print("\nConfiguração da Merkle Tree:")
        nome_arquivo = input("Nome do arquivo de transações (padrão: transacoes.txt): ").strip()
        if not nome_arquivo:
            nome_arquivo = "transacoes.txt"
        
        num_threads = input("Número de threads para processamento (padrão: 4): ").strip()
        num_threads = int(num_threads) if num_threads else 4
        
        num_transacoes = input("Número de transações a processar (padrão: 10000): ").strip()
        num_transacoes = int(num_transacoes) if num_transacoes else 10000
    
    print(f"\n" + "="*60)
    print("PARÂMETROS DE EXECUÇÃO:")
    print(f"Arquivo: {nome_arquivo}")
    print(f"Threads: {num_threads}")
    print(f"Transações a processar: {num_transacoes}")
    print("="*60)
    
    try:
        # Cria a Merkle Tree
        print("\nIniciando construção da Merkle Tree...")
        inicio_total = time.time()
        merkle_tree = Merkle_tree(
            nome_arquivo=nome_arquivo,
            num_threads=num_threads,
            transacoes_por_thread=num_transacoes
        )
        fim_total = time.time()
        
        if merkle_tree.raiz:
            print(f"\n" + "="*60)
            print(f"CONSTRUÇÃO CONCLUÍDA!")
            print(f"Tempo total de execução: {fim_total - inicio_total:.4f} segundos")
            print("="*60)
            
            # Menu interativo
            while True:
                print("\n" + "="*60)
                print("MENU PRINCIPAL")
                print("="*60)
                print("1. Buscar transação específica")
                print("2. Buscar transação aleatória")
                print("3. Gerar prova de inclusão")
                print("4. Mostrar estatísticas completas")
                print("5. Testar performance de busca")
                print("6. Mostrar transações selecionadas")
                print("7. Salvar estatísticas em CSV")
                print("8. Salvar transações selecionadas em CSV")
                print("9. Sair")
                print("="*60)
                
                try:
                    resposta = int(input("\nEscolha uma opção (1-9): "))
                except ValueError:
                    print("Opção inválida! Digite um número de 1 a 9.")
                    continue
                
                if resposta == 1:
                    print("\n" + "-"*60)
                    print("BUSCA DE TRANSAÇÃO ESPECÍFICA")
                    print("-"*60)
                    print("Exemplo de transação disponível:")
                    if merkle_tree.transacoes_selecionadas and len(merkle_tree.transacoes_selecionadas) > 0:
                        print(f"  {merkle_tree.transacoes_selecionadas[0][:50]}...")
                    
                    transacao = input("\nDigite a transação completa que deseja buscar: ").strip()
                    if transacao:
                        merkle_tree.busca_transacao(transacao)
                    else:
                        print("Transação não pode estar vazia!")
                
                elif resposta == 2:
                    print("\n" + "-"*60)
                    print("BUSCA DE TRANSAÇÃO ALEATÓRIA")
                    print("-"*60)
                    resultado, tempo = merkle_tree.buscar_transacao_aleatoria()
                    if resultado:
                        print(f"\n✓ Busca aleatória concluída em {tempo*1000:.2f} ms")
                    else:
                        print("\n✗ Transação não encontrada")
                
                elif resposta == 3:
                    print("\n" + "-"*60)
                    print("GERAÇÃO DE PROVA DE INCLUSÃO")
                    print("-"*60)
                    print("Exemplo de transação disponível:")
                    if merkle_tree.transacoes_selecionadas and len(merkle_tree.transacoes_selecionadas) > 0:
                        print(f"  {merkle_tree.transacoes_selecionadas[0][:50]}...")
                    
                    transacao = input("\nDigite a transação para gerar prova de inclusão: ").strip()
                    if transacao:
                        merkle_tree.gerar_prova_inclusao(transacao)
                    else:
                        print("Transação não pode estar vazia!")
                
                elif resposta == 4:
                    merkle_tree.mostrar_estatisticas()
                
                elif resposta == 5:
                    merkle_tree.testar_performance_busca()
                
                elif resposta == 6:
                    limite = input("Quantas transações mostrar (padrão: 10): ").strip()
                    limite = int(limite) if limite else 10
                    merkle_tree.mostrar_transacoes_selecionadas(limite)
                
                elif resposta == 7:
                    nome_arquivo_saida = input("Nome do arquivo CSV (padrão: estatisticas_merkle.csv): ").strip()
                    if not nome_arquivo_saida:
                        nome_arquivo_saida = "estatisticas_merkle.csv"
                    merkle_tree.salvar_estatisticas_csv(nome_arquivo_saida)
                
                elif resposta == 8:
                    nome_arquivo_saida = input("Nome do arquivo CSV (padrão: transacoes_selecionadas.csv): ").strip()
                    if not nome_arquivo_saida:
                        nome_arquivo_saida = "transacoes_selecionadas.csv"
                    merkle_tree.salvar_transacoes_selecionadas_csv(nome_arquivo_saida)
                
                elif resposta == 9:
                    print("\n" + "="*60)
                    print("PROGRAMA FINALIZADO")
                    print("="*60)
                    
                    # Pergunta se quer salvar antes de sair
                    salvar = input("\nDeseja salvar as estatísticas antes de sair? (s/n): ").strip().lower()
                    if salvar == 's':
                        merkle_tree.salvar_estatisticas_csv()
                    
                    # Mostra resumo final
                    if merkle_tree.tempos_busca:
                        tempo_medio = sum(merkle_tree.tempos_busca) / len(merkle_tree.tempos_busca)
                        print(f"\nRESUMO FINAL:")
                        print(f"  Total de buscas realizadas: {len(merkle_tree.tempos_busca)}")
                        print(f"  Tempo médio de busca: {tempo_medio*1000:.2f} ms")
                    
                    break
                
                else:
                    print("Opção inválida! Digite um número de 1 a 9.")
        
    except FileNotFoundError:
        print(f"\nERRO: Arquivo '{nome_arquivo}' não encontrado!")
        print("Verifique se o arquivo existe no diretório atual.")
    except ValueError as e:
        print(f"\nERRO: Valor inválido: {e}")
    except Exception as e:
        print(f"\nERRO durante a execução: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()

def executar_experimento_automatico(nome_arquivo, num_threads, num_transacoes, prefixo_saida="resultados"):
    """Executa um experimento automaticamente sem interação do usuário"""
    import os
    
    # Cria diretório de resultados se não existir
    os.makedirs(prefixo_saida, exist_ok=True)
    
    print(f"\n{'='*60}")
    print(f"EXPERIMENTO AUTOMÁTICO: {num_transacoes} transações")
    print(f"{'='*60}")
    
    # Cria a Merkle Tree
    inicio_total = time.time()
    merkle_tree = Merkle_tree(
        nome_arquivo=nome_arquivo,
        num_threads=num_threads,
        transacoes_por_thread=num_transacoes
    )
    fim_total = time.time()
    
    if not merkle_tree.raiz:
        print("ERRO: Falha na construção da árvore!")
        return False
    
    print(f"\n✓ Árvore construída em {fim_total - inicio_total:.4f} segundos")
    
    # Nomes dos arquivos de saída
    csv_estatisticas = f"{prefixo_saida}/estatisticas_merkle_{num_transacoes}.csv"
    csv_transacoes = f"{prefixo_saida}/transacoes_{num_transacoes}.csv"
    
    # Realiza algumas buscas para coletar estatísticas
    print("\nRealizando buscas de teste...")
    tempos_testes = []
    for i in range(min(5, len(merkle_tree.transacoes_selecionadas))):
        if merkle_tree.transacoes_selecionadas:
            transacao = merkle_tree.transacoes_selecionadas[i]
            resultado, tempo = merkle_tree.busca_transacao(transacao)
            if resultado:
                tempos_testes.append(tempo)
    
    # Salva estatísticas
    print(f"\nSalvando estatísticas em: {csv_estatisticas}")
    sucesso1 = merkle_tree.salvar_estatisticas_csv(csv_estatisticas)
    
    # Salva transações selecionadas
    print(f"Salvando transações em: {csv_transacoes}")
    sucesso2 = merkle_tree.salvar_transacoes_selecionadas_csv(csv_transacoes)
    
    if sucesso1 and sucesso2:
        print(f"\n✓ Experimento com {num_transacoes} transações concluído com sucesso!")
        return True
    else:
        print(f"\n✗ Erro ao salvar arquivos para {num_transacoes} transações")
        return False


def executar_todos_experimentos():
    """Executa todos os experimentos automaticamente"""
    print(f"{'='*70}")
    print("EXECUTANDO TODOS OS EXPERIMENTOS DE MERKLE TREE")
    print(f"{'='*70}")
    
    nome_arquivo = "transacoes.txt"
    num_threads = 4
    
    # Verifica se o arquivo existe
    if not os.path.exists(nome_arquivo):
        print(f"ERRO: Arquivo '{nome_arquivo}' não encontrado!")
        return
    
    # Lista de números de transações para testar
    numeros_transacoes = [2, 4, 8, 16, 32, 64, 128, 256, 512, 1024, 2048, 4096, 8192, 10000]
    
    resultados = []
    
    for n in numeros_transacoes:
        sucesso = executar_experimento_automatico(
            nome_arquivo=nome_arquivo,
            num_threads=num_threads,
            num_transacoes=n,
            prefixo_saida="resultados"
        )
        resultados.append((n, sucesso))
        
        # Pequena pausa entre experimentos
        time.sleep(1)
    
    # Resumo
    print(f"\n{'='*70}")
    print("RESUMO DOS EXPERIMENTOS")
    print(f"{'='*70}")
    
    sucessos = sum(1 for _, s in resultados if s)
    total = len(resultados)
    
    print(f"Experimentos concluídos: {sucessos}/{total}")
    
    for n, sucesso in resultados:
        status = "✓" if sucesso else "✗"
        print(f"  {status} {n:5} transações")
    
    print(f"\nArquivos salvos no diretório: resultados/")
    if os.path.exists("resultados"):
        arquivos = os.listdir("resultados")
        print(f"Total de arquivos: {len(arquivos)}")
        for arquivo in sorted(arquivos)[:10]:  # Mostra os primeiros 10
            print(f"  - {arquivo}")

if __name__ == "__main__":
    # Verifica se deve executar todos os experimentos
    if len(sys.argv) > 1 and sys.argv[1] == "--todos-experimentos":
        executar_todos_experimentos()
    elif len(sys.argv) > 1:
        # Modo normal com argumentos
        main()
    else:
        # Modo interativo sem argumentos
        main()