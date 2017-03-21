#=========================================================================
# UpdatesConnection.py
#=========================================================================
# UpdatesConnection class supports connections of variables and explicit
# constraints between update blocks and the read and write of Connectable
# variables

import py.code
from collections     import defaultdict, deque
from PyMTLObject     import PyMTLObject
from UpdatesExpl     import UpdatesExpl, verbose
from ConstraintTypes import U, RD, WR, ValueConstraint
from Connectable     import Connectable, Wire
from ASTHelper       import get_ast, get_read_write, DetectReadsAndWrites

class UpdatesConnection( UpdatesExpl ):

  def __new__( cls, *args, **kwargs ):

    inst = super( UpdatesConnection, cls ).__new__( cls, *args, **kwargs )

    # These will be collected recursively
    inst._read_blks   = defaultdict(list)
    inst._read_expls  = defaultdict(list)
    inst._write_blks  = defaultdict(list)
    inst._write_expls = defaultdict(list)
    inst._varid_net   = dict()

    # These are only processed at the current level
    inst._blkid_reads  = defaultdict(list)
    inst._blkid_writes = defaultdict(list)
    return inst

  # Override
  def update( s, blk ):
    super( UpdatesConnection, s ).update( blk )

    # I parse the asts of upblks. To also cache them across different
    # instances of the same class, I attach them to the class object.
    if not "_blkid_ast" in type(s).__dict__:
      type(s)._blkid_ast = dict()
    if blk.__name__ not in type(s)._blkid_ast:
      type(s)._blkid_ast[ blk.__name__ ] = get_ast( blk )

    get_read_write( type(s)._blkid_ast[ blk.__name__ ], blk, \
                    s._blkid_reads[ id(blk) ], s._blkid_writes[ id(blk) ] )
    return blk

  # Override
  def add_constraints( s, *args ):
    for (x0, x1) in args:
      if   isinstance( x0, U ) and isinstance( x1, U ): # U & U
        s._expl_constraints.add( (id(x0.func), id(x1.func)) )
      elif isinstance( x0, ValueConstraint ) and isinstance( x1, ValueConstraint ):
        assert False, "Constraints between two variables are not allowed!"
      elif isinstance( x0, ValueConstraint ) or isinstance( x1, ValueConstraint ):
        sign = 1 # RD(x) < U(x) is 1, RD(x) > U(x) is -1
        if isinstance( x1, ValueConstraint ):
          sign = -1
          x0, x1 = x1, x0

        if isinstance( x0, RD ):
          s._read_expls[ id(x0.var) ].append( (sign, id(x1.func) ) )
        else:
          s._write_expls[ id(x0.var) ].append( ( sign, id(x1.func) ) )

  # This elaboration process goes back and forth between two nested dfs
  # functions. One dfs only traverse s.x.y, i.e. single field. The other
  # dfs is in charge of expanding the indices of array element.

  def _elaborate_vars( s ):

    # Find s.x[0][*][2]
    def expand_array_index( print_typ, obj, name_depth, name, idx_depth, idx, id_blks, blk_id ):
      if idx_depth >= len(idx): 
        lookup_var( print_typ, obj, name_depth+1, name, id_blks, blk_id )
        return

      assert isinstance( obj, list ) or isinstance( obj, deque ), "%s is %s, not a list" % (field, type(obj))

      if isinstance( idx[idx_depth], int ): # handle x[2]'s case
        assert idx[idx_depth] < len(obj), "Index out of bound. Check the declaration of %s" % (".".join([ x[0]+"".join(["[%s]"%str(y) for y in x[1]]) for x in name]))
        expand_array_index( print_typ, obj[ idx[idx_depth] ], name_depth, name, idx_depth+1, idx, id_blks, blk_id )
      else: # handle x[*]'s case
        assert idx[idx_depth] == "*", "idk"
        for i in xrange(len(obj)):
          expand_array_index( print_typ, obj[i], name_depth, name, idx_depth+1, idx, id_blks, blk_id )

    # Add an array of objects, s.x = [ [ A() for _ in xrange(2) ] for _ in xrange(3) ]
    def add_all( obj, id_blks, blk_id ):
      if isinstance( obj, Connectable ):
        id_blks[ id(obj) ].add( blk_id )
        return
      if isinstance( obj, list ) or isinstance( obj, deque ):
        for i in xrange(len(obj)):
          add_all( obj[i], id_blks, blk_id )

    # Find the object s.a.b.c, if c is c[] then jump to expand_array_index
    def lookup_var( print_typ, obj, depth, name, id_blks, blk_id ):
      if depth >= len(name):
        if not callable(obj): # exclude function calls
          if verbose: print " -", print_typ, name, type(obj), hex(id(obj)), "in blk:", hex(blk_id), s._blkid_upblk[blk_id].__name__
          add_all( obj, id_blks, blk_id ) # if this object is a list/array again...
        return

      (field, idx) = name[ depth ]
      assert hasattr(obj, field), "\"%s\", in %s, is not a field of Class %s" %(field, s._blkid_upblk[blk_id].__name__, type(obj).__name__)
      obj = getattr( obj, field )

      if not idx: # just a variable
        lookup_var( print_typ, obj, depth+1, name, id_blks, blk_id )
      else: # let another function handle   s.x[4].y[*]
        assert isinstance( obj, list ) or isinstance( obj, deque ), "%s is %s, not a list" % (field, type(obj))
        expand_array_index( print_typ, obj, depth, name, 0, idx, id_blks, blk_id )

    # First check if each read/write variable exists, then bind the actual
    # variable id (not name anymore) to upblks that reads/writes it.

    read_blks  = defaultdict(set)
    write_blks = defaultdict(set)

    for blk_id, reads in s._blkid_reads.iteritems():
      for read_name in reads:
        lookup_var( "read", s, 0, read_name, read_blks, blk_id )
    for i in read_blks:
      s._read_blks[i].extend( list( read_blks[i] ) )

    for blk_id, writes in s._blkid_writes.iteritems():
      for write_name in writes:
        lookup_var( "write", s, 0, write_name, write_blks, blk_id )
    for i in write_blks:
      s._write_blks[i].extend( list( write_blks[i] ) )

  # Override
  def _synthesize_constraints( s ):
    read_blks   = s._read_blks
    write_blks  = s._write_blks
    read_expls  = s._read_expls
    write_expls = s._write_expls

    for read, rd_expls in read_expls.iteritems():
      rd_blks = read_blks[ read ]

      for (sign, blk) in rd_expls:
        for rd_blk in rd_blks:
          if blk != rd_blk:
            if sign == 1: # sign=1 --> rd_blk<blk
              s._expl_constraints.add( (rd_blk, blk) )
            else: # sign=-1 --> blk<rd_blk
              s._expl_constraints.add( (blk, rd_blk) )

    for write, wr_expls in write_expls.iteritems():
      wr_blks = write_blks[ write ]

      for (sign, blk) in wr_expls:
        for wr_blk in wr_blks:
          if blk != wr_blk:
            if sign == 1: # sign=1 --> wr_blk<blk
              s._expl_constraints.add( (wr_blk, blk) )
            else: # sign=-1 --> blk<wr_blk
              s._expl_constraints.add( (blk, wr_blk) )

    s._total_constraints = s._expl_constraints.copy()

  # Override
  def _collect_child_vars( s, child ):
    super( UpdatesConnection, s )._collect_child_vars( child )

    if isinstance( child, UpdatesConnection ):
      for k in child._read_blks:
        s._read_blks[k].extend( child._read_blks[k] )
      for k in child._write_blks:
        s._write_blks[k].extend( child._write_blks[k] )

      for k in child._read_expls:
        s._read_expls[k].extend( child._read_expls[k] )
      for k in child._write_expls:
        s._write_expls[k].extend( child._write_expls[k] )

      s._varid_net.update( child._varid_net )

    if isinstance( child, Connectable ):
      child.collect_nets( s._varid_net )

  # Override
  def _elaborate( s ):

    def cleanup_connectables( father ):
      if isinstance( father, list ):
        for i in xrange(len(father)):
          if isinstance( father[i], Wire ):
            print father[i].full_name()
            father[i] = father[i].default_value()
          else:
            cleanup_connectables( father[i] )

      if isinstance( father, PyMTLObject ):
        for name, obj in father.__dict__.iteritems():
          if not name.startswith("_"): # filter private variables
            if isinstance( obj, Wire ):
              print obj.full_name()
              setattr( father, name, obj.default_value() )
            else:
              cleanup_connectables( obj )

    super( UpdatesConnection, s )._elaborate()
    s._resolve_var_connections()
    cleanup_connectables( s )

  def _resolve_var_connections( s ):

    def make_func( writer, readers ):

      wobj        = writer._father
      wname, widx = writer._name_idx
      wname       = wname[-1]
      widx        = "".join(["[%s]" % x for x in widx[-1] ])

      robjs = []
      rstrs = []
      rstr_template = "robjs{i}.{rname}{ridx} = wobj.{wname}{widx}"
      for i in xrange(len(readers)):
        robj        = readers[i]._father
        rname, ridx = readers[i]._name_idx
        rname       = rname[-1]
        ridx        = "".join(["[%s]" % x for x in ridx[-1] ])

        robjs.append( robj )
        rstrs.append( rstr_template.format( **vars() ) )

      readers_str = "; ".join( rstrs )

      upblk_name  = "%s FANOUT=%d" % (writer.full_name(), len(readers))
      upblk_name_ = upblk_name.replace( ".", "_" ) \
                              .replace( " ", "_" ) \
                              .replace( "=", "_" ) \
                              .replace( "[", "_" ) \
                              .replace( "]", "_" ) \

      gen_connection_src = py.code.Source("""
        def gen_connection( s ):
          {}
          def {}():
            # The code below does the actual copy of variables.
            {}

          return {}
        """.format( "; ".join( map( "robjs{0} = robjs[{0}]".format,
                                    xrange( len( readers ) ) ) ),
                    upblk_name_, readers_str, upblk_name_
                  )
      )

      if verbose:
        print "Generate connection source: ", gen_connection_src
      exec gen_connection_src.compile() in locals()
      upblk = gen_connection(s)
      upblk.__name__ = upblk_name
      return upblk

    for (var, net) in s._varid_net.values():
      has_writer, writer = False, None
      readers = []

      # Writer means it is written somewhere else, so it will feed all other readers.
      # In these connection blocks, the writer's value is read by someone, i.e. v = writer

      for v in net:
        if id(v) in s._write_blks:
          assert not has_writer, "We don't allow %s and %s to write to the same net." %(writer.full_name(), v.full_name())
          has_writer, writer = True, v
        else:
          readers.append( v )
      assert has_writer, "This net %s needs a driver!" % [ x.full_name() for x in net ]
      # assert writer._root == writer, "%s is a driver of the following net. It should be on right hand side, \"* |= %s\": \n - %s" % \
            # ( writer.full_name(), writer.full_name(), "\n - ".join([ x.full_name() for x in net ] ))

      upblk          = make_func( writer, readers )
      blk_id         = id(upblk)
      if verbose:
        print "+ Net", ("[%s]" % writer.full_name()).center(12), " Readers", [ x.full_name() for x in readers ]
      s._name_upblk [ blk_id ] = upblk.__name__
      s._blkid_upblk[ blk_id ] = upblk
      s._read_blks  [ id(writer) ].append(blk_id)
      for v in readers:
        s._write_blks[ id(v) ].append(blk_id)

      # Create one block for each pair of writer/reader

      # for v in readers:
        # upblk          = make_func( writer, [v] )
        # blk_id         = id(upblk)
        # upblk.__name__ = "%s-%s" % (writer.full_name(), v.full_name())
        # if verbose:
          # print "+ Net", ("[%s]" % writer.full_name()).center(12), " Readers", v.full_name()

        # s._name_upblk [ blk_id ] = upblk.__name__
        # s._blkid_upblk[ blk_id ] = upblk
        # s._read_blks  [ id(writer) ].append(blk_id)
        # s._write_blks [ id(v) ].append(blk_id)
