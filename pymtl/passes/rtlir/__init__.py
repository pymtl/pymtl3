"""Expose method that returns RTLIR.

This module exposes get_rtlir method that converts PyMTL components
to RTLIR representation.
"""
from __future__ import absolute_import, division, print_function

# Expose modules containing class definitions that might be interesting
# to some users
# Expose passes
from .behavioral import (
    BehavioralRTLIR,
    BehavioralRTLIRGenPass,
    BehavioralRTLIRTypeCheckPass,
    BehavioralRTLIRVisualizationPass,
)
from .rtype import RTLIRDataType, RTLIRType
from .rtype.RTLIRDataType import get_rtlir_dtype
# Expose methods that generate RTLIR for a single object
from .rtype.RTLIRType import get_rtlir, is_rtlir_convertible
from .structural import StructuralRTLIRGenPass, StructuralRTLIRSignalExpr
