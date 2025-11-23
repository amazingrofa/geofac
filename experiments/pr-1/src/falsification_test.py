"""
Main Falsification Test Runner

Orchestrates the complete falsification experiment:
1. Generate isospectral tori
2. Embed semiprimes via GVA
3. Probe with QMC
4. Validate metrics
5. Report results

Falsification criteria:
- Metric deviation >5% (threshold <0.95)
- Runtime increase >10% (ratio >1.1)
"""

import argparse
import json
import logging
import time
import yaml
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple

import numpy as np
from scipy import stats

from torus_construction import IsospectraLatticeGenerator
from gva_embedding import GVAEmbedding
from qmc_probe import QMCProbe

logger = logging.getLogger(__name__)


class FalsificationTest:
    """
    Main test orchestrator for isospectral tori falsification experiment.
    """
    
    def __init__(self, config_path: str = "config.yaml"):
        """
        Initialize test with configuration.
        
        Args:
            config_path: Path to YAML configuration file
        """
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)
        
        self.results_dir = Path(self.config['output']['results_dir'])
        self.results_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Initialized falsification test with config: {config_path}")
    
    def load_test_cases(self, test_cases_path: str = "data/test_cases.json") -> List[Dict]:
        """
        Load test case configurations.
        
        Args:
            test_cases_path: Path to test cases JSON
        
        Returns:
            List of test case dictionaries
        """
        with open(test_cases_path, 'r') as f:
            data = json.load(f)
        
        return data['test_cases']
    
    def generate_test_semiprime(self, bit_length: int, seed: int = 42) -> Tuple[int, int, int]:
        """
        Generate a test semiprime with known factors.
        
        For this experiment, we use known semiprimes from validation gates.
        
        Args:
            bit_length: Target bit length
            seed: Random seed
        
        Returns:
            (n, p, q) where n = p * q
        """
        # Use validation gate numbers for reproducibility
        if bit_length <= 30:
            # Gate 1: 30-bit
            p, q = 32749, 32771
            n = 1073217479
        elif bit_length <= 60:
            # Gate 2: 60-bit
            p = 1073741789
            q = 1073741827
            n = 1152921470247108503
        elif bit_length <= 127:
            # Gate 3: 127-bit challenge
            p = 10508623501177419659
            q = 13086849276577416863
            n = 137524771864208156028430259349934309717
        else:
            # For larger sizes, generate pseudo-semiprimes
            # (In reality, would use proper prime generation)
            logger.warning(f"Using approximation for {bit_length}-bit semiprime")
            p = 2 ** (bit_length // 2) + 1
            q = 2 ** (bit_length // 2) + 3
            n = p * q
        
        logger.info(f"Using semiprime: n={n} (p={p}, q={q})")
        return n, p, q
    
    def run_baseline_test(self, n: int, dimension: int) -> Dict:
        """
        Run baseline test with isometric torus (negative control).
        
        Args:
            n: Target semiprime
            dimension: Torus dimension
        
        Returns:
            Baseline results dictionary
        """
        logger.info(f"Running baseline test: n={n}, dim={dimension}")
        
        start_time = time.time()
        
        # Use identity lattice (isometric)
        lattice = np.eye(dimension)
        
        # Initialize GVA and QMC
        gva = GVAEmbedding(precision=self.config['gva']['min_precision'])
        qmc = QMCProbe(dimension=dimension, 
                      n_samples=self.config['qmc']['base_samples'],
                      scramble=(self.config['qmc']['scrambling'] == 'owen'))
        
        # Probe
        samples, amplitudes = qmc.probe_torus(n, lattice)
        
        runtime = time.time() - start_time
        
        baseline = {
            'runtime': runtime,
            'mean_amplitude': float(np.mean(amplitudes)),
            'max_amplitude': float(np.max(amplitudes)),
            'convergence_error': float(qmc.estimate_convergence_error(amplitudes))
        }
        
        logger.info(f"Baseline test completed in {runtime:.2f}s")
        return baseline
    
    def run_isospectral_test(self, test_case: Dict, baseline: Dict) -> Dict:
        """
        Run main isospectral test case.
        
        Args:
            test_case: Test case configuration
            baseline: Baseline results for comparison
        
        Returns:
            Test results dictionary
        """
        logger.info(f"Running test case: {test_case['id']}")
        
        dimension = test_case['dimension']
        choir_size = test_case['expected_choir_number']
        
        # Generate test semiprime
        n, p, q = self.generate_test_semiprime(test_case['target_n']['bit_length'])
        
        start_time = time.time()
        
        # Generate isospectral choir
        generator = IsospectraLatticeGenerator(dimension=dimension)
        choir = generator.generate_isospectral_choir(choir_size=choir_size)
        
        # Initialize GVA
        precision = self.config['gva']['min_precision']
        if self.config['gva']['use_adaptive_precision']:
            bit_length = n.bit_length()
            precision = max(precision, 
                          bit_length * self.config['gva']['precision_factor'] + 200)
        
        gva = GVAEmbedding(precision=precision)
        
        # Compute metric preservation
        preservation_ratio = gva.compute_metric_preservation_ratio(n, p, q, choir)
        
        # QMC probing
        qmc = QMCProbe(dimension=dimension,
                      n_samples=self.config['qmc']['base_samples'],
                      scramble=(self.config['qmc']['scrambling'] == 'owen'))
        
        probe_results = qmc.parallel_probe_choir(n, choir)
        
        # Cross-validate resonances
        overlap_ratio, n_resonances = qmc.cross_validate_resonances(
            probe_results, 
            threshold=self.config['thresholds']['spectral_overlap']
        )
        
        runtime = time.time() - start_time
        
        # Compute metrics
        results = {
            'test_case_id': test_case['id'],
            'dimension': dimension,
            'choir_size': choir_size,
            'n': n,
            'p': p,
            'q': q,
            'runtime': runtime,
            'baseline_runtime': baseline['runtime'],
            'runtime_ratio': runtime / baseline['runtime'],
            'metric_preservation_ratio': preservation_ratio,
            'spectral_overlap_ratio': overlap_ratio,
            'n_consistent_resonances': n_resonances,
            'precision_used': precision
        }
        
        # Evaluate falsification criteria
        falsification_metric = preservation_ratio < self.config['thresholds']['metric_preservation']
        falsification_runtime = (runtime / baseline['runtime']) > self.config['thresholds']['runtime_ratio']
        
        results['falsified_by_metrics'] = falsification_metric
        results['falsified_by_runtime'] = falsification_runtime
        results['falsified'] = falsification_metric or falsification_runtime
        
        logger.info(f"Test case {test_case['id']} completed: "
                   f"preservation={preservation_ratio:.4f}, "
                   f"runtime_ratio={results['runtime_ratio']:.4f}, "
                   f"falsified={results['falsified']}")
        
        return results
    
    def run_statistical_validation(self, results: List[Dict]) -> Dict:
        """
        Run statistical validation on results.
        
        Performs Kolmogorov-Smirnov test for Poisson consistency.
        
        Args:
            results: List of test results
        
        Returns:
            Statistical validation results
        """
        logger.info("Running statistical validation")
        
        # Extract preservation ratios
        preservation_ratios = [r['metric_preservation_ratio'] for r in results]
        
        # KS test against uniform distribution (null hypothesis)
        ks_stat, p_value = stats.kstest(preservation_ratios, 'uniform')
        
        # Check if we reject null hypothesis
        alpha = self.config['statistics']['ks_test_alpha']
        rejects_null = p_value < alpha
        
        validation = {
            'ks_statistic': float(ks_stat),
            'p_value': float(p_value),
            'alpha': alpha,
            'rejects_poisson_consistency': rejects_null
        }
        
        logger.info(f"KS test: statistic={ks_stat:.4f}, p={p_value:.4f}, "
                   f"rejects_null={rejects_null}")
        
        return validation
    
    def generate_report(self, results: List[Dict], validation: Dict) -> Dict:
        """
        Generate final experiment report.
        
        Args:
            results: List of test results
            validation: Statistical validation results
        
        Returns:
            Complete report dictionary
        """
        n_total = len(results)
        n_falsified = sum(1 for r in results if r['falsified'])
        
        report = {
            'experiment': self.config['experiment'],
            'timestamp': datetime.now().isoformat(),
            'summary': {
                'total_tests': n_total,
                'falsified_tests': n_falsified,
                'falsification_rate': n_falsified / n_total if n_total > 0 else 0,
                'hypothesis_falsified': n_falsified >= (2 * n_total) / 3  # 2/3 threshold
            },
            'test_results': results,
            'statistical_validation': validation,
            'falsification_criteria': self.config['thresholds']
        }
        
        logger.info(f"Report generated: {n_falsified}/{n_total} tests falsified")
        
        return report
    
    def save_report(self, report: Dict, filename: str = None):
        """
        Save report to JSON file.
        
        Args:
            report: Report dictionary
            filename: Output filename (auto-generated if None)
        """
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"falsification_report_{timestamp}.json"
        
        output_path = self.results_dir / filename
        
        with open(output_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"Report saved to: {output_path}")
    
    def run_full_experiment(self):
        """
        Run the complete falsification experiment.
        """
        logger.info("=" * 60)
        logger.info("Starting Falsification Experiment")
        logger.info("=" * 60)
        
        # Load test cases
        test_cases = self.load_test_cases()
        logger.info(f"Loaded {len(test_cases)} test cases")
        
        all_results = []
        
        for test_case in test_cases:
            logger.info(f"\n--- Test Case: {test_case['id']} ---")
            
            # Run baseline
            n, _, _ = self.generate_test_semiprime(test_case['target_n']['bit_length'])
            baseline = self.run_baseline_test(n, test_case['dimension'])
            
            # Run isospectral test
            result = self.run_isospectral_test(test_case, baseline)
            all_results.append(result)
        
        # Statistical validation
        validation = self.run_statistical_validation(all_results)
        
        # Generate and save report
        report = self.generate_report(all_results, validation)
        self.save_report(report)
        
        # Print summary
        print("\n" + "=" * 60)
        print("EXPERIMENT SUMMARY")
        print("=" * 60)
        print(f"Total tests: {report['summary']['total_tests']}")
        print(f"Falsified: {report['summary']['falsified_tests']}")
        print(f"Falsification rate: {report['summary']['falsification_rate']:.2%}")
        print(f"Hypothesis falsified: {report['summary']['hypothesis_falsified']}")
        print("=" * 60)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Isospectral Tori Falsification Experiment"
    )
    parser.add_argument(
        '--config', 
        default='config.yaml',
        help='Path to configuration file'
    )
    parser.add_argument(
        '--log-level',
        default='INFO',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
        help='Logging level'
    )
    
    args = parser.parse_args()
    
    # Setup logging
    logging.basicConfig(
        level=getattr(logging, args.log_level),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Run experiment
    test = FalsificationTest(config_path=args.config)
    test.run_full_experiment()


if __name__ == "__main__":
    main()
