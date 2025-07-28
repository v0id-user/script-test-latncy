import asyncio
import json
import time
import statistics
import websockets

from rich.live import Live
from rich.table import Table
from rich.console import Console
from datetime import datetime, timezone

try:
    import nest_asyncio
    nest_asyncio.apply()
except ImportError:
    pass

import json
import urllib.request


ENDPOINT = "wss://edge-do-latency-test-19aca.v0id.me/"
PING_INTERVAL = 1
TEST_DURATION = 30  # seconds
latencies = []
console = Console()

def get_country_city_region() -> str:
    try:
        url = f"http://ip-api.com/json"
        with urllib.request.urlopen(url, timeout=5) as response:
            data = json.load(response)
            if data.get("status") == "success":
                return f"{data.get('country', 'Unknown')}, {data.get('city', 'Unknown')}, {data.get('regionName', 'Unknown')}"
            else:
                return f"Error: {data.get('message', 'Unknown error')}"
    except Exception as e:
        return f"Request failed: {e}"


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

        # Final stats
        p50 = statistics.median(latencies)
        p95 = percentile(latencies, 95)
        p99 = percentile(latencies, 99)
        sample_count = len(latencies)

        # Display table one last time
        console.print(create_table())
        console.print("\n[bold green]✅ Latency test completed.[/bold green]")

        timestamp_unix = time.time()
        timestamp_utc = datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')
        result = {
            "timestamp_unix": timestamp_unix,
            "timestamp_utc": timestamp_utc,
            "region": get_country_city_region(),
            "p50": round(p50, 2),
            "p95": round(p95, 2),
            "p99": round(p99, 2),
            "samples": sample_count
        }
        print("\n📤 [Raw Output for Log/Copy]")
        print(json.dumps(result, indent=2))


# Run it safely in all environments
if __name__ == "__main__":
    try:
        asyncio.run(main())
    except RuntimeError:
        loop = asyncio.get_event_loop()
        loop.run_until_complete(main())
