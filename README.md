# Automacao e Gestao Centralizada de Monitoramento

## Objetivo
Implementar um servico centralizado de monitoramento capaz de avaliar conectividade, latencia e disponibilidade de hosts simulados em uma rede Docker dedicada.

## Arquitetura
O ambiente possui tres containers conectados a rede `monitoring_net`:

- `network-monitor`: executa o script Python e realiza testes ICMP.
- `monitored-host-1`: primeiro host de destino (`host1`).
- `monitored-host-2`: segundo host de destino (`host2`).

Fluxo:

```text
                  monitoring_net (Docker bridge)
             +-----------------------------------+
             |                                   |
             |       +------------------+        |
             |       | network-monitor  |        |
             |       | Python + ICMP    |        |
             |       +--------+---------+        |
             |                |                  |
             |          ping / ICMP              |
             |          /           \\           |
             | +-------v------+ +----v---------+ |
             | |    host1     | |    host2     | |
             | +--------------+ +--------------+ |
             +-----------------------------------+
                         |
                         v
                results/*.csv/log/txt
```

## Metricas coletadas
- Disponibilidade: resposta ou falha no ICMP.
- Latencia: tempo de resposta do `ping`, em milissegundos.
- Perda/falha: percentual de amostras sem resposta.
- Latencia minima, media e maxima no relatorio consolidado.

Por padrao, o monitor executa 10 ciclos com intervalo de 5 segundos.

## Estrutura
```text
network-monitor/
├── docker-compose.yml
├── README.md
├── .gitignore
├── monitor/
│   ├── Dockerfile
│   └── monitor.py
└── results/
    └── .gitkeep
```

## Execucao
### 1. Construir as imagens
```bash
docker compose build
```

### 2. Iniciar somente os hosts
```bash
docker compose up -d host1 host2
```

### 3. Conferir a rede dedicada
```bash
docker network ls
docker network inspect monitoring_net
```

### 4. Executar o monitoramento
```bash
docker compose run --rm monitor
```

Os resultados serao gravados em `results/monitoring.csv`, `results/monitoring.log` e `results/report.txt`.

## Teste de falha de conectividade
Primeiro execute o monitor com mais ciclos:

```bash
MONITOR_CYCLES=20 docker compose run --rm -e MONITOR_CYCLES=20 monitor
```

Enquanto ele estiver executando, em outro terminal interrompa um host:

```bash
docker stop monitored-host-2
```

O monitor devera registrar `host2` como `DOWN`. Depois restaure o host:

```bash
docker start monitored-host-2
```

Execute novamente o monitor para registrar a recuperacao.

## Testes realizados e resultados esperados
1. Ping entre containers: `host1` e `host2` devem responder enquanto estiverem ativos.
2. Medicao de latencia: cada resposta ICMP deve registrar o tempo em milissegundos.
3. Falha simulada: ao parar `host2`, o monitor deve detectar indisponibilidade.
4. Recuperacao: ao iniciar `host2` novamente, novas execucoes devem voltar a registrar disponibilidade.
5. Consolidacao: o arquivo `report.txt` apresenta disponibilidade, perda e latencias minima/media/maxima por host.

> Os valores numericos reais devem ser obtidos na maquina do estudante e usados no relatorio do laboratorio.
