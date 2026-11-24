"""
Gera relatórios em imagem (PNG) a partir dos logs da `logsfacilitator`
e dos resultados (`ResultadoMochila`) das três abordagens.

    1. ler_logs(caminho)                    -> DataFrame com tempo/memória por execução
    2. grafico_desempenho(df, "x.png")      -> tempo de execução + pico de memória
    3. grafico_qualidade(resultados, "y.png") -> valor encontrado + proximidade do ótimo
"""
from __future__ import annotations
from logsfacilitator import check_existence_of_folder
import ast
import re
from pathlib import Path
from typing import Iterable, Optional
from os import path 
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

# Nome de cada função do log -> rótulo que aparece no gráfico
ROTULOS = {
    "mochila_classica": "Clássico (Prog. Dinâmica)",
    "mochila_qiskit": "Qiskit (QAOA)",
    "mochila_dwave": "D-Wave Ocean (Simulated Annealer)",
    # nomes dos métodos no ResultadoMochila.metodo
    "classico": "Clássico (Prog. Dinâmica)",
    "qiskit_qaoa": "Qiskit (QAOA)",
    "dwave_sa": "D-Wave Ocean (Simulated Annealer)",
}

# Um bloco do log, exatamente no formato que a sua biblioteca gera
_BLOCO = re.compile(
    r"Logs:(?P<data>.+)\n"
    r"Function: (?P<funcao>\w+), Args: (?P<args>\{.*\})\n"
    r"Time: (?P<minutos>[\d.]+):(?P<segundos>[\d.]+) seconds\n"
    r"Memory current: (?P<mem_atual>[\d.]+) MB, Memory maximum: (?P<mem_max>[\d.]+) MB"
)


# ----------------------------------------------------------------------
# 1) Leitura dos logs
# ----------------------------------------------------------------------
def ler_logs(caminho: str | Path) -> pd.DataFrame:
    """Lê o arquivo de log e devolve um DataFrame (uma linha por execução)."""
    diretorio_log = check_existence_of_folder(folder="data")
    caminho   = path.join(diretorio_log,"log.txt")
    texto = Path(caminho).read_text(encoding="utf-8")
    linhas = []
    for m in _BLOCO.finditer(texto):
        try:
            args = ast.literal_eval(m["args"])
        except (ValueError, SyntaxError):
            args = {}
        linhas.append({
            "data": m["data"].strip(),
            "funcao": m["funcao"],
            "metodo": ROTULOS.get(m["funcao"], m["funcao"]),
            # "14.0:21.3415" = 14 minutos e 21,3415 segundos
            "tempo_s": float(m["minutos"]) * 60 + float(m["segundos"]),
            "mem_atual_mb": float(m["mem_atual"]),
            "mem_max_mb": float(m["mem_max"]),
            "n_itens": len(args.get("valores", [])) or None,
        })
    if not linhas:
        raise ValueError("Nenhum bloco de log reconhecido em " + str(caminho))
    return pd.DataFrame(linhas)


# ----------------------------------------------------------------------
# Auxiliares de formatação
# ----------------------------------------------------------------------
def _fmt_tempo(s: float) -> str:
    if s >= 60:
        return f"{int(s // 60)}min {s % 60:.0f}s"
    return f"{s:.4f}s" if s < 1 else f"{s:.2f}s"


def _ajustar_escala(ax, valores, usar_log: Optional[bool], linear_zero: bool = False):
    """Usa escala logarítmica quando as barras diferem em ordens de grandeza
    (senão as menores ficam invisíveis, como o Qiskit em 14 min vs 0,0001 s)."""
    positivos = [v for v in valores if v > 0]
    if usar_log is None:
        usar_log = bool(positivos) and max(positivos) / min(positivos) > 100
    if usar_log:
        if linear_zero:   # memória pode ser 0.00 -> 'symlog' aceita zero
            ax.set_yscale("symlog", linthresh=0.01)
        else:
            ax.set_yscale("log")
    return usar_log


def _rotular_barras(ax, textos):
    # com `hue` o seaborn cria um container por barra, então anotamos pelas barras (patches)
    for barra, texto in zip(ax.patches, textos):
        ax.annotate(texto, (barra.get_x() + barra.get_width() / 2, barra.get_height()),
                    ha="center", va="bottom", xytext=(0, 3),
                    textcoords="offset points", fontsize=10)
    ax.margins(y=0.15)
    plt.setp(ax.get_xticklabels(), rotation=15, ha="right", fontsize=10)
    ax.set_xlabel("")


def _salvar(fig, saida):
    fig.tight_layout()
    fig.savefig(saida, dpi=200, bbox_inches="tight")
    plt.close(fig)
    return Path(saida)


# ----------------------------------------------------------------------
# 2) Gráfico de desempenho (tempo e memória)
# ----------------------------------------------------------------------
def grafico_desempenho(df: pd.DataFrame, saida: str = "desempenho.png",
                       somente_ultima: bool = True,
                       log_tempo: Optional[bool] = None,
                       log_memoria: Optional[bool] = None) -> Path:
    """
    Args:
        df: DataFrame vindo de `ler_logs`
        saida: nome do PNG
        somente_ultima: se a mesma função aparece várias vezes no log, usa só a última
        log_tempo / log_memoria: força (True/False) ou deixa automático (None) a escala log
    """
    sns.set_theme(style="whitegrid")
    if somente_ultima:
        df = df.drop_duplicates("funcao", keep="last")

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 5.5))

    sns.barplot(data=df, x="metodo", y="tempo_s", hue="metodo",
                palette="viridis", legend=False, ax=ax1)
    ax1.set_title("Tempo de Execução", fontweight="bold")
    ax1.set_ylabel("Tempo (s)")
    log1 = _ajustar_escala(ax1, df["tempo_s"], log_tempo)
    _rotular_barras(ax1, [_fmt_tempo(v) for v in df["tempo_s"]])
    if log1:
        ax1.set_ylabel("Tempo (s) — escala log")

    sns.barplot(data=df, x="metodo", y="mem_max_mb", hue="metodo",
                palette="magma", legend=False, ax=ax2)
    ax2.set_title("Pico de Memória RAM", fontweight="bold")
    ax2.set_ylabel("Memória (MB)")
    log2 = _ajustar_escala(ax2, df["mem_max_mb"], log_memoria, linear_zero=True)
    _rotular_barras(ax2, [f"{v:.2f}MB" for v in df["mem_max_mb"]])
    if log2:
        ax2.set_ylabel("Memória (MB) — escala symlog")

    return _salvar(fig, saida)


# ----------------------------------------------------------------------
# 3) Gráfico de qualidade (valor e proximidade do ótimo)
# ----------------------------------------------------------------------
def grafico_qualidade(resultados: Iterable, saida: str = "qualidade.png") -> Path:
    """
    Args:
        resultados: lista de `ResultadoMochila` (precisa incluir o método "classico",
                    que serve de referência ótima)
    """
    sns.set_theme(style="whitegrid")
    resultados = list(resultados)
    ref = next((r for r in resultados if r.metodo == "classico"), None)
    if ref is None:
        raise ValueError("Inclua o resultado de `mochila_classica` como referência do ótimo.")

    df = pd.DataFrame({
        "metodo": [ROTULOS.get(r.metodo, r.metodo) for r in resultados],
        "valor": [r.valor_total for r in resultados],
        # solução inviável não conta como "perto do ótimo"
        "proximidade": [100 * r.valor_total / ref.valor_total if r.viavel and ref.valor_total
                        else 0.0 for r in resultados],
        "viavel": [r.viavel for r in resultados],
    })

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 5.5))

    sns.barplot(data=df, x="metodo", y="valor", hue="metodo",
                palette="Blues_d", legend=False, ax=ax1)
    ax1.set_title("Valor Total na Mochila", fontweight="bold")
    ax1.set_ylabel("Valor total")
    _rotular_barras(ax1, [f"{v:g}" + ("" if ok else " (inviável)")
                          for v, ok in zip(df["valor"], df["viavel"])])

    sns.barplot(data=df, x="metodo", y="proximidade", hue="metodo",
                palette="Greens_d", legend=False, ax=ax2)
    ax2.set_title("Proximidade do Ótimo (%)", fontweight="bold")
    ax2.set_ylabel("Acurácia (%)")
    ax2.set_ylim(0, 115)
    _rotular_barras(ax2, [f"{v:.1f}%" for v in df["proximidade"]])

    return _salvar(fig, saida)


# ----------------------------------------------------------------------
# Exemplo de uso
# ----------------------------------------------------------------------
if __name__ == "__main__":
    df = ler_logs("logs.txt")               # arquivo gerado pela sua biblioteca
    print(df)
    grafico_desempenho(df, "desempenho.png")

    # Para o gráfico de qualidade, use os resultados retornados pelas funções:
    # from mochila import mochila_classica, mochila_qiskit, mochila_dwave
    # res = [mochila_classica(v, p, c), mochila_qiskit(v, p, c), mochila_dwave(v, p, c)]
    # grafico_qualidade(res, "qualidade.png")