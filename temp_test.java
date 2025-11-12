    @Test
    void testFactor127BitSemiprime() {
        System.out.println("\n=== Starting 127-bit Factorization Test ===");
        System.out.println("Geometric resonance must find the factors within 5 minutes...\n");

        long startTime = System.currentTimeMillis();
        FactorizationResult result = service.factor(N_127_BIT);
        long duration = System.currentTimeMillis() - startTime;

        System.out.printf("\nCompleted in %.2f seconds\n", duration / 1000.0);

        // Always expect successful factorization
        assertTrue(result.success(), "Geometric resonance must find the factors within timeout");
        
        // Verify result
        BigInteger p = result.p();
        BigInteger q = result.q();
        assertNotNull(p, "p should not be null");
        assertNotNull(q, "q should not be null");

        // Verify factors match expected values
        assertTrue(
            (p.equals(P_EXPECTED) && q.equals(Q_EXPECTED)) ||
            (p.equals(Q_EXPECTED) && q.equals(P_EXPECTED)),
            String.format("Factors should match expected values.\nExpected: p=%s, q=%s\nGot: p=%s, q=%s",
                P_EXPECTED, Q_EXPECTED, p, q)
        );

        // Verify product
        assertEquals(N_127_BIT, p.multiply(q), "Product of factors should equal N");

        System.out.println("\n✓ Test passed: Geometric resonance successfully found factors");
    }
