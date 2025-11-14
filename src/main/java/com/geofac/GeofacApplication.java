package com.geofac;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;

/**
 * Geofac - Geometric Factorization Tool
 *
 * A modern Spring Boot terminal application for integer factorization
 * using geometric resonance methods. See docs/VALIDATION_GATES.md for the
 * project's validation policy.
 *
 * Usage:
 *   ./gradlew bootRun
 *   shell> help
 *   shell> example
 */
@SpringBootApplication
public class GeofacApplication {

    public static void main(String[] args) {
        SpringApplication.run(GeofacApplication.class, args);
    }
}
