#=========================================================================
# ComponentLevel2.py
#=========================================================================

from ComponentLevel1 import ComponentLevel1
from Connectable     import Signal, InVPort, OutVPort, Wire, _overlap
from ConstraintTypes import U, RD, WR, ValueConstraint
from collections     import defaultdict
from errors import InvalidConstraintError, SignalTypeError, \
                   MultiWriterError, VarNotDeclaredError, InvalidFuncCallError, UpblkFuncSameNameError
import AstHelper

import inspect2, re, ast
p = re.compile('( *(@|def))')

class ComponentLevel2( ComponentLevel1 ):

  #-----------------------------------------------------------------------
  # Private methods
  #-----------------------------------------------------------------------

  def __new__( cls, *args, **kwargs ):
    inst = super( ComponentLevel2, cls ).__new__( cls, *args, **kwargs )

    inst._update_on_edge   = set()

    # constraint[var] = (sign, func)
    inst._RD_U_constraints = defaultdict(list)
    inst._WR_U_constraints = defaultdict(list)
    inst._name_func = {}

    return inst

  def _cache_func_meta( s, func ):
    """ Convention: the source of a function/update block across different
    instances should be the same. You can construct different functions
    based on the condition, but please use different names. This not only
    keeps the caching valid, but also make the code more readable.

    According to the convention, we can cache the information of a
    function in the *class object* to avoid redundant parsing. """
    cls = type(s)
    try:
      name_src = cls._name_src
      name_ast = cls._name_ast
      name_rd  = cls._name_rd
      name_wr  = cls._name_wr
      name_fc  = cls._name_fc
    except:
      name_src = cls._name_src = {}
      name_ast = cls._name_ast = {}
      name_rd  = cls._name_rd  = {}
      name_wr  = cls._name_wr  = {}
      name_fc  = cls._name_fc  = {}

    name = func.__name__
    if name not in name_src:
      name_src[ name ] = src  = p.sub( r'\2', inspect2.getsource(func) )
      name_ast[ name ] = tree = ast.parse( src )
      name_rd[ name ]  = rd   = []
      name_wr[ name ]  = wr   = []
      name_fc[ name ]  = fc   = []
      AstHelper.extract_read_write( func, tree, rd, wr )
      AstHelper.extract_func_calls( func, tree, fc )

  # Override
  def _declare_vars( s ):
    super( ComponentLevel2, s )._declare_vars()

    s._all_funcs = set()
    s._all_update_on_edge = set()

    s._all_RD_U_constraints = defaultdict(list)
    s._all_WR_U_constraints = defaultdict(list)

    # We don't collect func's metadata
    # because every func is local to the component
    s._all_upblk_reads  = {}
    s._all_upblk_writes = {}
    s._all_upblk_calls  = {}

  def _elaborate_read_write_func( s ):

    # We have parsed AST to extract every read/write variable name.
    # I refactor the process of materializing objects in this function
    # Pass in the func as well for error message

    def extract_obj_from_names( func, names ):

      def expand_array_index( obj, name_depth, name, idx_depth, idx, obj_list ):
        """ Find s.x[0][*][2], if index is exhausted, jump back to lookup_var """

        if idx_depth >= len(idx): # exhausted, go to next level of name
          lookup_var( obj, name_depth+1, name, obj_list )

        elif idx[ idx_depth ] == "*": # special case, materialize all objects
          if isinstance( obj, Signal ): # Signal[*] is the signal itself
            add_all( obj, obj_list )
          else:
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
          except IndexError:
            pass

      def add_all( obj, obj_list ):
        """ Already found, but it is an array of objects,
            s.x = [ [ A() for _ in xrange(2) ] for _ in xrange(3) ].
            Recursively collect all signals. """
        if   isinstance( obj, Signal ):
          obj_list.append( obj )
        elif isinstance( obj, list ): # SORRY
          for i, o in enumerate( obj ):
            add_all( o, obj_list )

      def lookup_var( obj, depth, name, obj_list ):
        """ Look up the object s.a.b.c in s. Jump to expand_array_index if c[] """

        if depth >= len(name): # exhausted
          if not callable(obj): # exclude function calls
            add_all( obj, obj_list ) # if this object is a list/array again...
          return
        else:
          field, idx = name[ depth ]
          try:
            obj = getattr( obj, field )
          except AttributeError:
            raise VarNotDeclaredError( obj, field )

          if not idx: lookup_var( obj, depth+1, name, obj_list )
          else:       expand_array_index( obj, depth, name, 0, idx, obj_list )

      """ extract_obj_from_names:
      Here we enumerate names and use the above functions to turn names
      into objects """

      all_objs = set()

      for name, astnode in names:
        objs = []
        try:
          lookup_var( s, 0, name, objs )
        except VarNotDeclaredError as e:
          s._tag_name_collect() # give full name to spawned object
          raise VarNotDeclaredError( e.obj, e.field, func, astnode.lineno )

        all_objs.update( objs )

        # Annotate astnode with actual objects. However, since I only
        # parse AST of an upblk/function once to avoid duplicated parsing,
        # I have to fold information across difference instances of the
        # same class into the unique AST. Thus I keep {blk/funcid:objs}
        # dict in each AST node to differentiate between different upblks.

        try:
          astnode._objs[ func ].update( objs )
        except AttributeError:
          astnode._objs = defaultdict(set)
          astnode._objs[ func ].update( objs )

        # TODO Attach astnode to object for error message lineno/coloff

      return all_objs

    def extract_call_from_names( func, names, name_func ):
      """ extract_calls_from_names:
      Here we turn name into function calls """

      all_calls = set()

      for name, astnode, isself in names:
        call = None

        # This is some instantiation I guess. TODO only support one layer
        if isself and len(name) == 1:
          try:
            call = getattr( s, name[0][0] )
          except AttributeError as e:
            s._tag_name_collect() # give full name to spawned object
            raise VarNotDeclaredError( call, name[0][0], func, astnode.lineno )

        # This is a function call without "s." prefix, check func list
        elif name[0][0] in name_func:
          call = name_func[ name[0][0] ]
          all_calls.add( call )

        if call is not None:
          try:
            astnode._funcs[ func ].add( call )
          except AttributeError:
            astnode._funcs = defaultdict(set)
            astnode._funcs[ func ].add( call )

      return all_calls

    """ elaborate_read_write_func """

    # Access cached data in this component

    cls = s.__class__
    try:
      name_rd, name_wr, name_fc = cls._name_rd, cls._name_wr, cls._name_fc
    except AttributeError: # This component doesn't have update block
      pass

    s._func_reads  = func_reads  = {}
    s._func_writes = func_writes = {}
    s._func_calls  = func_calls  = {}
    for name, func in s._name_func.iteritems():
      func_reads [ func ] = extract_obj_from_names( func, name_rd[ name ] )
      func_writes[ func ] = extract_obj_from_names( func, name_wr[ name ] )
      func_calls [ func ] = extract_call_from_names( func, name_fc[ name ], s._name_func )

    s._upblk_reads  = upblk_reads  = {}
    s._upblk_writes = upblk_writes = {}
    s._upblk_calls  = upblk_calls  = {}
    for name, blk in s._name_upblk.iteritems():
      upblk_reads [ blk ] = extract_obj_from_names( blk, name_rd[ name ] )
      upblk_writes[ blk ] = extract_obj_from_names( blk, name_wr[ name ] )
      upblk_calls [ blk ] = extract_call_from_names( blk, name_fc[ name ], s._name_func )

  # Override
  def _collect_vars( s, m ):
    super( ComponentLevel2, s )._collect_vars( m )

    if isinstance( m, ComponentLevel2 ):
      s._all_update_on_edge.update( m._update_on_edge )

      for k in m._RD_U_constraints:
        s._all_RD_U_constraints[k].extend( m._RD_U_constraints[k] )
      for k in m._WR_U_constraints:
        s._all_WR_U_constraints[k].extend( m._WR_U_constraints[k] )

      s._all_funcs.update( m._name_func.values() )

      # I assume different update blocks will always have different ids
      s._all_upblk_reads.update( m._upblk_reads )
      s._all_upblk_writes.update( m._upblk_writes )

      for blk, calls in m._upblk_calls.iteritems():
        s._all_upblk_calls[ blk ] = calls

        for call in calls:

          # Expand function calls. E.g. upA calls fx, fx calls fy and fz
          # This is invalid: fx calls fy but fy also calls fx
          # To detect this, we need to use dfs and see if the current node
          # has an edge to a previously marked ancestor

          def dfs( u, stk ):

            # Add all read/write of funcs to the outermost upblk
            s._all_upblk_reads [ blk ].update( m._func_reads[u] )
            s._all_upblk_writes[ blk ].update( m._func_writes[u] )

            for v in m._func_calls[ u ]:
              if v in caller: # v calls someone else there is a cycle
                raise InvalidFuncCallError( \
                  "In class {}\nThe full call hierarchy:\n - {}{}\nThese function calls form a cycle:\n {}\n{}".format(
                    type(v.hostobj).__name__,
                    "\n - ".join( [ "{} calls {}".format( caller[x][0].__name__, x.__name__ )
                                    for x in stk ] ),
                    "\n - {} calls {}".format( u.__name__, v.__name__ ),
                    "\n ".join( [ ">>> {} calls {}".format( caller[x][0].__name__, x.__name__)
                                    for x in stk[caller[v][1]+1: ] ] ),
                    " >>> {} calls {}".format( u.__name__, v.__name__ ) ) )

              caller[ v ] = ( u, len(stk) )
              stk.append( v )
              dfs( v, stk )
              del caller[ v ]
              stk.pop()

          # callee's id: (func, the caller's idx in stk)
          caller = { call: ( blk, 0 ) }
          stk    = [ call ] # for error message
          dfs( call, stk )

  def _check_upblk_writes( s ):

    write_upblks = defaultdict(set)
    for blk, writes in s._all_upblk_writes.iteritems():
      for wr in writes:
        write_upblks[ wr ].add( blk )

    for obj, wr_blks in write_upblks.iteritems():
      wr_blks = list(wr_blks)

      if len(wr_blks) > 1:
        raise MultiWriterError( \
        "Multiple update blocks write {}.\n - {}".format( repr(obj),
            "\n - ".join([ x.__name__+" at "+repr(x.hostobj) \
                           for x in wr_blks ]) ) )

      # See VarConstraintPass.py for full information
      # 1) WR A.b.b.b, A.b.b, A.b, A (detect 2-writer conflict)

      x = obj
      while x:
        if x is not obj and x in write_upblks:
          wrx_blks = list(write_upblks[x])

          if wrx_blks[0] != wr_blks[0]:
            raise MultiWriterError( \
            "Two-writer conflict in nested struct/slice. \n - {} (in {})\n - {} (in {})".format(
              repr(x), wrx_blks[0].__name__,
              repr(obj), wr_blks[0].__name__ ) )
        x = x._nested

      # 4) WR A.b[1:10], A.b[0:5], A.b[6] (detect 2-writer conflict)

      if obj._slice:
        for x in obj._nested._slices.values():
          # Recognize overlapped slices
          if x is not obj and _overlap( x._slice, obj._slice ) and x in write_upblks:
            wrx_blks = list(write_upblks[x])
            raise MultiWriterError( \
              "Two-writer conflict between sibling slices. \n - {} (in {})\n - {} (in {})".format(
                repr(x), wrx_blks[0].__name__,
                repr(obj), wr_blks[0].__name__ ) )

  def _check_port_in_upblk( s ):

    # Check read first
    for blk, reads in s._all_upblk_reads.iteritems():

      blk_hostobj = blk.hostobj

      for obj in reads:
        host = obj
        while not isinstance( host, ComponentLevel2 ):
          host = host._parent_obj # go to the component

        if   isinstance( obj, InVPort ):  pass
        elif isinstance( obj, OutVPort ): pass
        elif isinstance( obj, Wire ):
          if blk_hostobj != host:
            raise SignalTypeError("""[Type 1] Invalid read to Wire:

- Wire "{}" of {} (class {}) is read in update block
       "{}" of {} (class {}).

  Note: Please only read Wire "x.wire" in x's update block.
        (Or did you intend to declare it as an OutVPort?)""" \
          .format(  repr(obj), repr(host), type(host).__name__,
                    blk.__name__, repr(blk_hostobj), type(blk_hostobj).__name__ ) )

    # Then check write
    for blk, writes in s._all_upblk_writes.iteritems():

      blk_hostobj = blk.hostobj

      for obj in writes:
        host = obj
        while not isinstance( host, ComponentLevel2 ):
          host = host._parent_obj # go to the component

      # A continuous assignment is implied when a variable is connected to
      # an input port declaration. This makes assignments to a variable
      # declared as an input port illegal. -- IEEE

        if   isinstance( obj, InVPort ):
          if host._parent_obj != blk_hostobj:
            raise SignalTypeError("""[Type 2] Invalid write to an input port:

- InVPort "{}" of {} (class {}) is written in update block
          "{}" of {} (class {}).

  Note: Please only write to children's InVPort "x.y.in", not "x.in", in x's update block.""" \
          .format(  repr(obj), repr(host), type(host).__name__,
                    blk.__name__, repr(host), type(host).__name__ ) )

      # A continuous assignment is implied when a variable is connected to
      # the output port of an instance. This makes procedural or
      # continuous assignments to a variable connected to the output port
      # of an instance illegal. -- IEEE

        elif isinstance( obj, OutVPort ):
          if blk_hostobj != host:
            raise SignalTypeError("""[Type 3] Invalid write to output port:

- OutVPort \"{}\" of {} (class {}) is written in update block
           \"{}\" of {} (class {}).

  Note: Please only write to OutVPort "x.out", not "x.y.out", in x's update block.""" \
          .format(  repr(obj), repr(host), type(host).__name__,
                    blk.__name__, repr(blk_hostobj), type(blk_hostobj).__name__, ) )

      # The case of wire is special. We only allow Wire to be written in
      # the same object. One cannot write this from outside

        elif isinstance( obj, Wire ):
          if blk_hostobj != host:
            raise SignalTypeError("""[Type 4] Invalid write to Wire:

- Wire "{}" of {} (class {}) is written in update block
       "{}" of {} (class {}).

  Note: Please only write to Wire "x.wire" in x's update block.
        (Or did you intend to declare it as an InVPort?)""" \
          .format(  repr(obj), repr(host), type(host).__name__,
                    blk.__name__, repr(blk_hostobj), type(blk_hostobj).__name__ ) )

  #-----------------------------------------------------------------------
  # Construction-time APIs
  #-----------------------------------------------------------------------

  def func( s, func ): # @s.func is for those functions
    name = func.__name__
    if name in s._name_func or name in s._name_upblk:
      raise UpblkFuncSameNameError( name )

    s._name_func[ name ] = func
    func.hostobj = s

    s._cache_func_meta( func )
    return func

  # Override
  def update( s, blk ):
    super( ComponentLevel2, s ).update( blk )
    s._cache_func_meta( blk ) # add caching of src/ast
    return blk

  def update_on_edge( s, blk ):
    s._update_on_edge.add( blk )
    return s.update( blk )

  # Override
  def add_constraints( s, *args ): # add RD-U/WR-U constraints

    for (x0, x1) in args:
      if   isinstance( x0, U ) and isinstance( x1, U ): # U & U, same
        s._U_U_constraints.add( (x0.func, x1.func) )

      elif isinstance( x0, ValueConstraint ) and isinstance( x1, ValueConstraint ):
        raise InvalidConstraintError

      elif isinstance( x0, ValueConstraint ) or isinstance( x1, ValueConstraint ):
        sign = 1 # RD(x) < U is 1, RD(x) > U is -1
        if isinstance( x1, ValueConstraint ):
          sign = -1
          x0, x1 = x1, x0 # Make sure x0 is RD/WR(...) and x1 is U(...)

        if isinstance( x0, RD ):
          s._RD_U_constraints[ x0.var ].append( (sign, x1.func ) )
        else:
          s._WR_U_constraints[ x0.var ].append( (sign, x1.func ) )

  #-----------------------------------------------------------------------
  # elaborate
  #-----------------------------------------------------------------------

  # Override
  def elaborate( s ):
    s._declare_vars()

    s._tag_name_collect() # tag and collect first
    for obj in s._pymtl_objs:
      if isinstance( obj, ComponentLevel2 ):
        obj._elaborate_read_write_func()
      s._collect_vars( obj )
    s._tag_name_collect() # slicing will spawn extra objects

    s._check_upblk_writes()
    s._check_port_in_upblk()

  #-----------------------------------------------------------------------
  # Public APIs (only can be called after elaboration)
  #-----------------------------------------------------------------------

  def get_all_nets( s ):
    try:
      return s._all_nets
    except AttributeError:
      raise NotElaboratedError()
