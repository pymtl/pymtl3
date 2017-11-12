#-------------------------------------------------------------------------
# MetaBlkPass
#-------------------------------------------------------------------------

from pymtl import *
from pymtl.passes import BasePass
from collections  import deque, defaultdict
from graphviz     import Digraph
from errors import PassOrderError
from pymtl.model.errors import UpblkCyclicError
import ast, py

class MetaBlkPass( BasePass ):
  def __init__( self, dump = False ):
    self.dump = dump

  def apply( self, m, mode ):
    if not hasattr( m, "_all_constraints" ):
      raise PassOrderError( "_all_constraints" )

    self.schedule( m )
    self.generate_tick( m, mode )

  #-------------------------------------------------------------------------
  # schedule
  #-------------------------------------------------------------------------

  def schedule( self, m ):

    # Construct the graph

    vs  = m._all_id_upblk.keys()
    es  = defaultdict(list)
    InD = { v:0 for v in vs }
    OuD = { v:0 for v in vs }

    for (u, v) in list(m._all_constraints): # u -> v, always
      InD[v] += 1
      es [u].append( v )

    # Shunning: now we make the scheduling aware of meta blocks
    # Basically we enhance the topological sort to choose
    # branchy/unbranchy block based on the progress of the current meta
    # block. If there is no branch at all along the meta block, I let it
    # grow as long as possible. If we have to append one branchy update
    # block, we then append a couple of branchy blocks till the
    # branchiness bound is reached, after which we break the trace.
    #
    # TODO now I'm using binary-search. Ideally a double-ended
    # priority queue or a balanced binary search tree (AVL/Treap/RB) can
    # reduce it to O(nlogn). I didn't find any efficient python impl.

    serial = []

    def insert_sortedlist( arr, priority, item ):
      left, right = 0, len(arr)
      while left < right-1:
        mid = (left + right) >> 1
        if priority <= arr[mid][0]:
          right = mid
        else:
          left = mid
      arr.insert( right, (priority, item) )

    Q = []
    for v in vs:
      if not InD[v]:
        br = m._all_meta['br'][v]
        insert_sortedlist( Q, br, v )

    # Branchiness factor is the bound of branchiness in a meta block.
    branchiness_factor = 8

    # Countdown factor is the number of branchy block we allow at the end
    # of a meta block
    countdown_factor = 10000

    metas = []
    current_meta = []
    current_branchiness = 0
    countdown = 0

    while Q:
      # If currently there is no branchiness, append less branchy block
      if not current_branchiness:
        (br, u) = Q.pop(0)

        # Update the current
        current_branchiness += br
        current_meta.append( m._all_id_upblk[u] )

        if current_branchiness > branchiness_factor:
          metas.append( current_meta )
          current_branchiness = 0
          current_meta = []

      # We already append a branchy block
      else:
        # Find most branchy block
        (br, u) = Q.pop()

        # If no branchy block available, directly start a new metablock

        if not br:
          metas.append( current_meta )
          current_branchiness = countdown = 0
          current_meta = [ m._all_id_upblk[u] ]

        # Otherwise limit the number of branchy blocks

        else:
          current_meta.append( m._all_id_upblk[u] )

          countdown += 1
          current_branchiness += br
          if countdown > countdown_factor or \
             current_branchiness > branchiness_factor:
            metas.append( current_meta )
            current_branchiness = countdown = 0
            current_meta = []

      for v in es[u]:
        InD[v] -= 1
        if not InD[v]:
          insert_sortedlist( Q, m._all_meta['br'][ v ], v )

    # Append the last meta block
    if current_meta:
      metas.append( current_meta )

    # for meta in metas:
      # print "---------------"
      # for blk in meta:
        # print " - {}: {}".format( blk.__name__, m._all_meta['br'][ id(blk) ] )

    if sum( [ len(x) for x in metas] ) != len(vs):
      from graphviz import Digraph
      dot = Digraph()
      dot.graph_attr["rank"] = "same"
      dot.graph_attr["ratio"] = "compress"
      dot.graph_attr["margin"] = "0.1"

      leftovers = [ m._all_id_upblk[v] for v in vs if InD[v] ]
      for x in leftovers:
        dot.node( x.__name__+"\\n@"+repr(x.hostobj), shape="box")

      for (x, y) in m._all_constraints:
        upx, upy = m._all_id_upblk[x], m._all_id_upblk[y]
        if upx in leftovers and upy in leftovers:
          dot.edge( upx.__name__+"\\n@"+repr(upx.hostobj),
                    upy.__name__+"\\n@"+repr(upy.hostobj) )
      # dot.render( "/tmp/upblk-dag.gv", view=True )

      raise UpblkCyclicError( """
  Update blocks have cyclic dependencies.
  * Please consult update dependency graph for details."
      """)

    m._meta_schedule = metas

  #-------------------------------------------------------------------------
  # generate_tick
  #-------------------------------------------------------------------------

  def generate_tick( self, m, mode ):
    metas = m._meta_schedule
    print "meta_mode:", mode, "num_metablks:", len(metas)

    if mode == 'meta_break':
      # unroll

      # We will use pypyjit.dont_trace_here to disable tracing across
      # intermediate update blocks.
      gen_tick_src =  "try:\n"
      gen_tick_src += "  from pypyjit import dont_trace_here\n"
      gen_tick_src += "except ImportError:\n"
      gen_tick_src += "  pass\n"

      # The "comment" that will be used for update calls.
      schedule_names = {}

      for i in xrange( len(metas) ):
        meta = metas[i]
        for j in xrange( len(meta) ):
          blk = meta[j]
          schedule_names[ (i, j) ] = "[br: {}] {}" \
            .format( m._all_meta['br'][id(blk)], blk.__name__ )

          # Copy the scheduled functions to update_blkX__Y
          gen_tick_src += "update_blk{0}__{1} = metas[{0}][{1}];".format( i, j )

      for i in xrange( len(metas) ):
        meta_blk = m._meta_schedule[i]

        gen_tick_src += "\n\ndef meta_blk{}():\n  ".format(i)

        gen_tick_src += "\n  ".join( [ "update_blk{}__{}() # {}" \
                                      .format( i, j, schedule_names[(i, j)] )
                                      for j in xrange( len(meta_blk) )] )

        gen_tick_src += "\ntry:\n"
        gen_tick_src += "  dont_trace_here(0, False, meta_blk{}.__code__)\n".format( i )
        gen_tick_src += "except NameError:\n"
        gen_tick_src += "  pass\n"

      gen_tick_src += "\ndef tick_top():\n  "
      gen_tick_src += "; ".join( [ "meta_blk{}()".format(i) for i in xrange(len(metas)) ] )

      exec py.code.Source( gen_tick_src ).compile() in locals()

    elif mode == 'meta_loop':

      gen_tick_src = ""

      # The "comment" that will be used for update calls.
      schedule_names = {}

      for i in xrange( len(metas) ):
        meta = metas[i]
        for j in xrange( len(meta) ):
          blk = meta[j]
          schedule_names[ (i, j) ] = "[br: {}] {}" \
            .format( m._all_meta['br'][id(blk)], blk.__name__ )

          # Copy the scheduled functions to update_blkX__Y
          gen_tick_src += "update_blk{0}__{1} = metas[{0}][{1}];".format( i, j )

      self._meta_blks = []

      for i in xrange( len(metas) ):
        meta_blk = m._meta_schedule[i]

        gen_tick_src += "\n\ndef meta_blk_call{}():\n  ".format(i)

        gen_tick_src += "\n  ".join( [ "update_blk{}__{}() # {}" \
                                      .format( i, j, schedule_names[(i, j)] )
                                      for j in xrange( len(meta_blk) )] )
        gen_tick_src += "\n\nself._meta_blks.append(meta_blk_call{})".format(i)


      gen_tick_src += "\ndef tick_top():"
      gen_tick_src += "\n  for x in self._meta_blks:"
      gen_tick_src += "\n    x()\n"

      exec py.code.Source( gen_tick_src ).compile() in locals()

    else:
      assert False, mode

    # print gen_tick_src
    m._tick_src = gen_tick_src
    m.tick = tick_top
