#=========================================================================
# SystemVerilogTranslationPass.py
#=========================================================================
# This pass takes the top module of a PyMTL component and translates it 
# into SystemVerilog.
#
# Author : Shunning Jiang, Peitian Pan
# Date   : Jan 9, 2019

import inspect

from pymtl       import *
from RASTType    import *
from pymtl.dsl   import ComponentLevel1
from BasePass    import BasePass
from collections import defaultdict, deque
from errors      import TranslationError
from ComponentTranslationPass import ComponentTranslationPass

class SystemVerilogTranslationPass( BasePass ):

  def __call__( s, top ):
    """Recursively translate the top module with name top."""
    model_name            = top.__class__.__name__
    systemverilog_file    = model_name + '.sv'

    # Get all modules in the component hierarchy and analyze all
    # reader-writer relations. These are needed to generate the
    # continuous assignment statements.

    all_components = sorted( top.get_all_components(), key = repr )
    all_components.reverse()

    # Distribute net connections into components' assignments

    nets = top.get_all_value_nets()
    adjs = top.get_signal_adjacency_dict()

    connections_self_child  = defaultdict(set)
    connections_self_self   = defaultdict(set)
    connections_child_child = defaultdict(set)

    for writer, net in nets:
      S = deque( [ writer ] )
      visited = set( [ writer ] )
      while S:
        u = S.pop()
        writer_host        = u.get_host_component()
        writer_host_parent = writer_host.get_parent_object() 

        for v in adjs[u]:
          if v not in visited:
            visited.add( v )
            S.append( v )
            reader_host        = v.get_host_component()
            reader_host_parent = reader_host.get_parent_object()

            # Four possible cases for the reader and writer signals:
            # 1.   They have the same host component. Both need 
            #       to be added to the host component.
            # 2/3. One's host component is the parent of the other.
            #       Both need to be added to the parent component.
            # 4.   They have the same parent component.
            #       Both need to be added to the parent component.

            if writer_host is reader_host:
              connections_self_self[ writer_host ].add( ( u, v ) )

            elif writer_host_parent is reader_host:
              connections_self_child[ reader_host ].add( ( u, v ) )

            elif writer_host is reader_host_parent:
              connections_self_child[ writer_host ].add( ( u, v ) )

            elif writer_host_parent == reader_host_parent:
              connections_child_child[ writer_host_parent ].add( ( u, v ) )

            else: assert False
    
    # We need to construct the type environment of all components here to 
    # perform RAST type checking.

    type_env = {}

    s.extract_type_env( type_env, top )

    # Recursively translate the top component

    ret = ComponentTranslationPass( 
      type_env,
      connections_self_self, 
      connections_self_self,
      connections_child_child
    )( top )

    # Write output directly to a file

    with open( systemverilog_file, 'w' ) as sv_out_file:
      sv_out_file.write( ret )

    top._translated = True

  # Assume signal only has nbits attribute
  def extract_type_env( s, type_env, component ):
    """Add the types of all attributes of the given component 
    into the type environment."""

    obj_lst = [ obj for (name, obj) in component.__dict__.iteritems() \
      if isinstance( name, basestring ) if not name.startswith( '_' )
    ]

    while obj_lst:
      top_obj = obj_lst.pop()
      type_env[ freeze( top_obj ) ] = s.get_type( top_obj )

    for child in component.get_child_components():
      s.extract_type_env( type_env, child )

  def get_type( s, obj ):
    """return the RAST type of obj"""

    # child component of the given module
    if isinstance( obj, RTLComponent ):
      return Module( obj )

    # signals refer to in/out ports and wires
    elif isinstance( obj, ( InVPort, OutVPort, Wire ) ):
      try:
        nbits = obj._dsl.Type.nbits
      except AttributeError:
        assert False, 'signal instances must have Bits as their .Type field'

      return Signal( nbits )

    # integers have unset bitwidth (0) 
    elif isinstance( obj, int ):
      return Const( 0 )

    # Bits instances
    elif isinstance( obj, Bits ):
      return Const( obj.nbits )

    # array type
    elif isinstance( obj, list ):
      assert len( obj ) > 0

      type_list = map( lambda x: s.get_type( x ), obj )

      assert reduce(lambda x, y: x and (y == type_list[0]), type_list, True),\
        'Elements of list must have the same RAST type!'

      return Array( len( obj ), type_list[0] )

    assert False,\
      'Attributes of an RTLComponent must be signal, constant, list, or module!'

#-----------------------------------------------------------------------
# Helper functions
#-----------------------------------------------------------------------

def freeze( obj ):
  if isinstance( obj, list ):
    return tuple( freeze( o ) for o in obj )
  return obj
