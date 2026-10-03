import csv
import os
import re
import subprocess
import time
from datetime import datetime
from pathlib import Path

HOSTS = [h.strip() for h in os.getenv("MONITOR_HOSTS", "host1,host2").split(",") if h.strip()]
INTERVAL = int(os.getenv("MONITOR_INTERVAL", "5"))
CYCLES = int(os.getenv("MONITOR_CYCLES", "10"))
TIMEOUT = int(os.getenv("PING_TIMEOUT", "1"))
RESULT_DIR = Path(os.getenv("RESULT_DIR", "/app/results"))
RESULT_DIR.mkdir(parents=True, exist_ok=True)

CSV_FILE = RESULT_DIR / "monitoring.csv"
LOG_FILE = RESULT_DIR / "monitoring.log"
REPORT_FILE = RESULT_DIR / "report.txt"


def ping(host: str):
    cmd = ["ping", "-c", "1", "-W", str(TIMEOUT), host]
    started = time.perf_counter()
    result = subprocess.run(cmd, capture_output=True, text=True)
    elapsed_ms = (time.perf_counter() - started) * 1000

    if result.returncode == 0:
        match = re.search(r"time[=<]([0-9.]+)\s*ms", result.stdout)
        latency = float(match.group(1)) if match else round(elapsed_ms, 3)
        return True, latency
    return False, None


def write_log(message: str):
    print(message, flush=True)
    with LOG_FILE.open("a", encoding="utf-8") as file:
        file.write(message + "\n")


def collect():
    new_file = not CSV_FILE.exists()
    with CSV_FILE.open("a", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        if new_file:
            writer.writerow(["timestamp", "host", "available", "latency_ms"])

        for cycle in range(1, CYCLES + 1):
            write_log(f"--- Ciclo {cycle}/{CYCLES} ---")
            for host in HOSTS:
                timestamp = datetime.now().isoformat(timespec="seconds")
                available, latency = ping(host)
                status = "UP" if available else "DOWN"
                latency_text = f"{latency:.3f} ms" if latency is not None else "N/A"
                writer.writerow([timestamp, host, available, latency if latency is not None else ""])
                file.flush()
                write_log(f"[{timestamp}] {host}: {status} | latencia={latency_text}")

            if cycle < CYCLES:
                time.sleep(INTERVAL)


def generate_report():
    stats = {host: {"total": 0, "up": 0, "latencies": []} for host in HOSTS}

    with CSV_FILE.open(newline="", encoding="utf-8") as file:
        for row in csv.DictReader(file):
            host = row["host"]
            if host not in stats:
                stats[host] = {"total": 0, "up": 0, "latencies": []}
            stats[host]["total"] += 1
            if row["available"] == "True":
                stats[host]["up"] += 1
                if row["latency_ms"]:
                    stats[host]["latencies"].append(float(row["latency_ms"]))

    lines = [
        "RELATORIO CONSOLIDADO DE MONITORAMENTO",
        "=" * 42,
        f"Hosts monitorados: {', '.join(HOSTS)}",
        f"Intervalo configurado: {INTERVAL} segundos",
        f"Ciclos executados nesta execucao: {CYCLES}",
        "",
    ]

    for host, data in stats.items():
        total = data["total"]
        up = data["up"]
        availability = (up / total * 100) if total else 0
        loss = 100 - availability
        latencies = data["latencies"]
        avg = sum(latencies) / len(latencies) if latencies else 0
        minimum = min(latencies) if latencies else 0
        maximum = max(latencies) if latencies else 0

        lines.extend([
            f"Host: {host}",
            f"  Amostras: {total}",
            f"  Disponibilidade: {availability:.2f}%",
            f"  Perda/Falha: {loss:.2f}%",
            f"  Latencia media: {avg:.3f} ms",
            f"  Latencia minima: {minimum:.3f} ms",
            f"  Latencia maxima: {maximum:.3f} ms",
            "",
        ])

    REPORT_FILE.write_text("\n".join(lines), encoding="utf-8")
    write_log(f"Relatorio gerado em {REPORT_FILE}")


if __name__ == "__main__":
    write_log(f"Iniciando monitoramento: hosts={HOSTS}, intervalo={INTERVAL}s, ciclos={CYCLES}")
    collect()
    generate_report()
