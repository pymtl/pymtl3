"""
========================================================================
sim_utils.py
========================================================================
Simple util functions to bootstrap simulation without simulation passes.

Author : Shunning Jiang
Date   : Jan 1, 2018
"""
from __future__ import absolute_import, division, print_function

import random
from collections import defaultdict, deque

import py.code

from pymtl3.dsl.ComponentLevel1 import ComponentLevel1
from pymtl3.dsl.ComponentLevel2 import ComponentLevel2
from pymtl3.dsl.ComponentLevel3 import ComponentLevel3
from pymtl3.dsl.ComponentLevel4 import ComponentLevel4
from pymtl3.dsl.ComponentLevel5 import ComponentLevel5
from pymtl3.dsl.ComponentLevel6 import ComponentLevel6
from pymtl3.dsl.ComponentLevel7 import ComponentLevel7
from pymtl3.dsl.Connectable import (
    Const,
    Interface,
    MethodPort,
    NonBlockingInterface,
    Signal,
)
from pymtl3.dsl.errors import (
    LeftoverPlaceholderError,
    NotElaboratedError,
    UpblkCyclicError,
)
from pymtl3.dsl.NamedObject import NamedObject
from pymtl3.dsl.Placeholder import Placeholder


def simple_sim_pass( s, seed=0xdeadbeef ):
  #  random.seed( seed )
  assert isinstance( s, ComponentLevel1 )

  if not hasattr( s._dsl, "all_U_U_constraints" ):
    raise NotElaboratedError()

  placeholders = [ x for x in s._dsl.all_named_objects
                   if isinstance( x, Placeholder ) ]

  if placeholders:
    raise LeftoverPlaceholderError( placeholders )

  all_upblks = set( s._dsl.all_upblks )
  expl_constraints = set( s._dsl.all_U_U_constraints )

  gen_upblk_reads  = {}
  gen_upblk_writes = {}

  if isinstance( s, ComponentLevel2 ):
    all_update_on_edge = set( s._dsl.all_update_on_edge )

    if isinstance( s, ComponentLevel3 ):
      nets = s.get_all_value_nets()

      for writer, signals in nets:
        if len(signals) == 1: continue
        readers = [ x for x in signals if x is not writer ]

        fanout  = len( readers )
        wstr    = repr(writer)
        rstrs   = [ repr(x) for x in readers ]

        upblk_name = "{}__{}".format(repr(writer), fanout)\
                        .replace( ".", "_" ).replace( ":", "_" ) \
                        .replace( "[", "_" ).replace( "]", "" ) \
                        .replace( "(", "_" ).replace( ")", "" )

        src = """
        def {0}():
          common_writer = {1}
          {2}
        _recent_blk = {0}
        """.format( upblk_name, wstr, "; ".join(
                    [ "{} = common_writer".format( x ) for x in rstrs ] ) )
        exec(py.code.Source( src ).compile(), locals(), globals())

        all_upblks.add( _recent_blk )

        # Collect read/writer metadata, directly insert them into _all_X

        gen_upblk_reads [ _recent_blk ] = [ writer ]
        gen_upblk_writes[ _recent_blk ] = readers

    # s is ComponentLevel2

    #---------------------------------------------------------------------
    # Explicit constraint
    #---------------------------------------------------------------------
    # Schedule U1 before U2 when U1 == WR(x) < RD(x) == U2: combinational
    #
    # Explicitly, one should define these to invert the implicit constraint:
    # - RD(x) < U when U == WR(x) --> RD(x) ( == U') < U == WR(x)
    # - WR(x) > U when U == RD(x) --> RD(x) == U < WR(x) ( == U')
    # constraint RD(x) < U1 & U2 reads  x --> U2 == RD(x) <  U1
    # constraint RD(x) > U1 & U2 reads  x --> U1 <  RD(x) == U2 # impl
    # constraint WR(x) < U1 & U2 writes x --> U2 == WR(x) <  U1 # impl
    # constraint WR(x) > U1 & U2 writes x --> U1 <  WR(x) == U2
    # Doesn't work for nested data struct and slice:

    read_upblks = defaultdict(set)
    write_upblks = defaultdict(set)

    for data in [ s._dsl.all_upblk_reads, gen_upblk_reads ]:
      for blk, reads in data.iteritems():
        for rd in reads:
          read_upblks[ rd ].add( blk )

    for data in [ s._dsl.all_upblk_writes, gen_upblk_writes ]:
      for blk, writes in data.iteritems():
        for wr in writes:
          write_upblks[ wr ].add( blk )

    for typ in [ 'rd', 'wr' ]: # deduplicate code
      if typ == 'rd':
        constraints = s._dsl.all_RD_U_constraints
        equal_blks  = read_upblks
      else:
        constraints = s._dsl.all_WR_U_constraints
        equal_blks  = write_upblks

      # enumerate variable objects
      for obj, constrained_blks in constraints.iteritems():

        # enumerate upblks that has a constraint with x
        for (sign, co_blk) in constrained_blks:

          for eq_blk in equal_blks[ obj ]: # blocks that are U == RD(x)
            if co_blk != eq_blk:
              if sign == 1: # RD/WR(x) < U is 1, RD/WR(x) > U is -1
                # eq_blk == RD/WR(x) < co_blk
                expl_constraints.add( (eq_blk, co_blk) )
              else:
                # co_blk < RD/WR(x) == eq_blk
                expl_constraints.add( (co_blk, eq_blk) )

    #---------------------------------------------------------------------
    # Implicit constraint
    #---------------------------------------------------------------------
    # Synthesize total constraints between two upblks that read/write to
    # the "same variable" (we also handle the read/write of a recursively
    # nested field/slice)
    #
    # Implicitly, WR(x) < RD(x), so when U1 writes X and U2 reads x
    # - U1 == WR(x) & U2 == RD(x) --> U1 == WR(x) < RD(x) == U2

    impl_constraints = set()

    # Collect all objs that write the variable whose id is "read"
    # 1) RD A.b.b     - WR A.b.b, A.b, A
    # 2) RD A.b[1:10] - WR A.b[1:10], A.b, A
    # 3) RD A.b[1:10] - WR A.b[0:5], A.b[6], A.b[8:11]

    for obj, rd_blks in read_upblks.iteritems():
      writers = []

      # Check parents. Cover 1) and 2)
      x = obj
      while x.is_signal():
        if x in write_upblks:
          writers.append( x )
        x = x.get_parent_object()

      # Check the sibling slices. Cover 3)
      for x in obj.get_sibling_slices():
        if x.slice_overlap( obj ) and x in write_upblks:
          writers.append( x )

      # Add all constraints
      for writer in writers:
        for wr_blk in write_upblks[ writer ]:
          for rd_blk in rd_blks:
            if wr_blk != rd_blk:
              if rd_blk in all_update_on_edge:
                impl_constraints.add( (rd_blk, wr_blk) ) # rd < wr
              else:
                impl_constraints.add( (wr_blk, rd_blk) ) # wr < rd default

    # Collect all objs that read the variable whose id is "write"
    # 1) WR A.b.b.b, A.b.b, A.b, A (detect 2-writer conflict)
    # 2) WR A.b.b.b   - RD A.b.b, A.b, A
    # 3) WR A.b[1:10] - RD A.b[1:10], A,b, A
    # 4) WR A.b[1:10], A.b[0:5], A.b[6] (detect 2-writer conflict)
    # "WR A.b[1:10] - RD A.b[0:5], A.b[6], A.b[8:11]" has been discovered

    for obj, wr_blks in write_upblks.iteritems():
      readers = []

      # Check parents. Cover 2) and 3). 1) and 4) should be detected in elaboration
      x = obj
      while x.is_signal():
        if x in read_upblks:
          readers.append( x )
        x = x.get_parent_object()

      # Add all constraints
      for wr_blk in wr_blks:
        for reader in readers:
          for rd_blk in read_upblks[ reader ]:
            if wr_blk != rd_blk:
              if rd_blk in all_update_on_edge:
                impl_constraints.add( (rd_blk, wr_blk) ) # rd < wr
              else:
                impl_constraints.add( (wr_blk, rd_blk) ) # wr < rd default

    all_constraints = expl_constraints.copy()
    for (x, y) in impl_constraints:
      if (y, x) not in expl_constraints: # no conflicting expl
        all_constraints.add( (x, y) )
  else:
    all_constraints = expl_constraints.copy()

  #-----------------------------------------------------------------------
  # Process method constraints
  #----------------------------------------------------------------------
  # I assume method don't call other methods here

  # Do bfs to find out all potential total constraints associated with
  # each method, direction conflicts, and incomplete constraints

  verbose = False

  if isinstance( s, ComponentLevel4 ):
    method_blks = defaultdict(set)

    if isinstance( s, ComponentLevel5 ):
      for writer, net in s._dsl.all_method_nets:
        for member in net:
          if member is not writer:
            assert member.method is None
            member.method = writer.method

    # Collect each CalleePort/method is called in which update block
    # We use bounded method of CalleePort to identify each call
    for blk, calls in s._dsl.all_upblk_calls.iteritems():
      if verbose: print("--", blk, calls)
      for call in calls:
        if isinstance( call, MethodPort ):
          method_blks[ call.method ].add( blk )
        elif isinstance( call, NonBlockingInterface ):
          method_blks[ call.method.method ].add( blk )
        else:
          method_blks[ call ].add( blk )

    # Put all M-related constraints into predecessor and successor dicts
    pred = defaultdict(set)
    succ = defaultdict(set)

    # We also pre-process M(x) == M(y) constraints into per-method
    # equivalence sets
    equiv = defaultdict(set)

    for (x, y, is_equal) in s._dsl.all_M_constraints:
      if verbose: print((x,y,is_equal))

      if   isinstance( x, MethodPort ):
        xx = x.method

      # We allow the user to call the interface directly in a non-blocking
      # interface, so if they do call it, we use the actual method within
      # the method field
      elif isinstance( x, NonBlockingInterface ):
        xx = x.method.method

      else:
        xx = x

      if   isinstance( y, MethodPort ):
        yy = y.method

      elif isinstance( y, NonBlockingInterface ):
        yy = y.method.method

      else:
        yy = y

      pred[ yy ].add( xx )
      succ[ xx ].add( yy )

      if is_equal: # M(x) == M(y)
        equiv[xx].add( yy )
        equiv[yy].add( xx )

    for method, assoc_blks in method_blks.iteritems():
      visited = {  (method, 0)  }
      Q = deque( [ (method, 0) ] ) # -1: pred, 0: don't know, 1: succ

      if verbose: print()
      while Q:
        (u, w) = Q.pop()
        if verbose: print((u, w))

        if u in equiv:
          for v in equiv[u]:
            if (v, w) not in visited:
              visited.add( (v, w) )
              Q.append( (v, w) )

        if w <= 0:
          for v in pred[u]:

            if v in all_upblks:
              # Find total constraint (v < blk) by v < method_u < method_u'=blk
              # INVALID if we have explicit constraint (blk < method_u)

              for blk in assoc_blks:
                if blk not in pred[u]:
                  if v != blk:
                    if verbose: print("w<=0, v is blk".center(10),v, blk)
                    if verbose: print(v.__name__.center(25)," < ", \
                                blk.__name__.center(25))
                    all_constraints.add( (v, blk) )

            else:
              if v in method_blks:
                # TODO Now I'm leaving incomplete dependency chain because I didn't close the circuit loop.
                # E.g. I do port.wr() somewhere in __main__ to write to a port.

                # Find total constraint (vb < blk) by vb=method_v < method_u=blk
                # INVALID if we have explicit constraint (blk < method_v) or (method_u < vb)

                v_blks = method_blks[ v ]
                for vb in v_blks:
                  if vb not in succ[u]:
                    for blk in assoc_blks:
                      if blk not in pred[v]:
                        if vb != blk:
                          if verbose: print("w<=0, v is method".center(10),v, blk)
                          if verbose: print(vb.__name__.center(25)," < ", \
                                      blk.__name__.center(25))
                          all_constraints.add( (vb, blk) )

              if (v, -1) not in visited:
                visited.add( (v, -1) )
                Q.append( (v, -1) ) # ? < v < u < ... < method < blk_id

        if w >= 0:
          for v in succ[u]:

            if v in all_upblks:
              # Find total constraint (blk < v) by blk=method_u' < method_u < v
              # INVALID if we have explicit constraint (method_u < blk)

              for blk in assoc_blks:
                if blk not in succ[u]:
                  if v != blk:
                    if verbose: print("w>=0, v is blk".center(10),blk, v)
                    if verbose: print(blk.__name__.center(25)," < ", \
                                      v.__name__.center(25))
                    all_constraints.add( (blk, v) )

            else:
              if v in method_blks:
                # assert v in method_blks, "Incomplete elaboration, something is wrong! %s" % hex(v)
                # TODO Now I'm leaving incomplete dependency chain because I didn't close the circuit loop.
                # E.g. I do port.wr() somewhere in __main__ to write to a port.

                # Find total constraint (blk < vb) by blk=method_u < method_v=vb
                # INVALID if we have explicit constraint (vb < method_u) or (method_v < blk)

                v_blks = method_blks[ v ]
                for vb in v_blks:
                  if not vb in pred[u]:
                    for blk in assoc_blks:
                      if not blk in succ[v]:
                        if vb != blk:
                          if verbose: print("w>=0, v is method".center(10), blk, v)
                          if verbose: print(blk.__name__.center(25)," < ", \
                                            vb.__name__.center(25))
                          all_constraints.add( (blk, vb) )

              if (v, 1) not in visited:
                visited.add( (v, 1) )
                Q.append( (v, 1) ) # blk_id < method < ... < u < v < ?

  # Construct the graph

  vs  = all_upblks
  es  = defaultdict(list)
  InD = { v:0 for v in vs }

  for (u, v) in list( all_constraints ): # u -> v, always
    InD[v] += 1
    es [u].append( v )

  # Perform topological sort for a serial schedule.

  serial_schedule = []
  Q = deque( [ v for v in vs if not InD[v] ] )
  while Q:
    random.shuffle(Q)
    #  print Q
    u = Q.pop()
    serial_schedule.append( u )
    for v in es[u]:
      InD[v] -= 1
      if not InD[v]:
        Q.append( v )

  if len(serial_schedule) != len(vs):
    raise UpblkCyclicError(
      'Update blocks have cyclic dependencies.'
      '* Please consult update dependency graph for details.'
    )

  assert serial_schedule, "No update block found in the model"

  if verbose:
    from graphviz import Digraph
    dot = Digraph()
    dot.graph_attr["rank"] = "same"
    dot.graph_attr["ratio"] = "compress"
    dot.graph_attr["margin"] = "0.1"

    for x in vs:
      dot.node( x.__name__, shape="box")

    for (x, y) in all_constraints:
      dot.edge( x.__name__,
                y.__name__ )

    dot.render( "/tmp/upblk-dag.gv", view=True )

  def tick_normal():
    for blk in serial_schedule:
      blk()
  s.tick = tick_normal
  s._dsl.schedule = serial_schedule

  # Clean up Signals

  def cleanup_signals( m ):
    if isinstance( m, list ):
      for i, o in enumerate( m ):
        if   isinstance( o, Signal ): m[i] = o.default_value()
        elif isinstance( o, Const ):  m[i] = o.const
        else:                         cleanup_signals( o )

    elif isinstance( m, NamedObject ):
      for name, obj in m.__dict__.iteritems():
        if ( isinstance( name, basestring ) and not name.startswith("_") ) \
          or isinstance( name, tuple ):
          if   isinstance( obj, Signal ): setattr( m, name, obj.default_value() )
          elif isinstance( obj, Const ):  setattr( m, name, obj.const )
          else:                           cleanup_signals( obj )

  cleanup_signals( s )
