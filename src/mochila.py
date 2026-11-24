"""
Problema da mochila 0/1 em três abordagens com o MESMO formato de retorno:

    1. mochila_classica -> programação dinâmica (solução exata)
    2. mochila_qiskit   -> QAOA (qiskit, simulado em statevector)
    3. mochila_dwave    -> QUBO + simulated annealing (dwave-samplers)

Todas retornam um `ResultadoMochila`, então dá para comparar os métodos
diretamente (valor, peso, viabilidade, nº de qubits, etc.).
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Optional, Sequence

from logsfacilitator import measure_time_and_memory,check_existence_of_folder

# --- Qiskit ---
from qiskit.primitives import StatevectorSampler as Sampler
from qiskit_algorithms import QAOA
from qiskit_algorithms.optimizers import COBYLA
from qiskit_algorithms.utils import algorithm_globals
from qiskit_optimization import QuadraticProgram
from qiskit_optimization.algorithms import MinimumEigenOptimizer
from qiskit_optimization.converters import QuadraticProgramToQubo

# --- D-Wave ---
import dimod
from dwave.samplers import SimulatedAnnealingSampler


# ----------------------------------------------------------------------
# Formato de retorno comum
# ----------------------------------------------------------------------
@dataclass
class ResultadoMochila:
    metodo: str                              # "classico", "qiskit_qaoa", "dwave_sa"
    valor_total: float                       # soma dos valores dos itens escolhidos
    peso_total: int                          # soma dos pesos dos itens escolhidos
    itens: list[int]                         # índices dos itens escolhidos
    selecao: list[int]                       # vetor binário (0/1) de tamanho n
    viavel: bool                             # peso_total <= capacidade
    nomes: Optional[list[str]] = None        # nomes dos itens escolhidos (se fornecidos)
    num_variaveis: Optional[int] = None      # nº de qubits / variáveis do QUBO (None no clássico)
    extras: dict = field(default_factory=dict)  # parâmetros e detalhes de cada método

    def to_dict(self) -> dict:
        return asdict(self)


# ----------------------------------------------------------------------
# Funções auxiliares (compartilhadas)
# ----------------------------------------------------------------------
def _validar_entrada(valores, pesos, capacidade, nomes):
    if len(valores) == 0:
        raise ValueError("A lista de itens está vazia.")
    if len(valores) != len(pesos):
        raise ValueError("`valores` e `pesos` precisam ter o mesmo tamanho.")
    if nomes is not None and len(nomes) != len(valores):
        raise ValueError("`nomes` precisa ter o mesmo tamanho de `valores`.")
    if any(int(p) != p or p < 0 for p in pesos):
        raise ValueError("Os pesos precisam ser inteiros não negativos "
                         "(se forem decimais, multiplique por 10/100 para escalar).")
    if int(capacidade) != capacidade or capacidade < 0:
        raise ValueError("A capacidade precisa ser um inteiro não negativo.")
    return [int(p) for p in pesos], int(capacidade)


def _montar_resultado(metodo, valores, pesos, capacidade, selecao, nomes,
                      num_variaveis=None, **extras) -> ResultadoMochila:
    """Monta o resultado SEMPRE recalculando valor e peso a partir dos dados originais."""
    selecao = [int(s) for s in selecao]
    itens = [i for i, s in enumerate(selecao) if s]
    peso_total = sum(pesos[i] for i in itens)
    valor_total = sum(valores[i] for i in itens)
    return ResultadoMochila(
        metodo=metodo,
        valor_total=valor_total,
        peso_total=peso_total,
        itens=itens,
        selecao=selecao,
        viavel=peso_total <= capacidade,
        nomes=[nomes[i] for i in itens] if nomes is not None else None,
        num_variaveis=num_variaveis,
        extras=extras,
    )

def _caso_trivial(valores, pesos, capacidade):
    """Se todos os itens cabem, o ótimo é levar todos (os de valor positivo)."""
    if sum(pesos) <= capacidade:
        return [int(v > 0) for v in valores]
    return None

def _melhor_viavel(candidatos: Sequence[Sequence[int]], valores, pesos, capacidade):
    """Entre vários vetores 0/1, devolve o de maior valor que respeita a capacidade.
    Se nenhum for viável, devolve o primeiro (que será marcado como inviável)."""
    melhor, melhor_valor = None, float("-inf")
    for sel in candidatos:
        peso = sum(p * s for p, s in zip(pesos, sel))
        if peso <= capacidade:
            valor = sum(v * s for v, s in zip(valores, sel))
            if valor > melhor_valor:
                melhor, melhor_valor = sel, valor
    return melhor if melhor is not None else candidatos[0]


# ----------------------------------------------------------------------
# 1) Clássico: programação dinâmica
# ----------------------------------------------------------------------
@measure_time_and_memory("data")
def mochila_classica(valores: list[float], pesos: list[int], capacidade: int,
                     nomes: Optional[list[str]] = None, usar_atalho: bool = True) -> ResultadoMochila:
    """
    Args:
        valores: valor de cada item
        pesos: peso de cada item (inteiros)
        capacidade: capacidade da mochila (inteiro)
        nomes: nome de cada item (opcional)
    """
    pesos, capacidade = _validar_entrada(valores, pesos, capacidade, nomes)
    if usar_atalho:
        atalho = _caso_trivial(valores, pesos, capacidade)
        if atalho is not None:
            return _montar_resultado("classico", valores, pesos, capacidade,
                                    atalho, nomes, atalho_trivial=True)
    n = len(valores)

    tabela = [[0] * (capacidade + 1) for _ in range(n + 1)]
    for i in range(1, n + 1):
        v, p = valores[i - 1], pesos[i - 1]
        for w in range(capacidade + 1):          # começa em 0 para tratar itens de peso 0
            tabela[i][w] = tabela[i - 1][w]
            if p <= w:
                tabela[i][w] = max(tabela[i][w], v + tabela[i - 1][w - p])

    # Reconstrução dos itens escolhidos
    selecao = [0] * n
    w = capacidade
    for i in range(n, 0, -1):
        if tabela[i][w] != tabela[i - 1][w]:
            selecao[i - 1] = 1
            w -= pesos[i - 1]

    return _montar_resultado("classico", valores, pesos, capacidade, selecao, nomes,
                             valor_otimo_tabela=tabela[n][capacidade])


# ----------------------------------------------------------------------
# 2) Quântico: Qiskit + QAOA
# ----------------------------------------------------------------------
def _construir_qp(valores, pesos, capacidade) -> QuadraticProgram:
    n = len(valores)
    qp = QuadraticProgram("mochila")
    for i in range(n):
        qp.binary_var(f"x_{i}")
    qp.maximize(linear={f"x_{i}": valores[i] for i in range(n)})
    qp.linear_constraint(
        linear={f"x_{i}": pesos[i] for i in range(n)},
        sense="<=",
        rhs=capacidade,
        name="restricao_peso",
    )
    return qp


@measure_time_and_memory("data")
def mochila_qiskit(valores: list[float], pesos: list[int], capacidade: int,
                   nomes: Optional[list[str]] = None, reps: int = 1,
                   maxiter: int = 100, shots: int = 1024,
                   seed: Optional[int] = None,usar_atalho: bool = True) -> ResultadoMochila:
    """
    Args:
        reps: camadas (p) do QAOA
        maxiter: iterações máximas do COBYLA
        shots: nº de medições do sampler
        seed: semente para reprodutibilidade
    """
    pesos, capacidade = _validar_entrada(valores, pesos, capacidade, nomes)
    if usar_atalho:
        atalho = _caso_trivial(valores, pesos, capacidade)
        if atalho is not None:
            return _montar_resultado("qiskit_qaoa", valores, pesos, capacidade,
                                    atalho, nomes, atalho_trivial=True)
    n = len(valores)

    qp = _construir_qp(valores, pesos, capacidade)

    # QUBO só para contar quantos qubits são necessários (itens + variáveis de folga)
    qubo = QuadraticProgramToQubo().convert(qp)
    num_qubits = qubo.get_num_vars()

    if seed is not None:
        algorithm_globals.random_seed = seed
    sampler = Sampler(default_shots=shots, seed=seed)
    qaoa = QAOA(sampler=sampler, optimizer=COBYLA(maxiter=maxiter), reps=reps)

    # Passando o problema ORIGINAL, o optimizer já devolve só as n variáveis dos itens
    resultado = MinimumEigenOptimizer(qaoa).solve(qp)

    # Pega a melhor amostra VIÁVEL (o QAOA pode medir estados que violam a capacidade)
    candidatos = [[int(round(v)) for v in resultado.x[:n]]]
    candidatos += [[int(round(v)) for v in amostra.x[:n]] for amostra in resultado.samples]
    selecao = _melhor_viavel(candidatos, valores, pesos, capacidade)

    return _montar_resultado(
        "qiskit_qaoa", valores, pesos, capacidade, selecao, nomes,
        num_variaveis=num_qubits,
        reps=reps, maxiter=maxiter, shots=shots, seed=seed,
        n_amostras_distintas=len(resultado.samples),
    )


# ----------------------------------------------------------------------
# 3) D-Wave: QUBO + simulated annealing
# ----------------------------------------------------------------------
@measure_time_and_memory("data")
def mochila_dwave(valores: list[float], pesos: list[int], capacidade: int,
                  nomes: Optional[list[str]] = None, num_reads: int = 1000,
                  penalidade: Optional[float] = None,
                  seed: Optional[int] = None,usar_atalho: bool = True) -> ResultadoMochila:
    """
    Args:
        num_reads: nº de execuções do annealing
        penalidade: multiplicador de Lagrange da restrição (padrão: 2 * maior valor)
        seed: semente para reprodutibilidade
    """
    pesos, capacidade = _validar_entrada(valores, pesos, capacidade, nomes)
    if usar_atalho:
        atalho = _caso_trivial(valores, pesos, capacidade)
        if atalho is not None:
            return _montar_resultado("dwave_sa", valores, pesos, capacidade,
                                    atalho, nomes, atalho_trivial=True)
    n = len(valores)

    cqm = dimod.ConstrainedQuadraticModel()
    x = [dimod.Binary(f"x_{i}") for i in range(n)]
    cqm.set_objective(-sum(valores[i] * x[i] for i in range(n)))  # minimiza -valor
    cqm.add_constraint(sum(pesos[i] * x[i] for i in range(n)) <= capacidade,
                       label="capacidade_mochila")

    if penalidade is None:
        penalidade = (max(valores) * 2) or 1
    bqm, inverter = dimod.cqm_to_bqm(cqm, lagrange_multiplier=penalidade)
    num_variaveis = len(bqm.variables)  # itens + variáveis de folga

    sampleset = SimulatedAnnealingSampler().sample(bqm, num_reads=num_reads, seed=seed)
    sampleset = sampleset.aggregate()  # junta amostras repetidas

    # Converte cada amostra do QUBO de volta para as variáveis originais
    candidatos = []
    for dado in sampleset.data(["sample"], sorted_by="energy"):
        original = inverter(dado.sample)
        candidatos.append([int(original[f"x_{i}"]) for i in range(n)])
    selecao = _melhor_viavel(candidatos, valores, pesos, capacidade)

    return _montar_resultado(
        "dwave_sa", valores, pesos, capacidade, selecao, nomes,
        num_variaveis=num_variaveis,
        num_reads=num_reads, penalidade=penalidade, seed=seed,
        energia_minima=float(sampleset.first.energy),
    )


# ----------------------------------------------------------------------
# Exemplo de uso / comparação
# ----------------------------------------------------------------------
if __name__ == "__main__":
    valores = [40, 100, 50, 60]
    pesos = [20, 10, 40, 30]
    capacidade = 50

    resultados = [
        mochila_classica(valores, pesos, capacidade),
        mochila_qiskit(valores, pesos, capacidade, seed=42),
        mochila_dwave(valores, pesos, capacidade, seed=42),
    ]

    otimo = resultados[0].valor_total
    
    for r in resultados:
        razao = r.valor_total / otimo if otimo else float("nan")
        print(f"[{r.metodo:12}] valor={r.valor_total} peso={r.peso_total} "
              f"itens={r.itens} viavel={r.viavel} "
              f"variaveis={r.num_variaveis} razao_aprox={razao:.2%}")