package com.geofac;

import java.math.BigInteger;

/**
 * Policy enforcement for strict geometric resonance factorization.
 * 
 * This repository is locked to factor exactly one target integer using
 * only the geometric resonance algorithm. No alternative methods are permitted.
 */
public final class Policy {
    
    /**
     * The single target integer this repository is designed to factor.
     * N = 137524771864208156028430259349934309717
     * (127-bit semiprime = 10508623501177419659 × 13086849276577416863)
     */
    public static final BigInteger TARGET = new BigInteger("137524771864208156028430259349934309717");
    
    /**
     * When true, only geometric resonance is allowed. Fallback algorithms are disabled.
     */
    public static final boolean STRICT_GEOMETRIC_ONLY = true;
    
    /**
     * Exit code when user attempts to factor a number other than TARGET.
     */
    public static final int EXIT_TARGET_MISMATCH = 64;
    
    /**
     * Exit code when geometric resonance completes without finding a factor.
     */
    public static final int EXIT_NO_FACTOR_FOUND = 2;
    
    // Prevent instantiation
    private Policy() {
        throw new AssertionError("Policy class cannot be instantiated");
    }
}
