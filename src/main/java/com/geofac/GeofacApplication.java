package com.geofac;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;

/**
 * Geofac - Geometric Factorization Tool
 *
 * A modern Spring Boot terminal application for integer factorization
 * using geometric resonance methods.
 *
 * Usage:
 *   ./gradlew bootRun
 *   shell> factor 137524771864208156028430259349934309717
 */
@SpringBootApplication
public class GeofacApplication {

    public static void main(String[] args) {
        SpringApplication.run(GeofacApplication.class, args);
    }
}
