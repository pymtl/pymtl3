#-------------------------------------------------------------------------
# PrintMetadataPass
#-------------------------------------------------------------------------

from pymtl.passes import BasePass
from graphviz import Digraph
from collections import deque

class PrintMetadataPass( BasePass ):

  def apply( self, m, view_dag=False ): # apply pass to model m
    if hasattr( m, "_all_meta" ):
      self.print_read_write_func( m )

    if hasattr( m, "_all_nets" ):
      self.print_nets( m )

    if hasattr( m, "_all_constraints" ):
      self.print_constraints( m )
      if view_dag:
        self.print_upblk_dag( m )

    if hasattr( m, "_serial_schedule" ):
      self.print_schedule( m )

    if hasattr( m, "_tick_src" ):
      self.print_tick_src( m )

  def print_read_write_func( self, m ):
    print
    print "+-------------------------------------------------------------"
    print "+ Read/write/func in each @s.func function"
    print "+-------------------------------------------------------------"
    for funcid, func in m._all_id_func.iteritems():
      if not m._all_meta['reads'][ funcid ] and not m._all_meta['writes'][ funcid ] \
         and not m._all_meta['calls'][ funcid ]:
        continue

      print "\nIn {} (func) of {}:".format( func.__name__, func.hostobj )

      if m._all_meta['writes'][ funcid ]:
        print   "  * Write:"
        for o in m._all_meta['writes'][ funcid ]:
          print "    + {}".format( repr(o) )

      if m._all_meta['reads'][ funcid ]:
        print   "  * Read:"
        for o in m._all_meta['reads'][ funcid ]:
          print "    - {}".format( repr(o) )

      if m._all_meta['calls'][ funcid ]:
        print   "  * Call:"
        for o in m._all_meta['calls'][ funcid ]:
          print "    > {} (func)".format( o.__name__ )
    print
    print "+-------------------------------------------------------------"
    print "+ Read/write/func in each @s.update update block"
    print "+-------------------------------------------------------------"
    for blkid, blk in m._all_id_upblk.iteritems():

      if not m._all_meta['reads'][ blkid ] and not m._all_meta['writes'][ blkid ] \
         and not m._all_meta['calls'][ blkid ]:
        continue

      print "\nIn {} (update block) of {}:".format( blk.__name__, blk.hostobj )

      if m._all_meta['writes'][ blkid ]:
        print   "  * Write:"
        for o in m._all_meta['writes'][ blkid ]:
          print "    + {}".format( repr(o) )

      if m._all_meta['reads'][ blkid ]:
        print   "  * Read:"
        for o in m._all_meta['reads'][ blkid ]:
          print "    - {}".format( repr(o) )

      if m._all_meta['calls'][ blkid ]:
        for o in m._all_meta['calls'][ blkid ]:
          Q = deque( [ (o, 0) ] )
          while Q:
            u, width = Q.pop()
            prefix = " " * width

            print prefix + "  * Call:"
            print prefix + "    > {} (func)".format( u.__name__ )

            if m._all_meta['writes'][ id(u) ]:
              print prefix + "      * Write:"
              for obj in m._all_meta['writes'][ id(u) ]:
                print prefix + "        + {}".format( repr(obj) )

            if m._all_meta['reads'][ id(u) ]:
              print prefix + "      * Read:"
              for obj in m._all_meta['reads'][ id(u) ]:
                print prefix + "        - {}".format( repr(obj) )

            if m._all_meta['calls'][ id(u) ]:
              for v in m._all_meta['calls'][ id(u) ]:
                Q.append( (v, width + 4) )

  def print_nets( self, m ):
    print
    print "+-------------------------------------------------------------"
    print "+ All connected nets"
    print "+-------------------------------------------------------------"
    print

    for n in m._all_nets:
      writer, readers = n
      print "  * Writer:\n    + {}\n  * Reader(s):\n    - {}" \
            .format( repr(writer), "\n    - ".join([ repr(v) for v in readers ]) )
      print

  def print_constraints( self, m ):
    print
    print "+-------------------------------------------------------------"
    print "+ Constraints"
    print "+-------------------------------------------------------------"
    for (x, y) in m._all_expl_constraints:
      print m._all_id_upblk[x].__name__.center(34),"  <  ", m._all_id_upblk[y].__name__.center(34)

    if hasattr( m, "_all_impl_constraints" ):
      for (x, y) in m._all_impl_constraints:
        # no conflicting expl
        print m._all_id_upblk[x].__name__.center(34)," (<) ", m._all_id_upblk[y].__name__.center(34), \
              "(overridden)" if (y, x) in m._all_expl_constraints else ""

  def print_upblk_dag( self, m ):
    dot = Digraph()
    dot.graph_attr["rank"] = "same"
    dot.graph_attr["ratio"] = "compress"
    dot.graph_attr["margin"] = "0.1"

    for x in m._all_id_upblk.values():
      dot.node( x.__name__+"\\n@"+repr(x.hostobj), shape="box")
    print len(m._all_id_upblk), "update blocks in total"

    for (x, y) in m._all_constraints:
      upx, upy = m._all_id_upblk[x], m._all_id_upblk[y]
      dot.edge( upx.__name__+"\\n@"+repr(upx.hostobj),
                upy.__name__+"\\n@"+repr(upy.hostobj) )
    dot.render( "/tmp/upblk-dag.gv", view=True )

  def print_schedule( self, m ):
    print
    print "+-------------------------------------------------------------"
    print "+ Update block schedule"
    print "+-------------------------------------------------------------"
    print
    print "* Serial:"
    for (i, blk) in enumerate( m._serial_schedule ):
      print " ", i, blk.__name__
    print
    print "* Batch:"
    for x in m._batch_schedule:
      print " ", [ y.__name__ for y in x ]
      print

  def print_tick_src( self, m ):
    import textwrap
    print
    print "+-------------------------------------------------------------"
    print "+ Tick funtion source"
    print "+-------------------------------------------------------------"
    print textwrap.dedent(m._tick_src)
    print
