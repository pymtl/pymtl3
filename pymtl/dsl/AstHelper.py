"""
========================================================================
AstHelper.py
========================================================================
This file collects PyMTL ast visitors.

Author : Shunning Jiang
Date   : Jan 17, 2018
"""

from __future__ import absolute_import, division, print_function

import ast


class DetectVarNames( ast.NodeVisitor ):

  def __init__( self, upblk ):
    self.upblk   = upblk
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
        if   x in self.upblk.__globals__:
          low = self.upblk.__globals__[ x ] # TODO check low is int
        elif x in self.closure:
          low = self.closure[ x ]

      if isinstance( upper, ast.Num ):
        up = node.slice.upper.n
      elif isinstance( upper, ast.Name ):
        x = upper.id
        if   x in self.upblk.__globals__:
          up = self.upblk.__globals__[ x ] # TODO check low is int
        elif x in self.closure:
          up = self.closure[ x ]

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
          if   x in self.upblk.__globals__: # Only support global const indexing for now
            n = self.upblk.__globals__[ x ]
          elif x in self.closure:
            n = self.closure[ x ]
        elif isinstance( v, ast.Attribute ): # s.sel, may be constant
          self.visit( v )
        elif isinstance( v, ast.Call ): # int(x)
          for x in v.args:
            self.visit(x)

        num.append(n)

        nodelist.append( node )
        node = node.value

      if   isinstance( node, ast.Attribute ):
        obj_name.append( (node.attr, num[::-1]) )
      elif isinstance( node, ast.Name ):
        obj_name.append( (node.id, num[::-1]) )
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
        ( ".".join( [ obj_name[i][0] + "".join(["[%s]" % x for x in obj_name[i][1]]) for i in xrange(len(obj_name)) ] ) \
        +  "[%d:%d]" % (x[0], x[1]), self.upblk.__name__ )

      obj_name[0][1].append( slices[0] )

    obj_name = obj_name[::-1]
    nodelist = nodelist[::-1]
    return obj_name, nodelist

class DetectReadsWritesCalls( DetectVarNames ):

  def enter( self, node, read, write, calls ):
    self.read = []
    self.write = []
    self.calls = []
    self.visit( node )
    read.extend ( self.read )
    write.extend( self.write )
    calls.extend( self.calls )

  def visit_Attribute( self, node ): # s.a.b
    obj_name, nodelist = self._get_full_name( node )
    if not obj_name:  return

    pair = (obj_name, nodelist)

    if   isinstance( node.ctx, ast.Load ):
      self.read.append( pair )
    elif isinstance( node.ctx, ast.Store ):
      self.write.append( pair )
    else:
      assert False, type( node.ctx )

  def visit_Subscript( self, node ): # s.a.b[0:3] or s.a.b[0]
    obj_name, nodelist = self._get_full_name( node )
    if not obj_name:  return

    pair = (obj_name, nodelist)

    if   isinstance( node.ctx, ast.Load ):
      self.read.append( pair )
    elif isinstance( node.ctx, ast.Store ):
      self.write.append( pair )
    else:
      assert False, type( node.ctx )

    self.visit( node.slice )

  def visit_Call( self, node ):
    obj_name, nodelist = self._get_full_name( node.func )
    if not obj_name:  return

    self.calls.append( (obj_name, nodelist) )

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

def extract_reads_writes_calls( f, tree, read, write, calls ):

  # Traverse the ast to extract variable writes and reads
  # First check and remove @s.update and empty arguments
  assert isinstance(tree, ast.Module)
  tree = tree.body[0]
  assert isinstance(tree, ast.FunctionDef)

  for stmt in tree.body:
    DetectReadsWritesCalls( f ).enter( stmt, read, write, calls )

def get_method_calls( tree, upblk, methods ):
  DetectMethodCalls( upblk ).enter( tree, methods )
