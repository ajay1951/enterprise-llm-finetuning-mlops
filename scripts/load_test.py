import asyncio
import time
import httpx
import argparse
import statistics
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def make_request(client, url, api_key, model_name):
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": model_name,
        "messages": [{"role": "user", "content": "Hello, this is a load test."}],
        "max_tokens": 50
    }
    
    start_time = time.time()
    try:
        response = await client.post(url, json=payload, headers=headers)
        latency = (time.time() - start_time) * 1000
        is_success = response.status_code == 200
        return is_success, latency, response.status_code
    except Exception as e:
        latency = (time.time() - start_time) * 1000
        return False, latency, str(e)

async def main(url, api_key, model_name, num_requests, concurrency):
    logger.info(f"Starting load test on {url} for model {model_name}")
    logger.info(f"Requests: {num_requests}, Concurrency: {concurrency}")
    
    timeout = httpx.Timeout(10.0, connect=5.0)
    limits = httpx.Limits(max_connections=concurrency, max_keepalive_connections=concurrency)
    
    latencies = []
    success_count = 0
    error_count = 0
    status_codes = {}
    
    start_time = time.time()
    
    async with httpx.AsyncClient(timeout=timeout, limits=limits) as client:
        tasks = []
        for _ in range(num_requests):
            tasks.append(make_request(client, url, api_key, model_name))
            if len(tasks) >= concurrency:
                results = await asyncio.gather(*tasks)
                for success, latency, status in results:
                    latencies.append(latency)
                    if success:
                        success_count += 1
                    else:
                        error_count += 1
                    status_codes[status] = status_codes.get(status, 0) + 1
                tasks = []
                
        if tasks:
            results = await asyncio.gather(*tasks)
            for success, latency, status in results:
                latencies.append(latency)
                if success:
                    success_count += 1
                else:
                    error_count += 1
                status_codes[status] = status_codes.get(status, 0) + 1

    total_time = time.time() - start_time
    
    logger.info("=== Load Test Results ===")
    logger.info(f"Total Requests: {num_requests}")
    logger.info(f"Total Time: {total_time:.2f}s")
    logger.info(f"Requests/sec: {num_requests / total_time:.2f}")
    logger.info(f"Success Rate: {(success_count / num_requests) * 100:.2f}%")
    logger.info(f"Error Rate: {(error_count / num_requests) * 100:.2f}%")
    
    if latencies:
        logger.info(f"Average Latency: {statistics.mean(latencies):.2f}ms")
        logger.info(f"P50 Latency: {statistics.quantiles(latencies, n=100)[49]:.2f}ms")
        logger.info(f"P95 Latency: {statistics.quantiles(latencies, n=100)[94]:.2f}ms")
        logger.info(f"P99 Latency: {statistics.quantiles(latencies, n=100)[98]:.2f}ms")
        
    logger.info("Status Codes:")
    for code, count in status_codes.items():
        logger.info(f"  {code}: {count}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="ForgeLLM API Gateway Load Test")
    parser.add_argument("--url", default="http://localhost:8000/v1/chat/completions", help="API Endpoint")
    parser.add_argument("--api-key", default="test_key", help="ForgeLLM API Key")
    parser.add_argument("--model", default="customer-support", help="Model or alias to test")
    parser.add_argument("-n", "--requests", type=int, default=100, help="Number of requests")
    parser.add_argument("-c", "--concurrency", type=int, default=10, help="Concurrency level")
    
    args = parser.parse_args()
    asyncio.run(main(args.url, args.api_key, args.model, args.requests, args.concurrency))
