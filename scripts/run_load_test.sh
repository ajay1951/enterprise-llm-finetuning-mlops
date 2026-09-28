#!/bin/bash
echo "Starting Enterprise Load Test against ForgeLLM Gateway..."
echo "Targeting localhost:8000"

# Require locust to be installed
if ! command -v locust &> /dev/null
then
    echo "Locust could not be found. Please install it via: pip install locust"
    exit
fi

locust -f tests/load/locustfile.py \
       --host=http://localhost:8000 \
       --users 50 \
       --spawn-rate 5 \
       --run-time 1m \
       --html=benchmarks/load_test_report.html \
       --headless

echo "Load test complete! Report generated at benchmarks/load_test_report.html"
