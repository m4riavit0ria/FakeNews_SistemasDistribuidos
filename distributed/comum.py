"""
Funções Comuns - Simulação Distribuída
(Integrado com as Inovações de Negócio)
"""

import random

# --- INOVAÇÃO: NOVOS ESTADOS DA SIMULAÇÃO ---
FACT_CHECKER = -1
IGNORANTE = 0
ESPALHADOR = 1
INATIVO = 2
BOT = 3


def criar_grade(linhas, colunas, perc_espalhadores=0.03, perc_bots=0.01, perc_checkers=0.02, semente=123):
    gerador = random.Random(semente)
    grade = [[IGNORANTE for _ in range(colunas)] for _ in range(linhas)]
    total_celulas = linhas * colunas
    
    def popular_agentes(quantidade, estado):
        inseridos = 0
        while inseridos < quantidade:
            i, j = gerador.randint(0, linhas - 1), gerador.randint(0, colunas - 1)
            if grade[i][j] == IGNORANTE:
                grade[i][j] = estado
                inseridos += 1

    popular_agentes(int(total_celulas * perc_espalhadores), ESPALHADOR)
    popular_agentes(int(total_celulas * perc_bots), BOT)
    popular_agentes(int(total_celulas * perc_checkers), FACT_CHECKER)

    return grade


# INOVAÇÃO: Analisa a vizinhança mapeando os limites de blocos distribuídos (halos)
def analisar_vizinhanca_distribuida(grade_com_halo, linha_global, coluna, inicio_halo, total_linhas, total_colunas):
    peso_infeccao = 0
    tem_fact_checker = False

    for di in (-1, 0, 1):
        for dj in (-1, 0, 1):
            if di == 0 and dj == 0:
                continue

            linha_vizinha_global = linha_global + di
            coluna_vizinha = coluna + dj

            if 0 <= linha_vizinha_global < total_linhas and 0 <= coluna_vizinha < total_colunas:
                # Converte o índice global da matriz para o índice local do pacote de rede
                linha_vizinha_local = linha_vizinha_global - inicio_halo
                
                vizinho = grade_com_halo[linha_vizinha_local][coluna_vizinha]
                if vizinho == ESPALHADOR:
                    peso_infeccao += 1
                elif vizinho == BOT:
                    peso_infeccao += 2 # Bots têm força dobrada
                elif vizinho == FACT_CHECKER:
                    tem_fact_checker = True
                    
    return peso_infeccao, tem_fact_checker


def processar_bloco(grade_com_halo, linha_inicio, linha_fim, total_linhas):
    total_colunas = len(grade_com_halo[0])
    inicio_halo = max(0, linha_inicio - 1)
    fatia_nova = []

    for i in range(linha_inicio, linha_fim):
        indice_local = i - inicio_halo
        linha_calculada = []

        for j in range(total_colunas):
            estado_atual = grade_com_halo[indice_local][j]

            # IGNORANTE -> ESPALHADOR (Probabilidade e Fact-Checkers)
            if estado_atual == IGNORANTE:
                peso_infeccao, tem_fact_checker = analisar_vizinhanca_distribuida(
                    grade_com_halo, i, j, inicio_halo, total_linhas, total_colunas
                )
                
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


def contar_estados(grade):
    contagem = {FACT_CHECKER: 0, IGNORANTE: 0, ESPALHADOR: 0, INATIVO: 0, BOT: 0}
    for linha in grade:
        for celula in linha:
            contagem[celula] += 1
    return contagem