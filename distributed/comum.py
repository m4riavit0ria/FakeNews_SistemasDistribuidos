import random

# Estados possíveis de cada indivíduo
IGNORANTE = 0
ESPALHADOR = 1
INATIVO = 2


def criar_grade(linhas, colunas, percentual_espalhadores=0.05, semente=123):
    
    gerador = random.Random(semente)

    grade = [[IGNORANTE for _ in range(colunas)] for _ in range(linhas)]

    total_celulas = linhas * colunas
    total_espalhadores = int(total_celulas * percentual_espalhadores)

    for _ in range(total_espalhadores):
        i = gerador.randint(0, linhas - 1)
        j = gerador.randint(0, colunas - 1)
        grade[i][j] = ESPALHADOR

    return grade


def contar_vizinhos_espalhadores(
    grade, i, j, total_linhas, total_colunas
):
    
    total = 0

    for di in (-1, 0, 1):
        for dj in (-1, 0, 1):

            if di == 0 and dj == 0:
                continue

            ni = i + di
            nj = j + dj

            if 0 <= ni < total_linhas and 0 <= nj < total_colunas:
                if grade[ni][nj] == ESPALHADOR:
                    total += 1

    return total


def processar_bloco(
    grade_com_halo,
    linha_inicio,
    linha_fim,
    total_linhas,
    limiar_convencimento
):

    total_colunas = len(grade_com_halo[0])

    # Primeira linha global presente no bloco recebido
    inicio_halo = max(0, linha_inicio - 1)

    fatia_nova = []

    for i in range(linha_inicio, linha_fim):

        # Converte o índice global para o índice local do bloco
        indice_local = i - inicio_halo

        linha_calculada = []

        for j in range(total_colunas):

            estado_atual = grade_com_halo[indice_local][j]

            if estado_atual == IGNORANTE:

                vizinhos = 0

                for di in (-1, 0, 1):
                    for dj in (-1, 0, 1):

                        if di == 0 and dj == 0:
                            continue

                        linha_vizinha_global = i + di
                        coluna_vizinha = j + dj

                        if (
                            0 <= linha_vizinha_global < total_linhas
                            and 0 <= coluna_vizinha < total_colunas
                        ):
                            linha_vizinha_local = (
                                linha_vizinha_global - inicio_halo
                            )

                            if (
                                grade_com_halo[linha_vizinha_local]
                                [coluna_vizinha] == ESPALHADOR
                            ):
                                vizinhos += 1

                if vizinhos >= limiar_convencimento:
                    linha_calculada.append(ESPALHADOR)
                else:
                    linha_calculada.append(IGNORANTE)

            elif estado_atual == ESPALHADOR:
                linha_calculada.append(INATIVO)

            else:
                linha_calculada.append(INATIVO)

        fatia_nova.append(linha_calculada)

    return fatia_nova


def contar_estados(grade):
    
    contagem = {
        IGNORANTE: 0,
        ESPALHADOR: 0,
        INATIVO: 0
    }

    for linha in grade:
        for celula in linha:
            contagem[celula] += 1

    return contagem
