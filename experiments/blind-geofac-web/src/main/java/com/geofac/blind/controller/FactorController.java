package com.geofac.blind.controller;

import com.geofac.blind.model.FactorRequest;
import com.geofac.blind.model.FactorResponse;
import com.geofac.blind.model.FactorJob;
import com.geofac.blind.service.FactorService;
import com.geofac.blind.service.LogStreamRegistry;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.servlet.mvc.method.annotation.SseEmitter;

import java.util.Map;
import java.util.UUID;

@RestController
@RequestMapping("/api")
public class FactorController {

    private final FactorService factorService;
    private final LogStreamRegistry logStreamRegistry;

    public FactorController(FactorService factorService, LogStreamRegistry logStreamRegistry) {
        this.factorService = factorService;
        this.logStreamRegistry = logStreamRegistry;
    }

    @PostMapping(path = "/factor", consumes = MediaType.APPLICATION_JSON_VALUE, produces = MediaType.APPLICATION_JSON_VALUE)
    public ResponseEntity<FactorResponse> start(@RequestBody(required = false) FactorRequest request) {
        FactorRequest safeRequest = request == null ? new FactorRequest(null, null, null, null) : request;
        UUID jobId = factorService.startJob(safeRequest);
        return ResponseEntity.accepted().body(new FactorResponse(jobId, "QUEUED"));
    }

    @GetMapping(path = "/status/{jobId}", produces = MediaType.APPLICATION_JSON_VALUE)
    public ResponseEntity<?> status(@PathVariable UUID jobId) {
        FactorJob job = factorService.getJob(jobId);
        if (job == null)
            return ResponseEntity.notFound().build();
        return ResponseEntity.ok(Map.of(
                "jobId", job.getId(),
                "status", job.getStatus(),
                "n", job.getN().toString(),
                "p", job.getFoundP() == null ? null : job.getFoundP().toString(),
                "q", job.getFoundQ() == null ? null : job.getFoundQ().toString(),
                "createdAt", job.getCreatedAt(),
                "completedAt", job.getCompletedAt(),
                "topCandidates", job.getTopCandidates().stream().limit(5).toList()));
    }

    @GetMapping(path = "/config", produces = MediaType.APPLICATION_JSON_VALUE)
    public ResponseEntity<?> config() {
        return ResponseEntity.ok(Map.of(
                "engineSettings", factorService.currentSettings(),
                "notes", "Values are pre-adaptive; per-run scaling depends on N.bitLength()."));
    }

    @GetMapping(path = "/logs/{jobId}", produces = MediaType.TEXT_EVENT_STREAM_VALUE)
    public ResponseEntity<SseEmitter> stream(@PathVariable UUID jobId) {
        FactorService.SseSnapshot snap = factorService.logsSnapshot(jobId);
        if (snap == null)
            return ResponseEntity.notFound().build();
        SseEmitter emitter = logStreamRegistry.register(jobId);
        // push history first
        snap.logs().forEach(line -> {
            try {
                emitter.send(SseEmitter.event().data(line));
            } catch (Exception ignored) {
            }
        });
        return ResponseEntity.ok(emitter);
    }
}
