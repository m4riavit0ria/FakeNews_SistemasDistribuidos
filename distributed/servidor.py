from comum import criar_grade, contar_estados
import socket
import json
import time


def iniciar_servidor(ip, porta, quantidade_workers):
    servidor = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # Permite reutilizar a porta caso o servidor seja reiniciado
    servidor.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    servidor.bind((ip, porta))

    servidor.listen(quantidade_workers)

    print(f"Servidor aguardando {quantidade_workers} workers...")

    workers = []

    for i in range(quantidade_workers):
        cliente, endereco = servidor.accept()

        workers.append(cliente)

        print(f"Worker {i + 1} conectado: {endereco}")

    return servidor, workers


def receber_bytes(cliente, quantidade):
    dados = b""

    while len(dados) < quantidade:
        parte = cliente.recv(quantidade - len(dados))

        if not parte:
            raise ConnectionError("Conexão encerrada.")

        dados += parte

    return dados


def receber_mensagem(cliente):
    cabecalho = receber_bytes(cliente, 4)

    tamanho = int.from_bytes(cabecalho, byteorder="big")

    dados = receber_bytes(cliente, tamanho)

    return json.loads(dados.decode("utf-8"))


def enviar_mensagem(cliente, mensagem):
    dados = json.dumps(mensagem).encode("utf-8")

    cabecalho = len(dados).to_bytes(4, byteorder="big")

    cliente.sendall(cabecalho + dados)


def dividir_linhas(total_linhas, quantidade_workers):

    if quantidade_workers <= 0 or quantidade_workers > total_linhas:
        raise ValueError("Quantidade de workers inválida.")

    blocos = []

    linhas_por_worker = total_linhas // quantidade_workers
    resto = total_linhas % quantidade_workers

    inicio = 0

    for i in range(quantidade_workers):
        quantidade = linhas_por_worker

        if i < resto:
            quantidade += 1

        fim = inicio + quantidade

        blocos.append((inicio, fim))

        inicio = fim

    return blocos


def preparar_bloco(grade, inicio, fim):
    total_linhas = len(grade)

    inicio_halo = max(0, inicio - 1)

    fim_halo = min(total_linhas, fim + 1)

    return grade[inicio_halo:fim_halo]


def distribuir_tarefas(
    workers,
    grade,
    blocos,
    limiar_convencimento
):
    total_linhas = len(grade)

    for i, worker in enumerate(workers):
        inicio, fim = blocos[i]

        tarefa = {
            "grade": preparar_bloco(grade, inicio, fim),
            "linha_inicio": inicio,
            "linha_fim": fim,
            "total_linhas": total_linhas,
            "limiar_convencimento": limiar_convencimento
        }

        enviar_mensagem(worker, tarefa)

        print(
            f"Tarefa enviada ao Worker {i + 1}: "
            f"linhas {inicio} até {fim - 1}"
        )


def receber_resultados(workers, blocos):
    resultados = []

    for i, worker in enumerate(workers):
        mensagem = receber_mensagem(worker)

        inicio_esperado, fim_esperado = blocos[i]

        if mensagem["linha_inicio"] != inicio_esperado:
            raise ValueError("Resultado recebido com linhas incorretas.")

        resultados.append(mensagem["resultado"])

        print(
            f"Resultado recebido do Worker {i + 1}: "
            f"linhas {inicio_esperado} até {fim_esperado - 1}"
        )

    # Junta os blocos para formar a nova matriz
    nova_grade = []

    for bloco in resultados:
        nova_grade.extend(bloco)

    return nova_grade


def executar_simulacao(grade, workers, quantidade_geracoes, limiar_convencimento):
    quantidade_workers = len(workers)
    total_linhas = len(grade)
    blocos = dividir_linhas(total_linhas, quantidade_workers)

    for geracao in range(quantidade_geracoes):
        print(f"\n--- Geração {geracao + 1} ---")

        distribuir_tarefas(workers, grade, blocos, limiar_convencimento)
        grade = receber_resultados(workers, blocos)

        print(f"Geração {geracao + 1} concluída!")

        contagem = contar_estados(grade)

        if contagem[1] == 0:
            print(
                f"\nA propagação encerrou na geração {geracao + 1}: "
                "não há mais espalhadores."
            )
            break

    return grade

def encerrar_workers(workers):
    for worker in workers:
        try:
            enviar_mensagem(worker, {"acao": "encerrar"})
            worker.close()
        except OSError:
            pass


def main():
    IP = "127.0.0.1"
    PORTA = 5000

    QUANTIDADE_WORKERS = 4
    LINHAS = 1000
    COLUNAS = 1000
    GERACOES = 50
    LIMIAR_CONVENCIMENTO = 3
    REPETICOES = 5

    tempos = []

    servidor = None
    workers = []

    try:
        servidor, workers = iniciar_servidor(
            IP, PORTA, QUANTIDADE_WORKERS
        )

        print("\nIniciando testes de desempenho!")

        for teste in range(REPETICOES):
            print(f"\n========== TESTE {teste + 1} ==========")

            grade = criar_grade(LINHAS, COLUNAS)

            inicio = time.perf_counter()

            resultado = executar_simulacao(
                grade, workers, GERACOES, LIMIAR_CONVENCIMENTO
            )

            fim = time.perf_counter()
            tempo_total = fim - inicio

            tempos.append(tempo_total)

            print(f"Tempo do teste {teste + 1}: {tempo_total:.4f} segundos")
            print("Quantidade de indivíduos por estado:")
            print(contar_estados(resultado))

        media = sum(tempos) / len(tempos)

        print("\n========== RESULTADO FINAL ==========")

        for i, tempo in enumerate(tempos):
            print(f"Teste {i + 1}: {tempo:.4f} segundos")

        print(f"\nMédia dos 5 testes: {media:.4f} segundos")

    finally:
        encerrar_workers(workers)

        if servidor:
            servidor.close()


if __name__ == "__main__":
    main()
