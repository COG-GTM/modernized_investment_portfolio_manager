"""Batch-completion service scenario (synthetic demonstration).

End-of-day transaction posting jobs per portfolio/run date. When a job finishes,
a completion record is written. Invariant: exactly one completion record per
logical job, including after client retries and service restarts.
"""
