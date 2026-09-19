# ADR-008: Parallel Tailoring via asyncio.Semaphore

**Date**: 2026-02-28  
**Status**: Accepted

**Decision**: Run up to 4 tailoring API calls concurrently using `asyncio.gather` with a semaphore. Free tier: 4. Paid tier: 8.

**Rationale**: Serial tailoring of 6 JDs could take 10+ minutes. Parallel cuts this to ~3 minutes. The semaphore pattern is simple, doesn't require external infrastructure (no Redis/Celery yet), and the concurrency limit is trivially adjustable per tier.

**Alternatives considered**: Serial (too slow, defeats the "leave and come back" UX). Unlimited parallel (risks API rate limits and cost spikes).
