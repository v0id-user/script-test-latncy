import asyncio
import json
import time
import statistics
import websockets

from rich.live import Live
from rich.table import Table
from rich.console import Console

# Optional: Fix for interactive environments (like VS Code, IPython, etc.)
try:
    import nest_asyncio
    nest_asyncio.apply()
except ImportError:
    pass

ENDPOINT = "wss://edge-do-latency-test-19aca.v0id.me/"
PING_INTERVAL = 1
TEST_DURATION = 30  # seconds
latencies = []
console = Console()

def percentile(data, percent):
    if not data:
        return None
    k = int(round((percent / 100) * len(data)))
    return sorted(data)[min(k - 1, len(data) - 1)]

def create_table():
    table = Table(title="📡 Erebus Edge WebSocket Latency Monitor")

    table.add_column("RTT (ms)", justify="right")
    table.add_column("p50 (ms)", justify="right")
    table.add_column("p95 (ms)", justify="right")
    table.add_column("p99 (ms)", justify="right")
    table.add_column("Samples", justify="right")

    rtt = f"{latencies[-1]:.2f}" if latencies else "-"
    p50 = f"{statistics.median(latencies):.2f}" if latencies else "-"
    p95 = f"{percentile(latencies, 95):.2f}" if latencies else "-"
    p99 = f"{percentile(latencies, 99):.2f}" if latencies else "-"
    count = str(len(latencies))

    table.add_row(rtt, p50, p95, p99, count)
    return table

async def send_ping(ws):
    while True:
        await ws.send(json.dumps({
            "type": "ping",
            "timestamp": time.time()
        }))
        await asyncio.sleep(PING_INTERVAL)

async def receive_pong(ws):
    async for msg in ws:
        try:
            data = json.loads(msg)
            if data.get("type") == "pong":
                sent = data.get("timestamp")
                rtt = (time.time() - sent) * 1000
                latencies.append(rtt)
        except:
            pass

async def main():
    async with websockets.connect(ENDPOINT) as ws:
        sender = asyncio.create_task(send_ping(ws))
        receiver = asyncio.create_task(receive_pong(ws))

        with Live(create_table(), refresh_per_second=4, console=console) as live:
            start = time.time()
            while time.time() - start < TEST_DURATION:
                live.update(create_table())
                await asyncio.sleep(0.5)

        sender.cancel()
        receiver.cancel()
        console.print("\n[bold green]✅ Latency test completed.[/bold green]")

# Run it safely in all environments
if __name__ == "__main__":
    try:
        asyncio.run(main())
    except RuntimeError:
        loop = asyncio.get_event_loop()
        loop.run_until_complete(main())
