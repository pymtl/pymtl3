#-------------------------------------------------------------------------
# VarElaborationPass
#-------------------------------------------------------------------------

from pymtl import *
from pymtl.passes import TagNamePass, BasicElaborationPass
from pymtl.components import Signal, UpdateVar, _overlap
from collections import deque, defaultdict
from pymtl.components.errors import MultiWriterError, VarNotDeclaredError

class VarElaborationPass( BasicElaborationPass ):
  def __init__( self, dump=True ):
    self.dump = dump

  def execute( self, m ):
    m = TagNamePass().execute( m ) # tag name first for error message
    self.recursive_elaborate( m )
    m = TagNamePass().execute( m ) # slicing will spawn extra objects

    self.check_upblk_writes( m )

    if self.dump:
      self.print_read_write_func()

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

    self._blkid_reads  = {}
    self._blkid_writes = {}
    self._blkid_calls  = {}

    self._funcid_func   = {}
    self._funcid_reads  = {}
    self._funcid_writes = {}
    self._funcid_calls  = {}

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

      self._funcid_func.update( m._id_func )

  # Override
  def _elaborate_vars( self, m ):
    if isinstance( m, UpdateVar ):
      self._elaborate_read_write_func( m )

  def _elaborate_read_write_func( self, m ):

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
          if not isinstance( _index, slice ):
            raise VarNotDeclaredError( obj, _index )
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
      try:
        obj = getattr( obj, field )
      except AttributeError:
        raise VarNotDeclaredError( obj, field )

      if not idx:
        # just a variable, go recursively
        lookup_var( obj, depth+1, name, obj_list )
      else:
        # expand_array_index will handle s.x[4].y[*]
        expand_array_index( obj, depth, name, 0, idx, obj_list )

    # We have parsed AST to extract every read/write variable name.
    # I refactor the process of materializing objects in this function

    def extract_obj_from_names( func, names ):
      all_objs = []

      for name, astnode in names:
        objs = []
        try:
          lookup_var( m, 0, name, objs )
        except VarNotDeclaredError as e:
          TagNamePass().execute( m ) # give full name to spawned object
          raise VarNotDeclaredError( e.obj, e.field, func, astnode.lineno )

        all_objs.extend( objs )

        # Annotate astnode with actual objects. However, since I only
        # parse AST of an upblk once to avoid duplicated parsing, I have
        # to fold information across difference instances of the same
        # class into the unique AST. Thus I keep {blk/funcid:objs} dict
        # in each AST node to differentiate between different upblks.

        if not hasattr( astnode, "_objs" ):
          astnode._objs = defaultdict(set)
        astnode._objs[ id(func) ].update( [ id(o) for o in objs ] )

        # TODO Attach astnode to object for error message lineno/coloff

      return all_objs

    # First resolve all funcs' read/write and calling other functions
    # This is because function won't call update blocks.

    for funcid, func in m._id_func.iteritems():

      # Check read

      all_objs = extract_obj_from_names( func, func.rd )
      dedup    = { id(o): o for o in all_objs }.values()

      for obj in dedup:
        self._id_obj[ id(obj) ] = obj
      self._funcid_reads[ funcid ] = dedup

      # Check write

      all_objs = extract_obj_from_names( func, func.wr )
      dedup    = { id(o): o for o in all_objs }.values()

      for obj in dedup:
        self._id_obj[ id(obj) ] = obj
      self._funcid_writes[ funcid ] = dedup

      # Check function calls

      all_calls = []
      for name, astnode in func.fc:
        if name[0][0] not in m._name_func: # Bits1(1)?
          continue
        call = m._name_func[ name[0][0] ]

        if not hasattr( astnode, "_funcs" ):
          astnode._funcs = defaultdict(set)
        astnode._funcs[ funcid ].add( id(call) )

        all_calls.append( call )

      self._funcid_calls[ funcid ] = { id(o): o for o in all_calls }.values()

    # Then, upblk by upblk, name strings "materialize".

    for blkid, blk in m._id_upblk.iteritems():

      # Check read

      all_objs = extract_obj_from_names( blk, blk.rd )
      dedup    = { id(o): o for o in all_objs }.values()

      for obj in dedup:
        self._read_upblks[ id(obj) ].append( blkid )
        self._id_obj[ id(obj) ] = obj

      self._blkid_reads[ blkid ] = list(dedup)

      # Check write

      all_objs = extract_obj_from_names( blk, blk.wr )
      dedup    = { id(o): o for o in all_objs }.values()

      for obj in dedup:
        self._write_upblks[ id(obj) ].append( blkid )
        self._id_obj[ id(obj) ] = obj

      self._blkid_writes[ blkid ] = list(dedup)

      # Check function calls
      # Need to expand function calls and find read/write inside them

      all_calls = []
      for name, astnode in blk.fc:
        if name[0][0] not in m._name_func: # Bits1(1)?
          continue
        call = m._name_func[ name[0][0] ]

        if not hasattr( astnode, "_funcs" ):
          astnode._funcs = defaultdict(set)
        astnode._funcs[ blkid ].add( id(call) )

        all_calls.append( call )

      self._blkid_calls[ blkid ] = { id(o): o for o in all_calls }.values()


  # TODO add filename
  @staticmethod
  def check_upblk_writes( m ):
    write_upblks = m._write_upblks

    for wr_id, wr_blks in write_upblks.iteritems():
      obj = m._id_obj[ wr_id ]

      if len(wr_blks) > 1:
        raise MultiWriterError( \
        "Multiple update blocks write {}.\n - {}".format( repr(obj),
            "\n - ".join([ m._blkid_upblk[x].__name__+" at "+repr(m._blkid_upblk[x].hostobj) \
                           for x in write_upblks[wr_id] ]) ) )

      # See VarConstraintPass.py for full information
      # 1) WR A.b.b.b, A.b.b, A.b, A (detect 2-writer conflict)

      x = obj
      while x:
        if id(x) != wr_id and id(x) in write_upblks:
          raise MultiWriterError( \
          "Two-writer conflict in nested struct/slice. \n - {} (in {})\n - {} (in {})".format(
            repr(x), m._blkid_upblk[write_upblks[id(x)][0]].__name__,
            repr(obj), m._blkid_upblk[write_upblks[wr_id][0]].__name__ ) )
        x = x._nested

      # 4) WR A.b[1:10], A.b[0:5], A.b[6] (detect 2-writer conflict)

      if obj._slice:
        for x in obj._nested._slices.values():
          # Recognize overlapped slices
          if id(x) != wr_id and _overlap( x._slice, obj._slice ) and id(x) in write_upblks:
            raise MultiWriterError( \
              "Two-writer conflict between sibling slices. \n - {} (in {})\n - {} (in {})".format(
                repr(x), m._blkid_upblk[write_upblks[id(x)][0]].__name__,
                repr(obj), m._blkid_upblk[write_upblks[wr_id][0]].__name__ ) )

  def print_read_write_func( self ):
    print
    print "+-------------------------------------------------------------"
    print "+ Read/write/func in each @s.func function"
    print "+-------------------------------------------------------------"
    for funcid, func in self._funcid_func.iteritems():
      print "\nIn {} (func) of {}:".format( func.__name__, func.hostobj )

      if self._funcid_writes[ funcid ]:
        print   "  * Write:"
        for o in self._funcid_writes[ funcid ]:
          print "    + {}".format( repr(o) )

      if self._funcid_reads[ funcid ]:
        print   "  * Read:"
        for o in self._funcid_reads[ funcid ]:
          print "    - {}".format( repr(o) )

      if self._funcid_calls[ funcid ]:
        print   "  * Call:"
        for o in self._funcid_calls[ funcid ]:
          print "    > {}".format( o.__name__ )
    print
    print "+-------------------------------------------------------------"
    print "+ Read/write/func in each @s.update update block"
    print "+-------------------------------------------------------------"
    for blkid, blk in self._blkid_upblk.iteritems():
      print "\nIn {} (update block) of {}:".format( blk.__name__, blk.hostobj )

      if self._blkid_writes[ blkid ]:
        print   "  * Write:"
        for o in self._blkid_writes[ blkid ]:
          print "    + {}".format( repr(o) )

      if self._blkid_reads[ blkid ]:
        print   "  * Read:"
        for o in self._blkid_reads[ blkid ]:
          print "    - {}".format( repr(o) )

      if self._blkid_calls[ blkid ]:
        print   "  * Call:"
        for o in self._blkid_calls[ blkid ]:
          print "    > {}".format( o.__name__ )
