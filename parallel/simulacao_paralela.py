"""
Simulação Paralela de Propagação de Fake News usando multiprocessing
"""

import random
import time
import multiprocessing

IGNORANTE = 0
ESPALHADOR = 1
INATIVO = 2


# Cria a matriz inicial da população
def criar_grade(linhas, colunas, percentual_espalhadores=0.05, semente=42):
    random.seed(semente)
    grade = [[IGNORANTE for _ in range(colunas)] for _ in range(linhas)]

    total_celulas = linhas * colunas
    total_espalhadores = int(total_celulas * percentual_espalhadores)

    for _ in range(total_espalhadores):
        i = random.randint(0, linhas - 1)
        j = random.randint(0, colunas - 1)
        grade[i][j] = ESPALHADOR

    return grade


# Conta vizinhos espalhadores usando a Vizinhança de Moore
def contar_vizinhos_espalhadores(grade, i, j, total_linhas, total_colunas):
    total = 0
    for di in (-1, 0, 1):
        for dj in (-1, 0, 1):
            if di == 0 and dj == 0:
                continue
            ni, nj = i + di, j + dj
            if 0 <= ni < total_linhas and 0 <= nj < total_colunas:
                if grade[ni][nj] == ESPALHADOR:
                    total += 1
    return total



# Função executada de forma independente por cada processo/núcleo
# Recebe a grade atual, a linha de início, a linha de fim e o limiar
def processar_fatia_worker(args):
    grade_atual, linha_inicio, linha_fim, limiar_convencimento = args
    total_linhas = len(grade_atual)
    total_colunas = len(grade_atual[0])

    fatia_nova = []

    for i in range(linha_inicio, linha_fim):
        linha_calculada = []
        for j in range(total_colunas):
            estado_atual = grade_atual[i][j]

            if estado_atual == IGNORANTE:
                vizinhos = contar_vizinhos_espalhadores(grade_atual, i, j, total_linhas, total_colunas)
                if vizinhos >= limiar_convencimento:
                    linha_calculada.append(ESPALHADOR)
                else:
                    linha_calculada.append(IGNORANTE)

            elif estado_atual == ESPALHADOR:
                linha_calculada.append(INATIVO)

            else:  # INATIVO
                linha_calculada.append(INATIVO)

        fatia_nova.append(linha_calculada)

    return fatia_nova


# Divide a matriz em fatias e distribui o cálculo para o Pool de processos
def proxima_geracao_paralela(grade, pool, num_processos, limiar_convencimento):
    total_linhas = len(grade)
    tamanho_fatia = total_linhas // num_processos
    tarefas = []

    for p in range(num_processos):
        inicio_l = p * tamanho_fatia
        # O último processo pega o restante das linhas se houver sobra
        fim_l = total_linhas if p == num_processos - 1 else (p + 1) * tamanho_fatia
        tarefas.append((grade, inicio_l, fim_l, limiar_convencimento))

    # Executa em paralelo real usando multiprocessing
    resultados_fatias = pool.map(processar_fatia_worker, tarefas)

    # Junta as fatias calculadas de volta em uma única matriz
    nova_grade = []
    for fatia in resultados_fatias:
        nova_grade.extend(fatia)

    return nova_grade


# Conta o total de células em cada estado
def contar_estados(grade):
    contagem = {IGNORANTE: 0, ESPALHADOR: 0, INATIVO: 0}
    for linha in grade:
        for celula in linha:
            contagem[celula] += 1
    return contagem


def executar_simulacao_paralela(
    linhas=500,
    colunas=500,
    geracoes=50,
    percentual_espalhadores=0.05,
    limiar_convencimento=3,
    num_processos=None
):
    if num_processos is None:
        num_processos = multiprocessing.cpu_count()

    grade = criar_grade(linhas, colunas, percentual_espalhadores)

    print("=== SIMULAÇÃO PARALELA (MULTIPROCESSING) ===")
    print(f"Matriz: {linhas}x{colunas} | Processos/Threads: {num_processos} | Gerações: {geracoes}")

    inicio = time.time()

    # Cria o pool de processos reaproveitável
    with multiprocessing.Pool(processes=num_processos) as pool:
        for geracao in range(geracoes):
            grade = proxima_geracao_paralela(grade, pool, num_processos, limiar_convencimento)
            contagem = contar_estados(grade)

            if (geracao + 1) % 10 == 0 or geracao == geracoes - 1:
                print(f"Geração {geracao + 1:03d} | Ignorantes: {contagem[IGNORANTE]:>8,} | "
                      f"Espalhadores: {contagem[ESPALHADOR]:>8,} | Inativos: {contagem[INATIVO]:>8,}")

            if contagem[ESPALHADOR] == 0:
                print(f"\nA propagação encerrou na geração {geracao + 1}: não há mais espalhadores.")
                break

    fim = time.time()
    tempo_total = fim - inicio
    print(f"\nTempo total de execução (Paralela com {num_processos} processos): {tempo_total:.4f} segundos")
    return tempo_total


if __name__ == "__main__":
    # Garante compatibilidade com o multiprocessing em diferentes sistemas operacionais (Windows/Linux/Mac)
    multiprocessing.freeze_support()
    executar_simulacao_paralela(linhas=500, colunas=500, geracoes=50)
