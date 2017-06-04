#-------------------------------------------------------------------------
# VarElaborationPass
#-------------------------------------------------------------------------

from pymtl.passes import TagNamePass, BasicElaborationPass
from pymtl.components import Signal, UpdateVar
from collections import deque, defaultdict

class VarElaborationPass( BasicElaborationPass ):
  def __init__( self, dump=True ):
    self.dump = dump

  def execute( self, m ):
    m = TagNamePass().execute( m ) # tag name first for error message
    self.recursive_elaborate( m )
    m = TagNamePass().execute( m ) # slicing will spawn extra objects

    if self.dump:
      self.print_read_write()

    return m

  # Override
  def _declare_vars( self ):
    super( VarElaborationPass, self )._declare_vars()

    self._update_on_edge   = set()
    self._RD_U_constraints = defaultdict(list)
    self._WR_U_constraints = defaultdict(list)

    self._id_obj = {}
    self._read_upblks  = defaultdict(list)
    self._write_upblks = defaultdict(list)
    self._blkid_rdwr   = defaultdict(list)

  # Override
  def _store_vars( self, m ):
    super( VarElaborationPass, self )._store_vars( m )

    m._update_on_edge = self._update_on_edge
    m._RD_U_constraints = self._RD_U_constraints
    m._WR_U_constraints = self._WR_U_constraints

    m._id_obj = self._id_obj
    m._read_upblks  = self._read_upblks
    m._write_upblks = self._write_upblks

  # Override
  def _collect_vars( self, m ):
    super( VarElaborationPass, self )._collect_vars( m )

    if isinstance( m, UpdateVar ):
      self._update_on_edge.update( m._update_on_edge )

      for k in m._RD_U_constraints:
        self._RD_U_constraints[k].extend( m._RD_U_constraints[k] )
      for k in m._WR_U_constraints:
        self._WR_U_constraints[k].extend( m._WR_U_constraints[k] )

  # Override
  def _elaborate_vars( self, m ):
    if isinstance( m, UpdateVar ):
      self._elaborate_read_write( m )

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

      if   isinstance( obj, Signal ):
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

    for blkid, blk in m._id_upblk.iteritems():

      for typ in [ 'rd', 'wr' ]: # deduplicate code
        if typ == 'rd':
          varnames = blk.rd
          id_upblk = self._read_upblks
        else:
          varnames = blk.wr
          id_upblk = self._write_upblks

        all_objs = []
        for name, astnode in varnames:
          try:
            objs = []
            lookup_var( m, 0, name, objs )
            all_objs.extend( objs )

            # Here I annotate astnode with actual objects. However, since
            # I only parse AST of an upblk once to avoid duplicated
            # parsing, I have to fold information across difference
            # instances of the same class into the unique AST. As a
            # result, I keep {blkid:objs} dictionary in each AST node to
            # differentiate between different upblks.

            if not hasattr( astnode, "_objs" ):
              astnode._objs = defaultdict(set)
            astnode._objs[ blkid ].update( [ id(o) for o in objs ] )

            # Attach astnode to object for error message lineno/coloff

            for o in objs:
              if not hasattr( o, "_astnodes" ):
                o._astnodes = []
              o._astnodes.append( astnode )

          except Exception as e:
            print name, blk.__name__, "line", astnode.lineno #, lineno TODO
            raise

        dedup = { id(o): o for o in all_objs }
        for o in dedup.values():
          id_upblk[ id(o) ].append( blkid )
          self._id_obj[ id(o) ] = o

        self._blkid_rdwr[ blkid ] += [ (typ, o) for o in dedup.values() ]

  def print_read_write( self ):
    print
    print "+-------------------------------------------------------------"
    print "+ Read/write in each update block"
    print "+-------------------------------------------------------------"
    for blkid, entries in self._blkid_rdwr.iteritems():
      print "In < {} >".format( self._blkid_upblk[ blkid ].__name__ )

      wr_str = ""
      rd_str = ""
      for e in entries:
        if e[0] == 'wr':
          wr_str += "   + {}\n".format( repr(e[1]) )
      for e in entries:
        if e[0] == 'rd':
          rd_str += "   - {}\n".format( repr(e[1]) )

      if wr_str != "":
        print " * Write:\n{}".format( wr_str )
      if rd_str != "":
        print " * Read:\n{}".format( rd_str )
