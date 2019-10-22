"""
========================================================================
AstHelper.py
========================================================================
This file collects PyMTL ast visitors.

Author : Shunning Jiang
Date   : Jan 17, 2018
"""

import ast


class DetectVarNames( ast.NodeVisitor ):

  def __init__( self, upblk ):
    self.upblk   = upblk
    self.globals = upblk.__globals__
    self.closure = {}
    for i, var in enumerate( upblk.__code__.co_freevars ):
      try:  self.closure[ var ] = upblk.__closure__[i].cell_contents
      except ValueError: pass

  # Helper function to get the full name containing "s"

  def _get_full_name( self, node ):

    # We store the name/index linearly, and store the corresponding ast
    # nodes linearly for annotation purpose
    obj_name = []
    nodelist = []

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
        x = lower.id
        if   x in self.closure:
          low = self.closure[ x ]
        elif x in self.globals:
          low = self.globals[ x ] # TODO check low is int

      if isinstance( upper, ast.Num ):
        up = node.slice.upper.n
      elif isinstance( upper, ast.Name ):
        x = upper.id
        if   x in self.closure:
          up = self.closure[ x ]
        elif x in self.globals:
          up = self.globals[ x ] # TODO check low is int

      if low is not None and up is not None:
        slices.append( slice(low, up) )
      # FIXME
      # else:

      nodelist.append( node )
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
          x = v.id
          if   x in self.closure:
            n = self.closure[ x ]
          elif x in self.globals: # Only support global const indexing for now
            n = self.globals[ x ]
        elif isinstance( v, ast.Attribute ): # s.sel, may be constant
          self.visit( v )
        elif isinstance( v, ast.Call ): # int(x)
          for x in v.args:
            self.visit(x)

        num.append(n)

        nodelist.append( node )
        node = node.value

      if   isinstance( node, ast.Attribute ):
        obj_name.append( (node.attr, tuple(num[::-1])) )
      elif isinstance( node, ast.Name ):
        obj_name.append( (node.id, tuple(num[::-1])) )
      elif isinstance( node, ast.Call ): # a.b().c()
        # FIXME?
        return None, None
      else:
        assert isinstance( node, ast.Str ) # filter out line_trace
        return None, None

      nodelist.append( node )

      if not hasattr( node, "value" ):
        break
      node = node.value

    if slices:
      assert len(slices) == 1, "Multiple slices at the end of s.%s in update block %s" % \
        ( ".".join( [ obj_name[i][0] + "".join(["[%s]" % x for x in obj_name[i][1]]) for i in range(len(obj_name)) ] ) \
        +  "[%d:%d]" % (x[0], x[1]), self.upblk.__name__ )
      obj_name[0] = ( obj_name[0][0], obj_name[0][1] + tuple(slices) )

    return tuple(obj_name[::-1]), tuple(nodelist[::-1])

class DetectReadsWritesCalls( DetectVarNames ):

  def __init__( self, upblk, read, write, calls ):
    super().__init__( upblk )
    self.read  = read
    self.write = write
    self.calls = calls

  def enter( self, node ):
    self.visit( node )

  def visit_Attribute( self, node ): # s.a.b
    obj_name, nodelist = self._get_full_name( node )

    if obj_name:
      if   isinstance( node.ctx, ast.Load ):
        self.read.append( (obj_name, nodelist) )
      elif isinstance( node.ctx, ast.Store ):
        self.write.append( (obj_name, nodelist) )

  def visit_Subscript( self, node ): # s.a.b[0:3] or s.a.b[0]
    obj_name, nodelist = self._get_full_name( node )

    if obj_name:
      if   isinstance( node.ctx, ast.Load ):
        self.read.append( (obj_name, nodelist) )
      elif isinstance( node.ctx, ast.Store ):
        self.write.append( (obj_name, nodelist) )
      else:
        raise TypeError( f"Wrong ast node context {type( node.ctx )}" )

      self.visit( node.slice )

  def visit_Call( self, node ):
    obj_name, nodelist = self._get_full_name( node.func )

    if obj_name:
      self.calls.append( (obj_name, nodelist) )

      for x in node.args:
        self.visit( x )

class DetectMethodCalls( DetectVarNames ):

  def __init__( self, upblk, methods ):
    super().__init__( upblk )
    self.methods = methods

  def enter( self, node ):
    self.visit( node )

  def visit_Call( self, node ):
    obj_name = self._get_full_name( node.func )

    if obj_name: # to check node.func.id
      self.methods.append( (obj_name, node) )

      for x in node.args:
        self.visit( x )

def extract_reads_writes_calls( f, tree, read, write, calls ):

  # Traverse the ast to extract variable writes and reads
  # First check and remove @s.update and empty arguments
  assert isinstance(tree, ast.Module)
  tree = tree.body[0]
  assert isinstance(tree, ast.FunctionDef)

  visitor = DetectReadsWritesCalls( f, read, write, calls )
  for stmt in tree.body:
    visitor.enter( stmt )

def get_method_calls( tree, upblk, methods ):
  DetectMethodCalls( upblk, methods ).enter( tree )
