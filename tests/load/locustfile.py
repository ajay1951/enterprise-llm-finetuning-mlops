import time

from locust import HttpUser, between, events, task


class ForgeLLMUser(HttpUser):
    wait_time = between(1, 3)

    def on_start(self):
        # Setup basic auth or token if required
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": "Bearer test-token",
        }

    @task(3)
    def test_inference_stream(self):
        payload = {
            "model": "production-model",
            "messages": [
                {
                    "role": "user",
                    "content": "Explain the architecture of an enterprise MLOps platform in detail.",
                }
            ],
            "stream": True,
            "max_tokens": 100,
        }

        start_time = time.time()
        ttft = None

        with self.client.post(
            "/v1/chat/completions",
            json=payload,
            headers=self.headers,
            catch_response=True,
            stream=True,
        ) as response:
            if response.status_code != 200:
                response.failure(f"Failed with status {response.status_code}")
                return

            first_chunk = True
            for line in response.iter_lines():
                if line and first_chunk:
                    ttft = int((time.time() - start_time) * 1000)
                    events.request.fire(
                        request_type="STREAM_TTFT",
                        name="/v1/chat/completions (TTFT)",
                        response_time=ttft,
                        response_length=len(line),
                        exception=None,
                    )
                    first_chunk = False

    @task(1)
    def test_health_endpoints(self):
        self.client.get("/health", headers=self.headers)
        self.client.get("/metrics", headers=self.headers)
