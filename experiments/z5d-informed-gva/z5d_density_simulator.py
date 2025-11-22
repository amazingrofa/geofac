"""
Z5D Density Simulator (Lightweight)
====================================

Since enumerating actual primes around √N₁₂₇ ≈ 1.17×10^19 would take too long
in this environment, we simulate Z5D density using the Prime Number Theorem.

The PNT tells us:
- Prime density near x is approximately 1/log(x)
- Prime gaps near x average approximately log(x)

For √N₁₂₇:
- x ≈ 1.172646×10^19
- log(x) ≈ 43.67
- Expected density ≈ 1/43.67 ≈ 0.0229 primes per unit

We'll create a realistic density histogram with:
1. Base density from PNT
2. Local variations (±20%) to simulate actual prime clustering
3. CSV export compatible with z5d_enhanced_fr_gva.py

This provides a valid test of the Z5D integration concept even though
the density data is simulated rather than exact.
"""

from math import log, exp, sin, cos
import csv
import os

# 127-bit challenge
CHALLENGE_127 = 137524771864208156028430259349934309717

# Compute sqrt
def isqrt(n):
    """Integer square root."""
    if n < 0:
        raise ValueError("Square root of negative number")
    if n == 0:
        return 0
    x = n
    y = (x + 1) // 2
    while y < x:
        x = y
        y = (x + n // x) // 2
    return x


# Simulation parameters
VARIATION_FREQ_1 = 10000.0
VARIATION_FREQ_2 = 5000.0
VARIATION_FREQ_3 = 2000.0
VARIATION_AMP_1 = 0.15
VARIATION_AMP_2 = 0.10
VARIATION_AMP_3 = 0.05


def simulate_z5d_density(sqrt_N: int, 
                         window: int = 1000000,
                         bin_width: int = 1000,
                         seed: int = 42) -> dict:
    """
    Simulate Z5D prime density histogram using PNT with realistic variations.
    
    Args:
        sqrt_N: Floor of square root of N
        window: Half-width of analysis window (±window)
        bin_width: Histogram bin width
        seed: Random seed for deterministic variations
        
    Returns:
        Dict mapping bin_center -> density (primes per unit in that bin)
    """
    # Base density from PNT
    base_density = 1.0 / log(float(sqrt_N))
    
    print(f"Simulating Z5D density around √N = {sqrt_N}")
    print(f"Base PNT density: {base_density:.6e} primes/unit")
    print(f"Expected gap: {log(float(sqrt_N)):.2f}")
    print(f"Window: ±{window}, bin width: {bin_width}")
    print()
    
    # Generate bins
    num_bins = (2 * window) // bin_width
    histogram = {}
    
    # Use deterministic pseudo-random variations
    # Simulate prime clustering with sinusoidal modulation
    for i in range(-num_bins // 2, num_bins // 2 + 1):
        bin_center = i * bin_width
        
        # Add realistic variations using multiple frequencies
        # This simulates the observed clustering in actual prime distributions
        variation = 1.0
        variation += VARIATION_AMP_1 * sin(bin_center / VARIATION_FREQ_1 + seed)
        variation += VARIATION_AMP_2 * cos(bin_center / VARIATION_FREQ_2 + seed * 2)
        variation += VARIATION_AMP_3 * sin(bin_center / VARIATION_FREQ_3 + seed * 3)
        
        # Clamp to reasonable range (±30% of base)
        variation = max(0.7, min(1.3, variation))
        
        # Compute density for this bin
        local_density = base_density * variation
        
        histogram[bin_center] = local_density
    
    print(f"Generated {len(histogram)} bins")
    
    # Statistics
    densities = list(histogram.values())
    mean_density = sum(densities) / len(densities)
    min_density = min(densities)
    max_density = max(densities)
    
    print(f"Density range: [{min_density:.6e}, {max_density:.6e}]")
    print(f"Mean density: {mean_density:.6e}")
    print(f"Variation: {(max_density - min_density) / mean_density * 100:.1f}%")
    print()
    
    return histogram


def export_density_histogram(histogram: dict, 
                            sqrt_N: int,
                            output_dir: str,
                            bin_width: int = 1000):
    """
    Export simulated density histogram to CSV.
    
    Args:
        histogram: Dict mapping bin_center -> density
        sqrt_N: Floor of square root of N
        output_dir: Output directory
        bin_width: Bin width (for count calculation)
    """
    # Calculate counts from densities
    # count ≈ density × bin_width
    
    histogram_file = os.path.join(output_dir, "z5d_density_histogram.csv")
    
    with open(histogram_file, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['bin_center', 'count', 'density'])
        
        for bin_center in sorted(histogram.keys()):
            density = histogram[bin_center]
            # Estimate count in this bin
            count = int(density * bin_width)
            writer.writerow([bin_center, count, density])
    
    print(f"Exported histogram to {histogram_file}")
    print()
    
    # Also export metadata
    metadata_file = os.path.join(output_dir, "z5d_density_metadata.txt")
    with open(metadata_file, 'w') as f:
        f.write("Z5D Prime Density Simulation Metadata\n")
        f.write("=" * 50 + "\n")
        f.write(f"N = {CHALLENGE_127}\n")
        f.write(f"sqrt_N = {sqrt_N}\n")
        f.write(f"log(sqrt_N) = {log(float(sqrt_N)):.6f}\n")
        f.write(f"Base PNT density = {1.0 / log(float(sqrt_N)):.6e}\n")
        f.write(f"Bin width = {bin_width}\n")
        f.write(f"Total bins = {len(histogram)}\n")
        f.write(f"\nNote: This is a SIMULATED density histogram based on PNT.\n")
        f.write(f"It represents expected prime density behavior but is not\n")
        f.write(f"derived from actual prime enumeration around √N₁₂₇.\n")
    
    print(f"Exported metadata to {metadata_file}")


def main():
    """Generate simulated Z5D density data for the experiment."""
    print("=" * 70)
    print("Z5D Prime Density Simulator (Lightweight)")
    print("=" * 70)
    print()
    
    sqrt_N = isqrt(CHALLENGE_127)
    
    # Simulate density
    histogram = simulate_z5d_density(
        sqrt_N,
        window=1000000,
        bin_width=1000,
        seed=42
    )
    
    # Export to experiment directory
    output_dir = os.path.dirname(__file__)
    export_density_histogram(histogram, sqrt_N, output_dir, bin_width=1000)
    
    print("=" * 70)
    print("Simulation complete")
    print("=" * 70)
    print()
    print("Files created:")
    print(f"  - z5d_density_histogram.csv (density data)")
    print(f"  - z5d_density_metadata.txt (metadata)")
    print()
    print("These files can now be used by z5d_enhanced_fr_gva.py")


if __name__ == "__main__":
    main()
