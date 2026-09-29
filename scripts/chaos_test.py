import asyncio
import httpx
import argparse
import random


async def kill_random_worker(api_url):
    print("Initiating Chaos: Identifying workers...")
    async with httpx.AsyncClient() as client:
        res = await client.get(f"{api_url}/api/v1/workers")
        if res.status_code != 200:
            print("Failed to fetch workers")
            return

        workers = res.json()
        online_workers = [w for w in workers if w["status"] == "ONLINE"]

        if not online_workers:
            print("No online workers to kill.")
            return

        target = random.choice(online_workers)
        print(f"Chaos Target Selected: Worker {target['id']} ({target['hostname']})")

        # In a real environment, this might call a special agent endpoint to self-destruct,
        # or delete the kubernetes pod. For the mock, we simulate it by calling an admin endpoint
        # (if one exists) or just printing the required manual action.

        print(
            f"To simulate death, manually stop the worker process for {target['id']} or wait for heartbeats to time out."
        )
        print(
            "The ReconciliationController should detect the missing heartbeats within ~60 seconds, mark the replica FAILED, and schedule a replacement."
        )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="ForgeLLM Chaos Tester")
    parser.add_argument("--url", default="http://localhost:8000", help="API URL")

    args = parser.parse_args()
    asyncio.run(kill_random_worker(args.url))
