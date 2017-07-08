from pymtl import *
from collections  import deque, defaultdict
from pymtl.model.errors import UpblkCyclicError, NotElaboratedError
from pymtl.model import Signal, Const, NamedObject
import random

#-------------------------------------------------------------------------
# schedule_upblk
#-------------------------------------------------------------------------
# Based on all constraints on the update block list, calculate a feasible
# static schedule for update blocks.

def simple_sim_pass( m, seed=0xdeadbeef ):
  random.seed( seed )

  if not hasattr( m, "_all_constraints" ):
    raise NotElaboratedError()

  # Construct the graph

  vs  = m._all_id_upblk.keys()
  es  = defaultdict(list)
  InD = { v:0 for v in vs }

  for (u, v) in list(m._all_constraints): # u -> v, always
    InD[v] += 1
    es [u].append( v )

  # Perform topological sort for a serial schedule.

  m._serial_schedule = []
  Q = deque( [ v for v in vs if not InD[v] ] )
  while Q:
    random.shuffle(Q)
    u = Q.pop()
    m._serial_schedule.append( m._all_id_upblk[u] )
    for v in es[u]:
      InD[v] -= 1
      if not InD[v]:
        Q.append( v )

  if len(m._serial_schedule) != len(vs):
    raise UpblkCyclicError(
      'Update blocks have cyclic dependencies.'
      '* Please consult update dependency graph for details.'
    )

  schedule = m._serial_schedule
  assert schedule, "No update block found in the model"

  m._tick_src = """
    def tick_normal():
      for blk in schedule:
        blk()
    """

  def tick_normal():
    for blk in schedule:
      blk()
  m.tick = tick_normal

  # Clean up Signals

  def cleanup_signals( m ):
    if isinstance( m, list ):
      for i, o in enumerate( m ):
        if   isinstance( o, Signal ): m[i] = o.default_value()
        elif isinstance( o, Const ):  m[i] = o.const
        else:                         cleanup_signals( o )

    elif isinstance( m, NamedObject ):
      for name, obj in m.__dict__.iteritems():
        if ( isinstance( name, basestring ) and not name.startswith("_") ) \
          or isinstance( name, tuple ):
          if   isinstance( obj, Signal ): setattr( m, name, obj.default_value() )
          elif isinstance( obj, Const ):  setattr( m, name, obj.const )
          else:                           cleanup_signals( obj )

  cleanup_signals( m )
