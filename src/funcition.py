from logsfacilitator import measure_time_and_memory
from qiskit_optimization import QuadraticProgram
from qiskit_optimization.converters import QuadraticProgramToQubo
from qiskit_optimization.algorithms import MinimumEigenOptimizer
from qiskit_algorithms import QAOA
from qiskit.primitives import StatevectorSampler as Sampler
from qiskit_algorithms.optimizers import COBYLA
import dimod
from dwave.samplers import SimulatedAnnealingSampler

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


@measure_time_and_memory("data")
def mochila_quantica(valores, pesos, capacidade_maxima):
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
    
    sampler = Sampler()
    otimizador_classico = COBYLA(maxiter=500)
    qaoa = QAOA(sampler=sampler, optimizer=otimizador_classico, reps=3)
    
    otimizador_quantico = MinimumEigenOptimizer(qaoa)
    resultado = otimizador_quantico.solve(qubo)

    solucao_binaria = [int(x) for x in resultado.x]
    
    num_itens = len(valores)
    itens_reais = solucao_binaria[:num_itens]
    
    valor_real_encontrado = sum(valores[i] * itens_reais[i] for i in range(num_itens))
    
    return valor_real_encontrado, itens_reais

# Exemplo de uso com os mesmos dados:
@measure_time_and_memory("data")
def resolver_mochila_quantica(valores, pesos, capacidade_maxima):
    # 1. Configurar o problema de otimização matemática
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

    # 2. Conversão para QUBO e operador de Ising
    conversor = QuadraticProgramToQubo()
    qubo = conversor.convert(qp)
    
    operador_ising, offset = qubo.to_ising()
    num_qubits = operador_ising.num_qubits
    print(f"-> Mapeamento Quântico: O problema utilizou exatamente {num_qubits} qubits.")

    # 3. Execução usando o QAOA com o Sampler atualizado
    sampler = Sampler()
    otimizador_classico = COBYLA(maxiter=100)
    
    qaoa = QAOA(sampler=sampler, optimizer=otimizador_classico, reps=1)
    otimizador_quantico = MinimumEigenOptimizer(qaoa)
    resultado = otimizador_quantico.solve(qubo)

    solucao_binaria = [int(x) for x in resultado.x]
    
    return resultado.fval, solucao_binaria, num_qubits

@measure_time_and_memory("data")
def resolver_mochila_dwave(valores, pesos, capacidade_maxima, num_reads=1000):
    # 1. Criar o Modelo Quadrático com Restrições (CQM)
    cqm = dimod.ConstrainedQuadraticModel()
    
    # Criar uma variável binária (0 ou 1) para cada item
    itens = [dimod.Binary(f'x_{i}') for i in range(len(valores))]
    
    # Função Objetivo: Maximizar o valor total
    # Como o D-Wave sempre minimiza energia, multiplicamos os valores por -1
    cqm.set_objective(-sum(valores[i] * itens[i] for i in range(len(valores))))
    
    # Restrição de Peso: soma(pesos * x_i) <= capacidade_maxima
    cqm.add_constraint(
        sum(pesos[i] * itens[i] for i in range(len(pesos))) <= capacidade_maxima,
        label='capacidade_mochila'
    )
    
    # 2. Converter CQM para BQM (QUBO)
    # O multiplicador de Lagrange define a penalidade caso o peso ultrapasse o limite
    penalidade = max(valores) * 2
    bqm, inverter = dimod.cqm_to_bqm(cqm, lagrange_multiplier=penalidade)
    
    # Contabiliza o total de variáveis (itens reais + variáveis de folga criadas)
    total_variaveis_qubo = len(bqm.variables)
    
    # 3. Executar o amostrador local (simula o comportamento do hardware D-Wave)
    sampler = SimulatedAnnealingSampler()
    sampleset = sampler.sample(bqm, num_reads=num_reads)
    
    # 4. Extrair a solução de menor energia e remover as variáveis de folga
    melhor_amostra_bqm = sampleset.first.sample
    solucao_original = inverter(melhor_amostra_bqm)
    
    itens_escolhidos = [int(solucao_original[f'x_{i}']) for i in range(len(valores))]
    valor_total = sum(valores[i] * itens_escolhidos[i] for i in range(len(valores)))
    peso_total = sum(pesos[i] * itens_escolhidos[i] for i in range(len(valores)))
    
    return valor_total, peso_total, itens_escolhidos, total_variaveis_qubo


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
    val_q, itens_q, qubits_usados = resolver_mochila_quantica(valor, peso, capacidade)
    print(f"Quântico (QAOA) - Valor máximo encontrado: {val_q}")
    print(f"Itens escolhidos (Qubits ativados): {itens_q}")
