#=========================================================================
# StructuralRTLIRGenL1Pass_test.py
#=========================================================================
# Author : Peitian Pan
# Date   : May 19, 2019
"""Test the generation of level 1 structural RTLIR."""
from collections import defaultdict, deque

from pymtl3 import dsl
from pymtl3.datatypes import Bits1, Bits4, Bits32
from pymtl3.passes.rtlir.rtype import RTLIRDataType as rdt
from pymtl3.passes.rtlir.rtype import RTLIRType as rt
from pymtl3.passes.rtlir.structural import StructuralRTLIRSignalExpr as sexp
from pymtl3.passes.rtlir.structural.StructuralRTLIRGenL1Pass import (
    StructuralRTLIRGenL1Pass,
)
from pymtl3.passes.testcases import (
    CaseConnectBitsConstToOutComp,
    CaseConnectBitSelToOutComp,
    CaseConnectConstToOutComp,
    CaseConnectInToWireComp,
    CaseConnectPortIndexComp,
    CaseConnectSliceToOutComp,
    CaseConstBits32AttrComp,
    CaseInx2Outx2ConnectComp,
)


def gen_connections( top ):
  _inst_conns = defaultdict( set )

  # Generate the connections assuming no sub-components
  nets = top.get_all_value_nets()
  adjs = top.get_signal_adjacency_dict()

  for writer, net in nets:
    S = deque( [ writer ] )
    visited = {  writer  }
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
            _inst_conns[writer_host].add( ( u, v ) )
          elif writer_host_parent is reader_host:
            _inst_conns[reader_host].add( ( u, v ) )
          elif writer_host is reader_host_parent:
            _inst_conns[writer_host].add( ( u, v ) )
          elif writer_host_parent == reader_host_parent:
            _inst_conns[writer_host_parent].add( ( u, v ) )
          else:
            raise TypeError( "unexpected connection type!" )

  return _inst_conns

def test_L1_const_numbers():
  a = CaseConstBits32AttrComp.DUT()
  a.elaborate()
  a.apply( StructuralRTLIRGenL1Pass( gen_connections( a ) ) )
  consts = a.get_metadata( StructuralRTLIRGenL1Pass.consts )
  assert consts == [('const', rt.Array([5], rt.Const(rdt.Vector(32))), a.const)]

def test_L1_connection_order():
  a = CaseInx2Outx2ConnectComp.DUT()
  a.elaborate()
  a.apply( StructuralRTLIRGenL1Pass( gen_connections( a ) ) )
  connections = a.get_metadata( StructuralRTLIRGenL1Pass.connections )
  comp = sexp.CurComp(a, 's')
  assert connections == \
    [(sexp.CurCompAttr(comp, 'in_1'), sexp.CurCompAttr(comp, 'out1')),
     (sexp.CurCompAttr(comp, 'in_2'), sexp.CurCompAttr(comp, 'out2'))]

def test_L1_port_index():
  a = CaseConnectPortIndexComp.DUT()
  a.elaborate()
  a.apply( StructuralRTLIRGenL1Pass( gen_connections( a ) ) )
  connections = a.get_metadata( StructuralRTLIRGenL1Pass.connections )
  comp = sexp.CurComp(a, 's')
  assert connections == \
    [(sexp.PortIndex(sexp.CurCompAttr(comp, 'in_'), 2), sexp.CurCompAttr(comp, 'out'))]

def test_L1_wire_index():
  a = CaseConnectInToWireComp.DUT()
  a.elaborate()
  a.apply( StructuralRTLIRGenL1Pass( gen_connections( a ) ) )
  connections = a.get_metadata( StructuralRTLIRGenL1Pass.connections )
  comp = sexp.CurComp(a, 's')
  assert connections[0] == \
    (sexp.WireIndex(sexp.CurCompAttr(comp, 'wire_'), 2), sexp.CurCompAttr(comp, 'out'))

def test_L1_const_index():
  a = CaseConnectConstToOutComp.DUT()
  a.elaborate()
  a.apply( StructuralRTLIRGenL1Pass( gen_connections( a ) ) )
  connections = a.get_metadata( StructuralRTLIRGenL1Pass.connections )
  comp = sexp.CurComp(a, 's')
  # The expression structure is removed and only the constant value
  # is left in this node.
  assert connections == \
    [(sexp.ConstInstance(Bits32(a.const_[2]), 42), sexp.CurCompAttr(comp, 'out'))]

def test_L1_bit_selection():
  a = CaseConnectBitSelToOutComp.DUT()
  a.elaborate()
  a.apply( StructuralRTLIRGenL1Pass( gen_connections( a ) ) )
  connections = a.get_metadata( StructuralRTLIRGenL1Pass.connections )
  comp = sexp.CurComp(a, 's')
  # PyMTL DSL converts bit selection into 1-bit part selection!
  assert connections == \
    [(sexp.PartSelection(sexp.CurCompAttr(comp, 'in_'), 0, 1), sexp.CurCompAttr(comp, 'out'))]

def test_L1_part_selection():
  a = CaseConnectSliceToOutComp.DUT()
  a.elaborate()
  a.apply( StructuralRTLIRGenL1Pass( gen_connections( a ) ) )
  connections = a.get_metadata( StructuralRTLIRGenL1Pass.connections )
  comp = sexp.CurComp(a, 's')
  assert connections == \
    [(sexp.PartSelection(sexp.CurCompAttr(comp, 'in_'), 4, 8), sexp.CurCompAttr(comp, 'out'))]

def test_L1_bits_connection():
  a = CaseConnectBitsConstToOutComp.DUT()
  a.elaborate()
  a.apply( StructuralRTLIRGenL1Pass( gen_connections( a ) ) )
  connections = a.get_metadata( StructuralRTLIRGenL1Pass.connections )
  comp = sexp.CurComp(a, 's')
  assert connections == \
    [(sexp.ConstInstance(Bits32(0), 0), sexp.CurCompAttr(comp, 'out'))]
