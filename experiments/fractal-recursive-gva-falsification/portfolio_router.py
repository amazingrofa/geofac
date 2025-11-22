"""
Portfolio-Based Router for FR-GVA vs GVA
=========================================

Analyzes structural features of semiprimes to predict which factorization
method (FR-GVA or standard GVA) is likely to succeed.

Key features analyzed:
- Bit length
- Factor gap (|p - q|)
- κ (kappa) curvature profile
- Factor balance ratio

Based on empirical correlation from PR #93 results showing complementary
success patterns between FR-GVA and GVA.
"""

import mpmath as mp
from typing import Dict, Tuple, Optional, Literal
from math import log, e, sqrt
import sys
import os

# Add parent directories to path for imports
repo_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, repo_root)
sys.path.insert(0, os.path.join(repo_root, 'experiments', 'fractal-recursive-gva-falsification'))

from fr_gva_implementation import compute_kappa


MethodChoice = Literal["FR-GVA", "GVA"]

# Routing algorithm parameters
# These weights were empirically derived from PR #93 results analysis
BIT_LENGTH_WEIGHT = 2.0  # Bit length is the strongest predictor (weighted 2x)
KAPPA_WEIGHT = 1.0       # Kappa provides additional signal (weighted 1x)

# Distance decay parameters for inverse distance scoring
# Higher decay = more penalty for distance from average
BIT_DECAY_RATE = 0.5     # Moderate decay for bit length differences
KAPPA_DECAY_RATE = 2.0   # Stronger decay for kappa differences (more sensitive)


def extract_structural_features(N: int, p: Optional[int] = None, q: Optional[int] = None) -> Dict:
    """
    Extract structural features from a semiprime N.
    
    Features:
    - bit_length: Number of bits in N
    - approx_sqrt: Approximate integer square root
    - kappa: Curvature metric κ(N)
    - log_N: Natural logarithm of N
    
    If factors p, q are provided (for training/analysis):
    - factor_gap: Absolute difference |p - q|
    - factor_balance_ratio: min(p,q) / max(p,q)
    - gap_to_sqrt_ratio: factor_gap / sqrt(N)
    
    Args:
        N: Semiprime to analyze
        p, q: Optional known factors (for correlation analysis)
        
    Returns:
        Dictionary of features
    """
    features = {}
    
    # Basic features (always computable)
    features['N'] = N
    features['bit_length'] = N.bit_length()
    features['approx_sqrt'] = int(mp.sqrt(N))
    features['kappa'] = compute_kappa(N)
    features['log_N'] = log(N)
    
    # Derived features requiring known factors
    if p is not None and q is not None:
        features['p'] = p
        features['q'] = q
        features['factor_gap'] = abs(p - q)
        features['factor_balance_ratio'] = min(p, q) / max(p, q)
        features['gap_to_sqrt_ratio'] = features['factor_gap'] / features['approx_sqrt']
    
    return features


def analyze_correlation(test_results: list) -> Dict:
    """
    Analyze correlation between features and method success.
    
    Args:
        test_results: List of dicts with keys:
            - 'N', 'p', 'q': Test case identifiers
            - 'gva_success': bool
            - 'fr_gva_success': bool
            
    Returns:
        Dictionary containing:
        - feature_ranges: Feature ranges for successful cases per method
        - recommendations: Routing rules
    """
    gva_success_features = []
    fr_gva_success_features = []
    
    for result in test_results:
        features = extract_structural_features(result['N'], result.get('p'), result.get('q'))
        
        if result.get('gva_success'):
            gva_success_features.append(features)
        if result.get('fr_gva_success'):
            fr_gva_success_features.append(features)
    
    analysis = {
        'gva_success_patterns': summarize_feature_patterns(gva_success_features, "GVA"),
        'fr_gva_success_patterns': summarize_feature_patterns(fr_gva_success_features, "FR-GVA"),
    }
    
    # Derive routing rules
    analysis['routing_rules'] = derive_routing_rules(
        gva_success_features, 
        fr_gva_success_features
    )
    
    return analysis


def summarize_feature_patterns(features_list: list, method_name: str) -> Dict:
    """
    Summarize feature patterns for successful factorizations.
    
    Args:
        features_list: List of feature dicts from successful cases
        method_name: Name of the method (for logging)
        
    Returns:
        Summary statistics for each feature
    """
    if not features_list:
        return {}
    
    summary = {
        'count': len(features_list),
        'bit_length_range': (
            min(f['bit_length'] for f in features_list),
            max(f['bit_length'] for f in features_list)
        ),
        'kappa_range': (
            min(f['kappa'] for f in features_list),
            max(f['kappa'] for f in features_list)
        ),
    }
    
    # Add factor-based features if available
    if all('factor_gap' in f for f in features_list):
        summary['factor_gap_range'] = (
            min(f['factor_gap'] for f in features_list),
            max(f['factor_gap'] for f in features_list)
        )
        summary['gap_to_sqrt_ratio_range'] = (
            min(f['gap_to_sqrt_ratio'] for f in features_list),
            max(f['gap_to_sqrt_ratio'] for f in features_list)
        )
        summary['factor_balance_ratio_range'] = (
            min(f['factor_balance_ratio'] for f in features_list),
            max(f['factor_balance_ratio'] for f in features_list)
        )
    
    return summary


def derive_routing_rules(gva_features: list, fr_gva_features: list) -> Dict:
    """
    Derive routing rules from feature patterns.
    
    Analyzes features where methods succeed and creates decision boundaries.
    
    Args:
        gva_features: Features from GVA successful cases
        fr_gva_features: Features from FR-GVA successful cases
        
    Returns:
        Routing rules dictionary
    """
    rules = {}
    
    if not gva_features or not fr_gva_features:
        rules['strategy'] = 'try_both'
        rules['reason'] = 'Insufficient data for one or both methods'
        return rules
    
    # Analyze bit length patterns
    gva_bits = [f['bit_length'] for f in gva_features]
    fr_gva_bits = [f['bit_length'] for f in fr_gva_features]
    
    gva_bit_avg = sum(gva_bits) / len(gva_bits)
    fr_gva_bit_avg = sum(fr_gva_bits) / len(fr_gva_bits)
    
    # Analyze gap patterns (if available)
    if all('gap_to_sqrt_ratio' in f for f in gva_features) and \
       all('gap_to_sqrt_ratio' in f for f in fr_gva_features):
        
        gva_gap_ratios = [f['gap_to_sqrt_ratio'] for f in gva_features]
        fr_gva_gap_ratios = [f['gap_to_sqrt_ratio'] for f in fr_gva_features]
        
        gva_gap_avg = sum(gva_gap_ratios) / len(gva_gap_ratios)
        fr_gva_gap_avg = sum(fr_gva_gap_ratios) / len(fr_gva_gap_ratios)
        
        rules['gap_threshold'] = (gva_gap_avg + fr_gva_gap_avg) / 2
        rules['gap_gva_avg'] = gva_gap_avg
        rules['gap_fr_gva_avg'] = fr_gva_gap_avg
    
    # Analyze kappa patterns
    gva_kappas = [f['kappa'] for f in gva_features]
    fr_gva_kappas = [f['kappa'] for f in fr_gva_features]
    
    gva_kappa_avg = sum(gva_kappas) / len(gva_kappas)
    fr_gva_kappa_avg = sum(fr_gva_kappas) / len(fr_gva_kappas)
    
    rules['bit_threshold'] = (gva_bit_avg + fr_gva_bit_avg) / 2
    rules['bit_gva_avg'] = gva_bit_avg
    rules['bit_fr_gva_avg'] = fr_gva_bit_avg
    
    rules['kappa_threshold'] = (gva_kappa_avg + fr_gva_kappa_avg) / 2
    rules['kappa_gva_avg'] = gva_kappa_avg
    rules['kappa_fr_gva_avg'] = fr_gva_kappa_avg
    
    rules['strategy'] = 'feature_based'
    
    return rules


def route_factorization(N: int, routing_rules: Dict, verbose: bool = False) -> MethodChoice:
    """
    Route factorization attempt to FR-GVA or GVA based on structural features.
    
    Uses weighted distance-based scoring with exponential decay to handle
    borderline cases more effectively.
    
    Args:
        N: Semiprime to factor
        routing_rules: Rules derived from correlation analysis
        verbose: Enable detailed logging
        
    Returns:
        Recommended method: "FR-GVA" or "GVA"
    """
    features = extract_structural_features(N)
    
    if routing_rules.get('strategy') == 'try_both':
        if verbose:
            print(f"Router: Insufficient training data, defaulting to GVA")
        return "GVA"
    
    # Feature-based routing with weighted scoring
    bit_length = features['bit_length']
    kappa = features['kappa']
    
    # Use continuous distance-based scoring instead of discrete votes
    gva_score = 0.0
    fr_gva_score = 0.0
    
    # Bit length proximity (weighted heavily as primary predictor)
    if 'bit_threshold' in routing_rules:
        bit_diff_gva = abs(bit_length - routing_rules['bit_gva_avg'])
        bit_diff_fr_gva = abs(bit_length - routing_rules['bit_fr_gva_avg'])
        
        # Inverse distance scoring: closer = higher score
        # Use exponential decay to penalize distance
        gva_bit_score = 1.0 / (1.0 + bit_diff_gva * BIT_DECAY_RATE)
        fr_gva_bit_score = 1.0 / (1.0 + bit_diff_fr_gva * BIT_DECAY_RATE)
        
        gva_score += gva_bit_score * BIT_LENGTH_WEIGHT
        fr_gva_score += fr_gva_bit_score * BIT_LENGTH_WEIGHT
        
        if verbose:
            print(f"  Bit length {bit_length}: GVA dist={bit_diff_gva:.1f} (score={gva_bit_score:.3f}), "
                  f"FR-GVA dist={bit_diff_fr_gva:.1f} (score={fr_gva_bit_score:.3f})")
    
    # Kappa proximity (secondary signal)
    if 'kappa_threshold' in routing_rules:
        kappa_diff_gva = abs(kappa - routing_rules['kappa_gva_avg'])
        kappa_diff_fr_gva = abs(kappa - routing_rules['kappa_fr_gva_avg'])
        
        # Inverse distance scoring with exponential decay
        gva_kappa_score = 1.0 / (1.0 + kappa_diff_gva * KAPPA_DECAY_RATE)
        fr_gva_kappa_score = 1.0 / (1.0 + kappa_diff_fr_gva * KAPPA_DECAY_RATE)
        
        gva_score += gva_kappa_score * KAPPA_WEIGHT
        fr_gva_score += fr_gva_kappa_score * KAPPA_WEIGHT
        
        if verbose:
            print(f"  Kappa {kappa:.6f}: GVA dist={kappa_diff_gva:.6f} (score={gva_kappa_score:.3f}), "
                  f"FR-GVA dist={kappa_diff_fr_gva:.6f} (score={fr_gva_kappa_score:.3f})")
    
    # Make decision based on total weighted score
    if fr_gva_score > gva_score:
        method = "FR-GVA"
        margin = fr_gva_score - gva_score
    else:
        method = "GVA"
        margin = gva_score - fr_gva_score
    
    if verbose:
        print(f"Router decision: {method} (GVA score: {gva_score:.3f}, FR-GVA score: {fr_gva_score:.3f}, margin: {margin:.3f})")
    
    return method


def log_routing_decision(N: int, features: Dict, chosen_method: MethodChoice, 
                         routing_rules: Dict) -> None:
    """
    Log detailed routing decision for audit trail.
    
    Args:
        N: Semiprime being factored
        features: Extracted structural features
        chosen_method: Method chosen by router
        routing_rules: Rules used for routing
    """
    print(f"\n{'='*70}")
    print(f"ROUTING DECISION LOG")
    print(f"{'='*70}")
    print(f"N: {N}")
    print(f"Bit length: {features['bit_length']}")
    print(f"Kappa: {features['kappa']:.6f}")
    print(f"Approx sqrt(N): {features['approx_sqrt']}")
    print(f"\nRouting Rules:")
    
    if routing_rules.get('strategy') == 'feature_based':
        print(f"  Bit threshold: {routing_rules.get('bit_threshold', 'N/A'):.1f}")
        print(f"    GVA avg: {routing_rules.get('bit_gva_avg', 'N/A'):.1f}")
        print(f"    FR-GVA avg: {routing_rules.get('bit_fr_gva_avg', 'N/A'):.1f}")
        print(f"  Kappa threshold: {routing_rules.get('kappa_threshold', 'N/A'):.6f}")
        print(f"    GVA avg: {routing_rules.get('kappa_gva_avg', 'N/A'):.6f}")
        print(f"    FR-GVA avg: {routing_rules.get('kappa_fr_gva_avg', 'N/A'):.6f}")
    
    print(f"\n→ Chosen method: {chosen_method}")
    print(f"{'='*70}\n")
