import re, inspect, ast
p = re.compile('( *(@|def))')

def get_ast( func ):  
  src = p.sub( r'\2', inspect.getsource( func ) )
  return ast.parse( src )

def get_load_store( tree, load, store ):
  
  # Traverse the ast to extract variable writes and reads
  # First check and remove @s.update and empty arguments
  assert isinstance(tree, ast.Module)
  tree = tree.body[0]
  assert isinstance(tree, ast.FunctionDef)

  for stmt in tree.body:
    DetectLoadsAndStores().enter( stmt, load, store )

class DetectLoadsAndStores( ast.NodeVisitor ):

  def __init__( self ):
    self.load = []
    self.store = []

  def enter( self, node, load, store ):
    self.visit( node )
    load.extend ( self.load )
    store.extend( self.store )

  def get_full_name( self, node ):
    obj_name = []
    while hasattr( node, "value" ): # don't record the last "s."
      if isinstance( node, ast.Attribute ):
        obj_name.append( node.attr )
      else:
        assert isinstance( node, ast.Subscript )
      node = node.value
    return obj_name[::-1]

  def visit_Attribute( self, node ): # s.a.b
    obj_name = self.get_full_name( node )

    if   isinstance( node.ctx, ast.Load ):
      self.load  += [ obj_name ]
    elif isinstance( node.ctx, ast.Store ):
      self.store += [ obj_name ]
    else:
      assert False, type( node.ctx )

  def visit_Subscript( self, node ): # s.a.b[0:3] ld/st is in subscript
    obj_name = self.get_full_name( node )

    if   isinstance( node.ctx, ast.Load ):
      self.load  += [ obj_name ]
    elif isinstance( node.ctx, ast.Store ):
      self.store += [ obj_name ]
    else:
      assert False, type( node.ctx )
