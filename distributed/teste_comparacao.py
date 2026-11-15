import random
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))

from comum import criar_grade, processar_bloco, contar_estados, ESPALHADOR

from sequential.simulacao_sequencial import (
    proxima_geracao,
    criar_grade as criar_grade_sequencial
)


def executar_distribuida(grade, quantidade_workers, geracoes):
    total_linhas = len(grade)

    linhas_por_worker = total_linhas // quantidade_workers
    resto = total_linhas % quantidade_workers

    blocos = []
    inicio = 0

    for i in range(quantidade_workers):
        quantidade = linhas_por_worker

        if i < resto:
            quantidade += 1

        fim = inicio + quantidade
        blocos.append((inicio, fim))
        inicio = fim

    for _ in range(geracoes):
        nova_grade = []

        for inicio, fim in blocos:
            inicio_halo = max(0, inicio - 1)
            fim_halo = min(total_linhas, fim + 1)

            grade_com_halo = grade[inicio_halo:fim_halo]

            # Removido o limiar estático, agora usa nossa nova lógica de probabilidades
            resultado = processar_bloco(
                grade_com_halo,
                inicio,
                fim,
                total_linhas
            )

            nova_grade.extend(resultado)

        grade = nova_grade

        if contar_estados(grade)[ESPALHADOR] == 0:
            break

    return grade


# Configurações iguais às dos testes de desempenho
LINHAS = 1000
COLUNAS = 1000
GERACOES = 50
WORKERS = 4
SEMENTE = 123

# Criação das matrizes iniciais (agora usando as inovações embutidas)
grade_sequencial = criar_grade_sequencial(
    LINHAS,
    COLUNAS,
    semente=SEMENTE
)

grade_distribuida = criar_grade(
    LINHAS,
    COLUNAS,
    semente=SEMENTE
)

# Verifica se as matrizes iniciais são iguais
if grade_sequencial != grade_distribuida:
    print("ERRO: as matrizes iniciais são diferentes!")
    sys.exit()

print("Matrizes iniciais idênticas!")

# Executa a simulação sequencial
print("\nRodando simulação sequencial...")
random.seed(SEMENTE) # <-- Sincroniza a roleta para a sequencial
for _ in range(GERACOES):
    grade_sequencial = proxima_geracao(grade_sequencial)

    if contar_estados(grade_sequencial)[ESPALHADOR] == 0:
        break

# Executa a simulação distribuída por blocos simulados
print("Rodando simulação distribuída...")
random.seed(SEMENTE) # <-- Sincroniza a roleta com a mesma semente para a distribuída
grade_distribuida = executar_distribuida(
    grade_distribuida,
    WORKERS,
    GERACOES
)

# Compara os resultados finais
print("\nQuantidade de indivíduos por estado:")
print(contar_estados(grade_sequencial))

if grade_sequencial == grade_distribuida:
    print("\nSUCESSO: as matrizes finais são idênticas!")
else:
    print("\nERRO: as matrizes finais são diferentes!")