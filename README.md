GT-HDL for GTHDL Paper
==========================================================================

This repo simulates with the three designs (idiv, proc, cgra) used in
the evaluation and is meant to be the GT-HDL design point in the paper.

Changes
--------------------------------------------------------------------------

This branch is based on branch pp482-pldi-baseline-pymtl3. It should have
the same implementation as the baseline pymtl3 except for the following
changes
    - Type check `construct` arguments during elaboration
    - Signal assignments do not perform type checks at simulation time
    - Simulation time type checks are carefully inserted into the bounary
    between statically typed and dynamically typed components
