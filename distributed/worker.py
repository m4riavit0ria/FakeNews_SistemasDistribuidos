import socket
import json

from comum import processar_bloco

def iniciar_worker(ip_servidor, porta):
    cliente = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    cliente.connect((ip_servidor, porta))

    print("Worker conectado ao servidor!")

    return cliente

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

def processar_tarefa(tarefa):
    resultado = processar_bloco(
        grade_com_halo=tarefa["grade"],
        linha_inicio=tarefa["linha_inicio"],
        linha_fim=tarefa["linha_fim"],
        total_linhas=tarefa["total_linhas"],
        limiar_convencimento=tarefa["limiar_convencimento"]
    )

    return {
        "linha_inicio": tarefa["linha_inicio"],
        "resultado": resultado
    }

def enviar_mensagem(cliente, mensagem):
    dados = json.dumps(mensagem).encode("utf-8")

    cabecalho = len(dados).to_bytes(4, byteorder="big")

    cliente.sendall(cabecalho + dados)

def executar_worker(ip_servidor, porta):
    cliente = iniciar_worker(ip_servidor, porta)

    try:
        while True:
            tarefa = receber_mensagem(cliente)

            if tarefa.get("acao") == "encerrar":
                print("Servidor encerrou a execução.")
                break

            resultado = processar_tarefa(tarefa)

            enviar_mensagem(cliente, resultado)

            print(
                f"Bloco das linhas {resultado['linha_inicio']} "
                "processado com sucesso!"
            )

    except ConnectionError:
        print("Conexão com o servidor encerrada.")

    finally:
        cliente.close()

if __name__ == "__main__":
    executar_worker("127.0.0.1", 5000)