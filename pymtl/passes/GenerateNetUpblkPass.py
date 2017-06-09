#-------------------------------------------------------------------------
# GenerateNetUpblkPass
#-------------------------------------------------------------------------

from pymtl import *
from pymtl.passes import BasePass
from pymtl.components import UpdateVarNet, _overlap, Const
from errors import ModelTypeError, PassOrderError
from collections import deque
import ast

class GenerateNetUpblkPass( BasePass ):

  def __init__( self, dump=False, opt=True ):
    self.dump = dump
    self.opt = opt

  def execute( self, m ):
    if not isinstance( m, UpdateVarNet ):
      raise ModelTypeError( "UpdateVarNet" )
    if not hasattr( m, "_nets" ):
      raise PassOrderError( "_nets" )

    if self.opt:
      self.compact_net_readers( m ) # remove unread objs, for simulation
      if self.dump:
        print "Net readers have got compacted for simulation."

    self.generate_net_block( m )

    return m

  @staticmethod
  def compact_net_readers( m ):
    nets = m._nets

    # Each net is an update block. Readers are actually "written" here.
    #   s.net_reader1 = s.net_writer
    #   s.net_reader2 = s.net_writer
    # Collect readers in normal update blocks plus the writers in nets.

    all_reads = set()

    # First add normal update block reads
    for read in m._read_upblks:
      obj = m._id_obj[ read ]
      while obj:
        all_reads.add( id(obj) )
        obj = obj._nested

    # Then add net writers and top level output ports in the net!
    for writer, readers in nets:
      obj = writer
      while obj:
        all_reads.add( id(obj) )
        obj = obj._nested

      for reader in readers:
        if isinstance( reader, OutVPort ) and reader._host == m:
          obj = reader
          while obj:
            all_reads.add( id(obj) )
            obj = obj._nested

    # Now figure out if a reader can be safely removed from the net
    # Check if the reader itself, its ancestors, or sibling slices are
    # read somewhere else. If not, the reader can be moved from the net.

    for i in xrange(len(nets)):
      writer, readers = nets[i]
      new_readers = []

      for x in readers:
        flag = False
        obj = x
        while obj:
          if id(obj) in all_reads:
            flag = True
            break
          obj = obj._nested

        if x._slice:
          for obj in x._nested._slices.values(): # Check sibling slices
            if x != obj and _overlap(obj._slice, x._slice) and \
                id(obj) in all_reads:
              flag = True
              break

        if flag: new_readers.append( x ) # is read somewhere else

      nets[i] = (writer, new_readers)

  @staticmethod
  def generate_net_block( m ):

    for writer, readers in m._nets:
      if not readers:
        continue # Aha, the net is dummy

      # special case for const
      wr_lca  = writer._parent if isinstance( writer, Const ) else writer
      rd_lcas = readers[::]

      # Find common ancestor: iteratively go to parent level and check if
      # at the same level all objects' ancestor are the same

      mindep  = min( len( wr_lca._name_idx[1] ),
                     min( [ len(x._name_idx[1]) for x in rd_lcas ] ) )

      # First navigate all objects to the same level deep

      for i in xrange( mindep, len(wr_lca._name_idx[1]) ):
        wr_lca = wr_lca._parent

      for i, x in enumerate( rd_lcas ):
        for j in xrange( mindep, len( x._name_idx[1] ) ):
          x = x._parent
        rd_lcas[i] = x

      # Then iteratively check if their ancestor is the same

      while wr_lca != m:
        succeed = True
        for x in rd_lcas:
          if x != wr_lca:
            succeed = False
            break
        if succeed: break

        wr_lca = wr_lca._parent
        for i in xrange( len(rd_lcas) ):
          rd_lcas[i] = rd_lcas[i]._parent

      lca     = wr_lca # this is the object we want to insert the block to
      lca_len = len( repr(lca) )
      fanout  = len( readers )
      wstr    = repr(writer) if isinstance( writer, Const) \
                else ( "s." + repr(writer)[lca_len+1:] )
      rstrs   = [ "s." + repr(x)[lca_len+1:] for x in readers]

      upblk_name = "{}_FANOUT_{}".format(repr(writer), fanout)\
                    .replace( ".", "_" ).replace( ":", "_" ) \
                    .replace( "[", "_" ).replace( "]", "_" ) \
                    .replace( "(", "_" ).replace( ")", "_" )

      # TODO port common prefix optimization, currently only multi-writer

      # NO @s.update because I don't want to impair the original model
      if fanout == 1: # simple mode!
        gen_connection_src = """

def {0}():
  {1}
blk = {0}

        """.format( upblk_name,"{} = {}".format( rstrs[0], wstr ) )
      else:
        gen_connection_src = """

def {0}():
  common_writer = {1}
  {2}
blk = {0}
        """.format( upblk_name, wstr, "\n  ".join(
                    [ "{} = common_writer".format( x ) for x in rstrs] ) )

      # Collect block metadata

      blk         = lca.compile_update_block( gen_connection_src )
      blk.hostobj = lca
      blk.ast     = ast.parse( gen_connection_src )

      blk_id = id(blk)
      m._blkid_upblk[ blk_id ] = blk

      # Collect read/writer metadata

      m._read_upblks[ id(writer) ].append( blk_id )
      m._id_obj[ id(writer) ] = writer
      for x in readers:
        m._write_upblks[ id(x) ].append( blk_id )
        m._id_obj[ id(x) ] = x
