import asyncio
import httpx
import time
import argparse
import statistics


async def send_request(client, url, payload, headers):
    start = time.time()
    try:
        resp = await client.post(url, json=payload, headers=headers)
        return (resp.status_code, time.time() - start)
    except Exception as e:
        return (500, time.time() - start)


async def run_load_test(url, model_name, concurrency, total_requests):
    print(f"Starting load test on {url} for model '{model_name}'")
    print(f"Concurrency: {concurrency}, Total Requests: {total_requests}")

    payload = {
        "model": model_name,
        "messages": [{"role": "user", "content": "Hello, perform a load test."}],
    }
    headers = {"Content-Type": "application/json"}

    async with httpx.AsyncClient(timeout=30.0) as client:
        start_time = time.time()

        # We will dispatch requests in batches of 'concurrency'
        latencies = []
        status_codes = {}

        pending = total_requests

        while pending > 0:
            batch_size = min(concurrency, pending)
            tasks = [
                send_request(client, url, payload, headers) for _ in range(batch_size)
            ]
            results = await asyncio.gather(*tasks)

            for status, lat in results:
                latencies.append(lat)
                status_codes[status] = status_codes.get(status, 0) + 1

            pending -= batch_size

        total_time = time.time() - start_time

    print("\n--- Load Test Results ---")
    print(f"Total time: {total_time:.2f} seconds")
    print(f"Requests/sec: {total_requests / total_time:.2f}")
    print(f"Status codes: {status_codes}")

    if latencies:
        print(f"Average latency: {statistics.mean(latencies):.2f}s")
        print(
            f"p50 latency: {statistics.quantiles(latencies, n=100)[49]:.2f}s"
            if len(latencies) >= 2
            else f"p50: {latencies[0]:.2f}s"
        )
        print(
            f"p95 latency: {statistics.quantiles(latencies, n=100)[94]:.2f}s"
            if len(latencies) >= 20
            else f"p95: N/A"
        )
        print(
            f"p99 latency: {statistics.quantiles(latencies, n=100)[98]:.2f}s"
            if len(latencies) >= 100
            else f"p99: N/A"
        )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="ForgeLLM Inference Load Tester")
    parser.add_argument(
        "--url",
        default="http://localhost:8000/v1/chat/completions",
        help="Inference API URL",
    )
    parser.add_argument(
        "--model", required=True, help="Model name (matches Workload name)"
    )
    parser.add_argument(
        "-c",
        "--concurrency",
        type=int,
        default=10,
        help="Number of concurrent requests",
    )
    parser.add_argument(
        "-n",
        "--requests",
        type=int,
        default=100,
        help="Total number of requests to send",
    )

    args = parser.parse_args()
    asyncio.run(run_load_test(args.url, args.model, args.concurrency, args.requests))
