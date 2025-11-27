package com.geofac.experiments;

import com.geofac.FactorizationResult;
import com.geofac.FactorizerService;
import com.geofac.GeofacApplication;
import org.springframework.boot.WebApplicationType;
import org.springframework.boot.builder.SpringApplicationBuilder;
import org.springframework.context.ConfigurableApplicationContext;

import java.math.BigInteger;
import java.util.HashMap;
import java.util.Map;

/**
 * Deterministic runner that factors the 127-bit challenge number using the
 * production FactorizerService with the same tuning as the Gate 3 test.
 * <p>
 * Run with:
 * ./gradlew run127Challenge
 * <p>
 * (see build.gradle task definition added alongside this class)
 */
public final class Factorize127Runner {

    // 127-bit challenge (whitelist)
    private static final BigInteger N =
            new BigInteger("137524771864208156028430259349934309717");

    private Factorize127Runner() {
    }

    public static void main(String[] args) {
        Map<String, Object> props = new HashMap<>();
        props.put("spring.main.banner-mode", "off");

        // Same tuning used in FactorizerServiceTest Gate 3, with larger max radius
        props.put("geofac.allow-127bit-benchmark", true);
        props.put("geofac.precision", 260);
        props.put("geofac.samples", 2000);
        props.put("geofac.m-span", 260);
        props.put("geofac.j", 6);
        props.put("geofac.threshold", 0.95);
        props.put("geofac.k-lo", 0.20);
        props.put("geofac.k-hi", 0.50);
        props.put("geofac.search-timeout-ms", 1_200_000);
        props.put("geofac.max-search-radius", 200_000_000_000_000_000L); // 2e17

        try (ConfigurableApplicationContext ctx = new SpringApplicationBuilder(GeofacApplication.class)
                .web(WebApplicationType.NONE)
                .properties(props)
                .run(args)) {

            FactorizerService service = ctx.getBean(FactorizerService.class);
            long start = System.currentTimeMillis();
            FactorizationResult result = service.factor(N);
            long elapsedMs = System.currentTimeMillis() - start;

            System.out.printf("Elapsed: %.2f s%n", elapsedMs / 1000.0);
            if (result.success()) {
                System.out.println("SUCCESS");
                System.out.println("p = " + result.p());
                System.out.println("q = " + result.q());
                System.out.println("p*q = " + result.p().multiply(result.q()));
            } else {
                System.out.println("FAILURE");
                System.out.println("Error: " + result.errorMessage());
            }
        }
    }
}
