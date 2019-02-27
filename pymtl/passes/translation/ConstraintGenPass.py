#=========================================================================
# ConstraintGenPass.py
#=========================================================================
# This pass convert the constraint DAG into a sensitivity group file
# that can be used to import the translated top module back to PyMTL.
# This pass writes to <top_module>.ssg file in the current directory.
# The key assumption made by this pass to generate constraints is that
# each signal written by an upblk depends on all the signals read by
# this upblk.
#
# Author : Peitian Pan
# Date   : Feb 19, 2019

from copy                    import copy

from pymtl                   import *
from pymtl.passes            import BasePass
from pymtl.passes.simulation import GenDAGPass

class ConstraintGenPass( BasePass ):

  def __call__( s, top ):
    """ convert the constraint DAG of top into ssg files """

    model_name    = top.__class__.__name__
    ssg_file_name = model_name + '.ssg'

    # Collect all vertices and edges of the constraint DAG

    GenDAGPass()( top )

    seq_upblks  = top.get_all_update_on_edge()
    comb_upblks = ( top.get_all_update_blocks() | top._dag.genblks) - seq_upblks

    upblks = { 'CombPath' : comb_upblks, 'SeqPath' : seq_upblks }

    upblk_RD, upblk_WR, _ = top.get_all_upblk_metadata()

    for upblk, signal_list in top._dag.genblk_reads.iteritems():
      upblk_RD[ upblk ] = set( signal_list )

    for upblk, signal_list in top._dag.genblk_writes.iteritems():
      upblk_WR[ upblk ] = set( signal_list )
    
    # Construct net structure for top
    
    s.net = {}

    for path_type in ( 'CombPath', 'SeqPath' ):
      for upblk in upblks[ path_type ]:

        wr_signals = set()
        for wr_signal in upblk_WR[ upblk ]:
          wr_signals.add( ( wr_signal, path_type ) )

        for rd_signal in upblk_RD[ upblk ]:
          if rd_signal in s.net:
            s.net[ rd_signal ] |= copy( wr_signals )
          else:
            s.net[ rd_signal ] = copy( wr_signals )

    # Initialize the output port sensitivity group to 'not connected'

    top_inports  = top.get_input_value_ports()
    top_outports = top.get_output_value_ports()

    s.outport_ssg = {}

    for outport in top_outports:
      s.outport_ssg[ outport ] = {}
      for inport in top_inports:
        s.outport_ssg[ outport ][ inport ] = { 'CombPath':False, 'SeqPath':False }

    # Flood the nets to figure out the connections between inports and
    # outports

    for inport in top_inports:
      s.flood_mark( inport, lambda signal: signal in top_outports,\
        inport, 'CombPath' )

    # Print out the connections. For each outport, list all the inports
    # it depends on.
    
    with open( ssg_file_name, 'w' ) as ssg_file:
      for outport in top_outports:
        string = s.ssg_dict_to_str( top_inports, outport ) + '\n'
        ssg_file.write( string )

  def flood_mark( s, cur, flt, inport, pre_path_type ):
    if not cur in s.net: return
    for nxt, cur_path_type in s.net[ cur ]:
      path_type = 'SeqPath' if cur_path_type == 'SeqPath' else pre_path_type
      if flt( nxt ):
        s.outport_ssg[ nxt ][ inport ][ path_type ] = True
        continue
      s.flood_mark( nxt, flt, inport, path_type )

  def ssg_dict_to_str( s, inports, outport ):
    ret = ''
    inport_strs = []

    for inport in inports:

      comb = s.outport_ssg[ outport ][ inport ][ 'CombPath' ] == True
      seq  = s.outport_ssg[ outport ][ inport ][ 'SeqPath'  ] == True

      if   not comb and not seq: continue
      if   comb and seq:         prefix = 'B'
      elif comb and not seq:     prefix = 'C'
      elif not comb and seq:     prefix = 'S'

      inport_strs.append( prefix + inport._dsl.my_name )

    return ', '.join( inport_strs ) + ' => ' + outport._dsl.my_name
