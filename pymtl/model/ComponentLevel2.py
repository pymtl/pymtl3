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

  def __new__( cls, *args, **kwargs ):
    inst = super(ComponentLevel2, cls).__new__( cls, *args, **kwargs )

    inst._update_on_edge   = set()
    # constraint[id(var)] = (sign, id(func))
    inst._RD_U_constraints = defaultdict(list)
    inst._WR_U_constraints = defaultdict(list)
    inst._name_func = {}
    inst._id_func   = {}

    return inst

  # Override, add RD/WR constraints
  def add_constraints( s, *args ):

    for (x0, x1) in args:
      if   isinstance( x0, U ) and isinstance( x1, U ): # U & U, same
        s._U_U_constraints.add( (id(x0.func), id(x1.func)) )

      elif isinstance( x0, ValueConstraint ) and isinstance( x1, ValueConstraint ):
        raise InvalidConstraintError

      elif isinstance( x0, ValueConstraint ) or isinstance( x1, ValueConstraint ):
        sign = 1 # RD(x) < U is 1, RD(x) > U is -1
        if isinstance( x1, ValueConstraint ):
          sign = -1
          x0, x1 = x1, x0 # Make sure x0 is RD/WR(...) and x1 is U(...)

        if isinstance( x0, RD ):
          s._RD_U_constraints[ id(x0.var) ].append( (sign, id(x1.func) ) )
        else:
          s._WR_U_constraints[ id(x0.var) ].append( (sign, id(x1.func) ) )

  # Override, add caching for rd/wr/call
  def _cache_func_meta( s, func ):
    super( ComponentLevel2, s )._cache_func_meta( func ) # func.ast, func.src

    cls  = type(s)
    if not hasattr( cls, "_name_rd" ):
      cls._name_rd = {}
      cls._name_wr = {}
      cls._name_fc = {}
      cls._name_br = {}

    name = func.__name__
    if name not in cls._name_rd:
      cls._name_rd[ name ] = rd = []
      cls._name_wr[ name ] = wr = []
      cls._name_fc[ name ] = fc = []
      AstHelper.extract_read_write( func, rd, wr )
      AstHelper.extract_func_calls( func, fc )

      cls._name_br[ name ] = AstHelper.count_branches( func )

    func.rd = cls._name_rd[ name ]
    func.wr = cls._name_wr[ name ]
    func.fc = cls._name_fc[ name ]
    func.br = cls._name_br[ name ]

  # @s.func is for those functions
  def func( s, func ):
    name = func.__name__
    if name in s._name_func or name in s._name_upblk:
      raise UpblkFuncSameNameError( name )

    s._cache_func_meta( func )

    func.hostobj = s
    s._name_func[ name ] = s._id_func[ id(func) ] = func
    return func

  # Override
  def update( s, blk ):
    name = blk.__name__
    if name in s._name_func:
      raise UpblkFuncSameNameError( blk.__name__ )

    super( ComponentLevel2, s ).update( blk )
    return blk

  def update_on_edge( s, blk ):
    s._update_on_edge.add( id(blk) )
    return s.update( blk )

  # Override
  def elaborate( s ):
    s._declare_vars()

    s._tag_name_collect() # tag and collect first
    for obj in s._id_obj.values():
      if isinstance( obj, ComponentLevel2 ):
        obj._elaborate_read_write_func()
      s._collect_vars( obj )
    s._tag_name_collect() # slicing will spawn extra objects

    s._check_upblk_writes()
    s._check_port_in_upblk()

    s._process_constraints()

  # Override
  def _declare_vars( s ):
    super( ComponentLevel2, s )._declare_vars()

    s._all_id_func = {}
    s._all_update_on_edge   = set()

    s._all_RD_U_constraints = defaultdict(list)
    s._all_WR_U_constraints = defaultdict(list)

    s._all_read_upblks  = defaultdict(set)
    s._all_write_upblks = defaultdict(set)

    s._all_meta  = {
      "reads" : defaultdict(list),
      "writes": defaultdict(list),
      "calls" : defaultdict(list),
      "br"    : defaultdict(int),
    }

  def _elaborate_read_write_func( s ):

    s._id_meta  = {
      "reads" : defaultdict(list),
      "writes": defaultdict(list),
      "calls" : defaultdict(list),
    }

    # We have parsed AST to extract every read/write variable name.
    # I refactor the process of materializing objects in this function

    def extract_obj_from_names( func, names ):

      def expand_array_index( obj, name_depth, name, idx_depth, idx, obj_list ):
        """ Find s.x[0][*][2], if index is exhausted, jump back to lookup_var """

        if idx_depth >= len(idx):
          lookup_var( obj, name_depth+1, name, obj_list )
          return

        if idx[ idx_depth ] == "*": # special case, materialize all objects
          if isinstance( obj, Signal ): # Signal[*] is the signal itself
            add_all( obj, obj_list )
            return

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
            return

      def add_all( obj, obj_list ):
        """ Already found, but it is an array of objects, s.x = [ [ A() for _ in xrange(2) ] for _ in xrange(3) ],
        so recursively uncover all signals. """
        if   isinstance( obj, Signal ):
          obj_list.append( obj )
        elif isinstance( obj, list ): # SORRY
          for i, o in enumerate( obj ):
            add_all( o, obj_list )

      def lookup_var( obj, depth, name, obj_list ):
        """ Look up the object s.a.b.c in s. Jump to expand_array_index if c[] """
        if depth >= len(name):
          if not callable(obj): # exclude function calls
            add_all( obj, obj_list ) # if this object is a list/array again...
          return

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

      all_objs = []

      for name, astnode in names:
        objs = []
        try:
          lookup_var( s, 0, name, objs )
        except VarNotDeclaredError as e:
          s._tag_name_collect() # give full name to spawned object
          raise VarNotDeclaredError( e.obj, e.field, func, astnode.lineno )

        all_objs.extend( objs )

        # Annotate astnode with actual objects. However, since I only
        # parse AST of an upblk/function once to avoid duplicated parsing,
        # I have to fold information across difference instances of the
        # same class into the unique AST. Thus I keep {blk/funcid:objs}
        # dict in each AST node to differentiate between different upblks.

        if not hasattr( astnode, "_objs" ):
          astnode._objs = defaultdict(set)
        astnode._objs[ id(func) ].update( objs )

        # TODO Attach astnode to object for error message lineno/coloff

      return all_objs

    """ elaborate_read_write_func """

    # First resolve all funcs' read/write and calling other functions
    # This is because function won't call update blocks.
    # Since func/upblk metadata is differentiated by id in the same array
    # we put them together

    func_upblks = s._id_func.copy()

    for x in [ s._id_func, s._id_upblk ]:
      for id_, func in x.iteritems():

        s._id_meta['reads'][ id_ ] = { id(o): o \
          for o in extract_obj_from_names( func, func.rd ) }.values()

        s._id_meta['writes'][ id_ ] = { id(o): o \
          for o in extract_obj_from_names( func, func.wr ) }.values()

        all_calls = []
        for name, astnode, isself in func.fc:

          # This is some instantiation I guess
          # TODO now only support one layer

          if isself and len(name) == 1:
            try:
              call = getattr( s, name[0][0] )
            except AttributeError as e:
              s._tag_name_collect() # give full name to spawned object
              raise VarNotDeclaredError( call, name[0][0], func, astnode.lineno )

            if not hasattr( astnode, "_funcs" ):
              astnode._funcs = defaultdict(set)
            astnode._funcs[ id_ ].add( call )

          # This is a function call without "s." prefix, check func list

          elif name[0][0] in s._name_func:
            call = s._name_func[ name[0][0] ]

            if not hasattr( astnode, "_funcs" ):
              astnode._funcs = defaultdict(set)
            astnode._funcs[ id_ ].add( call )

            all_calls.append( call )

        s._id_meta['calls'][ id_ ] = { id(o): o for o in all_calls }.values()

  # Override
  def _collect_vars( s, m ):
    super( ComponentLevel2, s )._collect_vars( m )

    if isinstance( m, ComponentLevel2 ):
      s._all_update_on_edge.update( m._update_on_edge )

      for k in m._RD_U_constraints:
        s._all_RD_U_constraints[k].extend( m._RD_U_constraints[k] )
      for k in m._WR_U_constraints:
        s._all_WR_U_constraints[k].extend( m._WR_U_constraints[k] )

      s._all_id_func.update( m._id_func )

      for id_, reads in m._id_meta['reads'].iteritems():
        s._all_meta['reads'][ id_ ].extend( reads )

        if id_ not in m._id_upblk: continue
        for read in reads:
          s._all_read_upblks[ id(read) ].add( id_ )

      for id_, writes in m._id_meta['writes'].iteritems():
        s._all_meta['writes'][ id_ ].extend( writes )

        if id_ not in m._id_upblk: continue
        for write in writes:
          s._all_write_upblks[ id(write) ].add( id_ )

      # Summarize the branchiness as well
      for id_, upblk in m._id_upblk.iteritems():
        s._all_meta['br'][ id_ ] = upblk.br

      for id_, calls in m._id_meta['calls'].iteritems():
        s._all_meta['calls'][ id_ ].extend( calls )

        if id_ not in m._id_upblk:  continue
        for call in calls:

          # Expand function calls. E.g. upA calls fx, fx calls fy and fz
          # This is invalid: fx calls fy but fy also calls fx
          # To detect this, we need to use dfs and see if the current node
          # has an edge to a previously marked ancestor

          def dfs( u, stk ):

            # Add all read/write of funcs to the outermost upblk
            for read in m._id_meta['reads'][ id(u) ]:
              s._all_meta['reads'][ id_ ].append( read )
              s._all_read_upblks[ id(read) ].add( id_ )

            for write in m._id_meta['writes'][ id(u) ]:
              s._all_meta['writes'][ id_ ].append( write )
              s._all_write_upblks[ id(write) ].add( id_ )

            # add the branch count in the function to the upblk
            s._all_meta['br'][ id_ ] += m._id_func[ id(u) ].br

            for v in m._id_meta['calls'][ id(u) ]:
              if id(v) in caller: # v calls someone else there is a cycle
                raise InvalidFuncCallError( \
                  "In class {}\nThe full call hierarchy:\n - {}{}\nThese function calls form a cycle:\n {}\n{}".format(
                    type(v.hostobj).__name__,
                    "\n - ".join( [ "{} calls {}".format( caller[id(x)][0].__name__, x.__name__ )
                                    for x in stk ] ),
                    "\n - {} calls {}".format( u.__name__, v.__name__ ),
                    "\n ".join( [ ">>> {} calls {}".format( caller[id(x)][0].__name__, x.__name__)
                                    for x in stk[caller[id(v)][1]+1: ] ] ),
                    " >>> {} calls {}".format( u.__name__, v.__name__ ) ) )

              caller[ id(v) ] = ( u, len(stk) )
              stk.append( v )
              dfs( v, stk )
              del caller[ id(v) ]
              stk.pop()

          # callee's id: (func, the caller's idx in stk)
          caller = { id(call): ( m._id_upblk[ id_ ], 0 ) }
          stk    = [ call ] # for error message
          dfs( call, stk )

  def _process_constraints( s ):

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

    read_upblks  = s._all_read_upblks
    write_upblks = s._all_write_upblks

    for typ in [ 'rd', 'wr' ]: # deduplicate code
      if typ == 'rd':
        constraints = s._all_RD_U_constraints
        equal_blks  = read_upblks
      else:
        constraints = s._all_WR_U_constraints
        equal_blks  = write_upblks

      # enumerate variable objects
      for obj_id, constrained_blks in constraints.iteritems():
        obj = s._id_obj[ obj_id ]

        # enumerate upblks that has a constraint with x
        for (sign, co_blk) in constrained_blks:

          for eq_blk in equal_blks[ obj_id ]: # blocks that are U == RD(x)
            if co_blk != eq_blk:
              if sign == 1: # RD/WR(x) < U is 1, RD/WR(x) > U is -1
                # eq_blk == RD/WR(x) < co_blk
                s._all_expl_constraints.add( (eq_blk, co_blk) )
              else:
                # co_blk < RD/WR(x) == eq_blk
                s._all_expl_constraints.add( (co_blk, eq_blk) )

    #---------------------------------------------------------------------
    # Implicit constraint
    #---------------------------------------------------------------------
    # Synthesize total constraints between two upblks that read/write to
    # the "same variable" (we also handle the read/write of a recursively
    # nested field/slice)
    #
    # Implicitly, WR(x) < RD(x), so when U1 writes X and U2 reads x
    # - U1 == WR(x) & U2 == RD(x) --> U1 == WR(x) < RD(x) == U2

    s._all_impl_constraints = set()

    # Collect all objs that write the variable whose id is "read"
    # 1) RD A.b.b     - WR A.b.b, A.b, A
    # 2) RD A.b[1:10] - WR A.b[1:10], A.b, A
    # 3) RD A.b[1:10] - WR A.b[0:5], A.b[6], A.b[8:11]

    for rd_id, rd_blks in read_upblks.iteritems():
      obj     = s._id_obj[ rd_id ]
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
              if rd_blk in s._all_update_on_edge:
                s._all_impl_constraints.add( (rd_blk, wr_blk) ) # rd < wr
              else:
                s._all_impl_constraints.add( (wr_blk, rd_blk) ) # wr < rd default

    # Collect all objs that read the variable whose id is "write"
    # 1) WR A.b.b.b, A.b.b, A.b, A (detect 2-writer conflict)
    # 2) WR A.b.b.b   - RD A.b.b, A.b, A
    # 3) WR A.b[1:10] - RD A.b[1:10], A,b, A
    # 4) WR A.b[1:10], A.b[0:5], A.b[6] (detect 2-writer conflict)
    # "WR A.b[1:10] - RD A.b[0:5], A.b[6], A.b[8:11]" has been discovered

    for wr_id, wr_blks in write_upblks.iteritems():
      obj     = s._id_obj[ wr_id ]
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
              if rd_blk in s._all_update_on_edge:
                s._all_impl_constraints.add( (rd_blk, wr_blk) ) # rd < wr
              else:
                s._all_impl_constraints.add( (wr_blk, rd_blk) ) # wr < rd default

    s._all_constraints = s._all_expl_constraints.copy()

    for (x, y) in s._all_impl_constraints:
      if (y, x) not in s._all_expl_constraints: # no conflicting expl
        s._all_constraints.add( (x, y) )

  def _check_upblk_writes( s ):
    write_upblks = s._all_write_upblks

    for wr_id, wr_blks in write_upblks.iteritems():
      wr_blks = list(wr_blks)
      obj = s._id_obj[ wr_id ]

      if len(wr_blks) > 1:
        raise MultiWriterError( \
        "Multiple update blocks write {}.\n - {}".format( repr(obj),
            "\n - ".join([ s._all_id_upblk[x].__name__+" at "+repr(s._all_id_upblk[x].hostobj) \
                           for x in wr_blks ]) ) )

      # See VarConstraintPass.py for full information
      # 1) WR A.b.b.b, A.b.b, A.b, A (detect 2-writer conflict)

      x = obj
      while x:
        if id(x) != wr_id and id(x) in write_upblks:
          wrx_blks = list(write_upblks[id(x)])

          if wrx_blks[0] != wr_blks[0]:
            raise MultiWriterError( \
            "Two-writer conflict in nested struct/slice. \n - {} (in {})\n - {} (in {})".format(
              repr(x), s._all_id_upblk[wrx_blks[0]].__name__,
              repr(obj), s._all_id_upblk[wr_blks[0]].__name__ ) )
        x = x._nested

      # 4) WR A.b[1:10], A.b[0:5], A.b[6] (detect 2-writer conflict)

      if obj._slice:
        for x in obj._nested._slices.values():
          # Recognize overlapped slices
          if id(x) != wr_id and _overlap( x._slice, obj._slice ) and id(x) in write_upblks:
            wrx_blks = list(write_upblks[id(x)])
            raise MultiWriterError( \
              "Two-writer conflict between sibling slices. \n - {} (in {})\n - {} (in {})".format(
                repr(x), s._all_id_upblk[wrx_blks[0]].__name__,
                repr(obj), s._all_id_upblk[wr_blks[0]].__name__ ) )

  def _check_port_in_upblk( s ):

    # Check read first
    for rd, blks in s._all_read_upblks.iteritems():
      obj = s._id_obj[ rd ]

      host = obj
      while not isinstance( host, ComponentLevel2 ):
        host = host._parent # go to the component

      if   isinstance( obj, InVPort ):  pass
      elif isinstance( obj, OutVPort ): pass
      elif isinstance( obj, Wire ):
        for blkid in blks:
          blk = s._all_id_upblk[ blkid ]

          if blk.hostobj != host:
            raise SignalTypeError("""[Type 1] Invalid read to Wire:

- Wire "{}" of {} (class {}) is read in update block
       "{}" of {} (class {}).

  Note: Please only read Wire "x.wire" in x's update block.
        (Or did you intend to declare it as an OutVPort?)""" \
          .format(  repr(obj), repr(host), type(host).__name__,
                    blk.__name__, repr(blk.hostobj), type(blk.hostobj).__name__ ) )

    # Then check write

    for wr, blks in s._all_write_upblks.iteritems():
      obj = s._id_obj[ wr ]

      host = obj
      while not isinstance( host, ComponentLevel2 ):
        host = host._parent # go to the component

      # A continuous assignment is implied when a variable is connected to
      # an input port declaration. This makes assignments to a variable
      # declared as an input port illegal. -- IEEE

      if   isinstance( obj, InVPort ):
        for blkid in blks:
          blk = s._all_id_upblk[ blkid ]

          if host._parent != blk.hostobj:
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
        for blkid in blks:
          blk = s._all_id_upblk[ blkid ]

          if blk.hostobj != host:
            raise SignalTypeError("""[Type 3] Invalid write to output port:

- OutVPort \"{}\" of {} (class {}) is written in update block
           \"{}\" of {} (class {}).

  Note: Please only write to OutVPort "x.out", not "x.y.out", in x's update block.""" \
          .format(  repr(obj), repr(host), type(host).__name__,
                    blk.__name__, repr(blk.hostobj), type(blk.hostobj).__name__, ) )

      # The case of wire is special. We only allow Wire to be written in
      # the same object. One cannot write this from outside

      elif isinstance( obj, Wire ):
        for blkid in blks:
          blk = s._all_id_upblk[ blkid ]

          if blk.hostobj != host:
            raise SignalTypeError("""[Type 4] Invalid write to Wire:

- Wire "{}" of {} (class {}) is written in update block
       "{}" of {} (class {}).

  Note: Please only write to Wire "x.wire" in x's update block.
        (Or did you intend to declare it as an InVPort?)""" \
          .format(  repr(obj), repr(host), type(host).__name__,
                    blk.__name__, repr(blk.hostobj), type(blk.hostobj).__name__ ) )
