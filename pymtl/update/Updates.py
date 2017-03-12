#=========================================================================
# Updates.py
#=========================================================================
# Updates class supports connections of variables.

from UpdatesImpl import UpdatesImpl
from UpdatesExpl import UpdatesExpl
from Connectable import ConnectableValue

class Updates( UpdatesImpl ):

  # If this is a built-in type variable and not a private variable,
  # it is going to the simulation and not used by elaboration

  def __setattr__( s, x, v ):
    if not x.startswith("_"):
      if isinstance( v, int ) or isinstance( v, float ) or isinstance( v, bool ):
        v = ConnectableValue( v, s, x, -1 )
      elif isinstance( v, list ) and isinstance( v[0], int ):
        v = [ ConnectableValue( v[i], s, x, i ) for i in xrange(len(v)) ]
    super(UpdatesExpl, s).__setattr__( x, v )

  def _collect_connections( s, varid_vars ):
    for name, obj in s.__dict__.iteritems():
      if not name.startswith("_"): # filter private variables
        if   isinstance( obj, Updates ):
          obj._collect_connections( varid_vars )
        elif isinstance( obj, ConnectableValue ):
          root = obj._find_root()

          if len( root._connected ) > 1: # has actual connection
            if id(root) not in varid_vars:
              varid_vars[ id(root) ] = (root, root._connected)
          else:
            assert root == obj, "It doesn't make sense ..."

  def _resolve_connections( s ):

    def mk_v_v( o1, f1, o2, f2 ):
      def f(): o1.__setattr__( f1, o2.__getattribute__( f2 ) )
      return f

    def mk_v_a( o1, f1, o2, f2, i2 ):
      def f(): o1.__setattr__( f1, o2.__getattribute__( f2 )[i2] )
      return f

    def mk_a_v( o1, f1, i1, o2, f2 ):
      def f(): o1.__getattribute__( f1 )[i1] = o2.__getattribute__( f2 )
      return f

    def mk_a_a( o1, f1, i1, o2, f2, i2 ):
      def f(): o1.__getattribute__( f1 )[i1] = o2.__getattribute__( f2 )[i2]
      return f

    varid_net = dict()
    s._collect_connections( varid_net )

    for (var, net) in varid_net.values():
      # Writer means it is written somewhere else.
      # In these connection blocks, the writer's value is read, v = writer

      has_writer, writer = False, None
      for v in net:
        if id(v) in s._write_blks:
          assert not has_writer, "We don't allow %s and %s to write to the same net." %(writer._name, v._name)
          has_writer, writer = True, v
      if not has_writer: continue # TODO what the hell does this mean?

      wobj  = writer._obj
      wname = writer._name
      widx  = writer._idx

      for v in net:
        if v != writer:
          if widx < 0: # writer is var
            if v._idx < 0: upblk = mk_v_v( v._obj, v._name,         wobj, wname       )
            else:          upblk = mk_a_v( v._obj, v._name, v._idx, wobj, wname       )
          else:        # writer is arr
            if v._idx < 0: upblk = mk_v_a( v._obj, v._name,         wobj, wname, widx )
            else:          upblk = mk_a_a( v._obj, v._name, v._idx, wobj, wname, widx )

          upblk.__name__ = "up_%s%s_%s%s" % \
            ( writer._name, str(writer._idx) if writer._idx>=0 else "", \
              v._name, str(v._idx) if v._idx>=0 else "" )

          blk_id = id(upblk)
          s._name_upblk [ blk_id ] = upblk.__name__
          s._blkid_upblk[ blk_id ] = upblk
          s._write_blks [ id(v)  ].append(blk_id)
          s._read_blks  [ id(writer) ].append(blk_id)

  # Override
  def elaborate( s ):
    s._recursive_elaborate()
    s._resolve_connections() # This is done after recursive collections
    s._synthesize_constraints()
    s._schedule()
    s._cleanup_values()
