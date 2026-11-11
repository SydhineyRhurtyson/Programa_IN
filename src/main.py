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

if __name__ =="__main__":
    Check_library("pyspark")
bibliotecas =["logsfacilitator","qiskit_optimization","qiskit","qiskit_algorithms" ]
for biblioteca in bibliotecas:
    Check_library(biblioteca)
# from variaveis import *
from funcition import mochileiro , mochila_quantica
if __name__ == "__main__":
    valor = [40, 100, 50, 60]
    peso = [20, 10, 40, 30]
    capacidade =50
    capacidade = 50
    valorfinal , intens_escolhidos, intens_escolhidos_nomes= mochileiro(valor, peso,capacidade)
    print("=+="*50)
    print(f"O resultado final:{ valorfinal}")
    print(intens_escolhidos)
    print("=+="*50)
    val_q, itens_q = mochila_quantica(valor, peso, capacidade)
    print(f"Quântico (QAOA) - Valor máximo corrigido: {val_q}")
    print(f"Itens escolhidos (Apenas os itens reais): {itens_q}")