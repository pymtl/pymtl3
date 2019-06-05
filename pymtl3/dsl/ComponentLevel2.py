"""
========================================================================
ComponentLevel2.py
========================================================================
At level two we introduce implicit variable constraints.
By default we assume combinational semantics:
- upA reads Wire x while upB writes Wire x ==> upB = WR(x) < RD(x) = upA
When upA is marked as update_on_edge ==> for all upblks upX that
write/read variables in upA, upA < upX:
- upA = RD(x) < WR(x) = upB and upA = WR(x) < RD(x) = upB

Author : Shunning Jiang
Date   : Apr 16, 2018
"""
from __future__ import absolute_import, division, print_function

import ast
import gc
import inspect
import re
from collections import defaultdict

from . import AstHelper
from .ComponentLevel1 import ComponentLevel1
from .Connectable import Connectable, Const, InPort, Interface, OutPort, Signal, Wire
from .ConstraintTypes import RD, WR, U, ValueConstraint
from .errors import (
    InvalidConstraintError,
    InvalidFuncCallError,
    InvalidPlaceholderError,
    MultiWriterError,
    NotElaboratedError,
    SignalTypeError,
    UpblkFuncSameNameError,
    VarNotDeclaredError,
)
from .NamedObject import NamedObject
from .Placeholder import Placeholder

p = re.compile('( *(@|def))')

class ComponentLevel2( ComponentLevel1 ):

  #-----------------------------------------------------------------------
  # Private methods
  #-----------------------------------------------------------------------

  def __new__( cls, *args, **kwargs ):
    inst = super( ComponentLevel2, cls ).__new__( cls, *args, **kwargs )

    inst._dsl.update_on_edge = set()

    # constraint[var] = (sign, func)
    inst._dsl.RD_U_constraints = defaultdict(set)
    inst._dsl.WR_U_constraints = defaultdict(set)
    inst._dsl.name_func = {}

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
      name_src[ name ] = src  = p.sub( r'\2', inspect.getsource(func) )
      name_ast[ name ] = tree = ast.parse( src )
      name_rd[ name ]  = rd   = []
      name_wr[ name ]  = wr   = []
      name_fc[ name ]  = fc   = []
      AstHelper.extract_reads_writes_calls( func, tree, rd, wr, fc )

  def _elaborate_read_write_func( s ):

    # We have parsed AST to extract every read/write variable name.
    # I refactor the process of materializing objects in this function
    # Pass in the func as well for error message

    def extract_obj_from_names( func, names ):

      def expand_array_index( obj, name_depth, node_depth, idx_depth, idx, obj_list ):
        """ Find s.x[0][*][2], if index is exhausted, jump back to lookup_variable """

        if idx_depth >= len(idx): # exhausted, go to next level of name
          lookup_variable( obj, name_depth+1, node_depth+1, obj_list )

        elif idx[ idx_depth ] == "*": # special case, materialize all objects
          if isinstance( obj, NamedObject ): # Signal[*] is the signal itself
            add_all( obj, obj_list, node_depth )
          else:
            for i, child in enumerate( obj ):
              expand_array_index( child, name_depth, node_depth, idx_depth+1, idx, obj_list )
        else:
          try:
            child = obj[ idx[ idx_depth ] ]
          except TypeError: # cannot convert to integer
            raise VarNotDeclaredError( obj, idx[idx_depth], func, s, nodelist[node_depth].lineno )
          except IndexError:
            return

          s._dsl.astnode_objs[ nodelist[node_depth] ].append( child )
          expand_array_index( child, name_depth, node_depth, idx_depth+1, idx, obj_list )

      def add_all( obj, obj_list, node_depth ):
        """ Already found, but it is an array of objects,
            s.x = [ [ A() for _ in xrange(2) ] for _ in xrange(3) ].
            Recursively collect all signals. """
        if   isinstance( obj, NamedObject ):
          obj_list.add( obj )
        elif isinstance( obj, list ): # SORRY
          for i, child in enumerate( obj ):
            add_all( child, obj_list, node_depth+1 )

      def lookup_variable( obj, name_depth, node_depth, obj_list ):
        """ Look up the object s.a.b.c in s. Jump to expand_array_index if c[] """
        if obj is None:
          return

        if name_depth >= len(obj_name): # exhausted
          add_all( obj, obj_list, node_depth ) # if this object is a list/array again...
          return

        # still have names
        field, idx = obj_name[ name_depth ]
        try:
          child = getattr( obj, field )
        except AttributeError as e:
          print(e)
          raise VarNotDeclaredError( obj, field, func, s, nodelist[node_depth].lineno )

        s._dsl.astnode_objs[ nodelist[node_depth] ].append( child )

        if not idx: lookup_variable   ( child, name_depth+1, node_depth+1, obj_list )
        else:       expand_array_index( child, name_depth,   node_depth+1, 0, idx, obj_list )

      """ extract_obj_from_names:
      Here we enumerate names and use the above functions to turn names
      into objects """

      all_objs = set()

      for obj_name, nodelist in names:
        objs = set()

        if obj_name[0][0] == "s":
          s._dsl.astnode_objs[ nodelist[0] ].append( s )
          lookup_variable( s, 1, 1, objs )
          all_objs |= objs

        # This is a function call without "s." prefix, check func list
        elif obj_name[0][0] in s._dsl.name_func:
          call = s._dsl.name_func[ obj_name[0][0] ]
          all_objs.add( call )
          s._dsl.astnode_objs[ nodelist[0] ].append( call )

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
    s._dsl.astnode_objs = defaultdict(list)
    s._dsl.func_reads  = {}
    s._dsl.func_writes = {}
    s._dsl.func_calls  = {}
    for name, func in s._dsl.name_func.iteritems():
      s._dsl.func_reads [ func ] = extract_obj_from_names( func, name_rd[ name ] )
      s._dsl.func_writes[ func ] = extract_obj_from_names( func, name_wr[ name ] )
      s._dsl.func_calls [ func ] = extract_obj_from_names( func, name_fc[ name ] )

    s._dsl.upblk_reads  = {}
    s._dsl.upblk_writes = {}
    s._dsl.upblk_calls  = {}
    for name, blk in s._dsl.name_upblk.iteritems():
      s._dsl.upblk_reads [ blk ] = extract_obj_from_names( blk, name_rd[ name ] )
      s._dsl.upblk_writes[ blk ] = extract_obj_from_names( blk, name_wr[ name ] )
      s._dsl.upblk_calls [ blk ] = extract_obj_from_names( blk, name_fc[ name ] )

  # Override
  def _collect_vars( s, m ):
    super( ComponentLevel2, s )._collect_vars( m )

    if isinstance( m, ComponentLevel2 ):
      s._dsl.all_update_on_edge |= m._dsl.update_on_edge

      for k, k_cons in m._dsl.RD_U_constraints.iteritems():
        s._dsl.all_RD_U_constraints[k] |= k_cons

      for k, k_cons in m._dsl.WR_U_constraints.iteritems():
        s._dsl.all_WR_U_constraints[k] |= k_cons

      # I assume different update blocks will always have different ids
      s._dsl.all_upblk_reads.update( m._dsl.upblk_reads )
      s._dsl.all_upblk_writes.update( m._dsl.upblk_writes )

      for blk, calls in m._dsl.upblk_calls.iteritems():
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
    super( ComponentLevel2, s )._uncollect_vars( m )

    if isinstance( m, ComponentLevel2 ):
      s._dsl.all_update_on_edge -= m._dsl.update_on_edge

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
    for blk, writes in s._dsl.all_upblk_writes.iteritems():
      for wr in writes:
        write_upblks[ wr ].add( blk )

    for obj, wr_blks in write_upblks.iteritems():
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
    for blk, reads in s._dsl.all_upblk_reads.iteritems():

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
    for blk, writes in s._dsl.all_upblk_writes.iteritems():

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
      raise InvalidPlaceholderError( "Cannot define function "
              "in a placeholder component.".format( func.__name__ ) )
    name = func.__name__
    if name in s._dsl.name_func or name in s._dsl.name_upblk:
      raise UpblkFuncSameNameError( name )

    s._dsl.name_func[ name ] = func
    s._cache_func_meta( func )
    return func

  # Override
  def update( s, blk ):
    super( ComponentLevel2, s ).update( blk )
    s._cache_func_meta( blk ) # add caching of src/ast
    return blk

  def update_on_edge( s, blk ):
    s._dsl.update_on_edge.add( blk )
    return s.update( blk )

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
    super( ComponentLevel2, s )._elaborate_declare_vars()

    s._dsl.all_update_on_edge = set()

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
    for c in s._collect_all( [ lambda s: isinstance( s, ComponentLevel2 ) ] )[0]:
      c._elaborate_read_write_func()

    s._elaborate_collect_and_mark_all_named_objects()

    s._elaborate_declare_vars()
    s._elaborate_collect_all_vars()

    s._check_valid_dsl_code()

  #-----------------------------------------------------------------------
  # Post-elaborate public APIs (can only be called after elaboration)
  #-----------------------------------------------------------------------
  # We have moved these implementations to Component.py because the
  # outside world should only use Component.py
