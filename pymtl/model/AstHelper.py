import re, inspect2, ast
p = re.compile('( *(@|def))')

class DetectVarNames( ast.NodeVisitor ):

  def __init__( self, upblk ):
    self.upblk = upblk

  # Helper function to get the full name containing "s"

  def _get_full_name( self, node ):
    obj_name = []

    # First strip off all slices
    # s.x[1][2].y[i][3]
    slices = []
    while isinstance( node, ast.Subscript ) and isinstance( node.slice, ast.Slice ):
      lower = node.slice.lower
      upper = node.slice.upper
      # If the slice looks like a[i:i+1] where i is variable, I assume it
      # would access the whole variable

      low = up = None

      if isinstance( lower, ast.Num ):
        low = node.slice.lower.n
      elif isinstance( lower, ast.Name ):
        st = lower.id
        if st in self.upblk.func_globals:
          low = self.upblk.func_globals[ v.id ] # TODO check low is int
        else:
          for i, var in enumerate( self.upblk.__code__.co_freevars ):
            if var == lower.id:
              low = self.upblk.__closure__[i].cell_contents
              break

      if isinstance( upper, ast.Num ):
        up = node.slice.upper.n
      elif isinstance( upper, ast.Name ):
        st = upper.id
        if st in self.upblk.func_globals:
          up = self.upblk.func_globals[ v.id ] # TODO check low is int
        else:
          for i, var in enumerate( self.upblk.__code__.co_freevars ):
            if var == upper.id:
              up = self.upblk.__closure__[i].cell_contents
              break

      if low is not None and up is not None:
        slices.append( slice(low, up) )
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
          else:
            for i, var in enumerate( self.upblk.__code__.co_freevars ):
              if var == v.id:
                up = self.upblk.__closure__[i].cell_contents
                break
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

    if slices:
      assert len(slices) == 1, "Multiple slices at the end of s.%s in update block %s" % \
        ( ".".join( [ obj_name[i][0] + "".join(["[%s]" % x for x in obj_name[i][1]]) for i in xrange(len(obj_name)) ] ) \
        +  "[%d:%d]" % (x[0], x[1]), self.upblk.__name__ )

      obj_name[0][1].append( slices[0] )

    obj_name = obj_name[::-1]
    return obj_name

class DetectReadsAndWrites( DetectVarNames ):

  # This function is to extract variables
  def get_obj_name( self, node ):
    obj_name = self._get_full_name( node )

    # We only record s.*
    if obj_name[0][0] != "s":
      return None

    return obj_name[1:] # Unfortunately it's O(n), but I already [::-1] so not that bad

  def enter( self, node, read, write ):
    self.read = []
    self.write = []
    self.visit( node )
    read.extend ( self.read )
    write.extend( self.write )

  def visit_Attribute( self, node ): # s.a.b
    obj_name = self.get_obj_name( node )
    if not obj_name:  return

    pair = (obj_name, node)

    if   isinstance( node.ctx, ast.Load ):
      self.read.append( pair )
    elif isinstance( node.ctx, ast.Store ):
      self.write.append( pair )
    else:
      assert False, type( node.ctx )

  def visit_Subscript( self, node ): # s.a.b[0:3] or s.a.b[0]
    obj_name = self.get_obj_name( node )
    if not obj_name:  return

    pair = (obj_name, node)

    if   isinstance( node.ctx, ast.Load ):
      self.read.append( pair )
    elif isinstance( node.ctx, ast.Store ):
      self.write.append( pair )
    else:
      assert False, type( node.ctx )

    self.visit( node.slice )

class DetectFuncCalls( DetectVarNames ):

  def enter( self, node, calls ):
    self.calls = []
    self.visit( node )
    calls.extend( self.calls )

  def visit_Call( self, node ):
    obj_name = self._get_full_name( node.func )
    if not obj_name:  return

    isself = False # function call

    if obj_name[0][0] == "s":
      obj_name = obj_name[1:]
      isself = True

    self.calls.append( (obj_name, node, isself) )

    for x in node.args:
      self.visit( x )

class DetectMethodCalls( DetectVarNames ):

  def enter( self, node, methods ):
    self.methods = []
    self.visit( node )
    methods.extend( self.methods )

  def visit_Call( self, node ):
    obj_name = self.get_full_name( node.func )
    if not obj_name: return # to check node.func.id

    pair = (obj_name, node)

    self.methods.append( pair )

    for x in node.args:
      self.visit( x )

class CountBranches( DetectVarNames ):

  def enter( self, node ):
    self.num_br = 0
    self.visit( node )
    return self.num_br

  #-----------------------------------------------------------------------
  # Valid ast nodes
  #-----------------------------------------------------------------------

  def visit_If( self, node ):
    self.num_br += 1
    self.visit( node.test )

    for stmt in node.body:
      self.visit( stmt )

    for stmt in node.orelse:
      self.visit( stmt )

  def visit_IfExp( self, node ):
    self.num_br += 1
    self.visit( node.test )
    self.visit( node.body )
    self.visit( node.orelse )

  # A single for is estimated to be 10x of a branch
  def visit_For( self, node ):
    self.num_br += 0
    for stmt in node.body:
      self.visit( stmt )

  def visit_While( self, node ):
    self.num_br += 0
    for stmt in node.body:
      self.visit( stmt )

def extract_read_write( f, read, write ):

  # Traverse the ast to extract variable writes and reads
  # First check and remove @s.update and empty arguments
  tree = f.ast
  assert isinstance(tree, ast.Module)
  tree = tree.body[0]
  assert isinstance(tree, ast.FunctionDef)

  for stmt in tree.body:
    DetectReadsAndWrites( f ).enter( stmt, read, write )

def extract_func_calls( f, calls ):

  # Traverse the ast to extract variable writes and reads
  # First check and remove @s.update and empty arguments
  tree = f.ast
  assert isinstance(tree, ast.Module)
  tree = tree.body[0]
  assert isinstance(tree, ast.FunctionDef)

  for stmt in tree.body:
    DetectFuncCalls( f ).enter( stmt, calls )

def count_branches( f ):

  # Traverse the ast to extract variable writes and reads
  tree = f.ast
  assert isinstance(tree, ast.Module)
  assert isinstance(tree.body[0], ast.FunctionDef)

  return CountBranches( f ).enter( tree )

def get_method_calls( tree, upblk, methods ):
  DetectMethodCalls( upblk ).enter( tree, methods )
