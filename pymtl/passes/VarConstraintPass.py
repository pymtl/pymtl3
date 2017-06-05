#-------------------------------------------------------------------------
# VarConstraintPass
#-------------------------------------------------------------------------

from pymtl.passes import BasePass, BasicConstraintPass
from pymtl.components import _overlap

class VarConstraintPass( BasicConstraintPass ):
  def __init__( self, dump=False ):
    self.dump = dump

  def execute( self, m ): # execute pass on model m
    if not hasattr( m, "_write_upblks" ):
      raise PassOrderError( "_write_upblk/_read_upblks/_WR_U_constraints/_RD_U_constraints/_id_objs" )

    self.synthesize_var_constraints( m )

    if self.dump:
      self.print_constraints( m )
    return m

  @staticmethod
  def synthesize_var_constraints( m ):

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

    expl_constraints = set()

    read_upblks  = m._read_upblks
    write_upblks = m._write_upblks

    for typ in [ 'rd', 'wr' ]: # deduplicate code
      if typ == 'rd':
        constraints = m._RD_U_constraints
        equal_blks  = read_upblks
      else:
        constraints = m._WR_U_constraints
        equal_blks  = write_upblks

      # enumerate variable objects
      for obj_id, constrained_blks in constraints.iteritems():
        obj = m._id_obj[ obj_id ]

        # enumerate upblks that has a constraint with x
        for (sign, co_blk) in constrained_blks:

          for eq_blk in equal_blks[ obj_id ]: # blocks that are U == RD(x)
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

    for rd_id, rd_blks in read_upblks.iteritems():
      obj     = m._id_obj[ rd_id ]
      writers = []

      # Check parents. Cover 1) and 2)
      x = obj
      while x:
        if id(x) in write_upblks:
          writers.append( id(x) )
        x = x._nested

      # Check the sibling slices. Cover 3)
      if obj._slice:
        for x in obj._nested._slices.values():
          if _overlap( x._slice, obj._slice ) and id(x) in write_upblks:
            writers.append( id(x) )

      # Add all constraints
      for writer in writers:
        for wr_blk in write_upblks[ writer ]:
          for rd_blk in rd_blks:
            if wr_blk != rd_blk:
              if rd_blk in m._update_on_edge:
                impl_constraints.add( (rd_blk, wr_blk) ) # rd < wr
              else:
                impl_constraints.add( (wr_blk, rd_blk) ) # wr < rd default

    # Collect all objs that read the variable whose id is "write"
    # 1) WR A.b.b.b, A.b.b, A.b, A (detect 2-writer conflict)
    # 2) WR A.b.b.b   - RD A.b.b, A.b, A
    # 3) WR A.b[1:10] - RD A.b[1:10], A,b, A
    # 4) WR A.b[1:10], A.b[0:5], A.b[6] (detect 2-writer conflict)
    # "WR A.b[1:10] - RD A.b[0:5], A.b[6], A.b[8:11]" has been discovered

    for wr_id, wr_blks in write_upblks.iteritems():
      obj     = m._id_obj[ wr_id ]
      readers = []

      # Check parents. Cover 2) and 3). 1) and 4) should be detected in elaboration
      x = obj
      while x:
        if id(x) in read_upblks:
          readers.append( id(x) )
        x = x._nested

      # Add all constraints
      for wr_blk in wr_blks:
        for reader in readers:
          for rd_blk in read_upblks[ reader ]:
            if wr_blk != rd_blk:
              if rd_blk in m._update_on_edge:
                impl_constraints.add( (rd_blk, wr_blk) ) # rd < wr
              else:
                impl_constraints.add( (wr_blk, rd_blk) ) # wr < rd default

    m._impl_constraints = impl_constraints
    m._constraints = m._expl_constraints.copy()

    for (x, y) in impl_constraints:
      if (y, x) not in expl_constraints: # no conflicting expl
        m._constraints.add( (x, y) )

  @staticmethod
  def print_constraints( m ):

    print
    print "+-------------------------------------------------------------"
    print "+ Constraints"
    print "+-------------------------------------------------------------"
    for (x, y) in m._expl_constraints:
      print m._blkid_upblk[x].__name__.center(25),"  <  ", m._blkid_upblk[y].__name__.center(25)

    for (x, y) in m._impl_constraints:
       # no conflicting expl
      print m._blkid_upblk[x].__name__.center(25)," (<) ", m._blkid_upblk[y].__name__.center(25), \
            "(overridden)" if (y, x) in m._expl_constraints else ""
