from logsfacilitator import measure_time_and_memory
from qiskit_optimization import QuadraticProgram
from qiskit_optimization.converters import QuadraticProgramToQubo
from qiskit_optimization.algorithms import MinimumEigenOptimizer
from qiskit_algorithms import QAOA
from qiskit.primitives import StatevectorSampler as Sampler
from qiskit_algorithms.optimizers import COBYLA


@measure_time_and_memory("data")
def mochileiro(valores:list[float],peso:list[float],c:float,nomes:list[str]=None):
    """
    Args:
        valores (list[float]): lista de valores por cada item
        peso (list[float]): lista peso por de cada item  
        c (float): capacidade de peso que cabe na bolsa
        nomes (list[str],optional): lista de nome por cada item
    """
    n =len(valores)

    if n == len(peso):
        tabela =[[0 for _ in range(c+1)] for _ in range(n+1)]
        for i in range(1,n+1):
            for w in range(1,c+1):
                if peso[i-1] <= w:
                    tabela[i][w]= max(
                        valores[i-1] + tabela[i-1][w-peso[i-1]],
                        tabela[i-1][w] 
                    )
                else:
                    tabela[i][w] = tabela[i-1][w]
        #cr = capacidade restante
        cr = c
        #ie = Item Escolhido
        ie = []
        for i in range(n,0,-1):
            if tabela[i][cr] != tabela[i-1][cr]:
                ie.append(i - 1)
                cr -= peso[i-1]
        ie.reverse()
        #vm = Valor Maximo
        vm= tabela[n][c]
        if nomes:
            nie =[]
            for i in ie:
                nie.append(nomes[i])
            return vm,ie, nie
        else:
            return vm,ie,None


# Exemplo de uso:py -Sua_versão -m pip install --upgrade  logsfacilitator
@measure_time_and_memory("data")
def mochileiro_quantico(valores:list[float],peso:list[float],c:float,nomes:list[str]=None):
    pass

@measure_time_and_memory("data")
def resolver_mochila_quantica_ajustada(valores, pesos, capacidade_maxima):
    qp = QuadraticProgram()
    
    for i in range(len(valores)):
        qp.binary_var(f'x_{i}')

    qp.maximize(linear={f'x_{i}': valores[i] for i in range(len(valores))})

    qp.linear_constraint(
        linear={f'x_{i}': pesos[i] for i in range(len(pesos))},
        sense='<=',
        rhs=capacidade_maxima,
        name='restricao_peso'
    )

    conversor = QuadraticProgramToQubo()
    qubo = conversor.convert(qp)
    
    # AJUSTE 1: Aumentamos 'reps' de 1 para 3 (circuito mais profundo) 
    # e 'maxiter' para 500 (mais tentativas clássicas)
    sampler = Sampler()
    otimizador_classico = COBYLA(maxiter=500)
    qaoa = QAOA(sampler=sampler, optimizer=otimizador_classico, reps=3)
    
    otimizador_quantico = MinimumEigenOptimizer(qaoa)
    resultado = otimizador_quantico.solve(qubo)

    solucao_binaria = [int(x) for x in resultado.x]
    
    # AJUSTE 2: Filtrar apenas os qubits que representam os itens (ignorando as folgas)
    num_itens = len(valores)
    itens_reais = solucao_binaria[:num_itens]
    
    # AJUSTE 3: Recalcular o valor manualmente para evitar o erro do sinal negativo do QUBO
    valor_real_encontrado = sum(valores[i] * itens_reais[i] for i in range(num_itens))
    
    return valor_real_encontrado, itens_reais

# Exemplo de uso com os mesmos dados:


if __name__ == "__main__":
    # Example Usage
    # values1 = [60, 100, 120]
    # weights1 = [10, 20, 30]
    # W1 = 50
    # print("Maximum value in knapsack =", fractional_knapsack(values1, weights1, W1))  # Output: 240


    # nomes =[""]
    # W2 = 50
    #     nomes = [
    #     "Notebook", "Celular", "Tablet", "Monitor", "Teclado",
    #     "Mouse", "Impressora", "Cadeira", "Mesa", "Fone",
    #     "Microfone", "Webcam", "Roteador", "HD Externo", "SSD",
    #     "Memoria RAM", "Placa de Video", "Processador", "Fonte", "Gabinete",
    #     "Ventilador", "Liquidificador", "Cafeteira", "Air Fryer", "Microondas",
    #     "Televisao", "Controle", "Videogame", "Camera", "Tripé",
    #     "Mochila", "Mala", "Relogio", "Oculos", "Bicicleta",
    #     "Patinete", "Skate", "Bola", "Barraca", "Colchao",
    #     "Travesseiro", "Cobertor", "Luminaria", "Abajur", "Espelho",
    #     "Quadro", "Estante", "Sofá", "Poltrona", "Tapete"
    # ]

    #     peso = [
    #     8, 2, 3, 6, 1,
    #     1, 7, 12, 15, 1,
    #     2, 1, 1, 2, 1,
    #     1, 4, 2, 3, 5,
    #     4, 3, 2, 5, 12,
    #     18, 1, 4, 3, 2,
    #     2, 5, 1, 1, 14,
    #     8, 4, 1, 6, 10,
    #     2, 3, 2, 2, 5,
    #     3, 12, 25, 15, 8
    # ]

    #     valor = [
    #     3500, 1200, 1800, 1500, 150,
    #     80, 900, 1100, 1300, 250,
    #     400, 180, 300, 450, 600,
    #     350, 2800, 2200, 500, 700,
    #     180, 250, 200, 450, 650,
    #     3000, 100, 2500, 1800, 120,
    #     300, 500, 800, 600, 1600,
    #     900, 350, 120, 700, 500,
    #     150, 250, 180, 220, 400,
    #     350, 750, 2200, 1300, 600
    # ]
    valor = [40, 100, 50, 60]
    peso = [20, 10, 40, 30]
    capacidade =50
    val_q, itens_q = resolver_mochila_quantica_ajustada(valor, peso, capacidade)
    print(f"Quântico (QAOA) - Valor máximo corrigido: {val_q}")
    print(f"Itens escolhidos (Apenas os itens reais): {itens_q}")
    # print("Maximum value in knapsack =", fractional_knapsack(values2, weights2, W2))  # Output: 210