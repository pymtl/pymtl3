#=========================================================================
# DynamicSchedulePass.py
#=========================================================================
#
# Author : Shunning Jiang
# Date   : Apr 19, 2019

from collections import deque
from copy import deepcopy

import py

from pymtl3.dsl import InPort
from ..BasePass import BasePass, PassMetadata
from ..errors import PassOrderError

class EventDrivenPass( BasePass ):

  def __call__( self, top ):
    if not hasattr( top._dag, "all_constraints" ):
      raise PassOrderError( "all_constraints" )

    self.schedule( top )

  @staticmethod
  def schedule( top ):

    # Basically reuse results from GenDAGPass to construct sensitivity dict

    all_blks = top._dag.final_upblks

    default_blks = list( top.get_all_update_on_edge() )

    # Then check all update blocks affected by input port
    for x in top._dag.read_upblks:
      if x.get_host_component() is top:
        default_blks.extend( top._dag.read_upblks[ x ] )

    blk_sensitivity_objs = { x : set() for x in all_blks }
    blk_sensitivity_blks = { x : set() for x in all_blks }

    for (wr_blk, rd_blk), objs in top._dag.constraint_objs.items():
      blk_sensitivity_blks[ wr_blk ].add( rd_blk )
      blk_sensitivity_objs[ wr_blk ].update( objs )

    # Generate wrapped blocks

    def gen_wrapped_blk( s, blk, sense_signals, sense_blks, event_queue ):
      dc = deepcopy
      eq = event_queue.update
      w_blk_name = f"w_{blk.__name__}"
      if not sense_blks:
        return blk

      copy_srcs  = []
      check_srcs = []

      for i, sig in enumerate( sense_signals ):
        copy_srcs.append( "t{}=dc({})".format( hex(i)[2:], sig ) )
        check_srcs.append( "{}!=t{}".format( sig, hex(i)[2:] ) )

      src = f"""
      def {w_blk_name}():
        {';'.join( copy_srcs )}
        blk()
        if {' or '.join( check_srcs )}:
          eq( sense_blks )"""

      var = locals()
      var.update( globals() )
      exec( py.code.Source( src ).compile(), var )
      return var[ w_blk_name ]

    # Generate tick

    # OK the problem here is, there is a "livelock" between generating
    # a wrapped update block and calling other wrapped update blocks...
    # The solution I came up with (which is somewhat modifying the closure)
    # is to pass in a mutable set to store the original form of subsequent
    # blocks of a blk. Then after I compiled all the wrapped blocks, I
    # change the blocks stored of those mutable sets to wrapped blocked.

    def gen_tick( event_queue, w_default_blks ):
      eq_pop = event_queue.pop
      def tick():
        for w_blk in w_default_blks: # Mamba?
          w_blk()
        while event_queue:
          w_blk = eq_pop()
          w_blk()
      return tick

    event_queue = set()

    blk_wblk_mapping = {}

    w_default_blks = []
    for b in default_blks:
      w_b =  gen_wrapped_blk( top, b,
                              blk_sensitivity_objs[b],
                              blk_sensitivity_blks[b],
                              event_queue )
      w_default_blks.append( w_b )
      blk_wblk_mapping[b] = w_b

    top.tick = gen_tick( event_queue, w_default_blks )

    other_blks = all_blks - set(default_blks)

    for b in other_blks:
      w_b = gen_wrapped_blk( top, b,
                             blk_sensitivity_objs[b],
                             blk_sensitivity_blks[b],
                             event_queue )
      blk_wblk_mapping[b] = w_b

    for b, bs in blk_sensitivity_blks.items():
      # The goal is to substitute the original block with the wrapped
      # block **in the original set**. We cannot iterate and modify in the
      # same loop. As a result I have to create a set first and move all
      # the elements to the original set.
      tmp = set()
      while bs:
        b = bs.pop()
        if b in blk_wblk_mapping:
          tmp.add( blk_wblk_mapping[ b ] )
        else:
          tmp.add( b )
      bs.update( tmp )

    # Prime the simulation by putting all events on the event_queue
    # This will make sure all nodes come out of reset in a consistent
    # state. TODO: put this in reset() instead?
    for b, bb in blk_wblk_mapping.items():
      event_queue.add( bb )
