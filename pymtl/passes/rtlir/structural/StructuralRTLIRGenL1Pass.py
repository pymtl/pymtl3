#=========================================================================
# StructuralRTLIRGenL1Pass.py
#=========================================================================
# Author : Shunning Jiang, Peitian Pan
# Date   : Apr 3, 2019
"""Provide L1 structural RTLIR generation pass."""
from __future__ import absolute_import, division, print_function

from collections import defaultdict, deque

import pymtl
from pymtl.passes import BasePass
from pymtl.passes.BasePass import PassMetadata

from ..RTLIRType import *
from .StructuralRTLIRSignalExpr import gen_signal_expr


class StructuralRTLIRGenL1Pass( BasePass ):
  def __call__( s, top ):
    """ generate structural RTLIR for component `top` """
    if not hasattr( top, '_pass_structural_rtlir_gen' ):
      top._pass_structural_rtlir_gen = PassMetadata()
    s.top = top
    s.gen_rtlir_types( top )
    s.gen_constants( top )
    s.gen_connections( top )

  def gen_rtlir_types( s, top ):
    top._pass_structural_rtlir_gen.rtlir_type = get_rtlir( top )

  def gen_constants( s, m ):
    ns = m._pass_structural_rtlir_gen
    ns.consts = []
    rtype = ns.rtlir_type
    const_types = rtype.get_consts_packed()
    for const_name, const_rtype in const_types:
      hasattr(m, const_name)
      const_instance = getattr(m, const_name)
      ns.consts.append( ( const_name, const_rtype, const_instance ) )

  def gen_connections( s, top ):
    """Generate connections based on the net structure.
    
    Must be called from the top component!
    """
    ns = top._pass_structural_rtlir_gen
    ns.connections_self_self = defaultdict( set )
    ns.connections_self_child = defaultdict( set )
    ns.connections_child_child = defaultdict( set )

    # Generate the connections assuming no sub-components
    nets = top.get_all_value_nets()
    adjs = top.get_signal_adjacency_dict()

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
              s.add_conn_self_self( writer_host, u, v )
            elif writer_host_parent is reader_host:
              s.add_conn_self_child( reader_host, u, v )
            elif writer_host is reader_host_parent:
              s.add_conn_self_child( writer_host, u, v )
            elif writer_host_parent == reader_host_parent:
              s.add_conn_child_child( writer_host_parent, u, v )
            else: assert False
    s.sort_connections( top )

  def add_conn_self_self( s, component, writer, reader ):
    ns = s.top._pass_structural_rtlir_gen
    _rw_pair = ( gen_signal_expr( component, writer ),
                 gen_signal_expr( component, reader ) )
    ns.connections_self_self[ component ].add( _rw_pair )

  def add_conn_self_child( s, component, writer, reader ):
    raise NotImplementedError()

  def add_conn_child_child( s, component, writer, reader ):
    raise NotImplementedError()

  def collect_connections( s, m ):
    ns = s.top._pass_structural_rtlir_gen
    return map( lambda x: ( x, False ), ns.connections_self_self[m] )

  def sort_connections( s, m ):
    m_connections = s.collect_connections( m )
    connections = []
    for u, v in m.get_connect_order():
      _u, _v = gen_signal_expr( m, u ), gen_signal_expr( m, v )
      for idx, ( ( wr, rd ), visited ) in enumerate( m_connections ):

        if not visited and ( ( s.contains( u, wr ) and s.contains( v, rd ) ) or\
           ( s.contains( u, rd ) and s.contains( v, wr ) ) ):
          connections.append( ( wr, rd ) )
          m_connections[idx] = ( m_connections[idx][0], True )
          continue
    connections += map(lambda x:x[0],filter(lambda x:not x[1],m_connections))
    m._pass_structural_rtlir_gen.connections = connections

  def contains( s, obj, signal ):
    """Return if obj contains signal.
    
    At level 1 all signals have their corresponding object in `s.connect`. 
    Therefore just checking whether obj is equal to signal is enough at level 1.
    """
    return obj == signal
