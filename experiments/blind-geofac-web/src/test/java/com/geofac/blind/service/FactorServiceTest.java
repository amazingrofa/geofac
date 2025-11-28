package com.geofac.blind.service;

import com.geofac.blind.model.FactorJob;
import com.geofac.blind.model.FactorRequest;
import com.geofac.blind.model.JobStatus;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;

import java.math.BigInteger;
import java.util.UUID;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertNotNull;

@SpringBootTest(properties = {
        "geofac.samples=400",
        "geofac.m-span=120",
        "geofac.search-timeout-ms=60000",
        "geofac.enable-scale-adaptive=false"
})
class FactorServiceTest {

    @Autowired
    private FactorService service;

    @Test
    void testGeoFacFindsFactorWithinGate4() throws InterruptedException {
        // Balanced Gate-4 composite: ~1e14
        BigInteger p = BigInteger.valueOf(10000019L);
        BigInteger q = BigInteger.valueOf(10000079L);
        BigInteger n = p.multiply(q);

        FactorRequest request = new FactorRequest(n.toString(), 0, 60000L, 200);
        UUID jobId = service.startJob(request);

        FactorJob job = service.getJob(jobId);
        int attempts = 0;
        while (job.getStatus() == JobStatus.RUNNING || job.getStatus() == JobStatus.QUEUED) {
            Thread.sleep(200);
            attempts++;
            if (attempts > 100) {
                break; // 20s cap for test
            }
        }

        assertEquals(JobStatus.COMPLETED, job.getStatus(), "Job should complete successfully");
        assertNotNull(job.getFoundP());
        assertNotNull(job.getFoundQ());
        assertEquals(n, job.getFoundP().multiply(job.getFoundQ()));
    }
}
