Baseline PyMTL3 for GTHDL Paper
==========================================================================

This repo simulates with the three designs (idiv, proc, cgra) used in
the evaluation and is meant to be the baseline PyMTL3 in the paper.

Changes
--------------------------------------------------------------------------

This branch is based on PyMTL3 commit 95b584d8275d26693974b828d1fc4c9ee6eceda4
    - Expose necessary APIs in pymtl3/__init__.py (e.g., get_nbits, reveal_type, ...)
    - Add BypassQueue2RTL; changes in MagicMemCL
