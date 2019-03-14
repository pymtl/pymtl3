#=========================================================================
# ComponentUpblkTranslationPass.py
#=========================================================================
# Translation pass for all update blocks within one component. 
#
# Author : Shunning Jiang, Peitian Pan
# Date   : Oct 18, 2018

import ast

from pymtl                      import *
from pymtl.passes               import BasePass, PassMetadata

from pymtl.passes.rast          import ComponentUpblkRASTGenPass
from pymtl.passes.rast          import RASTVisualizationPass
from pymtl.passes.rast          import ComponentUpblkRASTTypeCheckPass
from pymtl.passes.rast.RASTType import Const, Signal

from ComponentUpblkRASTToSVPass import ComponentUpblkRASTToSVPass
from errors                     import TranslationError
from helpers                    import generate_signal_decl_from_type

class ComponentUpblkTranslationPass( BasePass ):
  def __init__( s, type_env ):
    s.type_env = type_env

  def __call__( s, m ):
    """ translate all upblks in component m and return the source code
    string"""

    m._pass_component_upblk_translation = PassMetadata()
    m._pass_component_upblk_translation.blk_srcs = {}
    m._pass_component_upblk_translation.freevars = {}
    m._pass_component_upblk_translation.tmpvars = {}

    # Generate and visualize RAST
    ComponentUpblkRASTGenPass()( m )
    ComponentUpblkRASTTypeCheckPass( s.type_env )( m )
    # RASTVisualizationPass()( m )
    ComponentUpblkRASTToSVPass()( m )

    # Copy generated SystemVerilog source code into this pass's namespace
    for blk in m.get_update_blocks():
      m._pass_component_upblk_translation.blk_srcs[ blk ] =\
        m._pass_component_upblk_rast_to_sv.sv[ blk ]

    for fvar, string in m._pass_component_upblk_rast_to_sv.freevars.iteritems():
      m._pass_component_upblk_translation.freevars[ fvar ] = string

    # Generate definitions for temporary variables

    tmpvar_type_env = m._pass_component_upblk_rast_type_check.tmpvar_type_env

    for tvar, _Type in tmpvar_type_env.iteritems():
      Type = _Type
      if isinstance( _Type, Const ):
        # Trying to assign constant value to a temporary variable
        # The correct type to declare should be Signal
        Type = Signal.cast( _Type )

      string = generate_signal_decl_from_type( tvar, Type )
      m._pass_component_upblk_translation.tmpvars[ tvar ] = string
