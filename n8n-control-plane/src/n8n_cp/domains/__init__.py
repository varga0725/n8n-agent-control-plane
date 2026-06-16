"""Domain subpackages (spec section 3).

Each domain module is a thin, typed convenience layer over the central tool
registry (``n8n_cp.endpoints``) and dispatcher (``n8n_cp.tools.run_tool``). The
registry stays the single source of truth — these modules just give per-domain
ergonomics (a TOOLS list and one wrapper function per endpoint). Safety gating,
confirmation and audit all still happen in the dispatcher.
"""
