"""
========================================================================
GuardedIfc.py
========================================================================
Generating guarded rdy interface

Author : Shunning Jiang
Date   : Mar 27, 2019
"""

from __future__ import absolute_import, division, print_function

from pymtl3 import *

guarded_ifc, GuardedCalleeIfc, GuardedCallerIfc = generate_guard_decorator_ifcs( "rdy" )
