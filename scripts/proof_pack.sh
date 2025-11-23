#!/bin/bash

# Proof Pack for Geometric Resonance Factorization
# Tailored for Intel Xeon and similar x86-64 architectures
#
# This script demonstrates factorization of a semiprime in the Gate 2 validation range
# using the updated timeout configuration from PR #37 (600000ms / 10 minutes).
#
# Project: geofac - Geometric Resonance Factorization
# Repo: https://github.com/zfifteen/geofac
# Validation Policy: docs/VALIDATION_GATES.md

set -euo pipefail

# Disable errexit for the entire script except where we explicitly want it
set +e

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RESULTS_DIR="${SCRIPT_DIR}/results/proof_pack_$(date +%Y%m%d_%H%M%S)"
JAR_PATH="${SCRIPT_DIR}/build/libs/geofac-0.1.0-SNAPSHOT.jar"

# Test semiprime from SimpleSemiprimeTest.java (Gate 2 range: 47 bits, ~1e14)
# N = 100000980001501 = 10000019 × 10000079
TARGET_N="100000980001501"
EXPECTED_P="10000019"
EXPECTED_Q="10000079"

echo -e "${BLUE}╔═══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║     Geofac Proof Pack - Hardware-Tailored Configuration      ║${NC}"
echo -e "${BLUE}╚═══════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Function to detect hardware
detect_hardware() {
    echo -e "${YELLOW}[INFO]${NC} Detecting hardware configuration..."
    
    if [ -f /proc/cpuinfo ]; then
        CPU_MODEL=$(grep "model name" /proc/cpuinfo | head -1 | cut -d':' -f2 | xargs)
        CPU_CORES=$(grep -c "^processor" /proc/cpuinfo)
        echo -e "${BLUE}  CPU:${NC} ${CPU_MODEL}"
        echo -e "${BLUE}  Cores:${NC} ${CPU_CORES}"
    elif command -v sysctl &> /dev/null; then
        CPU_MODEL=$(sysctl -n machdep.cpu.brand_string 2>/dev/null || echo "Unknown")
        CPU_CORES=$(sysctl -n hw.ncpu 2>/dev/null || echo "Unknown")
        echo -e "${BLUE}  CPU:${NC} ${CPU_MODEL}"
        echo -e "${BLUE}  Cores:${NC} ${CPU_CORES}"
    else
        echo -e "${YELLOW}  Could not detect CPU information${NC}"
        CPU_MODEL="Unknown"
        CPU_CORES="Unknown"
    fi
    
    # Detect total memory
    if [ -f /proc/meminfo ]; then
        TOTAL_MEM_KB=$(grep MemTotal /proc/meminfo | awk '{print $2}')
        TOTAL_MEM_GB=$((TOTAL_MEM_KB / 1024 / 1024))
        echo -e "${BLUE}  Memory:${NC} ${TOTAL_MEM_GB} GB"
    elif command -v sysctl &> /dev/null; then
        TOTAL_MEM=$(sysctl -n hw.memsize 2>/dev/null || echo "0")
        TOTAL_MEM_GB=$((TOTAL_MEM / 1024 / 1024 / 1024))
        echo -e "${BLUE}  Memory:${NC} ${TOTAL_MEM_GB} GB"
    else
        TOTAL_MEM_GB="Unknown"
        echo -e "${YELLOW}  Could not detect memory${NC}"
    fi
    
    # Detect OS
    if [ -f /etc/os-release ]; then
        OS_NAME=$(grep "^NAME=" /etc/os-release | cut -d'"' -f2)
        OS_VERSION=$(grep "^VERSION=" /etc/os-release | cut -d'"' -f2)
        echo -e "${BLUE}  OS:${NC} ${OS_NAME} ${OS_VERSION}"
    else
        OS_NAME=$(uname -s)
        echo -e "${BLUE}  OS:${NC} ${OS_NAME}"
    fi
    
    # Detect Java version
    if command -v java &> /dev/null; then
        JAVA_VERSION=$(java -version 2>&1 | head -1 | cut -d'"' -f2)
        echo -e "${BLUE}  Java:${NC} ${JAVA_VERSION}"
    else
        echo -e "${RED}  Java not found!${NC}"
        exit 1
    fi
    
    echo ""
}

# Function to check if JAR exists
check_build() {
    echo -e "${YELLOW}[INFO]${NC} Checking build artifacts..."
    
    if [ ! -f "${JAR_PATH}" ]; then
        echo -e "${RED}[ERROR]${NC} Application JAR not found at: ${JAR_PATH}"
        echo -e "${YELLOW}[INFO]${NC} Building application..."
        ./gradlew build --no-daemon
        
        if [ ! -f "${JAR_PATH}" ]; then
            echo -e "${RED}[ERROR]${NC} Build failed. Exiting."
            exit 1
        fi
    fi
    
    echo -e "${GREEN}[OK]${NC} Application JAR found"
    echo ""
}

# Function to create results directory
prepare_results_dir() {
    echo -e "${YELLOW}[INFO]${NC} Preparing results directory..."
    mkdir -p "${RESULTS_DIR}"
    echo -e "${GREEN}[OK]${NC} Results directory: ${RESULTS_DIR}"
    echo ""
}

# Function to save environment information
save_environment() {
    echo -e "${YELLOW}[INFO]${NC} Saving environment information..."
    
    cat > "${RESULTS_DIR}/env.txt" <<EOF
# Environment Information
# Generated: $(date -u +"%Y-%m-%dT%H:%M:%SZ")

## Hardware
CPU_MODEL=${CPU_MODEL}
CPU_CORES=${CPU_CORES}
TOTAL_MEMORY_GB=${TOTAL_MEM_GB}

## Operating System
OS=${OS_NAME}
KERNEL=$(uname -r)

## Java
JAVA_VERSION=${JAVA_VERSION}
JAVA_HOME=${JAVA_HOME:-"Not set"}

## Repository
GIT_COMMIT=$(git rev-parse HEAD 2>/dev/null || echo "Unknown")
GIT_BRANCH=$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo "Unknown")

## Test Target
TARGET_N=${TARGET_N}
TARGET_N_BITS=$(echo "import math; print(int(${TARGET_N}).bit_length())" | python3)
EXPECTED_P=${EXPECTED_P}
EXPECTED_Q=${EXPECTED_Q}
EOF
    
    echo -e "${GREEN}[OK]${NC} Environment saved to: ${RESULTS_DIR}/env.txt"
}

# Function to run factorization
run_factorization() {
    echo ""
    echo -e "${BLUE}╔═══════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║                 Starting Factorization                        ║${NC}"
    echo -e "${BLUE}╚═══════════════════════════════════════════════════════════════╝${NC}"
    echo ""
    echo -e "${YELLOW}[INFO]${NC} Target N: ${TARGET_N}"
    echo -e "${YELLOW}[INFO]${NC} Configuration (from PR #37):"
    echo -e "${BLUE}  precision:${NC} 240"
    echo -e "${BLUE}  samples:${NC} 5000"
    echo -e "${BLUE}  m-span:${NC} 180"
    echo -e "${BLUE}  j:${NC} 6"
    echo -e "${BLUE}  threshold:${NC} 0.92"
    echo -e "${BLUE}  k-lo:${NC} 0.25"
    echo -e "${BLUE}  k-hi:${NC} 0.45"
    echo -e "${BLUE}  search-timeout-ms:${NC} 600000 (10 minutes)"
    echo ""
    echo -e "${YELLOW}[INFO]${NC} Starting factorization (this may take up to 10 minutes)..."
    echo ""
    
    # Run the factorization and capture output
    local start_time=$(date +%s)
    local output_file="${RESULTS_DIR}/factorization_output.txt"
    
    # Configuration matching SimpleSemiprimeTest.java from PR #37
    java \
        -Dgeofac.precision=240 \
        -Dgeofac.samples=5000 \
        -Dgeofac.m-span=180 \
        -Dgeofac.j=6 \
        -Dgeofac.threshold=0.92 \
        -Dgeofac.k-lo=0.25 \
        -Dgeofac.k-hi=0.45 \
        -Dgeofac.search-timeout-ms=600000 \
        -jar "${JAR_PATH}" factor "${TARGET_N}" 2>&1 | tee "${output_file}"
    
    local exit_code=$?
    local end_time=$(date +%s)
    local duration=$((end_time - start_time))
    
    echo ""
    echo -e "${BLUE}Duration:${NC} ${duration} seconds"
    
    # Save timing information
    cat > "${RESULTS_DIR}/timing.txt" <<EOF
Start Time: $(date -d @${start_time} -u +"%Y-%m-%dT%H:%M:%SZ" 2>/dev/null || date -r ${start_time} -u +"%Y-%m-%dT%H:%M:%SZ")
End Time: $(date -d @${end_time} -u +"%Y-%m-%dT%H:%M:%SZ" 2>/dev/null || date -r ${end_time} -u +"%Y-%m-%dT%H:%M:%SZ")
Duration (seconds): ${duration}
Exit Code: ${exit_code}
EOF
    
    return $exit_code
}

# Function to verify results
verify_results() {
    local output_file="${RESULTS_DIR}/factorization_output.txt"
    
    echo ""
    echo -e "${BLUE}╔═══════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║                     Verifying Results                         ║${NC}"
    echo -e "${BLUE}╚═══════════════════════════════════════════════════════════════╝${NC}"
    echo ""
    
    if grep -q "✓ SUCCESS" "${output_file}"; then
        echo -e "${GREEN}[SUCCESS]${NC} Factorization completed successfully!"
        
        # Extract factors from output
        local found_p=$(grep "p =" "${output_file}" | sed 's/.*p = //' | sed 's/║.*//' | tr -d ' ' | head -1)
        local found_q=$(grep "q =" "${output_file}" | sed 's/.*q = //' | sed 's/║.*//' | tr -d ' ' | head -1)
        
        echo -e "${YELLOW}[INFO]${NC} Extracted factors:"
        echo -e "${BLUE}  p = ${NC}${found_p}"
        echo -e "${BLUE}  q = ${NC}${found_q}"
        
        # Verify factors match expected values (order may vary)
        if { [ "${found_p}" = "${EXPECTED_P}" ] && [ "${found_q}" = "${EXPECTED_Q}" ]; } || \
           { [ "${found_p}" = "${EXPECTED_Q}" ] && [ "${found_q}" = "${EXPECTED_P}" ]; }; then
            echo -e "${GREEN}[OK]${NC} Factors match expected values!"
            
            # Save verification result
            cat > "${RESULTS_DIR}/verification.txt" <<EOF
# Verification Result
Status: SUCCESS
N: ${TARGET_N}
Factor p: ${found_p}
Factor q: ${found_q}
Expected p: ${EXPECTED_P}
Expected q: ${EXPECTED_Q}
Verification: PASSED (factors match expected values)
EOF
            return 0
        else
            echo -e "${RED}[WARNING]${NC} Factors found but do not match expected values!"
            echo -e "${YELLOW}[INFO]${NC} This might be a different factorization or an error."
            
            cat > "${RESULTS_DIR}/verification.txt" <<EOF
# Verification Result
Status: SUCCESS (but unexpected factors)
N: ${TARGET_N}
Factor p: ${found_p}
Factor q: ${found_q}
Expected p: ${EXPECTED_P}
Expected q: ${EXPECTED_Q}
Verification: PARTIAL (factors found but don't match expected)
EOF
            return 1
        fi
    else
        echo -e "${RED}[FAILED]${NC} Factorization did not complete successfully."
        echo -e "${YELLOW}[INFO]${NC} This is expected for some semiprimes."
        echo -e "${YELLOW}[INFO]${NC} The algorithm may not find factors within the timeout for all numbers."
        
        cat > "${RESULTS_DIR}/verification.txt" <<EOF
# Verification Result
Status: FAILED
N: ${TARGET_N}
Expected p: ${EXPECTED_P}
Expected q: ${EXPECTED_Q}
Verification: FAILED (no factors found within timeout)
EOF
        return 1
    fi
}

# Function to create proof package
create_proof_package() {
    echo ""
    echo -e "${BLUE}╔═══════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║                   Creating Proof Package                      ║${NC}"
    echo -e "${BLUE}╚═══════════════════════════════════════════════════════════════╝${NC}"
    echo ""
    
    # Create summary
    cat > "${RESULTS_DIR}/README.txt" <<EOF
# Geofac Proof Pack - Execution Summary

Generated: $(date -u +"%Y-%m-%dT%H:%M:%SZ")

## Purpose
This proof pack demonstrates the geometric resonance factorization algorithm
on a Gate 2 range semiprime using the updated timeout configuration from PR #37.

## Test Case
Target N: ${TARGET_N}
Bit length: $(echo "import math; print(int(${TARGET_N}).bit_length())" | python3) bits
Expected factors: ${EXPECTED_P} × ${EXPECTED_Q}
Validation range: Gate 2 [1e14, 1e18]

## Configuration
- precision: 240
- samples: 5000
- m-span: 180
- j: 6
- threshold: 0.92
- k-lo: 0.25
- k-hi: 0.45
- search-timeout-ms: 600000 (10 minutes)

## Hardware
CPU: ${CPU_MODEL}
Cores: ${CPU_CORES}
Memory: ${TOTAL_MEM_GB} GB
OS: ${OS_NAME}

## Files in this Proof Pack
- README.txt: This file
- env.txt: Detailed environment information
- factorization_output.txt: Complete output from factorization
- timing.txt: Execution timing information
- verification.txt: Verification results

## Verification
To verify the results independently:
1. Check that p × q = N
2. Verify both p and q are prime
3. Confirm N is in the valid range [1e14, 1e18]

## References
- Repository: https://github.com/zfifteen/geofac
- Validation Policy: docs/VALIDATION_GATES.md
- PR #37: https://github.com/zfifteen/geofac/pull/37
EOF
    
    echo -e "${GREEN}[OK]${NC} Proof package created in: ${RESULTS_DIR}"
    echo ""
    echo -e "${YELLOW}[INFO]${NC} Proof pack contents:"
    ls -lh "${RESULTS_DIR}"
    echo ""
}

# Main execution
main() {
    detect_hardware
    check_build
    prepare_results_dir
    save_environment
    
    # Run factorization (allow failure)
    local factorization_success=false
    if run_factorization; then
        factorization_success=true
    fi
    
    # Verify results (allow failure)
    local verify_exit=1
    if verify_results; then
        verify_exit=0
    fi
    
    # Always create proof package
    create_proof_package
    
    echo ""
    echo -e "${BLUE}╔═══════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║                      Proof Pack Complete                      ║${NC}"
    echo -e "${BLUE}╚═══════════════════════════════════════════════════════════════╝${NC}"
    echo ""
    echo -e "${YELLOW}[INFO]${NC} Results directory: ${RESULTS_DIR}"
    echo ""
    
    if [ $verify_exit -eq 0 ]; then
        echo -e "${GREEN}[SUCCESS]${NC} Factorization successful and verified!"
        exit 0
    else
        echo -e "${YELLOW}[NOTE]${NC} Factorization did not complete successfully or verification failed."
        echo -e "${YELLOW}[NOTE]${NC} This is expected behavior for some semiprimes with this algorithm."
        echo -e "${YELLOW}[NOTE]${NC} See ${RESULTS_DIR}/verification.txt for details."
        exit 1
    fi
}

# Run main function
main
