"""
========================================================================
GenDAGPass.py
========================================================================
Generate a DAG of update blocks (including net connection blocks) from
a model.

Author : Shunning Jiang
Date   : Jan 18, 2018
"""
from collections import defaultdict, deque
from linecache import cache as line_cache

from pymtl3.datatypes import *
from pymtl3.datatypes.bitstructs import get_bitstruct_inst_all_classes
from pymtl3.dsl import *
from pymtl3.dsl.errors import LeftoverPlaceholderError
from pymtl3.extra.pypy import custom_exec
from pymtl3.passes.BasePass import BasePass, PassMetadata


class GenDAGPass( BasePass ):

  def __call__( self, top ):
    top.check()
    top._dag = PassMetadata()

    placeholders = [ x for x in top._dsl.all_named_objects
                     if isinstance( x, Placeholder ) ]

    if placeholders:
      raise LeftoverPlaceholderError( placeholders )

    self._generate_net_blocks( top )
    self._process_value_constraints( top )
    self._process_methods( top )

  def _generate_net_blocks( self, top ):
    """ _generate_net_blocks:
    Each net is an update block. Readers are actually "written" here.
      >>> s.net_reader1 = s.net_writer
      >>> s.net_reader2 = s.net_writer """

    top._dag.genblks = set()
    top._dag.genblk_hostobj = {}
    top._dag.genblk_reads   = {}
    top._dag.genblk_writes  = {}
    # top._dag.genblk_src     = {}

    # Fall back to compiling one block at a time
    # This is currently because there might be different structs with
    # the same name but essentially different type. It requires name
    # disambiguation to let them co-exist in closure. With block-by-block
    # compilation, we minimize the effect.

    # TODO see if directly compiling AST instead of source can be faster
    def compile_net_blk( _globals, src, writer ):
      _locals = {}
      fname = f"Net (writer is {writer!r}"
      custom_exec( compile( src, filename=fname, mode="exec"), _globals, _locals )
      line_cache[ fname ] = (len(src), None, src.splitlines(), fname )
      return list(_locals.values())[0]

    for writer, signals in top.get_all_value_nets():
      if len(signals) == 1:
        continue

      all_readers = [ x for x in signals if x is not writer ]
      all_fanout  = len( all_readers )

      # Here we remove every top-level signal from the reader list, but need to keep a shallow
      # one as the delegate
      #
      # - writer: a,  reader: b, c
      #   nothing
      # - writer: a,  reader: b[0], c
      #   # 1 selected_reader
      #   b[0] @= a
      # - writer: a,  reader: b[0], c[0]
      #   x = a[0]
      #   b[0] @= x
      #   c[0] @= x
      # - writer: a[0],  reader: b, c
      #   # 1 selected_reader
      #   b @= a[0]
      # - writer: a[0],  reader: b[0], c
      #   x = a[0]
      #   b[0] @= x
      #   c    @= x
      # - writer: a[0],  reader: b[0], c[0]
      #   x = a[0]
      #   b[0] @= x
      #   c[0] @= x

      readers = []
      if isinstance( writer, Const ) or writer.is_top_level_signal():
        for x in all_readers:
          if not x.is_top_level_signal():
            readers.append( x )
      else:
        residence = None
        for x in all_readers:
          if x.is_top_level_signal():
            if residence is None:
              residence = x
              readers.append( x )
            # skip other top signals
          else:
            readers.append( x )

      fanout = len(readers)

      genblk_name = f"{writer!r}__{all_fanout}_{fanout}".replace( " ", "" ) \
                      .replace( ".", "_" ).replace( ":", "_" ) \
                      .replace( "[", "_" ).replace( "]", "_" ) \
                      .replace( "(", "_" ).replace( ")", "_" ) \
                      .replace( ",", "_" )

      # If all signals are top-level, we still need to generate an empty
      # to convey the constraints using all_readers

      if fanout == 0:
        blk = compile_net_blk( {}, f"""def {genblk_name}(): pass""", writer )

        top._dag.genblks.add( blk )
        if writer.is_signal():
          top._dag.genblk_reads[ blk ] = [ writer ]
        top._dag.genblk_writes[ blk ] = all_readers
        continue
      # readers = all_readers
      # fanout  = all_fanout

      wr_lca  = writer.get_host_component()
      rd_lcas = [ x.get_host_component() for x in readers ]

      # Find common ancestor: iteratively go to parent level and check if
      # at the same level all objects' ancestors are the same

      mindep  = min( wr_lca.get_component_level(),
                min( [ x.get_component_level() for x in rd_lcas ] ) )

      # First navigate all objects to the same level deep

      for i in range( mindep, wr_lca.get_component_level() ):
        wr_lca = wr_lca.get_parent_object()

      for i, x in enumerate( rd_lcas ):
        for j in range( mindep, x.get_component_level() ):
          x = x.get_parent_object()
        rd_lcas[i] = x

      # Then iteratively check if their ancestor is the same

      while wr_lca is not top:
        succeed = True
        for x in rd_lcas:
          if x is not wr_lca:
            succeed = False
            break
        if succeed: break

        # Bring up all objects for another level
        wr_lca = wr_lca.get_parent_object()
        for i in range( fanout ):
          rd_lcas[i] = rd_lcas[i].get_parent_object()

      lca_len = len( repr(wr_lca) )
      _globals = {'s': wr_lca }

      if isinstance( writer, Const ) and type(writer._dsl.const) is not int:
        types = get_bitstruct_inst_all_classes( writer._dsl.const )

        for t in types:
          if t.__name__ in _globals:
            assert t is _globals[ t.__name__ ], "Cannot handle two subfields with the same struct name but different structs"
          _globals[ t.__name__ ] = t
        wstr = repr(writer)

      else:
        wstr = f"s.{repr(writer)[lca_len+1:]}"

      rstrs   = [ f"s.{repr(x)[lca_len+1:]}" for x in readers ]

      gen_src = """
def {}():
  x = {}
  {}""".format( genblk_name, wstr, '\n  '.join([ f"{rstr} @= x" for rstr in rstrs ]) )

      blk = compile_net_blk( _globals, gen_src, writer )

      top._dag.genblks.add( blk )
      if writer.is_signal():
        top._dag.genblk_reads[ blk ] = [ writer ]
      top._dag.genblk_writes[ blk ] = all_readers

    # Get the final list of update blocks
    top._dag.final_upblks = top.get_all_update_blocks() | top._dag.genblks

  def _process_value_constraints( self, top ):

    # Query update block metadata from top

    update_ff                    = top.get_all_update_ff()
    upblk_reads, upblk_writes, _ = top.get_all_upblk_metadata()
    genblk_reads, genblk_writes  = top._dag.genblk_reads, top._dag.genblk_writes
    U_U, RD_U, WR_U, U_M         = top.get_all_explicit_constraints()

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

    constraint_objs = defaultdict(set)
    expl_constraints = set( top._dsl.all_U_U_constraints )

    for data in [ upblk_reads, genblk_reads ]:
      for blk, reads in data.items():
        for rd in reads:
          read_upblks[ rd ].add( blk )

    for data in [ upblk_writes, genblk_writes ]:
      for blk, writes in data.items():
        for wr in writes:
          write_upblks[ wr ].add( blk )

    for typ in [ 'rd', 'wr' ]: # deduplicate code
      if typ == 'rd':
        constraints = RD_U
        equal_blks  = read_upblks
      else:
        constraints = WR_U
        equal_blks  = write_upblks

      # enumerate variable objects
      for obj, constrained_blks in constraints.items():

        # enumerate upblks that has a constraint with x
        for (sign, co_blk) in constrained_blks:

          for eq_blk in equal_blks[ obj ]: # blocks that are U == RD(x)
            if co_blk != eq_blk:
              if sign == 1: # RD/WR(x) < U is 1, RD/WR(x) > U is -1
                # eq_blk == RD/WR(x) < co_blk
                U_U.add( (eq_blk, co_blk) )
                constraint_objs[ (eq_blk, co_blk) ].add( obj )
              else:
                # co_blk < RD/WR(x) == eq_blk
                U_U.add( (co_blk, eq_blk) )
                constraint_objs[ (co_blk, eq_blk) ].add( obj )

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

    for obj, rd_blks in read_upblks.items():
      writers = []

      # Check parents. Cover 1) and 2)
      x = obj
      while x.is_signal():
        if x in write_upblks:
          writers.append( x )
        x = x.get_parent_object()

      # Check the sibling slices. Cover 3)
      if obj.is_signal():
        for x in obj.get_sibling_slices():
          if x.slice_overlap( obj ) and x in write_upblks:
            writers.append( x )

      # Add all constraints
      for writer in writers:
        for wr_blk in write_upblks[ writer ]:
          if wr_blk not in update_ff:
            for rd_blk in rd_blks:
              if wr_blk != rd_blk:
                # if rd_blk not in update_ff:
                impl_constraints.add( (wr_blk, rd_blk) ) # wr < rd default
                constraint_objs[ (wr_blk, rd_blk) ].add( obj )

    # Collect all objs that read the variable whose id is "write"
    # 1) WR A.b.b.b, A.b.b, A.b, A (detect 2-writer conflict)
    # 2) WR A.b.b.b   - RD A.b.b, A.b, A
    # 3) WR A.b[1:10] - RD A.b[1:10], A,b, A
    # 4) WR A.b[1:10], A.b[0:5], A.b[6] (detect 2-writer conflict)
    # "WR A.b[1:10] - RD A.b[0:5], A.b[6], A.b[8:11]" has been discovered

    for obj, wr_blks in write_upblks.items():
      readers = []

      # Check parents. Cover 2) and 3). 1) and 4) should be detected in elaboration
      x = obj
      while x.is_signal():
        if x in read_upblks:
          readers.append( x )
        x = x.get_parent_object()

      # Add all constraints
      for wr_blk in wr_blks:
        if wr_blk not in update_ff:
          for reader in readers:
              for rd_blk in read_upblks[ reader ]:
                if wr_blk != rd_blk:
                  # if rd_blk not in update_ff:
                  impl_constraints.add( (wr_blk, rd_blk) ) # wr < rd default
                  constraint_objs[ (wr_blk, rd_blk) ].add( obj )

    top._dag.constraint_objs = constraint_objs
    top._dag.all_constraints = { *U_U }
    for (x, y) in impl_constraints:
      if (y, x) not in U_U: # no conflicting expl
        top._dag.all_constraints.add( (x, y) )

  #-----------------------------------------------------------------------
  # Process methods
  #----------------------------------------------------------------------
  # I assume method don't call other methods here

  # Do bfs to find out all potential total constraints associated with
  # each method, direction conflicts, and incomplete constraints

  def _process_methods( self, top ):
    _, _, _, all_M_constraints = top.get_all_explicit_constraints()

    # Here we collect all top level callee ports and collect all
    # constraints that involves a top level callee. NOTE THAT it is
    # possible that the top level callee is connected to an actual callee
    # somewhere else. Hence we use the ACTUAL METHOD as identifier
    # because all members in the net will eventually point to the same
    # method object.

    top._dsl.top_level_callee_ports = top.get_all_object_filter(
      lambda x: isinstance(x, CalleePort) and x.get_host_component() is top )

    method_is_top_level_callee = set()

    all_method_nets = top.get_all_method_nets()
    for writer, net in all_method_nets:
      if writer is not None:
        for member in net:
          if member is not writer:
            assert member.method is None
            member.method = writer.method

          # If the member is a top level callee, we add the writer's
          # actual method to the set
          if member.get_host_component() is top:
            # if not writer.method.__name__.startswith('_binded_method'):
            method_is_top_level_callee.add( writer.method )

    # Add those callee ports that are not part of a net
    for callee in top._dsl.top_level_callee_ports:
      if callee.method:
        # if not callee.method.__name__.startswith('_binded_method'):
        method_is_top_level_callee.add( callee.method )

    method_blks = defaultdict(set)

    # Collect each CalleePort/method is called in which update block
    # We use the actual method of CalleePort to identify each call
    for blk, calls in top._dsl.all_upblk_calls.items():
      for call in calls:
        if isinstance( call, MethodPort ):
          method_blks[ call.method ].add( blk )
        elif isinstance( call, (NonBlockingIfc, BlockingIfc) ):
          method_blks[ call.method.method ].add( blk )
        else:
          method_blks[ call ].add( blk )

    # Put all M-related constraints into predecessor and successor dicts
    pred = defaultdict(set)
    succ = defaultdict(set)

    top._dag.top_level_callee_constraints = set()

    # We pre-process M(x) == M(y) constraints into per-method equivalence
    # sets. We have to do it here for potential open-loop constraints

    equiv = defaultdict(set)
    for (x, y, is_equal) in all_M_constraints:

      if is_equal: # M(x) == M(y)
        # Use the actual method object for constraints

        if   isinstance( x, MethodPort ):
          xx = x.method
        elif isinstance( x, (NonBlockingIfc, BlockingIfc) ):
          xx = x.method.method
        else:
          xx = x

        if   isinstance( y, MethodPort ):
          yy = y.method
        elif isinstance( y, (NonBlockingIfc, BlockingIfc) ):
          yy = y.method.method
        else:
          yy = y

        equiv[xx].add( yy )
        equiv[yy].add( xx )

    # flood-fill to find out all equivalent classes

    visited = set()
    for x in equiv:
      if x not in visited:
        equiv_class = set()
        visited.add( x )
        Q = deque( [x] )
        while Q:
          u = Q.popleft()
          equiv_class.add(u)

          for v in equiv[u]:
            if v not in visited:
              visited.add(v)
              Q.append(v)

        # Point all nodes in the equivalence class to the same set
        for u in equiv_class:
          equiv[ u ] = equiv_class

    for (x, y, is_equal) in all_M_constraints:
      if is_equal: continue

      # Use the actual method object for constraints

      if   isinstance( x, MethodPort ):
        xx = x.method
      elif isinstance( x, (NonBlockingIfc, BlockingIfc) ):
        xx = x.method.method
      else:
        xx = x

      if   isinstance( y, MethodPort ):
        yy = y.method
      elif isinstance( y, (NonBlockingIfc, BlockingIfc) ):
        yy = y.method.method
      else:
        yy = y

      pred[ yy ].add( xx )
      succ[ xx ].add( yy )

      if xx in equiv: # xx is in a equivalence class
        for zz in equiv[xx]:
          if zz in method_is_top_level_callee:
            top._dag.top_level_callee_constraints.add( (zz, yy) )
      else:
        if xx in method_is_top_level_callee:
          top._dag.top_level_callee_constraints.add( (xx, yy) )

      if yy in equiv: # yy is in a equivalence class
        for zz in equiv[yy]:
          if zz in method_is_top_level_callee:
            top._dag.top_level_callee_constraints.add( (xx, zz) )

      else:
        if yy in method_is_top_level_callee:
          top._dag.top_level_callee_constraints.add( (xx, yy) )

    verbose = False

    all_upblks = top.get_all_update_blocks()

    for method, assoc_blks in method_blks.items():
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
                    top._dag.all_constraints.add( (v, blk) )

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
                          top._dag.all_constraints.add( (vb, blk) )

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
                    top._dag.all_constraints.add( (blk, v) )

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
                          top._dag.all_constraints.add( (blk, vb) )

              if (v, 1) not in visited:
                visited.add( (v, 1) )
                Q.append( (v, 1) ) # blk_id < method < ... < u < v < ?

    # Mark update blocks that call blocking methods
    # (CalleeIfcFL/CallerIfcFL) for greenlet wrapping

    blocking_ifcs = top.get_all_object_filter( lambda x: isinstance( x, (CalleeIfcFL, CallerIfcFL) ) )

    top._dag.greenlet_upblks = set()

    for blocking_method in blocking_ifcs:
      for blk in method_blks[ blocking_method.method.method ]:
        top._dag.greenlet_upblks.add( blk )
