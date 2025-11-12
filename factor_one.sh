#!/bin/bash

# One-shot factorization of the target N using geometric resonance
# Produces results/single_N_run.json and plaintext factors if successful

TARGET_N="137524771864208156028430259349934309717"

echo "Starting one-shot factorization of N = $TARGET_N"

# Run the factorization command
output=$(java -jar build/libs/geofac-0.1.0-SNAPSHOT.jar --spring.shell.interactive=false factor $TARGET_N 2>&1)

# Print the output
echo "$output"

# Check for success
if grep -q "SUCCESS" <<< "$output"; then
    echo "Factorization successful."

    # Extract p and q from the output
    p=$(grep "p =" <<< "$output" | sed 's/.*p = //' | tr -d ' ')
    q=$(grep "q =" <<< "$output" | sed 's/.*q = //' | tr -d ' ')

    # Output plaintext
    echo "$p"
    echo "$q"
    echo "pq_matches_N=true"

    echo "Results saved to results/single_N_run.json"
else
    echo "Factorization failed."
    exit 1
fi