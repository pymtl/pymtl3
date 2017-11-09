#=========================================================================
# RTLComponent.py
#=========================================================================

from pymtl.datatypes import Bits1
from ComponentLevel3 import ComponentLevel3
from Connectable import Connectable, Signal, InVPort, OutVPort, Wire, Const, _overlap
from errors      import InvalidConnectionError, SignalTypeError, NoWriterError, MultiWriterError
from collections import defaultdict, deque

import inspect, ast # for error message

class RTLComponent( ComponentLevel3 ):

  def __new__( cls, *args, **kwargs ):
    inst = super(RTLComponent, cls).__new__( cls, *args, **kwargs )

    inst.clk   = InVPort( Bits1 )
    inst.reset = InVPort( Bits1 )

    return inst

  def sim_reset( s ):
    s.reset = Bits1( 1 )
    s.tick() # This tick propagates the reset signal
    s.tick()
    s.reset = Bits1( 0 )

  def _bringup_reset_clk( s ):
    visited = set( [ id(s) ] )
    for obj in s._id_obj.values():
      if isinstance( obj, RTLComponent ):
        while id(obj) not in visited:
          visited.add( id(obj) )
          assert hasattr( obj, "_parent" )
          parent = obj._parent
          s.connect( obj._parent.reset, obj.reset )
          s.connect( obj._parent.clk, obj.clk )
          obj = parent

  # Override
  def elaborate( s ):
    s._declare_vars()

    s._tag_name_collect() # tag and collect first
    s._bringup_reset_clk() # connect all reset/clk signals

    for obj in s._id_obj.values():
      if isinstance( obj, RTLComponent ):
        obj._elaborate_read_write_func() # this function is local to the object
      s._collect_vars( obj )

    s._tag_name_collect() # slicing will spawn extra objects

    s._check_upblk_writes()
    s._check_port_in_upblk()

    s._resolve_var_connections()
    s._check_port_in_nets()

    s._generate_net_blocks()

    s._process_constraints()
