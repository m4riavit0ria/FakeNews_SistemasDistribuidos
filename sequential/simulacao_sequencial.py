"""
Simulação Sequencial de Propagação de Fake News (Refatorado para Paralelização)

Estados:
0 = Ignorante (ainda não recebeu/acredita)
1 = Espalhador (acredita e compartilha)
2 = Inativo (recebeu, mas não compartilha mais)
"""

import random
import time

# Constantes de Estado
IGNORANTE = 0
ESPALHADOR = 1
INATIVO = 2


# Cria a matriz inicial da população com a porcentagem inicial de espalhadores
def criar_grade(linhas, colunas, percentual_espalhadores=0.02, semente=42):

    random.seed(semente)
    grade = [[IGNORANTE for _ in range(colunas)] for _ in range(linhas)]

    total_celulas = linhas * colunas
    total_espalhadores = int(total_celulas * percentual_espalhadores)

    for _ in range(total_espalhadores):
        i = random.randint(0, linhas - 1)
        j = random.randint(0, colunas - 1)
        grade[i][j] = ESPALHADOR

    return grade


# Conta quantos vizinhos ao redor da célula (i, j) estão espalhando (Vizinhança de Moore - até 8 vizinhos)
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


# Calcula a próxima geração para uma fatia específica de linhas (da linha_inicio até linha_fim)
def processar_fatia_linhas(grade_atual, linha_inicio, linha_fim, limiar_convencimento=2):

    total_linhas = len(grade_atual)
    total_colunas = len(grade_atual[0])

    # Fatia da nova geração contendo apenas as linhas deste bloco
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


# Gera a próxima geração da matriz inteira chamando o processamento de fatias
# A linha 0 até a última é processada em uma única chamada 
def proxima_geracao(grade, limiar_convencimento=2):

    total_linhas = len(grade)
    return processar_fatia_linhas(grade, 0, total_linhas, limiar_convencimento)


# Conta o total de células em cada estado
def contar_estados(grade):

    contagem = {IGNORANTE: 0, ESPALHADOR: 0, INATIVO: 0}
    for linha in grade:
        for celula in linha:
            contagem[celula] += 1
    return contagem


def executar_simulacao(
    linhas=500,
    colunas=500,
    geracoes=50,
    percentual_espalhadores=0.05,
    limiar_convencimento=3
):


    # Executa a simulação sequencial e exibe as estatísticas de desempenho
    grade = criar_grade(linhas, colunas, percentual_espalhadores)

    print("=== SIMULAÇÃO SEQUENCIAL REFATORADA ===")
    print(f"Matriz: {linhas}x{colunas} | Gerações: {geracoes} | Limiar: {limiar_convencimento}")
    
    inicio = time.time()

    for geracao in range(geracoes):
        grade = proxima_geracao(grade, limiar_convencimento)
        contagem = contar_estados(grade)

        if (geracao + 1) % 10 == 0 or geracao == geracoes - 1:
            print(f"Geração {geracao + 1:03d} | Ignorantes: {contagem[IGNORANTE]:>8,} | "
                  f"Espalhadores: {contagem[ESPALHADOR]:>8,} | Inativos: {contagem[INATIVO]:>8,}")

        if contagem[ESPALHADOR] == 0:
            print(f"\nA propagação encerrou na geração {geracao + 1}: não há mais espalhadores.")
            break

    fim = time.time()
    tempo_total = fim - inicio

    print(f"\nTempo total de execução (Sequencial): {tempo_total:.4f} segundos")
    return tempo_total


if __name__ == "__main__":
    executar_simulacao(linhas=500, colunas=500, geracoes=50)
