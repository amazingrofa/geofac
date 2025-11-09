package com.geofac;

/**
 * Exception thrown when geometric resonance fails to find a factor.
 * This indicates that the search completed without locating valid factors.
 */
public class NoFactorFoundException extends RuntimeException {
    
    public NoFactorFoundException(String message) {
        super(message);
    }
}
