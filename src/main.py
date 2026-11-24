from subprocess import check_call
from sys import executable

def Check_library(library):
    """Check if the library is already installed.

    if not, install it.

    Args:
        library(str): name of library

    """
    try:
        __import__(library)
        print("Library already installed")
    except ImportError:
        check_call([
            executable, "-m", "pip", "install", library
        ])
        print("Library installed")

# bibliotecas =["logsfacilitator","qiskit_optimization","qiskit","qiskit_algorithms", "dimod", "dwave-ocean-sdk" ]
# for biblioteca in bibliotecas:
#     Check_library(biblioteca)
from mochila import mochila_classica, mochila_dwave, mochila_qiskit
from variaveis import valor, peso, nomes
from relatorio_graficos import ler_logs, grafico_desempenho, grafico_qualidade

if __name__ == "__main__":
    # atvalor = [40, 100, 50, 60]
    # atpeso = [20, 10, 40, 30]
    # capacidade =50
    capacidade =13
    for nv in range(3,200):
    # nv= 3 #numero de variaveis em uma lista  

        atvalor = valor[0:nv]
        atpeso = peso[0:nv]
        atnomes = nomes[0:nv]
        resultados = [
            mochila_classica(atvalor, atpeso, capacidade,nomes=atnomes),
            mochila_qiskit(atvalor, atpeso, capacidade, seed=42,nomes=atnomes),
            mochila_dwave(atvalor, atpeso, capacidade, seed=42,nomes=atnomes),
        ]

        otimo = resultados[0].valor_total
        for r in resultados:
            razao = r.valor_total / otimo if otimo else float("nan")
            print(f"[{r.metodo:12}] valor={r.valor_total} peso={r.peso_total} "
                f"itens={r.itens} viavel={r.viavel} "
                f"variaveis={r.num_variaveis} razao_aprox={razao:.2%}")
        df = ler_logs("logs.txt")                    # lê o log e vira um DataFrame
        grafico_desempenho(df, f"figures/desempenhon{nv}.png")     # tempo + pico de memória

        # gráfico de qualidade (valor encontrado + % do ótimo)
        grafico_qualidade(resultados, f"figures/qualidade{nv}.png")