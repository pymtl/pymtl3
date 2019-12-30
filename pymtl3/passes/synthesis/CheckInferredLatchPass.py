"""
========================================================================
CheckInferredLatchPass.py
========================================================================

Author : Shunning Jiang
Date   : Dec 29, 2019
"""

from pymtl3.passes.BasePass import BasePass, PassMetadata


class CheckInferredLatchPass( BasePass ):

  def __call__( self, top ):
    if not hasattr( top, "_synth" ):
      top._synth = PassMetadata()

    violated = []

    # check all components and connectables
    for obj in top.get_all_signals():
      if not self.func( obj ):
        violated.append( obj )

    violated = sorted(violated, key=repr)
    top._linting.name_violated_signals = violated
    print("\n[CheckSignalNamePass] These signals violate the provided signal name rule: \n  - ",end="")
    print("\n  - ".join( [ f"{x!r} of class {x.__class__.__name__}" for x in violated ] ) )
