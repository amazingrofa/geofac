"""
Parameter Sweep Module
======================

Grid search over GVA parameters (k_values, candidate_budgets) to identify
parameter sensitivity and optimal configurations.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

import mpmath as mp
import numpy as np
import csv
import time
from typing import List, Dict, Tuple, Optional
from datetime import datetime
from multiprocessing import Pool, cpu_count
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

from gva_factorization import gva_factor_search


def test_parameters(args: Tuple) -> Dict:
    """
    Test GVA with specific parameter configuration.
    
    Args:
        args: Tuple of (N, p, q, k_value, candidate_budget, timeout)
        
    Returns:
        Dictionary with test results
    """
    N, p, q, k_value, candidate_budget, timeout = args
    
    start_time = time.time()
    
    try:
        # Run with timeout simulation (simplified - actual timeout in gva_factor_search)
        result = gva_factor_search(
            N, 
            k_values=[k_value], 
            max_candidates=candidate_budget,
            verbose=False,
            allow_any_range=True
        )
        
        elapsed = time.time() - start_time
        
        if result and result[0] * result[1] == N:
            # Check if it's the correct factors
            found_factors = set(result)
            expected_factors = {p, q}
            success = (found_factors == expected_factors)
            false_positive = not success
        else:
            success = False
            false_positive = False
        
        return {
            'N': N,
            'k': k_value,
            'budget': candidate_budget,
            'success': success,
            'false_positive': false_positive,
            'runtime': elapsed,
            'found_factors': result if result else None
        }
    
    except Exception as e:
        return {
            'N': N,
            'k': k_value,
            'budget': candidate_budget,
            'success': False,
            'false_positive': False,
            'runtime': time.time() - start_time,
            'error': str(e)
        }


def parameter_sweep(test_cases: List[Dict], 
                   k_values: List[float],
                   candidate_budgets: List[int],
                   timeout: int = 10,
                   output_dir: str = 'results',
                   parallel: bool = True) -> Dict:
    """
    Perform grid search over parameters.
    
    Args:
        test_cases: List of dicts with 'N', 'p', 'q' keys
        k_values: Geodesic exponents to test
        candidate_budgets: Candidate budget values to test
        timeout: Timeout per run in seconds
        output_dir: Output directory
        parallel: Use multiprocessing
        
    Returns:
        Sweep results
    """
    np.random.seed(42)  # Reproducibility
    
    print("=" * 70)
    print("Parameter Sweep Analysis")
    print("=" * 70)
    print(f"Test cases: {len(test_cases)}")
    print(f"k values: {k_values}")
    print(f"Candidate budgets: {candidate_budgets}")
    print(f"Timeout: {timeout}s per run")
    print(f"Parallel: {parallel}")
    print(f"Total runs: {len(test_cases) * len(k_values) * len(candidate_budgets)}")
    print()
    
    # Generate all parameter combinations
    tasks = []
    for case in test_cases:
        for k in k_values:
            for budget in candidate_budgets:
                tasks.append((case['N'], case['p'], case['q'], k, budget, timeout))
    
    # Execute sweep
    results = []
    
    if parallel:
        # Use multiprocessing for parallel execution
        num_workers = min(cpu_count(), 8)
        print(f"Using {num_workers} parallel workers")
        
        with Pool(num_workers) as pool:
            results = pool.map(test_parameters, tasks)
    else:
        # Sequential execution
        for i, task in enumerate(tasks):
            print(f"[{i+1}/{len(tasks)}] Testing N={task[0]}, k={task[3]}, budget={task[4]}")
            result = test_parameters(task)
            results.append(result)
    
    # Aggregate results
    os.makedirs(output_dir, exist_ok=True)
    
    csv_path = os.path.join(output_dir, 'param_sweep.csv')
    with open(csv_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=[
            'N', 'bit_length', 'k', 'budget', 'success', 'false_positive', 
            'runtime', 'found_factors'
        ])
        writer.writeheader()
        
        for r in results:
            writer.writerow({
                'N': r['N'],
                'bit_length': r['N'].bit_length(),
                'k': r['k'],
                'budget': r['budget'],
                'success': r['success'],
                'false_positive': r['false_positive'],
                'runtime': f"{r['runtime']:.3f}",
                'found_factors': r.get('found_factors', '')
            })
    
    print(f"CSV saved: {csv_path}")
    
    # Generate heatmap for each test case
    for case in test_cases:
        N = case['N']
        case_results = [r for r in results if r['N'] == N]
        
        # Build success rate matrix
        success_matrix = np.zeros((len(k_values), len(candidate_budgets)))
        runtime_matrix = np.zeros((len(k_values), len(candidate_budgets)))
        
        for r in case_results:
            k_idx = k_values.index(r['k'])
            b_idx = candidate_budgets.index(r['budget'])
            success_matrix[k_idx, b_idx] = 1.0 if r['success'] else 0.0
            runtime_matrix[k_idx, b_idx] = r['runtime']
        
        # Plot heatmap
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))
        
        # Success rate heatmap
        im1 = ax1.imshow(success_matrix, aspect='auto', cmap='RdYlGn', vmin=0, vmax=1)
        ax1.set_xticks(range(len(candidate_budgets)))
        ax1.set_xticklabels([f'{b//1000}k' for b in candidate_budgets], rotation=45)
        ax1.set_yticks(range(len(k_values)))
        ax1.set_yticklabels([f'{k:.2f}' for k in k_values])
        ax1.set_xlabel('Candidate Budget', fontsize=11)
        ax1.set_ylabel('k value', fontsize=11)
        ax1.set_title(f'Success Rate (N={N}, {N.bit_length()} bits)', fontsize=12)
        plt.colorbar(im1, ax=ax1, label='Success (1=pass, 0=fail)')
        
        # Runtime heatmap
        im2 = ax2.imshow(runtime_matrix, aspect='auto', cmap='plasma')
        ax2.set_xticks(range(len(candidate_budgets)))
        ax2.set_xticklabels([f'{b//1000}k' for b in candidate_budgets], rotation=45)
        ax2.set_yticks(range(len(k_values)))
        ax2.set_yticklabels([f'{k:.2f}' for k in k_values])
        ax2.set_xlabel('Candidate Budget', fontsize=11)
        ax2.set_ylabel('k value', fontsize=11)
        ax2.set_title(f'Runtime (seconds)', fontsize=12)
        plt.colorbar(im2, ax=ax2, label='Time (s)')
        
        plt.tight_layout()
        
        heatmap_path = os.path.join(output_dir, f'param_heatmap_{N.bit_length()}bit.png')
        plt.savefig(heatmap_path, dpi=150)
        plt.close()
        
        print(f"Heatmap saved: {heatmap_path}")
    
    # Summary statistics
    total_runs = len(results)
    successes = sum(1 for r in results if r['success'])
    false_positives = sum(1 for r in results if r['false_positive'])
    
    summary = {
        'timestamp': datetime.now().isoformat(),
        'total_runs': total_runs,
        'successes': successes,
        'false_positives': false_positives,
        'success_rate': successes / total_runs if total_runs > 0 else 0,
        'avg_runtime': np.mean([r['runtime'] for r in results]),
        'k_values': k_values,
        'candidate_budgets': candidate_budgets
    }
    
    print()
    print("=" * 70)
    print("Summary")
    print("=" * 70)
    print(f"Total runs: {total_runs}")
    print(f"Successes: {successes} ({100*summary['success_rate']:.1f}%)")
    print(f"False positives: {false_positives}")
    print(f"Avg runtime: {summary['avg_runtime']:.3f}s")
    print()
    
    return {
        'summary': summary,
        'results': results
    }


if __name__ == '__main__':
    # Test cases from 8d experiment failures
    test_cases = [
        # Gate 1: 30-bit (should succeed)
        {'N': 1073217479, 'p': 32749, 'q': 32771},
        
        # 47-bit balanced (8d failure)
        {'N': 100000980001501, 'p': 10000019, 'q': 10000079},
    ]
    
    k_values = [0.1, 0.15, 0.2, 0.25, 0.3, 0.35, 0.4, 0.45, 0.5]
    candidate_budgets = [10000, 50000, 100000]
    
    parameter_sweep(
        test_cases, 
        k_values, 
        candidate_budgets,
        timeout=10,
        output_dir='results',
        parallel=True
    )
