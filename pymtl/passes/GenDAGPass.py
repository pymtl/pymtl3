#=========================================================================
# GenDAGPass.py
#=========================================================================
# Generate a DAG of update blocks (including net connection blocks) from
# a model.
#
# Author : Shunning Jiang
# Date   : Jan 18, 2018

from pymtl import *
from BasePass import BasePass, PassMetadata
from pymtl.dsl import Const, MethodPort
import py, ast
from collections import defaultdict, deque

class GenDAGPass( BasePass ):

  def __call__( self, top ):
    top.check()
    top._dag = PassMetadata()

    self._generate_net_blocks( top )
    self._process_value_constraints( top )
    self._process_method_constraints( top )

  def _generate_net_blocks( self, top ):
    """ _generate_net_blocks:
    Each net is an update block. Readers are actually "written" here.
      >>> s.net_reader1 = s.net_writer
      >>> s.net_reader2 = s.net_writer """

    nets = top.get_all_value_nets()

    top._dag.genblks = set()
    top._dag.genblk_hostobj = {}
    top._dag.genblk_reads   = {}
    top._dag.genblk_writes  = {}
    top._dag.genblk_src     = {}

    # To reduce the time to compile update blocks, I first group the list
    # of update blocks that have the same host object together and fire
    # them in a single compile command.

    hostobj_allsrc = defaultdict(str)
    blkname_meta   = {}

    for i, (writer, signals) in enumerate( nets ):
      if len(signals) == 1:
        continue

      readers = sorted( [ x for x in signals if x is not writer ], key=repr )

      wr_lca  = writer.get_host_component()
      rd_lcas = [ x.get_host_component() for x in readers ]

      # Find common ancestor: iteratively go to parent level and check if
      # at the same level all objects' ancestors are the same

      mindep  = min( wr_lca.get_component_level(),
                     min( [ x.get_component_level() for x in rd_lcas ] ) )

      # First navigate all objects to the same level deep

      for i in xrange( mindep, wr_lca.get_component_level() ):
        wr_lca = wr_lca.get_parent_object()

      for i, x in enumerate( rd_lcas ):
        for j in xrange( mindep, x.get_component_level() ):
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
        for i in xrange( len(rd_lcas) ):
          rd_lcas[i] = rd_lcas[i].get_parent_object()

      lca     = wr_lca # this is the object we want to insert the block to
      lca_len = len( repr(lca) )
      fanout  = len( readers )
      wstr    = repr(writer) if isinstance( writer, Const ) \
                else ( "s." + repr(writer)[lca_len+1:] )
      rstrs   = [ "s." + repr(x)[lca_len+1:] for x in readers]
      upblk_name = "{}__{}".format(repr(writer), fanout) \
                    .replace( ".", "_" ).replace( ":", "_" ) \
                    .replace( "[", "_" ).replace( "]", "" ) \
                    .replace( "(", "_" ).replace( ")", "" )
      gen_src = """
@update
def {0}():
  {1} = {2}""".format( upblk_name, " = ".join( rstrs ), wstr )

      hostobj_allsrc[ lca ] += gen_src
      blkname_meta[ upblk_name ] = (gen_src, writer, readers)

    # Borrow the closure of hostobj to compile the block
    # To reduce the code needed, use a fake @update to collect metadata
    def compile_upblks( s, src ):

      def update( blk ):
        top._dag.genblks.add( blk )
        gen_src, writer, readers = blkname_meta[ blk.__name__ ]
        if writer.is_signal():
          top._dag.genblk_reads[ blk ] = [ writer ]
        top._dag.genblk_writes[ blk ] = readers
        top._dag.genblk_src   [ blk ] = ( gen_src, None )
        # TODO None -- I remove the ast parsing since it is slow

      var = locals()
      var.update( globals() )
      exec( compile( src, filename=repr(s), mode="exec") ) in var

    for hostobj, allsrc in hostobj_allsrc.iteritems():
      compile_upblks( hostobj, allsrc )

  def _process_value_constraints( self, top ):

    # Query update block metadata from top

    update_on_edge               = top.get_all_update_on_edge()
    upblk_reads, upblk_writes, _ = top.get_all_upblk_metadata()
    genblk_reads, genblk_writes  = top._dag.genblk_reads, top._dag.genblk_writes
    U_U, RD_U, WR_U              = top.get_all_explicit_constraints()

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

    for data in [ upblk_reads, genblk_reads ]:
      for blk, reads in data.iteritems():
        for rd in reads:
          read_upblks[ rd ].add( blk )

    for data in [ upblk_writes, genblk_writes ]:
      for blk, writes in data.iteritems():
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
              if rd_blk in update_on_edge:
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
              if rd_blk in update_on_edge:
                impl_constraints.add( (rd_blk, wr_blk) ) # rd < wr
              else:
                impl_constraints.add( (wr_blk, rd_blk) ) # wr < rd default

    top._dag.all_constraints = U_U.copy()
    for (x, y) in impl_constraints:
      if (y, x) not in U_U: # no conflicting expl
        top._dag.all_constraints.add( (x, y) )

  #-----------------------------------------------------------------------
  # Process method constraints
  #----------------------------------------------------------------------
  # I assume method don't call other methods here

  # Do bfs to find out all potential total constraints associated with
  # each method, direction conflicts, and incomplete constraints

  def _process_method_constraints( self, top ):

    try:
      all_M_constraints = top._dsl.all_M_constraints
    except AttributeError:
      return

    try:
      all_method_nets = top.get_all_method_nets()

      for writer, net in top.get_all_method_nets():
        if writer is not None:
          for member in net:
            if member is not writer:
              assert member.method is None
              member.method = writer.method

    except AttributeError:
      pass

    top._dag.top_level_callee_ports = top.get_all_object_filter(
      lambda x: isinstance(x, CalleePort) and x.get_parent_object() is top )
    top._dag.top_level_callee_constraints = set()

    method_blks = defaultdict(set)

    # Collect each CalleePort/method is called in which update block
    # We use bounded method of CalleePort to identify each call
    for blk, calls in top._dsl.all_upblk_calls.iteritems():
      for call in calls:
        if isinstance( call, MethodPort ):
          method_blks[ call.method ].add( blk )
        elif isinstance( call, Interface ):
          try:
            if call.guarded_ifc:
              method_blks[ call.method.method ].add( blk )
          except AttributeError:
            pass
        else:
          method_blks[ call ].add( blk )

    # Put all M-related constraints into predecessor and successor dicts
    pred = defaultdict(set)
    succ = defaultdict(set)

    for (x, y) in all_M_constraints:

      if   isinstance( x, MethodPort ):
        xx = x.method
      elif isinstance( x, Interface ):
        try:
          if x.guarded_ifc:
            xx = x.method.method
        except AttributeError:
          pass
      else:
        xx = x

      if   isinstance( y, MethodPort ):
        yy = y.method
      elif isinstance( y, Interface ):
        try:
          if y.guarded_ifc:
            yy = y.method.method
        except AttributeError:
          pass
      else:
        yy = y

      pred[ yy ].add( xx )
      succ[ xx ].add( yy )

      if x in top._dag.top_level_callee_ports or y in top._dag.top_level_callee_ports:
        top._dag.top_level_callee_constraints.add( (x, y) )

    verbose = False

    all_upblks = top.get_all_update_blocks()

    for method, assoc_blks in method_blks.iteritems():
      Q = deque( [ (method, 0) ] ) # -1: pred, 0: don't know, 1: succ
      if verbose: print
      while Q:
        (u, w) = Q.popleft()
        if verbose: print (u, w)

        if w <= 0:
          for v in pred[u]:

            if v in all_upblks:
              # Find total constraint (v < blk) by v < method_u < method_u'=blk
              # INVALID if we have explicit constraint (blk < method_u)

              for blk in assoc_blks:
                if blk not in pred[u]:
                  if v != blk:
                    if verbose: print "w<=0, v is blk".center(10),v, blk
                    if verbose: print v.__name__.center(25)," < ", \
                                blk.__name__.center(25)
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
                          if verbose: print "w<=0, v is method".center(10),v, blk
                          if verbose: print vb.__name__.center(25)," < ", \
                                      blk.__name__.center(25)
                          top._dag.all_constraints.add( (vb, blk) )

              Q.append( (v, -1) ) # ? < v < u < ... < method < blk_id

        if w >= 0:
          for v in succ[u]:

            if v in all_upblks:
              # Find total constraint (blk < v) by blk=method_u' < method_u < v
              # INVALID if we have explicit constraint (method_u < blk)

              for blk in assoc_blks:
                if blk not in succ[u]:
                  if v != blk:
                    if verbose: print "w>=0, v is blk".center(10),blk, v
                    if verbose: print blk.__name__.center(25)," < ", \
                                      v.__name__.center(25)
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
                          if verbose: print "w>=0, v is method".center(10), blk, v
                          if verbose: print blk.__name__.center(25)," < ", \
                                            vb.__name__.center(25)
                          top._dag.all_constraints.add( (blk, vb) )

              Q.append( (v, 1) ) # blk_id < method < ... < u < v < ?
