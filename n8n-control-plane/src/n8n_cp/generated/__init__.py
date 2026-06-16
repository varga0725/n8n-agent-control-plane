"""Generated, typed models from the n8n OpenAPI spec.

DO NOT EDIT BY HAND. Regenerate with:

    python3 scripts/generate_models.py        # or: make models

The hand-written safety/business logic in n8n_cp/* sits ABOVE this layer and is
never overwritten by regeneration. If ``models.py`` is absent, the package still
runs fully — the typed models are an optional aid for callers/validation, not a
runtime dependency.
"""
try:  # models.py is produced by the codegen step; import is best-effort.
    from .models import *  # noqa: F401,F403
    HAVE_MODELS = True
except Exception:  # pragma: no cover
    HAVE_MODELS = False
