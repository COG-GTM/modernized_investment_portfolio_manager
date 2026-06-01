"""Allow running the batch pipeline as: python -m app.batch.pipeline"""

from .pipeline import main

raise SystemExit(main())
