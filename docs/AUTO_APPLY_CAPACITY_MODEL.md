# Auto Apply Capacity & Scaling Model

## Baseline Worker Requirements
The Auto Apply engine utilizes headless Chromium via Playwright. This is computationally expensive and memory intensive.

### 1 Browser Worker (`celery_browser`)
- **Concurrency Setup**: `--concurrency=2` (Configured in `run_browser_worker.sh`)
- **Memory Footprint**: Base Celery overhead (~150MB) + 2x Headless Chromium instances (~300-600MB each).
- **Required RAM**: 1.5 GB per worker container minimum.
- **SHM Size**: Must have `/dev/shm` sized to at least `2gb` in Docker config to prevent Chromium crashes.

### Capacity Math
- Average application time: 1.5 minutes.
- 1 Worker (concurrency=2) = 2 concurrent applications.
- Throughput: ~80 applications per hour per worker container.
- Daily Throughput: ~1,920 applications per day per worker container.

## Scaling Strategy
- **Horizontal Pod Autoscaling (HPA)**: If moving to Kubernetes, scale based on the Celery `automation` queue length.
- **Database Connection Pooling**: Ensure `CONN_MAX_AGE` is set to prevent connection thrashing as workers scale. The current docker-compose setup handles this.
- **API Rate Limits**: Ensure LLM providers (OpenAI/Groq) are aware of scaling to prevent 429 rate limit errors.

## Limitations
Never set `--concurrency` higher than 4 on a standard worker node, as CPU contention will cause Playwright timeout errors and fail applications silently. It is better to scale the container horizontally than to increase internal worker concurrency.
