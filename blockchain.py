import hashlib  # para poder usar o sha-256
import os # para abrir arquivos
import threading # para simular várias operações vindo em tempos diferentes
import random

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
    def __init__(self,nome_arquivo):
        self.folhas = []
        self.raiz = None

        if not os.path.exists(nome_arquivo):
            print(f"Erro: Arquivo '{nome_arquivo}' não encontrado!")
            return

        transacoes_nao_feitas = self.leitura_arquivo(nome_arquivo)

        if not transacoes_nao_feitas:
            print("Problema na leitura das transacoes")
            return

        print("Iniciando o processo de criar as folhas")

        threads = []

        for i in range(8):
            t = threading.Thread(target=self.salva_transacao,args=(transacoes_nao_feitas,))
            t.start()
            threads.append(t)


        for t in threads:
            t.join()
        
        print(f"Folhas criadas: {len(self.folhas)}")

        print("Terminou o processo de criar as folhas")

        if not self.folhas:
            print("Problema ao criar as folhas")

        print("Iniciando o processo de montar a árvore com o hash dos filhos e vizinhos")
        self.raiz = self.monta_tudo(self.folhas) 
        print("Terminou o processo de montar a árvore com o hash dos filhos e vizinhos")

        

    def leitura_arquivo(self,nome_arquivo):
        transacoes_nao_feitas = []

        if not os.path.exists(nome_arquivo):
            print("Erro ao abrir o arquivo")

        with open(nome_arquivo, "r", encoding="utf-8") as f:
            for linha in f:
                dado = linha.strip()
                if dado:
                    transacoes_nao_feitas.append(dado)
        
        return transacoes_nao_feitas

    # funcao que irá ser chamada por todas as threads para criar todas as folhas
    def salva_transacao(self,transacoes_nao_feitas):
        while True:
            with lock_nao_feitas:
                if not transacoes_nao_feitas:
                    break
                transacao = random.choice(transacoes_nao_feitas)
                transacoes_nao_feitas.remove(transacao)
            
            # nesse caso na hora de salvar a folha será aplicada duas vezes a funcao de hash sha-256 isso é feito no bitcoin pois
            # serve para proteção contra ataques e é uma herança do hashcash

            dado_hash = sha_256(sha_256(transacao))

            with lock_feitas:
                self.folhas.append(No(valor_hash=dado_hash))

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
        print(f"Procurando transação com hash: {hash_procurado}")
        
        resultado = self._busca_no(self.raiz, hash_procurado)
        
        if resultado:
            print(f"Transação existe na árvore")
            return resultado
        else:
            print(f"Transação não existe na árvore")
            return None
    
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
    
    def gerar_prova_inclusao(self, transacao):
        # gera a prova de inclusão
        if not self.raiz:
            print("Árvore não foi construída!")
            return None
        
        hash_transacao = sha_256(sha_256(transacao))
        caminho = []
        hash_alvo = hash_transacao
        
        # Encontra o caminho da folha até a raiz
        if self._encontrar_caminho(self.raiz, hash_transacao, caminho):
            print(f"    Prova de inclusão para: {transacao}")
            print(f"    Hash da transação: {hash_transacao}")
            print(" Caminho até a raiz:")
            for i, (hash_irmao, direcao) in enumerate(caminho):
                print(f"    Nível {i}: {direcao} -> {hash_irmao}")
            print(f"   Hash raiz: {self.raiz.hash}")
            return caminho
        else:
            print("Transação não encontrada para gerar prova")
            return None
    
    def _encontrar_caminho(self, no, hash_procura, caminho):
        # para encontrar o caminho até o nó
        if no is None:
            return False
        
        if no.hash == hash_procura:
            return True
        
        # Verifica filho esquerdo
        if self._encontrar_caminho(no.esq, hash_procura, caminho):
            if no.dir:
                caminho.append((no.dir.hash, "direita"))
            return True
        
        # Verifica filho direito
        if self._encontrar_caminho(no.dir, hash_procura, caminho):
            if no.esq:
                caminho.append((no.esq.hash, "esquerda"))
            return True
        
        return False

# parte principal

nome_arquivo = input("Insira o nome do arquivo (garanta que está na mesma pasta):")
#nome_arquivo = "teste.txt"

merkle_tree = Merkle_tree(nome_arquivo=nome_arquivo)


while True:
    resposta = int(input("\n\nEscolha o que você quer fazer:\n1. Buscar transação na árvore\n2. Gerar Prova de inclusão\n3. Sair\n\n"))

    if resposta == 1:
        transacao = input("\n\nDigite a transação que deseja buscar: ").strip()
        if transacao:
            merkle_tree.busca_transacao(transacao)
        else:
            print("Transação não pode estar vazia!")
    elif resposta == 2:
        transacao = input("\n\nDigite a transação para gerar prova de inclusão: ").strip()
        if transacao:
            merkle_tree.gerar_prova_inclusao(transacao)
        else:
            print("Transação não pode estar vazia!")
    elif resposta == 3:
        print("\n\nSaindo\n")
        break

        




