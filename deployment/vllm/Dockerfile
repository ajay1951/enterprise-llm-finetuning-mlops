FROM vllm/vllm-openai:v0.6.3.post1

LABEL maintainer="ForgeLLM AI Infrastructure Team"
LABEL description="ForgeLLM High-Throughput vLLM Model Serving Container"

ENV PYTHONUNBUFFERED=1
ENV VLLM_LOGGING_LEVEL=INFO

WORKDIR /app

COPY config.yaml /app/config.yaml

EXPOSE 8000

HEALTHCHECK --interval=10s --timeout=5s --retries=5 \
  CMD python3 -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

ENTRYPOINT ["python3", "-m", "vllm.entrypoints.openai.api_server", \
            "--model", "Qwen/Qwen2.5-0.5B", \
            "--host", "0.0.0.0", \
            "--port", "8000", \
            "--gpu-memory-utilization", "0.90", \
            "--max-model-len", "2048", \
            "--trust-remote-code"]
