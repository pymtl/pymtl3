from pymtl import *
from collections  import deque, defaultdict
from pymtl.model.errors import UpblkCyclicError, NotElaboratedError
from pymtl.model import Signal, Const, NamedObject, _overlap
from pymtl.model import ComponentLevel1, ComponentLevel2, ComponentLevel3
import random, py.code

def simple_sim_pass( s, seed=0xdeadbeef ):
  random.seed( seed )
  assert isinstance( s, ComponentLevel1 )

  if not hasattr( s, "_all_U_U_constraints" ):
    raise NotElaboratedError()

  all_upblks = set( s._all_upblks )
  expl_constraints = set( s._all_U_U_constraints )

  gen_upblk_reads  = {}
  gen_upblk_writes = {}

  if isinstance( s, ComponentLevel2 ):
    all_update_on_edge = set( s._all_update_on_edge )
    if isinstance( s, ComponentLevel3 ):
      nets = s._all_nets

      for writer, readers in nets:
        if not readers: continue

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
        exec py.code.Source( src ).compile() in locals(), globals()

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

    for data in [ s._all_upblk_reads, gen_upblk_reads ]:
      for blk, reads in data.iteritems():
        for rd in reads:
          read_upblks[ rd ].add( blk )

    for data in [ s._all_upblk_writes, gen_upblk_writes ]:
      for blk, writes in data.iteritems():
        for wr in writes:
          write_upblks[ wr ].add( blk )

    for typ in [ 'rd', 'wr' ]: # deduplicate code
      if typ == 'rd':
        constraints = s._all_RD_U_constraints
        equal_blks  = read_upblks
      else:
        constraints = s._all_WR_U_constraints
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
      while x:
        if x in write_upblks:
          writers.append( x )
        x = x._nested

      # Check the sibling slices. Cover 3)
      if obj._slice:
        for x in obj._nested._slices.values():
          if _overlap( x._slice, obj._slice ) and x in write_upblks:
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
      while x:
        if x in read_upblks:
          readers.append( x )
        x = x._nested

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

  def tick_normal():
    for blk in serial_schedule:
      blk()
  s.tick = tick_normal

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
