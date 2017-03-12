import re, inspect, ast
p = re.compile('( *(@|def))')

def get_ast( func ):  
  src = p.sub( r'\2', inspect.getsource( func ) )
  return ast.parse( src )

def get_read_write( tree, upblk, read, write ):
  
  # Traverse the ast to extract variable writes and reads
  # First check and remove @s.update and empty arguments
  assert isinstance(tree, ast.Module)
  tree = tree.body[0]
  assert isinstance(tree, ast.FunctionDef)

  for stmt in tree.body:
    DetectReadsAndWrites().enter( upblk, stmt, read, write )

class DetectReadsAndWrites( ast.NodeVisitor ):

  def __init__( self ):
    self.read = []
    self.write = []

  def enter( self, upblk, node, read, write ):
    self.upblk = upblk
    self.visit( node )
    read.extend ( self.read )
    write.extend( self.write )

  def get_full_name( self, node ): # only allow one layer array reference
    obj_name = []

    while hasattr( node, "value" ): # don't record the last "s."
      if   isinstance( node, ast.Attribute ):
        obj_name.append( (node.attr, "x") )

      else:
        assert isinstance( node, ast.Subscript )

        if isinstance( node.slice, ast.Index ):
          v   = node.slice.value
          num = "*"

          if isinstance( v, ast.Name ): # Only support global const indexing for now
            assert v.id in self.upblk.func_globals, "Global variable %s is undefined!" % v.id
            num = self.upblk.func_globals[ v.id ]
          else:
            assert isinstance( v, ast.Attribute )
            self.visit( v )

          assert isinstance( node.value, ast.Attribute )
          node = node.value
          obj_name.append( (node.attr, num) )

        else:
          assert isinstance( node.slice, ast.Slice )
      node = node.value
    return obj_name[::-1]

  def visit_Attribute( self, node ): # s.a.b
    obj_name = self.get_full_name( node )

    if   isinstance( node.ctx, ast.Load ):
      self.read  += [ obj_name ]
    elif isinstance( node.ctx, ast.Store ):
      self.write += [ obj_name ]
    else:
      assert False, type( node.ctx )

  def visit_Subscript( self, node ): # s.a.b[0:3] or s.a.b[0]
    obj_name = self.get_full_name( node )

    if   isinstance( node.ctx, ast.Load ):
      self.read  += [ obj_name ]
    elif isinstance( node.ctx, ast.Store ):
      self.write += [ obj_name ]
    else:
      assert False, type( node.ctx )
