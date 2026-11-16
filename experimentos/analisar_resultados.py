"""
Script de Análise de Desempenho e Geração de Gráficos
Lê 'resultados/experimentos.csv', calcula médias, speedup e eficiência com pandas,
exporta tabelas resumidas e gera os 4 gráficos obrigatórios com matplotlib.
"""

from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt


def main():
    caminho_csv = Path("resultados/experimentos.csv")
    if not caminho_csv.exists():
        print("ERRO: Arquivo 'resultados/experimentos.csv' não encontrado. Execute primeiro 'rodar_experimentos.py'.")
        return

    pasta_graficos = Path("resultados/graficos")
    pasta_graficos.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(caminho_csv)

    # Agrupa repetições calculando média e desvio padrão
    resumo = (
        df.groupby(
            ["grupo", "versao", "tam_matriz", "geracoes", "pct_espalhadores", "n_threads", "n_hosts"],
            as_index=False,
        )
        .agg(
            tempo_medio_s=("tempo_s", "mean"),
            tempo_std_s=("tempo_s", "std"),
            comunicacao_media_s=("tempo_comunicacao_s", "mean"),
            calculo_medio_s=("tempo_calculo_s", "mean"),
        )
    )

    # Salva tabela resumida geral
    resumo.to_csv("resultados/resumo_metricas.csv", index=False)

    # ==========================================================================
    # CÁLCULO DE SPEEDUP E EFICIÊNCIA (VARIAÇÃO DE THREADS - PARALELA)
    # ==========================================================================
    df_threads = resumo[resumo["grupo"] == "var_threads"].copy().sort_values("n_threads")
    t_base_threads = df_threads.loc[df_threads["n_threads"] == 1, "tempo_medio_s"].values[0]

    df_threads["speedup"] = t_base_threads / df_threads["tempo_medio_s"]
    df_threads["eficiencia_pct"] = (df_threads["speedup"] / df_threads["n_threads"]) * 100
    df_threads.to_csv("resultados/metricas_paralela_threads.csv", index=False)

    # ==========================================================================
    # CÁLCULO DE SPEEDUP E EFICIÊNCIA (VARIAÇÃO DE HOSTS/WORKERS - DISTRIBUÍDA)
    # ==========================================================================
    df_hosts = resumo[resumo["grupo"] == "var_hosts"].copy().sort_values("n_hosts")
    t_base_hosts = df_hosts.loc[df_hosts["n_hosts"] == 1, "tempo_medio_s"].values[0]

    df_hosts["speedup"] = t_base_hosts / df_hosts["tempo_medio_s"]
    df_hosts["eficiencia_pct"] = (df_hosts["speedup"] / df_hosts["n_hosts"]) * 100
    df_hosts.to_csv("resultados/metricas_distribuida_hosts.csv", index=False)

    # ==========================================================================
    # GRÁFICO 1: Speedup x Threads (com linha ideal de referência)
    # ==========================================================================
    plt.figure(figsize=(8, 5))
    plt.plot(df_threads["n_threads"], df_threads["speedup"], marker="o", linewidth=2, label="Speedup Obtido (Paralela)")
    plt.plot(df_threads["n_threads"], df_threads["n_threads"], linestyle="--", color="gray", label="Speedup Ideal (Linear)")
    plt.title("Speedup × Número de Processos (Matriz 500×500, 50 gerações)")
    plt.xlabel("Número de Processos (Threads)")
    plt.ylabel("Speedup")
    plt.xticks(df_threads["n_threads"])
    plt.grid(True, linestyle=":", alpha=0.7)
    plt.legend()
    plt.tight_layout()
    plt.savefig(pasta_graficos / "1_speedup_vs_threads.png", dpi=300)
    plt.close()

    # ==========================================================================
    # GRÁFICO 2: Eficiência x Threads
    # ==========================================================================
    plt.figure(figsize=(8, 5))
    plt.plot(df_threads["n_threads"], df_threads["eficiencia_pct"], marker="s", color="darkorange", linewidth=2, label="Eficiência (%)")
    plt.axhline(100, linestyle="--", color="gray", label="Eficiência Ideal (100%)")
    plt.title("Eficiência Paralela × Número de Processos")
    plt.xlabel("Número de Processos (Threads)")
    plt.ylabel("Eficiência (%)")
    plt.xticks(df_threads["n_threads"])
    plt.ylim(0, 115)
    plt.grid(True, linestyle=":", alpha=0.7)
    plt.legend()
    plt.tight_layout()
    plt.savefig(pasta_graficos / "2_eficiencia_vs_threads.png", dpi=300)
    plt.close()

    # ==========================================================================
    # GRÁFICO 3: Tempo x Tamanho da Matriz (3 versões juntas)
    # ==========================================================================
    df_matriz = resumo[resumo["grupo"] == "var_matriz"].copy().sort_values("tam_matriz")

    plt.figure(figsize=(9, 5))
    for versao, rotulo, marcador in [
        ("sequencial", "Sequencial", "o"),
        ("paralela", "Paralela (4 processos)", "s"),
        ("distribuida", "Distribuída (4 workers TCP)", "^"),
    ]:
        sub = df_matriz[df_matriz["versao"] == versao]
        plt.plot(sub["tam_matriz"], sub["tempo_medio_s"], marker=marcador, linewidth=2, label=rotulo)

    plt.title("Tempo de Execução × Tamanho da Matriz (50 gerações)")
    plt.xlabel("Dimensão da Matriz (N × N)")
    plt.ylabel("Tempo Médio (s)")
    plt.xticks(sorted(df_matriz["tam_matriz"].unique()))
    plt.grid(True, linestyle=":", alpha=0.7)
    plt.legend()
    plt.tight_layout()
    plt.savefig(pasta_graficos / "3_tempo_vs_tamanho_matriz.png", dpi=300)
    plt.close()

    # ==========================================================================
    # GRÁFICO 4: Tempo de Comunicação x Tempo de Cálculo (Versão Distribuída)
    # ==========================================================================
    df_dist_mat = df_matriz[df_matriz["versao"] == "distribuida"].sort_values("tam_matriz")
    x_labels = [f"{n}×{n}" for n in df_dist_mat["tam_matriz"]]

    plt.figure(figsize=(8, 5))
    plt.bar(x_labels, df_dist_mat["calculo_medio_s"], label="Tempo de Cálculo (Workers)", color="#2b7bba")
    plt.bar(
        x_labels,
        df_dist_mat["comunicacao_media_s"],
        bottom=df_dist_mat["calculo_medio_s"],
        label="Tempo de Comunicação (Sockets TCP + JSON + Halos)",
        color="#e66101",
    )
    plt.title("Versão Distribuída: Tempo de Cálculo × Tempo de Comunicação")
    plt.xlabel("Tamanho da Matriz")
    plt.ylabel("Tempo Médio (s)")
    plt.grid(True, axis="y", linestyle=":", alpha=0.7)
    plt.legend()
    plt.tight_layout()
    plt.savefig(pasta_graficos / "4_comunicacao_vs_calculo_distribuida.png", dpi=300)
    plt.close()

    # Exibe resumo no terminal
    print("\n=== TABELA: VARIAÇÃO DE THREADS (PARALELA) ===")
    print(df_threads[["n_threads", "tempo_medio_s", "speedup", "eficiencia_pct"]].to_string(index=False))

    print("\n=== TABELA: VARIAÇÃO DE WORKERS (DISTRIBUÍDA) ===")
    print(df_hosts[["n_hosts", "tempo_medio_s", "speedup", "eficiencia_pct"]].to_string(index=False))

    print("\n=== TABELA: TEMPO POR TAMANHO DA MATRIZ ===")
    piv_matriz = df_matriz.pivot(index="tam_matriz", columns="versao", values="tempo_medio_s")
    print(piv_matriz.to_string())

    print(f"\nGráficos salvos com sucesso em: {pasta_graficos.resolve()}")


if __name__ == "__main__":
    main()