package com.geofac.blind.service;

import com.geofac.blind.model.FactorJob;
import com.geofac.blind.model.FactorRequest;
import com.geofac.blind.model.JobStatus;
import org.junit.jupiter.api.Test;

import java.math.BigInteger;
import java.util.UUID;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.doNothing;
import static org.mockito.Mockito.mock;

class FactorServiceTest {

    @Test
    void testGeoFacFindsFactor() throws InterruptedException {
        // Setup
        LogStreamRegistry registry = mock(LogStreamRegistry.class);
        doNothing().when(registry).send(any(), any());
        doNothing().when(registry).close(any());
        try (FactorService service = new FactorService(registry)) {
            // N = 15 (3 * 5)
            // GeoFac should easily find 3 or 5.
            FactorRequest request = new FactorRequest("15", 1000, 5000L, 1);
            UUID jobId = service.startJob(request);

            // Wait for async job
            FactorJob job = service.getJob(jobId);
            int attempts = 0;
            while (job.getStatus() == JobStatus.RUNNING || job.getStatus() == JobStatus.QUEUED) {
                Thread.sleep(100);
                attempts++;
                if (attempts > 50)
                    break; // 5s timeout
            }

            if (job.getStatus() != JobStatus.COMPLETED) {
                System.out.println("Job failed. Logs:");
                job.getLogsSnapshot().forEach(System.out::println);
            }
            assertEquals(JobStatus.COMPLETED, job.getStatus());
            assertNotNull(job.getFoundP());
            assertNotNull(job.getFoundQ());
            assertEquals(BigInteger.valueOf(15), job.getFoundP().multiply(job.getFoundQ()));

            System.out.println("Found factors: " + job.getFoundP() + " * " + job.getFoundQ());
            System.out.println("Top candidates count: " + job.getTopCandidates().size());
            if (!job.getTopCandidates().isEmpty()) {
                System.out.println("Top candidate score: " + job.getTopCandidates().get(0).score());
            }
        }
    }
}
