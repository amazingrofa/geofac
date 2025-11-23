#!/usr/bin/env python3
"""
Theil-Sen Robust Estimator Implementation

A non-parametric robust regression method that uses the median of pairwise slopes.
Resistant to outliers and doesn't assume Gaussian errors.

References:
- Theil, H. (1950). A rank-invariant method of linear and polynomial regression analysis.
- Sen, P. K. (1968). Estimates of the regression coefficient based on Kendall's tau.
"""

from itertools import combinations
from typing import List, Tuple, Optional


def theil_sen(x: List[float], y: List[float]) -> Tuple[float, float]:
    """
    Compute robust linear fit using Theil-Sen estimator.
    
    Method:
    1. Compute slope between every pair of points: m_ij = (y_j - y_i) / (x_j - x_i)
    2. Slope = median of all pairwise slopes
    3. Intercept = median of (y_i - m * x_i)
    
    Args:
        x: List of x values
        y: List of y values
        
    Returns:
        (slope, intercept) tuple
        
    Raises:
        ValueError: If inputs have different lengths or insufficient data
    """
    if len(x) != len(y):
        raise ValueError(f"x and y must have same length: {len(x)} vs {len(y)}")
    
    if len(x) < 2:
        raise ValueError(f"Need at least 2 points for regression, got {len(x)}")
    
    # Compute all pairwise slopes, skipping identical x values
    slopes = []
    for i, j in combinations(range(len(x)), 2):
        if abs(x[j] - x[i]) > 1e-10:  # Avoid division by near-zero
            slope = (y[j] - y[i]) / (x[j] - x[i])
            slopes.append(slope)
    
    if not slopes:
        raise ValueError("All x values are identical, cannot compute slope")
    
    # Slope is median of all pairwise slopes
    slopes_sorted = sorted(slopes)
    n = len(slopes_sorted)
    if n % 2 == 0:
        m = (slopes_sorted[n // 2 - 1] + slopes_sorted[n // 2]) / 2
    else:
        m = slopes_sorted[n // 2]
    
    # Intercept is median of (y_i - m * x_i)
    intercepts = [y[i] - m * x[i] for i in range(len(x))]
    intercepts_sorted = sorted(intercepts)
    n = len(intercepts_sorted)
    if n % 2 == 0:
        b = (intercepts_sorted[n // 2 - 1] + intercepts_sorted[n // 2]) / 2
    else:
        b = intercepts_sorted[n // 2]
    
    return m, b


def ols_regression(x: List[float], y: List[float]) -> Tuple[float, float]:
    """
    Ordinary least squares linear regression for comparison.
    
    Minimizes sum of squared residuals: Σ(y_i - (mx_i + b))²
    
    Args:
        x: List of x values
        y: List of y values
        
    Returns:
        (slope, intercept) tuple
    """
    if len(x) != len(y):
        raise ValueError(f"x and y must have same length: {len(x)} vs {len(y)}")
    
    if len(x) < 2:
        raise ValueError(f"Need at least 2 points for regression, got {len(x)}")
    
    n = len(x)
    sum_x = sum(x)
    sum_y = sum(y)
    sum_xx = sum(xi * xi for xi in x)
    sum_xy = sum(xi * yi for xi, yi in zip(x, y))
    
    denom = n * sum_xx - sum_x * sum_x
    if abs(denom) < 1e-10:
        raise ValueError("Cannot compute OLS: degenerate case (all x values identical)")
    
    m = (n * sum_xy - sum_x * sum_y) / denom
    b = (sum_y - m * sum_x) / n
    
    return m, b


def compute_residuals(x: List[float], y: List[float], slope: float, intercept: float) -> List[float]:
    """Compute residuals: y_i - (m*x_i + b)"""
    return [y[i] - (slope * x[i] + intercept) for i in range(len(x))]


def median_absolute_deviation(residuals: List[float]) -> float:
    """
    Compute Median Absolute Deviation (MAD) - robust measure of spread.
    
    MAD = median(|residual_i - median(residuals)|)
    """
    sorted_res = sorted(residuals)
    n = len(sorted_res)
    if n == 0:
        return 0.0
    
    if n % 2 == 0:
        median_res = (sorted_res[n // 2 - 1] + sorted_res[n // 2]) / 2
    else:
        median_res = sorted_res[n // 2]
    
    abs_deviations = sorted([abs(r - median_res) for r in residuals])
    n = len(abs_deviations)
    if n % 2 == 0:
        mad = (abs_deviations[n // 2 - 1] + abs_deviations[n // 2]) / 2
    else:
        mad = abs_deviations[n // 2]
    
    return mad


def sum_squared_residuals(residuals: List[float]) -> float:
    """Compute sum of squared residuals - used for OLS evaluation"""
    return sum(r * r for r in residuals)


def evaluate_fit(x: List[float], y: List[float], slope: float, intercept: float) -> dict:
    """
    Evaluate quality of linear fit.
    
    Returns dict with:
    - slope, intercept
    - residuals
    - mad (Median Absolute Deviation)
    - ssr (Sum of Squared Residuals)
    """
    residuals = compute_residuals(x, y, slope, intercept)
    mad = median_absolute_deviation(residuals)
    ssr = sum_squared_residuals(residuals)
    
    return {
        'slope': slope,
        'intercept': intercept,
        'residuals': residuals,
        'mad': mad,
        'ssr': ssr
    }
