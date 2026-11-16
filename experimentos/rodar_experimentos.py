"""
Script Unificado de Experimentos de Desempenho
Executa as versões Sequencial, Paralela (multiprocessing) e Distribuída (Sockets TCP),
variando um parâmetro por vez e gravando os resultados em CSV.
"""

import csv
import json
import multiprocessing
import os
import platform
import random
import socket
import subprocess
import sys
import time
from pathlib import Path

# ==============================================================================
# 1. REGRAS DO MODELO E CONSTANTES (IDÊNTICAS NAS 3 VERSÕES)
# ==============================================================================
FACT_CHECKER = -1
IGNORANTE = 0
ESPALHADOR = 1
INATIVO = 2
BOT = 3

SEMENTE_PADRAO = 123
PERC_BOTS_PADRAO = 0.01
PERC_CHECKERS_PADRAO = 0.02


def coletar_info_ambiente():
    try:
        import psutil
        ram_gb = round(psutil.virtual_memory().total / (1024 ** 3), 2)
    except ImportError:
        ram_gb = "N/A (instale psutil)"

    return {
        "processador": platform.processor() or "AMD Ryzen 5 7235HS",
        "nucleos_logicos": os.cpu_count(),
        "ram_gb": ram_gb,
        "sistema_operacional": f"{platform.system()} {platform.release()} ({platform.version()})",
        "versao_python": platform.python_version(),
    }


def criar_grade(linhas, colunas, perc_espalhadores=0.03, perc_bots=PERC_BOTS_PADRAO,
                perc_checkers=PERC_CHECKERS_PADRAO, semente=SEMENTE_PADRAO):
    gerador = random.Random(semente)
    grade = [[IGNORANTE for _ in range(colunas)] for _ in range(linhas)]
    total_celulas = linhas * colunas

    def popular_agentes(quantidade, estado):
        inseridos = 0
        while inseridos < quantidade:
            i = gerador.randint(0, linhas - 1)
            j = gerador.randint(0, colunas - 1)
            if grade[i][j] == IGNORANTE:
                grade[i][j] = estado
                inseridos += 1

    popular_agentes(int(total_celulas * perc_espalhadores), ESPALHADOR)
    popular_agentes(int(total_celulas * perc_bots), BOT)
    popular_agentes(int(total_celulas * perc_checkers), FACT_CHECKER)
    return grade


def contar_estados(grade):
    contagem = {FACT_CHECKER: 0, IGNORANTE: 0, ESPALHADOR: 0, INATIVO: 0, BOT: 0}
    for linha in grade:
        for celula in linha:
            contagem[celula] += 1
    return contagem


def analisar_vizinhanca_halo(grade_com_halo, linha_global, coluna, inicio_halo, total_linhas, total_colunas):
    peso_infeccao = 0
    tem_fact_checker = False

    for di in (-1, 0, 1):
        for dj in (-1, 0, 1):
            if di == 0 and dj == 0:
                continue
            ni = linha_global + di
            nj = coluna + dj
            if 0 <= ni < total_linhas and 0 <= nj < total_colunas:
                vizinho = grade_com_halo[ni - inicio_halo][nj]
                if vizinho == ESPALHADOR:
                    peso_infeccao += 1
                elif vizinho == BOT:
                    peso_infeccao += 2
                elif vizinho == FACT_CHECKER:
                    tem_fact_checker = True

    return peso_infeccao, tem_fact_checker


def processar_bloco(grade_com_halo, linha_inicio, linha_fim, total_linhas, seed_bloco=None):
    rng = random.Random(seed_bloco) if seed_bloco is not None else random
    total_colunas = len(grade_com_halo[0])
    inicio_halo = max(0, linha_inicio - 1)
    fatia_nova = []

    for i in range(linha_inicio, linha_fim):
        indice_local = i - inicio_halo
        linha_calculada = []

        for j in range(total_colunas):
            estado_atual = grade_com_halo[indice_local][j]

            if estado_atual == IGNORANTE:
                peso_infeccao, tem_fact_checker = analisar_vizinhanca_halo(
                    grade_com_halo, i, j, inicio_halo, total_linhas, total_colunas
                )
                if peso_infeccao > 0:
                    chance = 0.20 + (peso_infeccao * 0.15)
                    if tem_fact_checker:
                        chance *= 0.3
                    linha_calculada.append(ESPALHADOR if rng.random() < chance else IGNORANTE)
                else:
                    linha_calculada.append(IGNORANTE)

            elif estado_atual == ESPALHADOR:
                linha_calculada.append(INATIVO if rng.random() < 0.35 else ESPALHADOR)

            elif estado_atual == INATIVO:
                linha_calculada.append(IGNORANTE if rng.random() < 0.05 else INATIVO)

            else:
                linha_calculada.append(estado_atual)

        fatia_nova.append(linha_calculada)

    return fatia_nova


def dividir_linhas(total_linhas, n_partes):
    linhas_por_parte = total_linhas // n_partes
    resto = total_linhas % n_partes
    blocos = []
    inicio = 0
    for i in range(n_partes):
        qtd = linhas_por_parte + (1 if i < resto else 0)
        fim = inicio + qtd
        blocos.append((inicio, fim))
        inicio = fim
    return blocos


# ==============================================================================
# 2. EXECUÇÃO SEQUENCIAL
# ==============================================================================
def rodar_sequencial(tam_matriz, geracoes, pct_espalhadores):
    grade = criar_grade(tam_matriz, tam_matriz, perc_espalhadores=pct_espalhadores, semente=SEMENTE_PADRAO)
    inicio = time.perf_counter()

    for g in range(geracoes):
        # Usa seed determinística por geração para preservar comportamento lógico
        grade = processar_bloco(grade, 0, tam_matriz, tam_matriz, seed_bloco=SEMENTE_PADRAO + g)
        if contar_estados(grade)[ESPALHADOR] == 0:
            break

    tempo_total = time.perf_counter() - inicio
    return tempo_total, 0.0, tempo_total, contar_estados(grade)


# ==============================================================================
# 3. EXECUÇÃO PARALELA (MULTIPROCESSING)
# ==============================================================================
def _worker_pool(args):
    grade, inicio, fim, total_linhas, seed_bloco = args
    return processar_bloco(grade, inicio, fim, total_linhas, seed_bloco=seed_bloco)


def rodar_paralela(tam_matriz, geracoes, pct_espalhadores, n_processos):
    grade = criar_grade(tam_matriz, tam_matriz, perc_espalhadores=pct_espalhadores, semente=SEMENTE_PADRAO)
    blocos = dividir_linhas(tam_matriz, n_processos)

    inicio = time.perf_counter()
    with multiprocessing.Pool(processes=n_processos) as pool:
        for g in range(geracoes):
            tarefas = [
                (grade, ini, fim, tam_matriz, SEMENTE_PADRAO + g * 100 + idx)
                for idx, (ini, fim) in enumerate(blocos)
            ]
            fatias = pool.map(_worker_pool, tarefas)
            nova_grade = []
            for fatia in fatias:
                nova_grade.extend(fatia)
            grade = nova_grade

            if contar_estados(grade)[ESPALHADOR] == 0:
                break

    tempo_total = time.perf_counter() - inicio
    return tempo_total, 0.0, tempo_total, contar_estados(grade)


# ==============================================================================
# 4. EXECUÇÃO DISTRIBUÍDA (SOCKETS TCP + MEDIÇÃO DE COMUNICAÇÃO VS CÁLCULO)
# ==============================================================================
def _enviar_msg(sock, obj):
    dados = json.dumps(obj).encode("utf-8")
    sock.sendall(len(dados).to_bytes(4, "big") + dados)


def _receber_bytes(sock, n):
    buf = b""
    while len(buf) < n:
        parte = sock.recv(n - len(buf))
        if not parte:
            raise ConnectionError("Conexão encerrada.")
        buf += parte
    return buf


def _receber_msg(sock):
    tam = int.from_bytes(_receber_bytes(sock, 4), "big")
    return json.loads(_receber_bytes(sock, tam).decode("utf-8"))


def _modo_worker_tcp(porta):
    cliente = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    for _ in range(30):
        try:
            cliente.connect(("127.0.0.1", porta))
            break
        except ConnectionRefusedError:
            time.sleep(0.1)

    try:
        while True:
            tarefa = _receber_msg(cliente)
            if tarefa.get("acao") == "encerrar":
                break

            t_calc_ini = time.perf_counter()
            resultado = processar_bloco(
                grade_com_halo=tarefa["grade"],
                linha_inicio=tarefa["linha_inicio"],
                linha_fim=tarefa["linha_fim"],
                total_linhas=tarefa["total_linhas"],
                seed_bloco=tarefa["seed_bloco"],
            )
            t_calc = time.perf_counter() - t_calc_ini

            _enviar_msg(cliente, {
                "linha_inicio": tarefa["linha_inicio"],
                "resultado": resultado,
                "tempo_calculo": t_calc,
            })
    finally:
        cliente.close()


def rodar_distribuida(tam_matriz, geracoes, pct_espalhadores, n_workers, porta=5050):
    grade = criar_grade(tam_matriz, tam_matriz, perc_espalhadores=pct_espalhadores, semente=SEMENTE_PADRAO)
    blocos = dividir_linhas(tam_matriz, n_workers)

    servidor = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    servidor.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    servidor.bind(("127.0.0.1", porta))
    servidor.listen(n_workers)

    processos_workers = []
    for _ in range(n_workers):
        p = subprocess.Popen([sys.executable, __file__, "--worker", str(porta)])
        processos_workers.append(p)

    conexoes = []
    for _ in range(n_workers):
        conn, _ = servidor.accept()
        conexoes.append(conn)

    tempo_calculo_acumulado = 0.0
    inicio_total = time.perf_counter()

    try:
        for g in range(geracoes):
            # Envio de tarefas (com halos)
            for idx, conn in enumerate(conexoes):
                ini, fim = blocos[idx]
                ini_halo = max(0, ini - 1)
                fim_halo = min(tam_matriz, fim + 1)
                _enviar_msg(conn, {
                    "grade": grade[ini_halo:fim_halo],
                    "linha_inicio": ini,
                    "linha_fim": fim,
                    "total_linhas": tam_matriz,
                    "seed_bloco": SEMENTE_PADRAO + g * 100 + idx,
                })

            # Recebimento de resultados
            nova_grade = []
            max_calc_rodada = 0.0
            for conn in conexoes:
                resp = _receber_msg(conn)
                nova_grade.extend(resp["resultado"])
                # Como os workers rodam em paralelo, o tempo de cálculo da rodada é o maior entre eles
                if resp["tempo_calculo"] > max_calc_rodada:
                    max_calc_rodada = resp["tempo_calculo"]

            tempo_calculo_acumulado += max_calc_rodada
            grade = nova_grade

            if contar_estados(grade)[ESPALHADOR] == 0:
                break

        tempo_total = time.perf_counter() - inicio_total
        tempo_comunicacao = max(0.0, tempo_total - tempo_calculo_acumulado)

    finally:
        for conn in conexoes:
            try:
                _enviar_msg(conn, {"acao": "encerrar"})
                conn.close()
            except OSError:
                pass
        servidor.close()
        for p in processos_workers:
            p.wait(timeout=5)

    return tempo_total, tempo_comunicacao, tempo_calculo_acumulado, contar_estados(grade)


# ==============================================================================
# 5. ORQUESTRADOR DA BATERIA DE EXPERIMENTOS
# ==============================================================================
def main():
    Path("resultados").mkdir(exist_ok=True)

    # Salva configuração do ambiente
    env_info = coletar_info_ambiente()
    with open("resultados/ambiente_experimental.json", "w", encoding="utf-8") as f:
        json.dump(env_info, f, indent=2, ensure_ascii=False)
    print("Ambiente registrado:", env_info)

    # Parâmetros base (quando não estão sendo variados)
    BASE_MATRIZ = 500
    BASE_GERACOES = 50
    BASE_PCT_ESP = 0.03
    BASE_THREADS = 4
    BASE_HOSTS = 4
    REPETICOES = 3  # Pode alterar para 5 se quiser mais repetições

    # Lista de cenários variando UM parâmetro por vez
    # Formato: (grupo_experimento, versao, tam_matriz, geracoes, pct_espalhadores, n_threads, n_hosts)
    cenarios = []

    # Cenário A: Variação do tamanho da matriz (100, 500, 1000, 2000) nas 3 versões
    for tam in [100, 500, 1000, 2000]:
        cenarios.append(("var_matriz", "sequencial", tam, BASE_GERACOES, BASE_PCT_ESP, 1, 1))
        cenarios.append(("var_matriz", "paralela", tam, BASE_GERACOES, BASE_PCT_ESP, BASE_THREADS, 1))
        cenarios.append(("var_matriz", "distribuida", tam, BASE_GERACOES, BASE_PCT_ESP, 1, BASE_HOSTS))

    # Cenário B: Variação de gerações (50, 100, 500)
    for ger in [50, 100, 500]:
        cenarios.append(("var_geracoes", "sequencial", BASE_MATRIZ, ger, BASE_PCT_ESP, 1, 1))
        cenarios.append(("var_geracoes", "paralela", BASE_MATRIZ, ger, BASE_PCT_ESP, BASE_THREADS, 1))
        cenarios.append(("var_geracoes", "distribuida", BASE_MATRIZ, ger, BASE_PCT_ESP, 1, BASE_HOSTS))

    # Cenário C: Variação do % de espalhadores (1%, 5%, 10%)
    for pct in [0.01, 0.05, 0.10]:
        cenarios.append(("var_espalhadores", "sequencial", BASE_MATRIZ, BASE_GERACOES, pct, 1, 1))
        cenarios.append(("var_espalhadores", "paralela", BASE_MATRIZ, BASE_GERACOES, pct, BASE_THREADS, 1))
        cenarios.append(("var_espalhadores", "distribuida", BASE_MATRIZ, BASE_GERACOES, pct, 1, BASE_HOSTS))

    # Cenário D: Variação de threads/processos na versão paralela (1, 2, 4, 8)
    for th in [1, 2, 4, 8]:
        cenarios.append(("var_threads", "paralela", BASE_MATRIZ, BASE_GERACOES, BASE_PCT_ESP, th, 1))

    # Cenário E: Variação de workers/hosts na versão distribuída (1, 2, 3, 4)
    for wk in [1, 2, 3, 4]:
        cenarios.append(("var_hosts", "distribuida", BASE_MATRIZ, BASE_GERACOES, BASE_PCT_ESP, 1, wk))

    arquivo_saida = "resultados/experimentos.csv"
    colunas = [
        "grupo", "versao", "tam_matriz", "geracoes", "pct_espalhadores",
        "n_threads", "n_hosts", "repeticao", "tempo_s",
        "tempo_comunicacao_s", "tempo_calculo_s",
        "final_ignorantes", "final_espalhadores", "final_inativos"
    ]

    porta_atual = 5050

    with open(arquivo_saida, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(colunas)

        total_runs = len(cenarios) * REPETICOES
        run_atual = 0

        for grupo, versao, tam, ger, pct, n_th, n_hosts in cenarios:
            for rep in range(1, REPETICOES + 1):
                run_atual += 1
                print(
                    f"[{run_atual}/{total_runs}] {grupo} | {versao} | "
                    f"N={tam} | G={ger} | Esp={pct*100:.0f}% | Th={n_th} | Hosts={n_hosts} | Rep={rep}"
                )

                if versao == "sequencial":
                    t_tot, t_com, t_calc, estados = rodar_sequencial(tam, ger, pct)
                elif versao == "paralela":
                    t_tot, t_com, t_calc, estados = rodar_paralela(tam, ger, pct, n_th)
                elif versao == "distribuida":
                    t_tot, t_com, t_calc, estados = rodar_distribuida(tam, ger, pct, n_hosts, porta=porta_atual)
                    porta_atual += 1  # Evita conflito de porta TIME_WAIT no Windows

                writer.writerow([
                    grupo, versao, tam, ger, pct,
                    n_th, n_hosts, rep, round(t_tot, 6),
                    round(t_com, 6), round(t_calc, 6),
                    estados[IGNORANTE], estados[ESPALHADOR], estados[INATIVO]
                ])
                f.flush()

    print(f"\nConcluído! Resultados salvos em '{arquivo_saida}'.")


if __name__ == "__main__":
    multiprocessing.freeze_support()
    if len(sys.argv) >= 3 and sys.argv[1] == "--worker":
        _modo_worker_tcp(int(sys.argv[2]))
    else:
        main()