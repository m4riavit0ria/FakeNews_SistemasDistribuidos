# Simulação Paralela e Distribuída de Propagação de Fake News

Este repositório contém a implementação do trabalho prático da disciplina de **Programação Distribuída e Paralela**. O objetivo é simular e analisar a dinâmica de propagação de *fake news* em uma população estruturada em uma matriz bidimensional (usando a **Vizinhança de Moore**), comparando o desempenho das abordagens **Sequencial**, **Paralela** e **Distribuída**.

---

## Integrantes do Grupo e Divisão de Papéis

* **Maria Vitoria — Líder da Versão Paralela & Refatoração Base:** Refatoração do código sequencial, implementação do paralelismo de memória compartilhada em Python via `multiprocessing` (livre do GIL) e garantia de sincronização/consistência.
* **Giovana — Líder da Versão Distribuída:** Arquitetura de sistemas distribuídos via Sockets/RMI, particionamento de matriz entre múltiplos nós e sincronização das bordas/fronteiras.
* **Patrícia — Líder de Inovações e Extensões:** Proposição e implementação das regras estendidas (probabilidades variáveis, influenciadores, bots, resistência, múltiplas fake news e visualizações gráficos).
* **Lívia — Líder de DevOps, Análise de Dados e Documentação:** Automação de testes experimentais, coleta de métricas, cálculo de Speedup/Eficiência, geração de gráficos comparativos e gestão do repositório.

---

## Visão Geral do Modelo

A população é representada por uma matriz $N \times M$, onde cada célula possui um dos seguintes estados:
* **0 (Ignorante):** Indivíduo que ainda não recebeu/não acredita na informação.
* **1 (Espalhador):** Indivíduo que acredita e compartilha a fake news com seus vizinhos.
* **2 (Inativo):** Indivíduo que recebeu a informação, mas deixou de compartilhá-la.

A transição de estados a cada geração $t \to t+1$ é calculada analisando os **8 vizinhos imediatos** (Vizinhança de Moore) de cada célula.

---

## Estrutura do Repositório

```text
.
├── sequential/        # Código sequencial original e refatorado
├── parallel/          # Implementação paralela com multiprocessing
├── distributed/       # Implementação distribuída com Sockets/RMI
├── extensions/        # Módulos de inovações (bots, influenciadores, etc.)
├── scripts/           # Scripts de automação de testes e geração de gráficos
├── docs/              # Apresentação do projeto e relatórios
├── requirements.txt   # Dependências do projeto Python
└── README.md          # Documentação principal
```

---

## Requisitos e Pré-requisitos

* **Python:** 3.8 ou superior.
* **Bibliotecas Python:** `matplotlib`, `numpy` (apenas para plotagem de gráficos/interface), `psutil`.

Para instalar todas as dependências necessárias, execute:

```bash
pip install -r requirements.txt
```

---

## Como Executar

### 1. Versão Sequencial
Para executar a simulação sequencial de referência:
```bash
python sequential/main.py --size 500 --generations 100 --spreaders 0.05
```

### 2. Versão Paralela (`multiprocessing`)
Para rodar a versão paralela especificando o número de workers/processos:
```bash
python parallel/main.py --size 500 --generations 100 --workers 4
```

### 3. Versão Distribuída (Sockets)

Para executar a versão distribuída, abra terminais separados para o servidor e os workers.

**No Servidor / Nó Mestre:**

    python distributed/servidor.py

**Nos Nós Trabalhadores (Workers):**

    python distributed/worker.py

**Configurações atuais:**
- Porta: 5000
- Quantidade de workers: 4
- Tamanho da matriz: 1000 × 1000
- Máximo de gerações: 50

A configuração dos parâmetros é realizada diretamente no arquivo `servidor.py`.

**Observação:** atualmente, a execução utiliza `127.0.0.1`, permitindo testes na mesma máquina. Para executar em computadores diferentes na rede local, será necessário configurar o IP do servidor no arquivo `worker.py`.

## Automação de Experimentos e Métricas

Para rodar a suíte automática de testes de desempenho (variando tamanho de matriz, threads e nós) e gerar as tabelas e gráficos comparativos de **Speedup** e **Eficiência**:

```bash
python scripts/run_benchmarks.py
```

Os resultados e gráficos gerados serão salvos automaticamente na pasta `docs/results/`.

---

## Inovações e Extensões Implementadas

O projeto conta com as seguintes melhorias:
1. **Probabilidades Assimétricas: ... (ALTERAR CONFORME DESENVOLVIMENTO DO PROJETO)**

---

## Licença e Referências

Trabalho desenvolvido para a disciplina de Programação Distribuída e Paralela.
