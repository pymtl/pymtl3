"""
========================================================================
CheckSignalNamePass.py
========================================================================

Author : Shunning Jiang
Date   : Dec 29, 2019
"""

from pymtl3.dsl import MetadataKey
from pymtl3.passes.BasePass import BasePass


class CheckSignalNamePass( BasePass ):

  result = MetadataKey(list)

  def __init__( self, func=lambda x: x.get_field_name().islower() ):
    self.func = func

  def __call__( self, top ):
    violated = []

    # check all components and connectables
    for obj in top.get_all_signals():
      if not self.func( obj ):
        violated.append( obj )

    violated = sorted(violated, key=repr)
    top.set_metadata( self.result, violated)
    print("\n[CheckSignalNamePass] These signals violate the provided signal name rule: \n  - ",end="")
    print("\n  - ".join( [ f"{x!r} of class {x.__class__.__name__}" for x in violated ] ) )
