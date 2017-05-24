from SimLevel1 import *
from pymtl.components import UpdateWithVar, Connectable
from collections import defaultdict, deque

class SimLevel2( SimLevel1 ):

  def __init__( self, model ):
    self.model = model

    self.recursive_tag_name( model )
    self.recursive_elaborate( model )
    self.recursive_tag_name( model )

    assert False
    serial, batch = self.schedule( self._blkid_upblk, self._constraints )
    print_schedule( serial, batch )

    self.tick = self.generate_tick_func( serial )

    if hasattr( model, "line_trace" ):
      self.line_trace = model.line_trace

  # Override
  def _declare_vars( self ):
    super( SimLevel2, self )._declare_vars()

    self._update_on_edge   = set()
    self._RD_U_constraints = defaultdict(list)
    self._WR_U_constraints = defaultdict(list)

    self._id_obj = {}
    self._RD_upblks = defaultdict(list)
    self._WR_upblks = defaultdict(list)

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

      if isinstance( obj, Connectable ):
        obj_list.append( obj )
        return

      # SORRY
      if isinstance( obj, list ) or isinstance( obj, deque ):
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

      print "\nblk {}".format( blk.__name__ )

      for typ in [ 'rd', 'wr' ]: # deduplicate code
        if typ == 'rd':  names, id_upblk = blk.rd, self._RD_upblks
        else:            names, id_upblk = blk.wr, self._WR_upblks

        objs = []
        for name in names:
          try:
            lookup_var( m, 0, name, objs )
          except Exception as e:
            print name, blk.__name__ #, lineno TODO
            raise

        for o in objs:
          oid = id(o)
          id_upblk[ oid ].append( blkid )
          self._id_obj[ oid ] = o

        if objs:
          SimLevel1.recursive_tag_name( m )
          dedup = { id(o): o for o in objs }
          print "  {}: {}".format( typ,
                "  ".join([ "\n   - {}".format( o.full_name() ) for o in dedup.values()] ))
