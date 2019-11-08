#=========================================================================
# bug_injector.py
#=========================================================================
# A bug injector that recognizes and mutates PyMTL-specific Python AST.
#
# A typical work flow of the injector works as follows:
# 1. The injector takes a json file that specifies a list of target files.
# 2. The injector randomly mutates one file in the list IN PLACE.
# 3. Top level script calls type checking / simulation. The bug injector
#    will print to stdout the line and col which was mutated.
# 4. Use `git reset --hard` to discard the bug injected file.
#
# It's important to have your working directory clean before invoking the
# bug injector, which makes automated testing possbile.
#
# Author : Peitian Pan
# Date:    Nov 7, 2019

import ast
import astunparse
import argparse
import json
import os
from contextlib import contextmanager
from random import randint

class BugInjectionContext:

  def __init__( s ):
    s.all_ctxt = []

  def push( s, node ):
    s._check_valid_context(node)
    s.all_ctxt.append(node)

  def pop( s ):
    assert len(s.all_ctxt) > 0
    s.all_ctxt.pop()

  def _check_valid_context( s, node ):
    assert isinstance(node, (ast.ClassDef, ast.FunctionDef))
    if isinstance(node, ast.ClassDef):
      assert len(s.all_ctxt) == 0
    elif isinstance(node, ast.FunctionDef):
      if node.name == 'construct':
        assert s.is_cur_component()
      else:
        # Take it as update block
        # if not s.is_cur_construct():
        #   import pdb
        #   pdb.set_trace()
        assert s.is_cur_construct()
    else:
      raise AssertionError

  def is_cur_component( s ):
    return len(s.all_ctxt) > 0 and \
           isinstance(s.all_ctxt[-1], ast.ClassDef) and \
           isinstance(s.all_ctxt[-1].bases[0], ast.Name) and \
           s.all_ctxt[-1].bases[0].id == 'Component'

  def is_cur_construct( s ):
    return len(s.all_ctxt) > 0 and \
           isinstance(s.all_ctxt[-1], ast.FunctionDef) and \
           s.all_ctxt[-1].name == 'construct'

  def is_cur_upblk( s ):
    return len(s.all_ctxt) > 0 and \
           isinstance(s.all_ctxt[-1], ast.FunctionDef) and \
           s.all_ctxt[-1].name != 'construct'

@contextmanager
def enter_ctxt( ctxt, node ):
  ctxt.push(node)
  yield ctxt
  ctxt.pop()

class ParametricExprVisitor( ast.NodeVisitor ):

  def __init__( s ):
    s.is_valid = False
    super().__init__()

  def check( s, node ):
    s.is_valid = False
    s.visit( node )
    return s.is_valid

  def visit_Subscript( s, node ):
    if isinstance(node.value, ast.Name) and node.value.id == 'Const' and \
       isinstance(node.slice, ast.Index) and isinstance(node.slice.value, ast.Name) and \
       node.slice.value.id.startswith('Bits'):
      # Target found: Const[BitsN]
      s.is_valid = True

class TargetExtractor( ast.NodeVisitor ):
  """Walk the AST to extract potential targets for mutation."""

  # Currently only injecting bug in assignments in upblks

  def __init__( s ):
    s.ctxt = BugInjectionContext()
    s.mutation_targets = []
    s.param_expr_visitor = ParametricExprVisitor()
    super().__init__()

  def visit_ClassDef( s, node ):
    with enter_ctxt(s.ctxt, node):
      for stmt in node.body:
        s.visit(stmt)

  def visit_FunctionDef( s, node ):
    if node.name == 'line_trace':
      # Nothing to look at inside the line trace method
      return
    with enter_ctxt(s.ctxt, node):
      for stmt in node.body:
        s.visit(stmt)

  def visit_Assign( s, node ):
    if s.ctxt.is_cur_upblk() and s.param_expr_visitor.check(node):
      s.mutation_targets.append(node.value)

def parse_cmdline():
  p = argparse.ArgumentParser()
  p.add_argument( "--input-spec" )
  p.add_argument( "--no-overwrite", action = 'store_true', default = False )
  p.add_argument( "--no-astdump",   action = 'store_true', default = False )

  opts = p.parse_args()
  return opts

# Mutate the AST located in r
def mutate(r, bug):
  extractor = TargetExtractor()
  extractor.visit(r)

  # Randomly pick one target to mutate
  target = extractor.mutation_targets[randint(0, len(extractor.mutation_targets)-1)]

  # Get BitsN
  N = int(target.func.slice.value.id[4:]) + 1
  target.func.slice.value.id = 'Bits' + str(N)

  return target.lineno, target.col_offset

if __name__ == "__main__":
  opts = parse_cmdline()
  print("===============================")

  # Randomly pick one file from the list as target
  with open( opts.input_spec, "r" ) as fd:
    targets = json.load(fd)
    target = targets[randint(0, len(targets)-1)]
    print(f"Chose to mutate {target} out of {len(targets)} targets")

  with open( target, "r" ) as fd:
    tree = ast.parse(fd.read())

  # Pre-mutation AST dump
  if not opts.no_astdump:
    with open( target + ".pre-ast", "w" ) as fd:
      fd.write(astunparse.dump(tree))

  # Mutation here
  lineno, col = mutate(tree, "type-parameter-in-upblk")

  print(f"Mutation happened on line {lineno}, col {col}")
  print(f"  Currently only mutating type parameter inside an upblk")

  # Post-mutation AST dump
  if not opts.no_astdump:
    with open( target + ".post-ast", "w" ) as fd:
      fd.write(astunparse.dump(tree))

  # Write mutated source code to a temporary file
  with open( target + ".tmp", "w" ) as fd:
    fd.write(astunparse.unparse(tree))

  # Rename the tmp file to the overwrite the target
  if not opts.no_overwrite:
    os.rename( target + ".tmp", target )

  print()
