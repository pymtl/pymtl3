#-------------------------------------------------------------------------
# MetaConsolidateBlkPass
#-------------------------------------------------------------------------

from pymtl import *
from pymtl.passes import BasePass
from collections  import deque, defaultdict
from graphviz     import Digraph
from errors import PassOrderError
from pymtl.model.errors import UpblkCyclicError
import ast, py

class MetaConsolidateBlkPass( BasePass ):
  def __init__( self, dump = False ):
    self.dump = dump

  def apply( self, m, mode ):
    if not hasattr( m, "_all_constraints" ):
      raise PassOrderError( "_all_constraints" )

    self.schedule( m, mode )
    self.generate_tick( m, mode )

  #-------------------------------------------------------------------------
  # schedule
  #-------------------------------------------------------------------------

  def schedule( self, m, mode ):

    # Construct the graph

    vs  = m._all_id_upblk.keys()
    es  = defaultdict(list)
    InD = { v:0 for v in vs }
    OuD = { v:0 for v in vs }

    for (u, v) in list(m._all_constraints): # u -> v, always
      InD[v] += 1
      es [u].append( v )

    # TODO: use an ordered set here instead for O( logn ) searches.
    Q = []
    for v in vs:
      if not InD[v]:
        Q.append(v)

    metas = []
    current_meta = []

    self.i = 0
    self.hostobjs = None

    def schedule_blks( blks ):

      # Make sure wr already generated a version of the block without a
      # closure.
      for other_blk in blks:
        if other_blk.blk_without_closure is None:
          other_blk.hostobj.strip_closure( other_blk )

      hostobjs = [ b.hostobj for b in blks ]

      assert blk.blk_without_closure
      current_meta.append( ( blk.blk_without_closure,
                             hostobjs,
                             blks ) )

      for other_blk in blks:
        # Remove item from the queue.
        Q.remove( id( other_blk ) )

      # Update all InD values.
      for other_blk in blks:
        for v in es[ id(other_blk) ]:
          InD[v] -= 1
          if not InD[v]:
            Q.insert( 0, v )

      # Reset the queue position.
      self.i = 0

      # Store the hostobjs so that we can try combining more into the same
      # for loop.
      self.hostobjs = hostobjs


    while Q:
      # Peek the current position in the queue.
      u = Q[ self.i ]
      blk = m._all_id_upblk[u]

      # Find blocks that are similar (same update block of the same
      # component, but a different instant). This should have already been
      # recoreded by ComponentLevel1.
      similar_blks = blk.hostobj.__class__._blks[ blk.__name__ ]

      # If we have previous hostobjs recorded, greedily try to find
      # another set of blocks that uses the same hostobjs.
      if self.hostobjs is not None:
        if blk.hostobj in self.hostobjs:
          hostobjs = [ b.hostobj for b in similar_blks ]

          similar_blks = \
              [ similar_blks[i] for i, ho in enumerate(hostobjs)
                if ho in self.hostobjs ]

          # Check if all of the blocks can be scheduled.
          if all( ( id( b ) in Q for b in similar_blks ) ):

            schedule_blks( similar_blks )
            continue

        # Loop around.
        self.i += 1

        if self.i == len( Q ):
          # Reached the end of the queue, and couldn't find
          # opportunities to merge for blocks. Reset i, remove
          # self.hostobjs and try again.
          self.i = 0
          self.hostobjs = None
          continue

      # Check if all blocks of the type are schedulable.
      for other_blk in similar_blks:

        if id( other_blk ) not in Q:
          self.i += 1

          # Couldn't schedule all blocks of the same type, schedule as
          # many as possible for head of the queue.
          if self.i == len( Q ):
            u = Q[0]

            blk = m._all_id_upblk[u]
            similar_blks = [ b for b in blk.hostobj.__class__._blks[ blk.__name__ ]
                             if id( b ) in Q ]
            schedule_blks( similar_blks )

          break

      else:

        # Can schedule all similar blocks, so do that.
        schedule_blks( similar_blks )


    # Append the last meta block
    if current_meta:
      metas.append( current_meta )

    num_scheduled = sum( [ sum( [ len(y) for _,y,_ in x ] ) for x in metas ] )

    if num_scheduled != len(vs):
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
        blk = meta[j][0]
        schedule_names[ (i, j) ] = "[br: {}] {}" \
          .format( m._all_meta['br'][id(blk)], blk.__name__ )

        # Copy the scheduled functions to update_blkX__Y
        gen_tick_src += "update_blk{0}__{1} = metas[{0}][{1}][0];".format( i, j )

    for i in xrange( len(metas) ):
      meta_blk = m._meta_schedule[i]

      nc_tick_src = ""
      cl_tick_src = ""
      for j in xrange( len( meta_blk ) ):
        for k in xrange( len( meta_blk[j][1] ) ):
          gen_tick_src += "ins_vars_{0}_{1}_{2} = metas[{0}][{1}][1][{2}]\n" \
                  .format(i, j, k)

      gen_tick_src += "\n\ndef meta_blk_call{}():\n".format(i)

      self._meta_blks = []
      prev_hostobjs = None

      current_num_iters = -1
      current_hostobjs_list = []
      current_hostobjs_idxs = []
      current_loop_body_str = ""

      def emit_loop():
        loop_str = "  for {} in ( {} ):\n".format(
            ", ".join(
                [ "_s" + str(x) for x in xrange( len( current_hostobjs_list ) ) ] ),
            ", ".join(
                [ "(" + (
                  ", ".join(
                    [ "ins_vars_{}_{}_{}".format( i, j, k )
                       for j in current_hostobjs_idxs ] )
                  ) + ")" for k in xrange( current_num_iters )] ) )
        loop_str += current_loop_body_str
        return loop_str

      for j in xrange( len( meta_blk ) ):

        if len( metas[i][j][1] ) > 1:
          hostobjs = metas[i][j][1]

          if len( hostobjs ) == current_num_iters:
            # If the number of hostobjs matches the current num
            # iterations, try to use the same loop.

            hostobjs_set = set( hostobjs )
            if hostobjs_set in current_hostobjs_list:
              # Find the instance variable names to use.
              ins_var_idx = current_hostobjs_list.index( hostobjs_set )
            else:
              ins_var_idx = len( current_hostobjs_list )
              current_hostobjs_list.append( hostobjs_set )
              current_hostobjs_idxs.append( j )

            current_loop_body_str += \
                "    update_blk{}__{}( _s{} ) # {}\n".format(
                            i, j, ins_var_idx, schedule_names[(i, j)] )


          else:
            if current_num_iters != -1:
              gen_tick_src += emit_loop()

            current_num_iters = len( hostobjs )
            current_hostobjs_list = [ set( hostobjs ) ]
            current_hostobjs_idxs = [ j ]
            current_loop_body_str = \
                "    update_blk{}__{}( _s0 ) # {}\n".format(
                            i, j, schedule_names[(i, j)] )

        else:
          if current_num_iters != -1:
            gen_tick_src += emit_loop()

          current_num_iters = -1

          gen_tick_src += "  update_blk{0}__{1}( ins_vars_{0}_{1}_0 ) # {2}\n" \
                            .format( i, j, schedule_names[(i, j)] )

      if current_num_iters != -1:
        gen_tick_src += emit_loop()

      current_num_iters = -1

      gen_tick_src += "\n\nself._meta_blks.append(meta_blk_call{})\n".format(i)


    gen_tick_src += "\ndef tick_top():"
    gen_tick_src += "\n  for x in self._meta_blks:"
    gen_tick_src += "\n    x()\n"

    exec py.code.Source( gen_tick_src ).compile() in locals()

    print gen_tick_src
    m._tick_src = gen_tick_src
    m.tick = tick_top
