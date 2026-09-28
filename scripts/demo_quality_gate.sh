#!/bin/bash

echo "=========================================================="
echo " ForgeLLM CI/CD Quality Gate Demonstration"
echo "=========================================================="
echo "This script demonstrates the automated Quality Gate evaluating"
echo "Experiment EXP-000010 against configurable thresholds."
echo ""

echo "----------------------------------------------------------"
echo " SCENARIO 1: PASSING THE QUALITY GATE"
echo "----------------------------------------------------------"
echo "Configuration: --max-rouge-degradation 0.05"
echo "We tolerate a slight regression up to -0.05 ROUGE-L."
echo "Since the delta is ~0.0, this should PASS as 'EQUIVALENT'."
echo ""

set +e
forge evaluate EXP-000010 --max-rouge-degradation 0.05
PASS_EXIT=$?
set -e

if [ $PASS_EXIT -eq 0 ]; then
    echo -e "\n✅ SUCCESS: The pipeline correctly PASSED the Quality Gate."
else
    echo -e "\n❌ ERROR: The pipeline unexpectedly FAILED the Quality Gate."
    exit 1
fi

echo ""
echo "----------------------------------------------------------"
echo " SCENARIO 2: FAILING THE QUALITY GATE"
echo "----------------------------------------------------------"
echo "Configuration: --min-rouge-improvement 0.50"
echo "We strictly demand a massive +0.50 improvement in ROUGE-L."
echo "Since the model hasn't improved that much, this MUST FAIL."
echo ""

set +e
forge evaluate EXP-000010 --min-rouge-improvement 0.50
FAIL_EXIT=$?
set -e

if [ $FAIL_EXIT -eq 1 ]; then
    echo -e "\n✅ SUCCESS: The pipeline correctly FAILED and blocked the degradation."
else
    echo -e "\n❌ ERROR: The pipeline unexpectedly PASSED a failing model (Exit Code: $FAIL_EXIT)."
    exit 1
fi

echo ""
echo "=========================================================="
echo " Demonstration Complete."
echo "=========================================================="
