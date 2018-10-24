#=========================================================================
# SystemVerilogTranslationPass.py
#=========================================================================
# This pass takes the top module of a PyMTL component
# and translates it into SystemVerilog.
#
# Author : Shunning Jiang, Peitian Pan
# Date   : Oct 18, 2018

from pymtl                import *
from pymtl.dsl            import ComponentLevel1
from BasePass             import BasePass
from collections          import defaultdict, deque
from errors               import TranslationError

from ComponentTranslationPass import ComponentTranslationPass

class SystemVerilogTranslationPass( BasePass ):

  def __call__( s, top ):
    """ recursively translate the top module with name top """
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

    connections_self_child    = defaultdict(set)
    connections_self_self     = defaultdict(set)
    connections_child_child   = defaultdict(set)

    for writer, net in nets:
      S = deque( [ writer ] )
      visited = set( [ writer ] )
      while S:
        u = S.pop()
        writer_host         = u.get_host_component()
        writer_host_parent  = writer_host.get_parent_object() 

        for v in adjs[u]:
          if v not in visited:
            visited.add( v )
            S.append( v )
            reader_host         = v.get_host_component()
            reader_host_parent  = reader_host.get_parent_object()

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

    # Recursively translate the top component

    ret = ComponentTranslationPass( 
          connections_self_self, 
          connections_self_self,
          connections_child_child
        )( top )

    # Write output directly to a file

    with open( systemverilog_file, 'w' ) as sv_out_file:
      sv_out_file.write( ret )

    top._translated = True

