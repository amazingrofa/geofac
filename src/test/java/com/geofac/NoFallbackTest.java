package com.geofac;

import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.test.context.TestPropertySource;

import java.math.BigInteger;

import static org.junit.jupiter.api.Assertions.*;



@SpringBootTest



@TestPropertySource(properties = {



    "geofac.search-timeout-ms=1", // Force resonance search to time out immediately



    "geofac.allow-127bit-benchmark=true" // Allow numbers outside the default gate for testing



})



class NoFallbackTest {







    @Autowired



    private FactorizerService factorizerService;







    @Test



    void testFactorizationFailsWithoutFallback() {



        // Given the official Gate 1 challenge number (see docs/VALIDATION_GATES.md)



        BigInteger gate1ChallengeNumber = new BigInteger("137524771864208156028430259349934309717");







        // When the factorization is attempted with a very short timeout



        FactorizationResult result = factorizerService.factor(gate1ChallengeNumber);







        // Then the result should indicate failure and not success



        assertFalse(result.success(), "Factorization should have failed without a fallback.");



        assertNotNull(result.errorMessage(), "An error message should be present on failure.");



        assertTrue(result.errorMessage().contains("NO_FACTOR_FOUND"), "Error message should indicate that no factor was found.");



    }



}




