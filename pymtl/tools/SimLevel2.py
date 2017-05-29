from SimLevel1 import SimLevel1
from pymtl.components import UpdateWithVar, NamedObject
from pymtl.components import Connectable, Wire, _overlap
from collections import defaultdict, deque

class SimLevel2( SimLevel1 ):

  def __init__( self, model, tick_mode='unroll' ):
    self.model = model

    self.recursive_tag_name( model )
    self.recursive_elaborate( model )
    self.recursive_tag_name( model ) # slicing will spawn extra objects

    expl, impl    = self.synthesize_var_constraints()
    serial, batch = self.schedule( self._blkid_upblk, self._constraints )

    # self.print_read_write()
    # self.print_constraints( expl, impl )
    # self.print_schedule( serial, batch )
    # self.print_upblk_dag( self._blkid_upblk, self._constraints )

    self.tick = self.generate_tick_func( serial, tick_mode )
    self.cleanup_wires( self.model )

  def cleanup_wires( self, m ):

    # SORRY
    if isinstance( m, list ) or isinstance( m, deque ):
      for i, o in enumerate( m ):
        if isinstance( o, Wire ):
          m[i] = o.default_value()
        else:
          self.cleanup_wires( o )

    elif isinstance( m, NamedObject ):
      for name, obj in m.__dict__.iteritems():
        if ( isinstance( name, basestring ) and not name.startswith("_") ) \
          or isinstance( name, tuple ):
            if isinstance( obj, Wire ):
              setattr( m, name, obj.default_value() )
            else:
              self.cleanup_wires( obj )

  # Override
  def _declare_vars( self ):
    super( SimLevel2, self )._declare_vars()

    self._update_on_edge   = set()
    self._RD_U_constraints = defaultdict(list)
    self._WR_U_constraints = defaultdict(list)

    self._id_obj = {}
    self._read_upblks  = defaultdict(list)
    self._write_upblks = defaultdict(list)
    self._blkid_rdwr   = defaultdict(list)

  # Override
  def _elaborate_vars( self, m ):
    if isinstance( m, UpdateWithVar ):
      self._elaborate_read_write( m )

  # Override
  def _collect_vars( self, m ):
    super( SimLevel2, self )._collect_vars( m )

    if isinstance( m, UpdateWithVar ):
      self._update_on_edge.update( m._update_on_edge )

      for k in m._RD_U_constraints:
        self._RD_U_constraints[k].extend( m._RD_U_constraints[k] )
      for k in m._WR_U_constraints:
        self._WR_U_constraints[k].extend( m._WR_U_constraints[k] )

  def _elaborate_read_write( self, m ):

    # Find s.x[0][*][2], if index is exhausted, jump back to lookup_var

    def expand_array_index( obj, name_depth, name, idx_depth, idx, obj_list ):
      if idx_depth >= len(idx):
        lookup_var( obj, name_depth+1, name, obj_list )
        return

      if idx[ idx_depth ] == "*": # special case, materialize all objects
        for i, o in enumerate( obj ):
          expand_array_index( o, name_depth, name, idx_depth+1, idx, obj_list )
      else:
        _index = idx[ idx_depth ]
        try:
          index = int( _index ) # handle x[2]'s case
          expand_array_index( obj[index], name_depth, name, idx_depth+1, idx, obj_list )

        except TypeError: # cannot convert to integer
          assert isinstance( _index, slice )
          expand_array_index( obj[_index], name_depth, name, idx_depth+1, idx, obj_list )

    # Have already found the variable, but it is an array of objects,
    # s.x = [ [ A() for _ in xrange(2) ] for _ in xrange(3) ]

    def add_all( obj, obj_list ):

      if   isinstance( obj, Connectable ):
        obj_list.append( obj )

      elif isinstance( obj, list ) or isinstance( obj, deque ): # SORRY
        for i, o in enumerate( obj ):
          add_all( o, obj_list )

    # Find the object s.a.b.c, if c is c[] then jump to expand_array_index

    def lookup_var( obj, depth, name, obj_list ):
      if depth >= len(name):
        if not callable(obj): # exclude function calls
          add_all( obj, obj_list ) # if this object is a list/array again...
        return

      # <obj>.<field> should be an object
      (field, idx) = name[ depth ]
      obj = getattr( obj, field )

      if not idx:
        # just a variable, go recursively
        lookup_var( obj, depth+1, name, obj_list )
      else:
        # expand_array_index will handle s.x[4].y[*]
        expand_array_index( obj, depth, name, 0, idx, obj_list )

    # We have parsed AST to extract every read/write variable name. Then,
    # upblk by upblk, name strings "materialize".

    for blkid, blk in m._blkid_upblk.iteritems():

      for typ in [ 'rd', 'wr' ]: # deduplicate code
        if typ == 'rd':
          varnames = blk.rd
          id_upblk = self._read_upblks
        else:
          varnames = blk.wr
          id_upblk = self._write_upblks

        objs = []
        for name in varnames:
          try:
            lookup_var( m, 0, name, objs )
          except Exception as e:
            print name, blk.__name__ #, lineno TODO
            raise

        dedup = { id(o): o for o in objs }
        for o in dedup.values():
          id_upblk[ id(o) ].append( blkid )
          self._id_obj[ id(o) ] = o

        self._blkid_rdwr[ blkid ] += [ (typ, o) for o in dedup.values() ]

  def synthesize_var_constraints( self ):

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
    # Doesn't for nested data struct and slice:

    expl_constraints = set()

    read_upblks  = self._read_upblks
    write_upblks = self._write_upblks

    for typ in [ 'rd', 'wr' ]: # deduplicate code
      if typ == 'rd':
        constraints = self._RD_U_constraints
        equal_blks  = read_upblks
      else:
        constraints = self._WR_U_constraints
        equal_blks  = write_upblks

      # enumerate variable objects
      for obj_id, constrained_blks in constraints.iteritems():
        obj = self._id_obj[ obj_id ]

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
      obj     = self._id_obj[ rd_id ]
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
              if rd_blk in self._update_on_edge:
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
      obj     = self._id_obj[ wr_id ]
      readers = []

      # Check parents. Cover 1), 2) and 3)
      x = obj
      while x:
        if id(x) != wr_id:
          assert id(x) not in write_upblks, "Two-writer conflict in nested data struct/slice. \n - %s (in %s)\n - %s (in %s)" % \
                                        ( x.full_name(), self._blkid_upblk[write_upblks[id(x)][0]].__name__, obj.full_name(), self._blkid_upblk[write_upblks[wr_id][0]].__name__ )
        if id(x) in read_upblks:
          readers.append( id(x) )
        x = x._nested

      # Check the sibling slices. Cover 4)
      if obj._slice:
        for x in obj._nested._slices.values():
          # Recognize overlapped slices
          if id(x) != wr_id and _overlap( x._slice, obj._slice ):
            assert id(x) not in write_upblks, "Two-writer conflict in nested data struct/slice. \n - %s (in %s)\n - %s (in %s)" % \
                                        ( x.full_name(), self._blkid_upblk[write_upblks[id(x)][0]].__name__, obj.full_name(), self._blkid_upblk[write_upblks[wr_id][0]].__name__ )

      # Add all constraints
      for wr_blk in wr_blks:
        for reader in readers:
          for rd_blk in read_upblks[ reader ]:
            if wr_blk != rd_blk:
              if rd_blk in self._update_on_edge:
                impl_constraints.add( (rd_blk, wr_blk) ) # rd < wr
              else:
                impl_constraints.add( (wr_blk, rd_blk) ) # wr < rd default

    self._constraints = expl_constraints.copy()

    for (x, y) in impl_constraints:
      if (y, x) not in expl_constraints: # no conflicting expl
        self._constraints.add( (x, y) )

    self._constraints = list(self._constraints)

    return expl_constraints, impl_constraints

  def print_read_write( self ):
    print
    for blkid, entries in self._blkid_rdwr.iteritems():
      print "In <{}>".format( self._blkid_upblk[ blkid ].__name__ )
      print " * write:"
      for e in entries:
        if e[0] == 'wr':
          print "   + {}".format( e[1].full_name() )

      print " * read:"
      for e in entries:
        if e[0] == 'rd':
          print "   - {}".format( e[1].full_name() )
      print

  def print_constraints( self, explicit, implicit ):

    print
    for (x, y) in explicit:
      print self._blkid_upblk[x].__name__.center(25),"  <  ", self._blkid_upblk[y].__name__.center(25)

    for (x, y) in implicit:
       # no conflicting expl
      print self._blkid_upblk[x].__name__.center(25)," (<) ", self._blkid_upblk[y].__name__.center(25), \
            "(overridden)" if (y, x) in explicit else ""
