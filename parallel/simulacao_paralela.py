"""
Simulação Paralela de Propagação de Fake News usando multiprocessing
(Integrado com as 6 Inovações de Negócio)
"""

import random
import time
import multiprocessing
import csv
import os

# INOVAÇÃO: NOVOS ESTADOS DA SIMULAÇÃO 
FACT_CHECKER = -1
IGNORANTE = 0
ESPALHADOR = 1
INATIVO = 2
BOT = 3

# Cria a matriz inicial com proporções de diferentes agentes
def criar_grade(linhas, colunas, perc_espalhadores=0.03, perc_bots=0.01, perc_checkers=0.02, semente=42):
    random.seed(semente)
    grade = [[IGNORANTE for _ in range(colunas)] for _ in range(linhas)]
    total_celulas = linhas * colunas
    
    def popular_agentes(quantidade, estado):
        inseridos = 0
        while inseridos < quantidade:
            i, j = random.randint(0, linhas - 1), random.randint(0, colunas - 1)
            if grade[i][j] == IGNORANTE:
                grade[i][j] = estado
                inseridos += 1

    popular_agentes(int(total_celulas * perc_espalhadores), ESPALHADOR)
    popular_agentes(int(total_celulas * perc_bots), BOT)
    popular_agentes(int(total_celulas * perc_checkers), FACT_CHECKER)

    return grade


# INOVAÇÃO: Analisa a vizinhança mapeando ameaças e resistências
def analisar_vizinhanca(grade, i, j, total_linhas, total_colunas):
    peso_infeccao = 0
    tem_fact_checker = False

    for di in (-1, 0, 1):
        for dj in (-1, 0, 1):
            if di == 0 and dj == 0:
                continue

            ni, nj = i + di, j + dj
            if 0 <= ni < total_linhas and 0 <= nj < total_colunas:
                vizinho = grade[ni][nj]
                if vizinho == ESPALHADOR:
                    peso_infeccao += 1
                elif vizinho == BOT:
                    peso_infeccao += 2 # Bots têm força dobrada
                elif vizinho == FACT_CHECKER:
                    tem_fact_checker = True
                    
    return peso_infeccao, tem_fact_checker


# Função executada de forma independente por cada processo/núcleo (Agora com as inovações)
def processar_fatia_worker(args):
    grade_atual, linha_inicio, linha_fim = args
    total_linhas = len(grade_atual)
    total_colunas = len(grade_atual[0])

    fatia_nova = []

    for i in range(linha_inicio, linha_fim):
        linha_calculada = []
        for j in range(total_colunas):
            estado_atual = grade_atual[i][j]

            # IGNORANTE -> ESPALHADOR (Probabilidade e Fact-Checkers)
            if estado_atual == IGNORANTE:
                peso_infeccao, tem_fact_checker = analisar_vizinhanca(grade_atual, i, j, total_linhas, total_colunas)
                
                if peso_infeccao > 0:
                    chance = 0.20 + (peso_infeccao * 0.15)
                    if tem_fact_checker:
                        chance *= 0.3 
                        
                    if random.random() < chance:
                        linha_calculada.append(ESPALHADOR)
                    else:
                        linha_calculada.append(IGNORANTE)
                else:
                    linha_calculada.append(IGNORANTE)

            # ESPALHADOR -> INATIVO (Maturação)
            elif estado_atual == ESPALHADOR:
                if random.random() < 0.35:
                    linha_calculada.append(INATIVO)
                else:
                    linha_calculada.append(ESPALHADOR)

            # INATIVO -> IGNORANTE (Recaída)
            elif estado_atual == INATIVO:
                if random.random() < 0.05:
                    linha_calculada.append(IGNORANTE)
                else:
                    linha_calculada.append(INATIVO)

            else: 
                linha_calculada.append(estado_atual)

        fatia_nova.append(linha_calculada)

    return fatia_nova


# Divide a matriz em fatias e distribui o cálculo para o Pool de processos
def proxima_geracao_paralela(grade, pool, num_processos):
    total_linhas = len(grade)
    tamanho_fatia = total_linhas // num_processos
    tarefas = []

    for p in range(num_processos):
        inicio_l = p * tamanho_fatia
        fim_l = total_linhas if p == num_processos - 1 else (p + 1) * tamanho_fatia
        # Passando apenas grade, inicio e fim (removido o limiar estático)
        tarefas.append((grade, inicio_l, fim_l))

    # Executa em paralelo real usando multiprocessing
    resultados_fatias = pool.map(processar_fatia_worker, tarefas)

    # Junta as fatias calculadas de volta em uma única matriz
    nova_grade = []
    for fatia in resultados_fatias:
        nova_grade.extend(fatia)

    return nova_grade


# Conta o total de células em cada estado
def contar_estados(grade):
    contagem = {FACT_CHECKER: 0, IGNORANTE: 0, ESPALHADOR: 0, INATIVO: 0, BOT: 0}
    for linha in grade:
        for celula in linha:
            contagem[celula] += 1
    return contagem


def executar_simulacao_paralela(linhas=500, colunas=500, geracoes=50, num_processos=None):
    if num_processos is None:
        num_processos = multiprocessing.cpu_count()

    grade = criar_grade(linhas, colunas)
    
    # INOVAÇÃO: CSV específico para a versão paralela para a Pessoa 4 comparar os tempos
    arquivo_csv = 'resultados_paralelo.csv'
    dados_csv = [["Geracao", "Ignorantes", "Espalhadores", "Inativos", "Bots", "Fact_Checkers"]]

    print("=== SIMULAÇÃO PARALELA (MULTIPROCESSING) COM INOVAÇÕES ===")
    print(f"Matriz: {linhas}x{colunas} | Processos: {num_processos} | Gerações: {geracoes}\n")

    inicio = time.time()

    # Cria o pool de processos reaproveitável
    with multiprocessing.Pool(processes=num_processos) as pool:
        for geracao in range(geracoes):
            grade = proxima_geracao_paralela(grade, pool, num_processos)
            contagem = contar_estados(grade)
            
            dados_csv.append([
                geracao + 1, contagem[IGNORANTE], contagem[ESPALHADOR], 
                contagem[INATIVO], contagem[BOT], contagem[FACT_CHECKER]
            ])

            if (geracao + 1) % 10 == 0 or geracao == geracoes - 1:
                print(f"Geração {geracao + 1:03d} | Espalhadores: {contagem[ESPALHADOR]:>7,} | "
                      f"Inativos: {contagem[INATIVO]:>7,} | Ignorantes: {contagem[IGNORANTE]:>7,}")

            if contagem[ESPALHADOR] == 0:
                print(f"\nA propagação encerrou na geração {geracao + 1}.")
                break

    fim = time.time()
    tempo_total = fim - inicio

    with open(arquivo_csv, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerows(dados_csv)

    print(f"\nTempo total de execução (Paralela): {tempo_total:.4f} segundos")
    print(f"Relatório de dados salvo em '{arquivo_csv}'.")
    return tempo_total


if __name__ == "__main__":
    multiprocessing.freeze_support()
    # Usando 1000x1000 para manter o mesmo padrão da versão sequencial que você testou
    executar_simulacao_paralela(linhas=1000, colunas=1000, geracoes=50)