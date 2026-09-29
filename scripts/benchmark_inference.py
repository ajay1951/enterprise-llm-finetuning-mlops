#!/usr/bin/env python3
import asyncio
import time
import json
import statistics
import aiohttp
import os
from pathlib import Path

# Config
TARGET_URL = os.environ.get("TARGET_URL", "http://localhost:8080/v1/chat/completions")
CONCURRENCY_LEVELS = [1, 2, 4]
ITERATIONS = 5
WARMUP_ITERATIONS = 2
PROMPT = "Explain the architecture of a Transformer neural network in detail."


async def run_single_request(session, payload):
    start_time = time.time()
    ttft = None

    try:
        async with session.post(TARGET_URL, json=payload) as response:
            if response.status != 200:
                return {"error": f"HTTP {response.status}"}

            if payload.get("stream"):
                first_token = False
                async for line in response.content:
                    if line and not first_token:
                        ttft = time.time() - start_time
                        first_token = True
            else:
                await response.json()

            end_time = time.time()
            return {
                "ttft": ttft if ttft else end_time - start_time,
                "latency": end_time - start_time,
                "status": "success",
            }
    except Exception as e:
        return {"error": str(e)}


async def run_concurrency_test(concurrency):
    print(f"\n--- Running Concurrency Level: {concurrency} ---")
    payload = {
        "model": "benchmark-model",
        "messages": [{"role": "user", "content": PROMPT}],
        "stream": True,
        "max_tokens": 100,
    }

    async with aiohttp.ClientSession() as session:
        # Warmup
        print(f"Warming up ({WARMUP_ITERATIONS} iterations)...")
        for _ in range(WARMUP_ITERATIONS):
            await run_single_request(session, payload)

        print(f"Running benchmark ({ITERATIONS} iterations)...")
        results = []
        for _ in range(ITERATIONS):
            tasks = [run_single_request(session, payload) for _ in range(concurrency)]
            batch_results = await asyncio.gather(*tasks)
            results.extend(batch_results)

        return results


def calculate_metrics(results, concurrency):
    successful = [r for r in results if "error" not in r]
    errors = len(results) - len(successful)

    if not successful:
        return {"concurrency": concurrency, "error": "All requests failed"}

    latencies = [r["latency"] * 1000 for r in successful]  # ms
    ttfts = [r["ttft"] * 1000 for r in successful]  # ms

    # Rough estimate of tokens based on max_tokens=100
    total_tokens = len(successful) * 100
    total_time_seconds = sum([r["latency"] for r in successful])
    throughput = total_tokens / total_time_seconds if total_time_seconds > 0 else 0

    return {
        "concurrency": concurrency,
        "success_rate": f"{(len(successful) / len(results)) * 100}%",
        "errors": errors,
        "ttft_ms": {
            "avg": sum(ttfts) / len(ttfts),
            "p50": statistics.median(ttfts),
            "p95": statistics.quantiles(ttfts, n=20)[18]
            if len(ttfts) > 1
            else ttfts[0],
        },
        "latency_ms": {
            "avg": sum(latencies) / len(latencies),
            "p50": statistics.median(latencies),
            "p95": statistics.quantiles(latencies, n=20)[18]
            if len(latencies) > 1
            else latencies[0],
        },
        "throughput_tokens_per_sec": throughput,
    }


async def main():
    print(f"Starting vLLM Benchmark Target: {TARGET_URL}")
    print(f"CPU Mode Test - Concurrency levels: {CONCURRENCY_LEVELS}")

    all_metrics = []

    for c in CONCURRENCY_LEVELS:
        results = await run_concurrency_test(c)
        metrics = calculate_metrics(results, c)
        all_metrics.append(metrics)
        print(json.dumps(metrics, indent=2))

    # Save results
    save_dir = Path("benchmarks/inference/cpu")
    save_dir.mkdir(parents=True, exist_ok=True)

    with open(save_dir / "results.json", "w") as f:
        json.dump(all_metrics, f, indent=2)

    print(f"\nBenchmark complete. Results saved to {save_dir}/results.json")


if __name__ == "__main__":
    asyncio.run(main())
