#=========================================================================
# HierarchyTranslationPass.py
#=========================================================================
# Translation pass for an RTLComponent instance. This pass will 
# recursively translate all child components. 
# This pass does not have a namespace to write to because it returns the
# string representation of the given model upon called.
#
# Author : Shunning Jiang, Peitian Pan
# Date   : Oct 18, 2018

import re
import inspect

from pymtl       import *
from pymtl.dsl   import ComponentLevel1
from BasePass    import BasePass
from errors      import TranslationError
from Helpers     import make_indent
from RASTType    import get_type
from ComponentTranslationPass import ComponentTranslationPass

class HierarchyTranslationPass( BasePass ):

  def __init__( s, translated, type_env, connections_self_self,
                connections_self_child, connections_child_child ):
    """ create a translator for components """

    s.translated = translated

    s.component_translator = ComponentTranslationPass(
      type_env, connections_self_self, connections_self_child, 
      connections_child_child
    )

  def __call__( s, m ):
    """ translates a single RTLComponent instance and returns its source """

    # Check if this component has been translated
    if m in s.translated: return s.translated[ m ]

    # Translate component m
    ret = s.component_translator( m )

    # Mark this component as translated
    s.translated[ m ] = ''

    # Recursively translate all sub-components
    for obj in sorted( m.get_child_components(), key = repr ):
      ret += s.__call__( obj )

    # Update the full string for this component
    s.translated[ m ] = ret

    return ret
