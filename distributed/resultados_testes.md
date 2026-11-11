# Resultados dos Testes — Versão Distribuída

## Teste 1 — Desempenho com 3 workers

### Configurações
- Matriz: 500 x 500
- Máximo de gerações: 50
- Gerações efetivamente executadas: 3
- Limiar de convencimento: 3
- Percentual inicial de espalhadores: 5%
- Quantidade de workers: 3
- Comunicação: Sockets TCP
- Ambiente: mesmo computador (localhost)

### Tempos das cinco execuções

| Teste | Tempo (s) |
|---|---:|
| 1 | 0.3466 |
| 2 | 0.3706 |
| 3 | 0.3828 |
| 4 | 0.3558 |
| 5 | 0.3612 |
| Média | 0.3634 |

### Resultado final dos estados
- Ignorantes: 236518
- Espalhadores: 0
- Inativos: 13482

### Observações
As cinco execuções apresentaram resultados finais idênticos.
A propagação encerrou na terceira geração, pois não havia mais espalhadores.

A média do tempo de execução da versão distribuída foi de 0.3634 segundos.

Os testes foram realizados com três workers no mesmo computador, utilizando comunicação TCP via localhost.


## Teste 2 — Comparação com a versão sequencial

### Tempos das cinco execuções

| Teste | Sequencial (s) | Distribuída (s) |
|---|---:|---:|
| 1 | 0.7356 | 0.3466 |
| 2 | 0.7511 | 0.3706 |
| 3 | 0.7412 | 0.3828 |
| 4 | 0.7559 | 0.3558 |
| 5 | 0.7869 | 0.3612 |
| Média | 0.7541 | 0.3634 |

### Indicadores de desempenho

- Speedup: 2.08
- Eficiência: 69.2%
- Redução do tempo: 51.8%

### Análise

A implementação distribuída apresentou menor tempo médio de execução em comparação com a implementação sequencial.

Com três workers, foi obtido um speedup aproximado de 2.08, indicando que a versão distribuída executou a simulação cerca de duas vezes mais rápido neste cenário.

Os resultados indicam um ganho de desempenho mesmo considerando a comunicação entre servidor e workers via Sockets TCP.


## Teste 3 — Comparação entre quantidades de workers

### Tempos médios

| Implementação | Tempo médio (s) |
|---|---:|
| Sequencial | 0.7541 |
| Distribuída - 2 workers | 0.4882 |
| Distribuída - 3 workers | 0.3634 |
| Distribuída - 4 workers | 0.3053 |

### Indicadores

| Workers | Speedup | Eficiência |
|---|---:|---:|
| 2 | 1.54 | 77.3% |
| 3 | 2.08 | 69.2% |
| 4 | 2.47 | 61.8% |

### Análise

O aumento da quantidade de workers proporcionou uma redução
no tempo médio de execução nos cenários avaliados.

A configuração com quatro workers apresentou o melhor
resultado, com tempo médio de 0.3053 segundos e speedup
de aproximadamente 2.47 em relação à versão sequencial.

Apesar da redução da eficiência percentual conforme
aumentou a quantidade de workers, houve ganho no tempo
absoluto de execução.

Os testes foram realizados em um único computador,
utilizando comunicação TCP via localhost.


## Teste 4 — Comparação com matriz 1000x1000

**Configuração:**
- Matriz: 1000x1000
- Semente: 123
- Percentual inicial de espalhadores: 5%
- Limiar de convencimento: 3
- Máximo de gerações: 50
- Repetições: 5
- Workers: 4 na versão distribuída

### Tempos sequenciais
- Teste 1: 3.1118 s
- Teste 2: 3.0484 s
- Teste 3: 3.0492 s
- Teste 4: 3.0962 s
- Teste 5: 3.1119 s
- Média: 3.0835 s

### Tempos distribuídos
- Teste 1: 1.2783 s
- Teste 2: 1.1376 s
- Teste 3: 1.1766 s
- Teste 4: 1.1838 s
- Teste 5: 1.2470 s
- Média: 1.2047 s

### Indicadores de desempenho
- Speedup: 2.56
- Eficiência: 63.99%
- Redução do tempo: 60.93%

**Observação:** Os testes foram realizados localmente, com os quatro workers executando na mesma máquina, utilizando comunicação TCP via localhost.
