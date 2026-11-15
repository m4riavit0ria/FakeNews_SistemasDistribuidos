"""
Simulação Sequencial de Propagação de Fake News 
(Refatorado para Paralelização com Inovações de Negócio)

Inovações implementadas (Pessoa 3):
1. Probabilidade de Convencimento dinâmica.
2. Agentes Fact-Checkers (Imunes que reduzem o contágio ao redor).
3. Bots Super-espalhadores (Peso de persuasão dobrado).
4. Maturação/Persistência (Espalhadores duram mais de um turno).
5. Recaída (Inativos podem esquecer o assunto e voltar a ser suscetíveis).
6. Geração Automática de Relatório CSV (Apoio à Pessoa 4 para gráficos).
"""

import random
import time
import csv
import os

# --- INOVAÇÃO: NOVOS ESTADOS DA SIMULAÇÃO ---
FACT_CHECKER = -1
IGNORANTE = 0
ESPALHADOR = 1
INATIVO = 2
BOT = 3

# Cria a matriz inicial com proporções de diferentes agentes
def criar_grade(linhas, colunas, perc_espalhadores=0.03, perc_bots=0.01, perc_checkers=0.02, semente=123):
    random.seed(semente)
    grade = [[IGNORANTE for _ in range(colunas)] for _ in range(linhas)]

    total_celulas = linhas * colunas
    
    # Função auxiliar para popular agentes aleatoriamente
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
                    peso_infeccao += 2 # Bots têm força de convencimento dobrada
                elif vizinho == FACT_CHECKER:
                    tem_fact_checker = True
                    
    return peso_infeccao, tem_fact_checker

# Calcula a próxima geração mantendo suporte às fatias (threads/distribuída)
def processar_fatia_linhas(grade_atual, linha_inicio, linha_fim):
    total_linhas = len(grade_atual)
    total_colunas = len(grade_atual[0])
    fatia_nova = []

    for i in range(linha_inicio, linha_fim):
        linha_calculada = []
        for j in range(total_colunas):
            estado_atual = grade_atual[i][j]

            # IGNORANTE -> ESPALHADOR (Inovação 1 e 2: Probabilidade e Fact-Checkers)
            if estado_atual == IGNORANTE:
                peso_infeccao, tem_fact_checker = analisar_vizinhanca(grade_atual, i, j, total_linhas, total_colunas)
                
                if peso_infeccao > 0:
                    # Chance base de 20% + 15% por cada peso de infecção ao redor
                    chance = 0.20 + (peso_infeccao * 0.15)
                    
                    # Fact-checkers reduzem drasticamente a chance de acreditar na fake news
                    if tem_fact_checker:
                        chance *= 0.3 
                        
                    if random.random() < chance:
                        linha_calculada.append(ESPALHADOR)
                    else:
                        linha_calculada.append(IGNORANTE)
                else:
                    linha_calculada.append(IGNORANTE)

            # ESPALHADOR -> INATIVO (Inovação 4: Maturação)
            elif estado_atual == ESPALHADOR:
                # 35% de chance de cansar de espalhar a notícia a cada rodada
                if random.random() < 0.35:
                    linha_calculada.append(INATIVO)
                else:
                    linha_calculada.append(ESPALHADOR)

            # INATIVO -> IGNORANTE (Inovação 5: Recaída / Suscetível Novamente)
            elif estado_atual == INATIVO:
                # 5% de chance da pessoa esquecer e poder ser enganada de novo depois de um tempo
                if random.random() < 0.05:
                    linha_calculada.append(IGNORANTE)
                else:
                    linha_calculada.append(INATIVO)

            # FACT_CHECKER e BOT mantêm seus papéis estruturais até o fim
            else: 
                linha_calculada.append(estado_atual)

        fatia_nova.append(linha_calculada)

    return fatia_nova

def proxima_geracao(grade):
    total_linhas = len(grade)
    return processar_fatia_linhas(grade, 0, total_linhas)

def contar_estados(grade):
    contagem = {FACT_CHECKER: 0, IGNORANTE: 0, ESPALHADOR: 0, INATIVO: 0, BOT: 0}
    for linha in grade:
        for celula in linha:
            contagem[celula] += 1
    return contagem

def executar_simulacao(linhas=500, colunas=500, geracoes=50):
    grade = criar_grade(linhas, colunas)
    
    # INOVAÇÃO 6: Preparando arquivo CSV para a Pessoa 4 gerar os gráficos
    arquivo_csv = 'resultados_simulacao.csv'
    dados_csv = [["Geracao", "Ignorantes", "Espalhadores", "Inativos", "Bots", "Fact_Checkers"]]

    print("=== SIMULAÇÃO SEQUENCIAL COM INOVAÇÕES ===")
    print(f"Matriz: {linhas}x{colunas} | Gerações: {geracoes}\n")
    
    inicio = time.time()

    for geracao in range(geracoes):
        grade = proxima_geracao(grade)
        contagem = contar_estados(grade)
        
        # Salva o log na memória para o CSV
        dados_csv.append([
            geracao + 1, contagem[IGNORANTE], contagem[ESPALHADOR], 
            contagem[INATIVO], contagem[BOT], contagem[FACT_CHECKER]
        ])

        if (geracao + 1) % 10 == 0 or geracao == geracoes - 1:
            print(f"Geração {geracao + 1:03d} | Espalhadores: {contagem[ESPALHADOR]:>7,} | "
                  f"Inativos: {contagem[INATIVO]:>7,} | Ignorantes: {contagem[IGNORANTE]:>7,}")

        if contagem[ESPALHADOR] == 0:
            print(f"\nA propagação encerrou na geração {geracao + 1}: não há mais espalhadores comuns ativos.")
            break

    fim = time.time()
    tempo_total = fim - inicio

    # Exportando o CSV
    with open(arquivo_csv, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerows(dados_csv)

    print(f"\nTempo total de execução: {tempo_total:.4f} segundos")
    print(f"Relatório de dados salvo em '{arquivo_csv}' (Pronto para plotagem).")
    return tempo_total

if __name__ == "__main__":
    executar_simulacao(linhas=1000, colunas=1000, geracoes=50)