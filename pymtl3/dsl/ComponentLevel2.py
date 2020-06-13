"""
========================================================================
ComponentLevel2.py
========================================================================
At level two we introduce implicit variable constraints.
By default we assume combinational semantics:
- upA reads Wire x while upB writes Wire x ==> upB = WR(x) < RD(x) = upA
When upA is marked as update_ff ==> for all upblks upX that
write/read variables in upA, upA < upX:
- upA = RD(x) < WR(x) = upB and upA = WR(x) < RD(x) = upB

Author : Shunning Jiang
Date   : Apr 16, 2018
"""
import ast
import gc
import inspect
import re
from collections import defaultdict

from pymtl3.datatypes import Bits, is_bitstruct_class

from . import AstHelper
from .ComponentLevel1 import ComponentLevel1
from .Connectable import Connectable, Const, InPort, Interface, OutPort, Signal, Wire
from .ConstraintTypes import RD, WR, U, ValueConstraint
from .errors import (
    InvalidConstraintError,
    InvalidFuncCallError,
    InvalidIndexError,
    InvalidPlaceholderError,
    MultiWriterError,
    NotElaboratedError,
    PyMTLDeprecationError,
    SignalTypeError,
    UpblkFuncSameNameError,
    UpdateBlockWriteError,
    UpdateFFBlockWriteError,
    UpdateFFNonTopLevelSignalError,
    VarNotDeclaredError,
    WriteNonSignalError,
)
from .NamedObject import NamedObject
from .Placeholder import Placeholder

compiled_re = re.compile('( *(@|def))')

def update_ff( blk ):
  NamedObject._elaborate_stack[-1]._update_ff( blk )
  return blk

class ComponentLevel2( ComponentLevel1 ):

  #-----------------------------------------------------------------------
  # Private methods
  #-----------------------------------------------------------------------

  def __new__( cls, *args, **kwargs ):
    inst = super().__new__( cls, *args, **kwargs )

    inst._dsl.update_ff = set()

    # constraint[var] = (sign, func)
    inst._dsl.RD_U_constraints = defaultdict(set)
    inst._dsl.WR_U_constraints = defaultdict(set)
    inst._dsl.name_func = {}

    return inst

  def _cache_func_meta( s, func, is_update_ff, given=None ):
    """ Convention: the source of a function/update block across different
    instances should be the same. You can construct different functions
    based on the condition, but please use different names. This not only
    keeps the caching valid, but also make the code more readable.

    According to the convention, we can cache the information of a
    function in the *class object* to avoid redundant parsing. """
    cls = s.__class__
    try:
      name_info = cls._name_info
      name_rd   = cls._name_rd
      name_wr   = cls._name_wr
      name_fc   = cls._name_fc
    except Exception:
      name_info = cls._name_info = {}
      name_rd   = cls._name_rd  = {}
      name_wr   = cls._name_wr  = {}
      name_fc   = cls._name_fc  = {}

    name = func.__name__

    # Always override lambda
    if given is not None:
      _src, _ast, _line, _file = given

      name_info[ name ] = ( True, _src, _line, _file, _ast )
      name_rd[ name ]   = _rd = []
      name_wr[ name ]   = _wr = []
      name_fc[ name ]   = _fc = []
      AstHelper.extract_reads_writes_calls( s, func, _ast, _rd, _wr, _fc )

    elif name not in name_info:
      _src, _line = inspect.getsourcelines( func )
      _src = "".join( _src )
      _ast = ast.parse( compiled_re.sub( r'\2', _src ) )

      name_info[ name ] = (False, _src, _line, inspect.getsourcefile( func ), _ast )
      name_rd[ name ]   = _rd   = []
      name_wr[ name ]   = _wr   = []
      name_fc[ name ]   = _fc   = []
      AstHelper.extract_reads_writes_calls( s, func, _ast, _rd, _wr, _fc )

  def _elaborate_read_write_func( s ):

    # We have parsed AST to extract every read/write variable name.
    # I refactor the process of materializing objects in this function
    # Pass in the func as well for error message

    def extract_obj_from_names( func, names, update_ff=False, is_write=False ):

      def expand_array_index( obj, name_depth, node_depth, idx_depth, idx ):
        """ Find s.x[0][*][2], if index is exhausted, jump back to lookup_variable """

        if idx_depth >= len(idx): # exhausted, go to next level of name
          lookup_variable( obj, name_depth+1, node_depth+1 )
          return

        current_idx = idx[ idx_depth ]

        if current_idx == "*": # special case, materialize all objects
          if isinstance( obj, NamedObject ): # Signal[*] is the signal itself
            objs.add( obj )
          else:
            for i, child in enumerate( obj ):
              expand_array_index( child, name_depth, node_depth, idx_depth+1, idx )

        # Here we try to find the value of free variables in the current
        # component scope.
        # tuple: [x] where x is a closure/global variable
        # slice: [x:y] where x and y are either normal integers or
        #        closure/global variable.
        else:
          if isinstance( current_idx, tuple ):
            is_closure, name = current_idx
            current_idx = _closure[ name ] if is_closure else _globals[ name ]
          elif isinstance( current_idx, slice ):
            start = current_idx.start
            if isinstance( start, tuple ):
              is_closure, name = start
              start = _closure[ name ] if is_closure else _globals[ name ]
            stop  = current_idx.stop
            if isinstance( stop, tuple ):
              is_closure, name = stop
              stop = _closure[ name ] if is_closure else _globals[ name ]
            current_idx = slice(start, stop)

          try:
            child = obj[ current_idx ]
          except TypeError: # cannot convert to integer
            raise VarNotDeclaredError( obj, current_idx, func, s, nodelist[node_depth].lineno )
          except IndexError:
            return
          except AssertionError:
            raise InvalidIndexError( obj, current_idx, func, s, nodelist[node_depth].lineno )

          expand_array_index( child, name_depth, node_depth, idx_depth+1, idx )

      def lookup_variable( obj, name_depth, node_depth ):
        """ Look up the object s.a.b.c in s. Jump to expand_array_index if c[] """
        if obj is None:
          return

        if name_depth >= len(obj_name): # exhausted
          if   isinstance( obj, NamedObject ):
            objs.add( obj )
          elif isinstance( obj, list ) and obj: # Exhaust all the elements in the high-d array
            Q = [ *obj ] # PEP 448 -- see https://stackoverflow.com/a/43220129/6470797
            while Q:
              m = Q.pop()
              if isinstance( m, NamedObject ):
                objs.add( m )
              elif isinstance( m, list ):
                Q.extend( m )
          return

        # still have names
        field, idx = obj_name[ name_depth ]
        try:
          child = getattr( obj, field )
        except AttributeError as e:
          print(e)
          raise VarNotDeclaredError( obj, field, func, s, nodelist[node_depth].lineno )

        if not idx: lookup_variable   ( child, name_depth+1, node_depth+1 )
        else:       expand_array_index( child, name_depth,   node_depth+1, 0, idx )

      """ extract_obj_from_names:
      Here we enumerate names and use the above functions to turn names
      into objects """

      _globals = func.__globals__

      _closure = {}
      for i, var in enumerate( func.__code__.co_freevars ):
        try:  _closure[ var ] = func.__closure__[i].cell_contents
        except ValueError: pass

      all_objs = set()

      # Now we turn names into actual objects
      for obj_name, nodelist, op in names:
        if obj_name[0][0] == "s":
          objs = set()
          lookup_variable( s, 1, 1 )

          if not is_write or not objs:
            all_objs |= objs
            continue

          # Now we perform write checks

          for obj in objs: # The objects in objs are all NamedObject
            if not isinstance( obj, Signal ):
              raise WriteNonSignalError( s, func, nodelist[0].lineno, obj )
            all_objs.add( obj )

          # Check all assignments in update_ff and update
          # - <<= in update_ff
          # - @= in update
          # - = in update/update_ff

          if update_ff:
            # - signals can only be at LHS of <<=
            #   * only top level signals
            # - signals cannot be at LHS of @= or =

            if op is None:
              raise UpdateFFBlockWriteError( s, func, '=', nodelist[0].lineno,
                "Fix the '=' assignment with '<<='")
            elif op == 'for':
              raise UpdateFFBlockWriteError( s, func, op, nodelist[0].lineno,
                "Fix the loop variable in for-loop assignment")
            elif not isinstance( op, ast.LShift ):
              if isinstance( op, ast.MatMult ):
                raise UpdateFFBlockWriteError( s, func, '@=', nodelist[0].lineno,
                  "Fix the '@=' assignment with '<<='")

              raise UpdateFFBlockWriteError( s, func, op+'=', nodelist[0].lineno,
                "Fix the signal assignment with '<<='")


            for x in objs:
              if not x.is_top_level_signal():
                raise UpdateFFNonTopLevelSignalError( s, func, nodelist[0].lineno )

              x._dsl.needs_double_buffer = True

          else: # update
            # - signals can only be at LHS of @=
            # - signals cannot be at LHS of <<= or =
            if op is None:
              raise UpdateBlockWriteError( s, func, '=', nodelist[0].lineno,
                "Fix the '=' assignment with '@='")
            elif op == 'for':
              raise UpdateBlockWriteError( s, func, op, nodelist[0].lineno,
                "Fix the loop variable in for-loop assignment")
            elif not isinstance( op, ast.MatMult ):
              if isinstance( op, ast.LShift ):
                raise UpdateBlockWriteError( s, func, '<<=', nodelist[0].lineno,
                  "Fix the '<<=' assignment with '@='")
              raise UpdateBlockWriteError( s, func, op+'=', nodelist[0].lineno,
                "Fix the signal assignment with '@='")

        # This is a function call without "s." prefix, check func list
        elif obj_name[0][0] in s._dsl.name_func:
          call = s._dsl.name_func[ obj_name[0][0] ]
          all_objs.add( call )

      return all_objs

    """ elaborate_read_write_func """

    # Access cached data in this component

    cls = s.__class__
    try:
      name_rd, name_wr, name_fc = cls._name_rd, cls._name_wr, cls._name_fc
    except AttributeError: # This component doesn't have update block
      pass

    # what object each astnode corresponds to. You can't have two update
    # blocks in one component that have the same ast.
    s._dsl.func_reads  = {}
    s._dsl.func_writes = {}
    s._dsl.func_calls  = {}
    for name, func in s._dsl.name_func.items():
      s._dsl.func_reads [ func ] = extract_obj_from_names( func, name_rd[ name ] )
      s._dsl.func_writes[ func ] = extract_obj_from_names( func, name_wr[ name ] )
      s._dsl.func_calls [ func ] = extract_obj_from_names( func, name_fc[ name ] )

    s._dsl.upblk_reads  = {}
    s._dsl.upblk_writes = {}
    s._dsl.upblk_calls  = {}
    for name, blk in s._dsl.name_upblk.items():
      s._dsl.upblk_reads [ blk ] = extract_obj_from_names( blk, name_rd[ name ] )
      s._dsl.upblk_writes[ blk ] = extract_obj_from_names( blk, name_wr[ name ],
                                    update_ff = blk in s._dsl.update_ff, is_write=True )
      s._dsl.upblk_calls [ blk ] = extract_obj_from_names( blk, name_fc[ name ] )

  # Override
  def _collect_vars( s, m ):
    super()._collect_vars( m )

    if isinstance( m, ComponentLevel2 ):
      s._dsl.all_update_ff |= m._dsl.update_ff

      for k, k_cons in m._dsl.RD_U_constraints.items():
        s._dsl.all_RD_U_constraints[k] |= k_cons

      for k, k_cons in m._dsl.WR_U_constraints.items():
        s._dsl.all_WR_U_constraints[k] |= k_cons

      # I assume different update blocks will always have different ids
      s._dsl.all_upblk_reads.update( m._dsl.upblk_reads )
      s._dsl.all_upblk_writes.update( m._dsl.upblk_writes )

      for blk, calls in m._dsl.upblk_calls.items():
        s._dsl.all_upblk_calls[ blk ] = calls

        for call in calls:

          # Expand function calls. E.g. upA calls fx, fx calls fy and fz
          # This is invalid: fx calls fy but fy also calls fx
          # To detect this, we need to use dfs and see if the current node
          # has an edge to a previously marked ancestor

          def dfs( u, stk ):
            if u not in m._dsl.func_reads:
              return

            # Add all read/write of funcs to the outermost upblk
            s._dsl.all_upblk_reads [ blk ] |= m._dsl.func_reads[u]
            s._dsl.all_upblk_writes[ blk ] |= m._dsl.func_writes[u]

            for v in m._dsl.func_calls[ u ]:
              if v in caller: # v calls someone else there is a cycle
                raise InvalidFuncCallError( \
                  "In class {}\nThe full call hierarchy:\n - {}{}\nThese function calls form a cycle:\n {}\n{}".format(
                    type(m).__name__, # function's hostobj must be m
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

  def _uncollect_vars( s, m ):
    super()._uncollect_vars( m )

    if isinstance( m, ComponentLevel2 ):
      s._dsl.all_update_ff -= m._dsl.update_ff

      for k in m._dsl.RD_U_constraints:
        s._dsl.all_RD_U_constraints[k] -= m._dsl.RD_U_constraints[k]
      for k in m._dsl.WR_U_constraints:
        s._dsl.all_WR_U_constraints[k] -= m._dsl.RD_U_constraints[k]

      for k in m._dsl.upblks:
        del s._dsl.all_upblk_reads[k]
        del s._dsl.all_upblk_writes[k]
        del s._dsl.all_upblk_calls[k]

  def _check_upblk_writes( s ):

    write_upblks = defaultdict(set)
    for blk, writes in s._dsl.all_upblk_writes.items():
      for wr in writes:
        write_upblks[ wr ].add( blk )

    for obj, wr_blks in write_upblks.items():
      wr_blks = list(wr_blks)

      if len(wr_blks) > 1:
        raise MultiWriterError( \
        "Multiple update blocks write {}.\n - {}".format( repr(obj),
            "\n - ".join([ x.__name__+" at "+repr(s._dsl.all_upblk_hostobj[x]) \
                           for x in wr_blks ]) ) )

      # See VarConstraintPass.py for full information
      # 1) WR A.b.b.b, A.b.b, A.b, A (detect 2-writer conflict)

      x = obj
      while x.is_signal():
        if x is not obj and x in write_upblks:
          wrx_blks = list(write_upblks[x])

          if wrx_blks[0] != wr_blks[0]:
            raise MultiWriterError( \
            "Two-writer conflict in nested struct/slice. \n - {} (in {})\n - {} (in {})".format(
              repr(x), wrx_blks[0].__name__,
              repr(obj), wr_blks[0].__name__ ) )
        x = x.get_parent_object()

      # 4) WR A.b[1:10], A.b[0:5], A.b[6] (detect 2-writer conflict)

      for x in obj.get_sibling_slices():
        # Recognize overlapped slices
        if x.slice_overlap( obj ) and x in write_upblks:
          wrx_blks = list(write_upblks[x])
          raise MultiWriterError( \
            "Two-writer conflict between sibling slices. \n - {} (in {})\n - {} (in {})".format(
              repr(x), wrx_blks[0].__name__,
              repr(obj), wr_blks[0].__name__ ) )

  def _check_port_in_upblk( s ):

    # Check read first
    for blk, reads in s._dsl.all_upblk_reads.items():

      blk_hostobj = s._dsl.all_upblk_hostobj[ blk ]

      for obj in reads:
        host = obj
        while not isinstance( host, ComponentLevel2 ):
          host = host.get_parent_object() # go to the component

        if   isinstance( obj, (InPort, OutPort) ):  pass
        elif isinstance( obj, Wire ):
          if blk_hostobj != host:
            raise SignalTypeError("""[Type 1] Invalid read to Wire:

- Wire "{}" of {} (class {}) is read in update block
       "{}" of {} (class {}).

  Note: Please only read Wire "x.wire" in x's update block.
        (Or did you intend to declare it as an OutPort?)""" \
          .format(  repr(obj), repr(host), type(host).__name__,
                    blk.__name__, repr(blk_hostobj), type(blk_hostobj).__name__ ) )

    # Then check write
    for blk, writes in s._dsl.all_upblk_writes.items():

      blk_hostobj = s._dsl.all_upblk_hostobj[ blk ]

      for obj in writes:
        host = obj
        while not isinstance( host, ComponentLevel2 ):
          host = host.get_parent_object() # go to the component

      # A continuous assignment is implied when a variable is connected to
      # an input port declaration. This makes assignments to a variable
      # declared as an input port illegal. -- IEEE

        if   isinstance( obj, InPort ):
          if host.get_parent_object() != blk_hostobj:
            raise SignalTypeError("""[Type 2] Invalid write to an input port:

- InPort "{}" of {} (class {}) is written in update block
          "{}" of {} (class {}).

  Note: Please only write to children's InPort "x.y.in", not "x.in", in x's update block.""" \
          .format(  repr(obj), repr(host), type(host).__name__,
                    blk.__name__, repr(host), type(host).__name__ ) )

      # A continuous assignment is implied when a variable is connected to
      # the output port of an instance. This makes procedural or
      # continuous assignments to a variable connected to the output port
      # of an instance illegal. -- IEEE

        elif isinstance( obj, OutPort ):
          if blk_hostobj != host:
            raise SignalTypeError("""[Type 3] Invalid write to output port:

- OutPort \"{}\" of {} (class {}) is written in update block
           \"{}\" of {} (class {}).

  Note: Please only write to OutPort "x.out", not "x.y.out", in x's update block.""" \
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
        (Or did you intend to declare it as an InPort?)""" \
          .format(  repr(obj), repr(host), type(host).__name__,
                    blk.__name__, repr(blk_hostobj), type(blk_hostobj).__name__ ) )

  # TODO rename
  def _check_valid_dsl_code( s ):
    s._check_upblk_writes()
    s._check_port_in_upblk()

  #-----------------------------------------------------------------------
  # Construction-time APIs
  #-----------------------------------------------------------------------

  def func( s, func ): # @s.func is for those functions
    if isinstance( s, Placeholder ):
      raise InvalidPlaceholderError( "Cannot define function {}"
              "in a placeholder component.".format( func.__name__ ) )
    name = func.__name__
    if name in s._dsl.name_func or name in s._dsl.name_upblk:
      raise UpblkFuncSameNameError( name )

    s._dsl.name_func[ name ] = func
    s._cache_func_meta( func, is_update_ff=False )
    return func

  # Override
  def _update( s, blk ):
    super()._update( blk )

    s._cache_func_meta( blk, is_update_ff=False ) # add caching of src/ast

  def update_on_edge( s, blk ):
    raise PyMTLDeprecationError("\ns.update_on_edge decorator has been deprecated! "
                                "\n- Please use @update_ff instead.")

  def _update_ff( s, blk ):
    super()._update( blk )

    s._dsl.update_ff.add( blk )
    s._cache_func_meta( blk, is_update_ff=True ) # add caching of src/ast

  # Override
  def add_constraints( s, *args ): # add RD-U/WR-U constraints
    if isinstance( s, Placeholder ):
      raise InvalidPlaceholderError( "Cannot define constraints "
              "in a placeholder component." )

    for (x0, x1, is_equal) in args:

      if   isinstance( x0, U ) and isinstance( x1, U ): # U & U, same
        assert is_equal == False
        assert (x0.func, x1.func) not in s._dsl.U_U_constraints, \
          "Duplicated constraint"
        s._dsl.U_U_constraints.add( (x0.func, x1.func) )

      elif isinstance( x0, ValueConstraint ) and isinstance( x1, ValueConstraint ):
        raise InvalidConstraintError

      elif isinstance( x0, ValueConstraint ) or isinstance( x1, ValueConstraint ):
        assert is_equal == False
        sign = 1 # RD(x) < U is 1, RD(x) > U is -1
        if isinstance( x1, ValueConstraint ):
          sign = -1
          x0, x1 = x1, x0 # Make sure x0 is RD/WR(...) and x1 is U(...)

        if isinstance( x0, RD ):
          assert (sign, x1.func) not in s._dsl.RD_U_constraints[ x0.var ], \
            "Duplicated constraint"
          s._dsl.RD_U_constraints[ x0.var ].add( (sign, x1.func) )
        else:
          assert (sign, x1.func ) not in s._dsl.WR_U_constraints[ x0.var ], \
            "Duplicated constraint"
          s._dsl.WR_U_constraints[ x0.var ].add( (sign, x1.func) )

  #-----------------------------------------------------------------------
  # elaborate
  #-----------------------------------------------------------------------

  # Override
  def _elaborate_declare_vars( s ):
    super()._elaborate_declare_vars()

    s._dsl.all_update_ff = set()

    s._dsl.all_RD_U_constraints = defaultdict(set)
    s._dsl.all_WR_U_constraints = defaultdict(set)

    # We don't collect func's metadata
    # because every func is local to the component
    s._dsl.all_upblk_reads  = {}
    s._dsl.all_upblk_writes = {}
    s._dsl.all_upblk_calls  = {}

    # Like all_components in level1, although this all_signals is a subset
    # of all_named_objects in NamedObject class, I still maintain it here
    # because we want to avoid redundant isinstance check. I'm going to pay the
    # extra cost of removing from both all_named_objects and all_signals
    # when I delete a signal
    s._dsl.all_signals = set()

  # Override
  def _elaborate_collect_all_vars( s ):
    for c in s._dsl.all_named_objects:
      if isinstance( c, Signal ):
        s._dsl.all_signals.add( c )
      elif isinstance( c, ComponentLevel1 ):
        s._dsl.all_components.add( c )
        s._collect_vars( c )

  # Override
  def elaborate( s ):
    # Don't directly use the base class elaborate anymore
    s._elaborate_construct()

    # First elaborate all functions to spawn more named objects
    for c in s._collect_all_single( lambda s: isinstance( s, ComponentLevel2 ) ):
      c._elaborate_read_write_func()

    s._elaborate_collect_all_named_objects()

    s._elaborate_declare_vars()
    s._elaborate_collect_all_vars()

    s._check_valid_dsl_code()

  #-----------------------------------------------------------------------
  # Post-elaborate public APIs (can only be called after elaboration)
  #-----------------------------------------------------------------------
  # We have moved these implementations to Component.py because the
  # outside world should only use Component.py
