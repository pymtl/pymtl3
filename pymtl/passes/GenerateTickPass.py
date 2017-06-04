#-------------------------------------------------------------------------
# GenerateTickPass
#-------------------------------------------------------------------------
from pymtl.passes import BasePass
import ast, py

class GenerateTickPass( BasePass ):
  def __init__( self, mode='unroll', dump=False ):
    self.mode = mode
    self.dump = dump

  def execute( self, m ):
    assert hasattr( m, "_serial_schedule" ), "Please apply other passes to generate model._serial_schedule"
    m.tick = self.generate_tick_func( m, self.mode, self.dump )
    return m

  #-------------------------------------------------------------------------
  # generate_tick_func
  #-------------------------------------------------------------------------
  # After we come up with a schedule, we generate a tick function that calls
  # all update blocks. We can do "JIT" here.

  @staticmethod
  def generate_tick_func( m, mode, dump ):
    assert mode in [ 'normal', 'unroll', 'hacky' ]

    schedule = m._serial_schedule

    if mode == 'normal':
      gen_tick_src = """
      def tick_normal():
        for blk in schedule:
          blk()
      """
      def tick_normal():
        for blk in schedule:
          blk()

      ret = tick_normal

    if mode == 'unroll': # Berkin's recipe
      strs = map( "  update_blk{}() # {}".format, xrange( len(schedule) ), \
                                                [ x.__name__ for x in schedule ] )
      gen_tick_src = """
        {}
        def tick_unroll():
          # The code below does the actual calling of update blocks.
          {}

        """.format( "; ".join( map(
                    "update_blk{0} = schedule[{0}]".format,
                        xrange( len( schedule ) ) ) ),
                    "\n          ".join( strs ) )

      exec py.code.Source( gen_tick_src ).compile() in locals()
      ret = tick_unroll

    if mode == 'hacky':

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

    if dump:
      import textwrap
      print
      print "+-------------------------------------------------------------"
      print "+ Tick funtion source"
      print "+-------------------------------------------------------------"
      print
      print textwrap.dedent(gen_tick_src)
      print

    return ret
