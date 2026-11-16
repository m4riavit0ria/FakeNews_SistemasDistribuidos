# Simulação Paralela e Distribuída de Propagação de Fake News

Projeto desenvolvido para a disciplina de **Sistemas Distribuídos (UTFPR)** com o objetivo de modelar, implementar e comparar o desempenho da propagação de notícias falsas em uma grade bidimensional ($N \times N$) utilizando vizinhança de Moore sob três paradigmas de execução: **Sequencial**, **Paralela (`multiprocessing`)** e **Distribuída (Sockets TCP)**.

---

## 1. Descrição do Modelo e Regras de Transição

O sistema simula uma rede de indivíduos dispostos em uma matriz bidimensional onde cada célula interage com seus 8 vizinhos imediatos (vizinhança de Moore). Os estados possíveis de cada agente são:

* **Ignorante (`0`):** Indivíduo suscetível que ainda não teve contato com a notícia falsa.
* **Espalhador (`1`):** Indivíduo que acredita na notícia falsa e a propaga para vizinhos ignorantes.
* **Inativo (`2`):** Indivíduo que perdeu o interesse em compartilhar a notícia (imune temporariamente).
* **Bot (`3`):** Super-espalhador automatizado que permanece ativo durante toda a simulação com **peso dobrado** de influência ($+2$).
* **Fact-Checker (`-1`):** Agente verificador imune que reduz em **70%** a probabilidade de contágio ao seu redor ($\text{chance} \times 0,3$).

### Regras de Evolução por Geração
1. **Contágio (`Ignorante -> Espalhador`):** Se houver ao menos um vizinho espalhador (peso `+1`) ou bot (peso `+2`), a probabilidade base de convencimento é `P = 0,20 + 0,15 × peso_infeccao` (atenuada para `0,3 × P` na presença de um *Fact-Checker*).
2. **Maturação (`Espalhador -> Inativo`):** A cada geração, um espalhador comum tem **35%** de chance de cessar o compartilhamento.
3. **Recaída (`Inativo -> Ignorante`):** A cada geração, um indivíduo inativo tem **5%** de chance de esquecer a checagem e tornar-se suscetível novamente.
4. **Reprodutibilidade:** Todas as execuções utilizam semente fixa (`semente = 123`) para garantir que as três implementações partam exatamente da mesma matriz inicial e preservem o comportamento lógico.

---

## 2. Estrutura do Repositório

```text
FakeNews_SistemasDistribuidos/
├── sequential/
│   └── simulacao_sequencial.py       # Implementação sequencial base
├── parallel/
│   └── simulacao_paralela.py         # Implementação paralela com multiprocessing.Pool
├── distributed/
│   ├── comum.py                      # Regras do modelo e processamento de blocos com halos
│   ├── servidor.py                   # Nó mestre TCP que divide a matriz e coordena gerações
│   ├── worker.py                     # Nó trabalhador TCP que processa fatias da grade
│   ├── teste_comparacao.py           # Validação de equivalência lógica entre versões
│   └── resultados_testes.md          # Histórico de testes preliminares
├── experimentos/
│   ├── rodar_experimentos.py         # Orquestrador automatizado de benchmarks (CSV)
│   └── analisar_resultados.py        # Análise estatística (pandas) e gráficos (matplotlib)
├── resultados/
│   ├── ambiente_experimental.json    # Metadados de hardware e SO coletados
│   ├── experimentos.csv              # Dados brutos das 78 execuções experimentais
│   ├── resumo_metricas.csv           # Médias e desvios padrão agrupados por cenário
│   └── graficos/                     # Gráficos PNG gerados para o relatório
├── requirements.txt                  # Dependências Python para análise e gráficos
└── README.md                         # Documentação do projeto
```

---

## 3. Configuração do Ambiente Experimental

Os experimentos foram executados localmente sob as seguintes especificações de hardware e software:

| Componente | Especificação |
| :--- | :--- |
| **Processador (CPU)** | AMD Ryzen 5 7235HS |
| **Núcleos Físicos / Lógicos** | 4 núcleos físicos / 8 processadores lógicos (threads) |
| **Memória RAM** | 15,69 GB (aprox. 16 GB) |
| **Sistema Operacional** | Microsoft Windows 11 Home (Build 10.0.26300) |
| **Linguagem e Versão** | Python 3.13.17 |
| **Comunicação Distribuída** | Sockets TCP (`127.0.0.1`, serialização JSON com cabeçalho de 4 bytes) |

---

## 4. Requisitos e Instalação

A execução das simulações utiliza apenas bibliotecas nativas da biblioteca padrão do Python (`socket`, `multiprocessing`, `json`, `random`, `csv`, `time`). Para executar os scripts de análise e geração de gráficos, instale as dependências listadas em `requirements.txt`:

```powershell
pip install -r requirements.txt
```

---

## 5. Como Executar Cada Versão

### 5.1. Versão Sequencial
```powershell
python sequential/simulacao_sequencial.py
```

### 5.2. Versão Paralela (`multiprocessing`)
```powershell
python parallel/simulacao_paralela.py
```

### 5.3. Versão Distribuída (Sockets TCP)
Abra um terminal para o servidor e 4 terminais para os workers dentro da pasta `distributed/`:
```powershell
cd distributed
python servidor.py
```
Em outros 4 terminais (também dentro de `distributed/`):
```powershell
python worker.py
```

### 5.4. Bateria Completa de Experimentos e Geração de Gráficos
Na raiz do repositório:
```powershell
python experimentos/rodar_experimentos.py
python experimentos/analisar_resultados.py
```

---

## 6. Resultados Experimentais e Análise de Desempenho

### 6.1. Comparação Geral por Tamanho da Matriz (50 gerações, 3% espalhadores)

| Dimensão ($N \times N$) | Sequencial (s) | Paralela — 4 proc. (s) | Distribuída — 4 workers (s) | Speedup Paralela | Speedup Distribuída |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **100 × 100** | 0,3507 | 0,3946 | 0,2255 | 0,89× | 1,56× |
| **500 × 500** | 8,3955 | 4,2577 | 4,4038 | 1,97× | 1,91× |
| **1000 × 1000** | 33,2224 | 15,6057 | 16,4222 | 2,13× | 2,02× |
| **2000 × 2000** | 149,5590 | 74,3004 | 91,9155 | 2,01× | 1,63× |

### 6.2. Escalabilidade por Processos na Versão Paralela (Matriz 500×500, 50 gerações)

| Processos ($N$) | Tempo Médio (s) | Speedup | Eficiência (%) |
| :---: | :---: | :---: | :---: |
| **1** | 9,0619 | 1,00× | 100,00% |
| **2** | 5,3605 | 1,69× | 84,52% |
| **4** | 4,1987 | 2,16× | 53,96% |
| **8** | 4,2700 | 2,12× | 26,53% |

### 6.3. Escalabilidade por Workers na Versão Distribuída (Matriz 500×500, 50 gerações)

| Workers ($N$) | Tempo Médio (s) | Speedup | Eficiência (%) |
| :---: | :---: | :---: | :---: |
| **1** | 11,1444 | 1,00× | 100,00% |
| **2** | 6,2586 | 1,78× | 89,03% |
| **3** | 4,8645 | 2,29× | 76,37% |
| **4** | 4,4125 | 2,53× | 63,14% |

### 6.4. Principais Gargalos Identificados
1. **Matrizes pequenas em paralelo (`100 × 100`):** A versão paralela ($0,3946\text{ s}$) foi mais lenta que a sequencial ($0,3507\text{ s}$) porque o custo de criação dos processos (`spawn` no Windows) e serialização da grade supera o tempo de cálculo de apenas 10.000 células.
2. **Saturação acima de 4 processos:** Como o processador possui **4 núcleos físicos**, escalar de 4 para 8 processos não trouxe ganho de tempo ($4,20\text{ s} \to 4,27\text{ s}$) e reduziu a eficiência de $53,96\%$ para $26,53\%$ devido à contenção de CPU e cópia de memória entre processos.
3. **Custo de comunicação na versão distribuída:** Em matrizes grandes ($2000 \times 2000$), a versão distribuída ($91,92\text{ s}$) fica atrás da paralela ($74,30\text{ s}$) devido à serialização JSON e à transferência síncrona das fatias e bordas (*halos*) via Sockets TCP a cada geração.

---

## 7. Como Gerar o Arquivo ZIP de Entrega

Para empacotar o repositório limpo (excluindo caches `__pycache__` e metadados internos do Git), execute na raiz do projeto:

```powershell
Compress-Archive -Path sequential, parallel, distributed, experimentos, resultados, requirements.txt, README.md -DestinationPath FakeNews_SistemasDistribuidos_Entrega.zip -Force
```

---

## 8. Referências
* DALEY, D. J.; KENDALL, D. G. *Epidemics and Rumours*. Nature, v. 204, p. 1118, 1964.
* Documentação oficial do Python 3.13 — módulos `multiprocessing` e `socket`.