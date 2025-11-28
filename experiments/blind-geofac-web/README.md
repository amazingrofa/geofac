# Blind Geofac Web (Spring Boot, Java 21)

A minimal SPA + REST/SSE service to run a blind geofac band-scan against a 127-bit challenge number.

## Running

```bash
# from repo root
./gradlew -p experiments/blind-geofac-web bootRun
```
Then open http://localhost:8080/ and start a job.

## API
- `POST /api/factor` `{ n?, maxIterations?, timeLimitMillis?, logEvery? }` → `{ jobId, status }`
- `GET /api/status/{jobId}` → job status and found factors
- `GET /api/logs/{jobId}` → SSE stream of log lines

## Notes
- Default N: `137524771864208156028430259349934309717` (factors *not* embedded).
- The factoring loop is intentionally limited (band around sqrt(N)) and serves as a blind pipeline scaffold; extend scoring/banding as needed.
- Logs stream live; prior logs replay when reconnecting.
