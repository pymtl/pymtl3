import re, inspect, ast
p = re.compile('( *(@|def))')

class DetectVarNames( ast.NodeVisitor ):

  def __init__( self, upblk ):
    self.upblk = upblk

  def get_full_name( self, node ): # only allow one layer array reference
    obj_name = []

    while hasattr( node, "value" ): # don't record the last "s."
      # s.x[1][2].y[i][3]

      # First strip off all slices [0:32]
      while isinstance( node, ast.Subscript ) and \
            isinstance( node.slice, ast.Slice ):
        # TODO handle slices. Squash them into one, or keep them?
        node = node.value

      # Then strip off all array indices
      num = []
      while isinstance( node, ast.Subscript ) and \
            isinstance( node.slice, ast.Index ):
        v = node.slice.value
        n = "*"

        if   isinstance( v, ast.Num ):
          n = v.n
        elif isinstance( v, ast.Name ): 
          if v.id in self.upblk.func_globals: # Only support global const indexing for now
            n = self.upblk.func_globals[ v.id ]
        else:
          assert isinstance( v, ast.Attribute ), type(v)
          self.visit( v )

        num.append(n)
        node = node.value

      assert isinstance( node, ast.Attribute ), "what the hell?"    
      obj_name.append( (node.attr, num[::-1]) )
      node = node.value

    return obj_name[::-1]

class DetectReadsAndWrites( DetectVarNames ):

  def enter( self, node, read, write ):
    self.read = []
    self.write = []
    self.visit( node )
    read.extend ( self.read )
    write.extend( self.write )

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

class DetectMethodCalls( DetectVarNames ):

  def enter( self, node, methods ):
    self.methods = []
    self.visit( node )
    methods.extend( self.methods )

  def visit_Call( self, node ):

    if not isinstance( node.func, ast.Name ): # filter min,max. Only accept s.x....y()
      obj_name    = self.get_full_name( node.func.value )
      method_name = node.func.attr

      self.methods.append( (obj_name, method_name) )

      # print obj_name,method_name
    # else:
      # print node.func.id

    for x in node.args:
      self.visit( x )

def get_ast_src( func ):
  src = p.sub( r'\2', inspect.getsource( func ) )
  return ast.parse( src ), src

def get_read_write( tree, upblk, read, write ):

  # Traverse the ast to extract variable writes and reads
  # First check and remove @s.update and empty arguments
  assert isinstance(tree, ast.Module)
  tree = tree.body[0]
  assert isinstance(tree, ast.FunctionDef)

  for stmt in tree.body:
    DetectReadsAndWrites( upblk ).enter( stmt, read, write )

def get_method_calls( tree, upblk, methods ):
  DetectMethodCalls( upblk ).enter( tree, methods )
