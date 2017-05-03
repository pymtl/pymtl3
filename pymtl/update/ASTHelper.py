import re, inspect2, ast
p = re.compile('( *(@|def))')

class DetectVarNames( ast.NodeVisitor ):

  def __init__( self, upblk ):
    self.upblk = upblk

  def get_full_name( self, node ): # only allow one layer array reference
    obj_name = []

    # First strip off all slices
    # s.x[1][2].y[i][3]
    slices = []
    while isinstance( node, ast.Subscript ) and isinstance( node.slice, ast.Slice ):
      lower = node.slice.lower
      upper = node.slice.upper
      # If the slice looks like a[i:i+1] where i is variable, I assume it
      # would access the whole variable a
      if isinstance( lower, ast.Num ) and isinstance( upper, ast.Num ):
        slices.append( slice(node.slice.lower.n, node.slice.upper.n) )
      # FIXME
      # else:
      node = node.value

    # s.x[1][2].y[i]
    while True:
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
        elif isinstance( v, ast.Attribute ): # s.sel, may be constant
          self.visit( v )
        elif isinstance( v, ast.Call ): # int(x)
          for x in v.args:
            self.visit(x)

        num.append(n)
        node = node.value

      if   isinstance( node, ast.Attribute ):
        obj_name.append( (node.attr, num[::-1]) )
      elif isinstance( node, ast.Name ):
        obj_name.append( (node.id, num[::-1]) )
      elif isinstance( node, ast.Call ): # a.b().c()
        return
      else:
        assert isinstance( node, ast.Str ) # filter out line_trace
        return

      if not hasattr( node, "value" ):
        break
      node = node.value

    if obj_name[-1][0] != "s": # We only record s.*
      return
    obj_name.pop()
    obj_name = obj_name[::-1]

    if slices:
      assert len(slices) == 1, "Multiple slices at the end of s.%s in update block %s" % \
        ( ".".join( [ obj_name[i][0] + "".join(["[%s]" % x for x in obj_name[i][1]]) for i in xrange(len(obj_name)) ] ) \
        +  "[%d:%d]" % (x[0], x[1]), self.upblk.__name__ )

      obj_name[-1][1].append( slices[0] )

    return obj_name

class DetectReadsAndWrites( DetectVarNames ):

  def enter( self, node, read, write ):
    self.read = []
    self.write = []
    self.visit( node )
    read.extend ( self.read )
    write.extend( self.write )

  def visit_Attribute( self, node ): # s.a.b
    obj_name = self.get_full_name( node )
    if not obj_name:  return

    if   isinstance( node.ctx, ast.Load ):
      self.read  += [ obj_name ]
    elif isinstance( node.ctx, ast.Store ):
      self.write += [ obj_name ]
    else:
      assert False, type( node.ctx )

  def visit_Subscript( self, node ): # s.a.b[0:3] or s.a.b[0]
    obj_name = self.get_full_name( node )
    if not obj_name:  return

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
    obj_name = self.get_full_name( node.func )

    if obj_name:
      self.methods.append( obj_name )
    # else:
      # print node.func.id

    for x in node.args:
      self.visit( x )

def get_ast( func ):
  src = p.sub( r'\2', inspect2.getsource( func ) )
  return ast.parse( src )

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
