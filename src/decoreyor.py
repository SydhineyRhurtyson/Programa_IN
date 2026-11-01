from functools import lru_cache,wraps
from time import perf_counter
from datetime import datetime

def medir_tempo(funcao):
    @wraps(funcao)
    def interna(*args, **kwargs):

        inicio = perf_counter()
        print(20*"=+=")
        print(f" Regristo de log : {datetime.now()}")
        resultado = funcao(*args, **kwargs)

        fim = perf_counter()
        registro = f"Registo de log : {datetime.now()} - Tempo de execução da função {funcao.__name__}: {fim - inicio:.4f} segundos"
        print(registro)

        return resultado

    return interna