#=========================================================================
# GuardedIfc.py
#=========================================================================
# Generating guarded rdy interface
#
# Author : Shunning Jiang
# Date   : Mar 27, 2019

from pymtl import *

guarded_ifc, GuardedCalleeIfc, GuardedCallerIfc = generate_guard_decorator_ifcs( "rdy" )
