#-------------------------------------------------------------------------
# GenerateTickPass
#-------------------------------------------------------------------------

from pymtl import *
from pymtl.passes import BasePass
import ast, py

class GenerateTickPass( BasePass ):
  def __init__( self, mode='unroll', dump=False ):
    self.mode = mode
    self.dump = dump

  def apply( self, m ):
    if not hasattr( m, "_serial_schedule" ):
      raise PassOrderError( "_serial_schedule" )

    self.generate_tick_func( m )

  # After we come up with a schedule, we generate a tick function that calls
  # all update blocks. We can do "JIT" here.

  def generate_tick_func( self, m ):
    assert self.mode in [ 'normal', 'unroll', 'unroll_hierarchical', 'hacky' ]

    schedule = m._serial_schedule
    assert schedule, "No update block found in the model"

    if self.mode == 'normal':
      gen_tick_src = """
      def tick_normal():
        for blk in schedule:
          blk()
      """
      def tick_normal():
        for blk in schedule:
          blk()

      ret = tick_normal

    if self.mode == 'unroll': # Berkin's recipe
      strs = map( "  update_blk{}() # {}".format, xrange( len(schedule) ), \
                                                [ x.__name__ for x in schedule ] )
      gen_tick_src = """
        {}
        def tick_unroll():
          # The code below does the actual calling of update blocks.
          {}""".format( "; ".join( map(
                    "update_blk{0} = schedule[{0}]".format,
                        xrange( len( schedule ) ) ) ),
                    "\n          ".join( strs ) )

      exec py.code.Source( gen_tick_src ).compile() in locals()
      ret = tick_unroll

    if self.mode == 'unroll_hierarchical':
      # Hierarchy factor is the maximum number of update blocks per upper
      # level of update block.
      hierarchy_factor = 100
      # Branchiness factor is the maximum factor of branchiness before
      # breaking the update block.
      branchiness_factor = 1

      schedule_names = [ "{} br: {}".format( x.__name__, m._all_meta['br'][id(x)] )
                         for x in schedule ]
      schedule_branchiness = [ m._all_meta['br'][id(x)] for x in schedule ]
      schedule_level = 1

      gen_tick_src =  "try:\n"
      gen_tick_src += "  from pypyjit import dont_trace_here\n"
      gen_tick_src += "except ImportError:\n"
      gen_tick_src += "  pass\n"
      gen_tick_src += "; ".join( map(
                    "update_blk{0}__0 = schedule[{0}]".format,
                    xrange( len( schedule ) ) ) )

      while len( schedule_names ) > 1:

        i = 0
        j = 0
        while i < len( schedule_names ):
          gen_tick_src += "\n\ndef update_blk{}__{}():\n".format(
                  j, schedule_level )
          num_calls_in_this_block = 0

          while i < len( schedule_names ):
            gen_tick_src += "  update_blk{}__{}() # {}\n".format(
                    i, schedule_level - 1, schedule_names[i] )

            branchiness = schedule_branchiness[ i ]
            i += 1
            num_calls_in_this_block += 1

            if num_calls_in_this_block >= hierarchy_factor or \
                  branchiness >= branchiness_factor:
              break

          if schedule_level >= 1:
            gen_tick_src += "\ntry:\n"
            gen_tick_src += \
                "  dont_trace_here(0, False, update_blk{}__{}.__code__)\n" \
                .format( j, schedule_level )
            gen_tick_src += "except NameError:\n"
            gen_tick_src += "  pass\n"

          j += 1

        schedule_level += 1
        schedule_names = [ "" for i in xrange( j ) ]
        schedule_branchiness = [ 0 for i in xrange( j ) ]

      # Rename the top-level update block to tick_top.
      assert len( schedule_names ) == 1
      gen_tick_src += "\ntick_top = update_blk0__{}".format( schedule_level - 1 )

      exec py.code.Source( gen_tick_src ).compile() in locals()
      ret = tick_top

    if self.mode == 'hacky':

      class RewriteSelf(ast.NodeVisitor):
        def visit_Attribute( self, node ):
          if isinstance( node.value, ast.Name ): # s.x
            if node.value.id == "s": # this is not optimized by "common writer"
              node.value.id = "hostobj"
          else:
            self.visit( node.value )

      s        = m
      rewriter = RewriteSelf()

      # Construct a new FunctionDef AST node and the Module wrapper

      newfunc = ast.FunctionDef()
      newfunc.col_offset = 0
      newfunc.lineno     = 0
      newfunc.name = "tick_hacky"
      newfunc.decorator_list = []
      newfunc.body = []
      newfunc.args = ast.arguments()
      newfunc.args.args = []
      newfunc.args.kwarg = None
      newfunc.args.defaults = []
      newfunc.args.vararg = None

      newroot = ast.Module()
      newroot.body = [ newfunc ]

      # Concatenate update block statements

      func_globals = dict()
      for blk in schedule:
        func_globals.update( blk.func_globals )

        hostobj = repr( blk.hostobj )
        root    = blk.ast

        # in the form of:
        # >>> hostobj = s.reg # this is hostobj_stmt
        # >>> hostobj.out = hostobj.in_ # stmt

        if hostobj != "s":
          hostobj_stmt = ast.parse( "hostobj = " + hostobj ).body[0]
          newfunc.body.append( ast.fix_missing_locations( hostobj_stmt ) )

        for stmt in root.body[0].body:
          if hostobj != "s": rewriter.visit( stmt )
          newfunc.body.append( stmt )

      if dump:
        import astor
        gen_tick_src = astor.to_source(newroot)

      exec compile( newroot, "<string>", "exec") in locals()
      tick_hacky.func_globals.update( func_globals )
      ret = tick_hacky

    m._tick_src = gen_tick_src
    m.tick = ret
