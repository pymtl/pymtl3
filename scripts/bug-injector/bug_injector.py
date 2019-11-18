#=========================================================================
# bug_injector.py
#=========================================================================
# A bug injector that recognizes and mutates PyMTL-specific Python AST.
#
# A typical work flow of the injector is as follows:
# 1. The injector takes a json file that specifies a list of target files.
# 2. The injector randomly mutates one file in the list IN PLACE.
# 3. Top level script calls type checking / simulation.
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
from random import randint, sample

BUG_BITWIDTH  = 0
BUG_COMP_ATTR = 1
BUG_PORT_DIR  = 2
BUG_NAME_EXPR = 3
BUG_ATTR_BASE = 4
BUG_CONST     = 5
BUG_OPERATOR  = 6
BUG_SENTINEL  = 7
BUGS = range(BUG_SENTINEL)
BUG_STR = {
    BUG_BITWIDTH  : 'bit width mutation',
    BUG_COMP_ATTR : 'component attribute name mutation',
    BUG_PORT_DIR  : 'port direction mutation',
    BUG_NAME_EXPR : 'name expression mutation',
    BUG_ATTR_BASE : 'attribute base mutation',
    BUG_CONST     : 'constant number mutation',
    BUG_OPERATOR  : 'operator mutation',
}


#-------------------------------------------------------------------------
# Helper functions and classes
#-------------------------------------------------------------------------

class TargetExtractor( ast.NodeVisitor ):

  def __init__( s ):
    s.ctxt = BugInjectionContext()
    s.mutation_targets = []
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


def parse_cmdline():
  p = argparse.ArgumentParser()
  p.add_argument( "--input-spec" )
  p.add_argument( "--no-overwrite", action = 'store_true', default = False )
  p.add_argument( "--no-astdump",   action = 'store_true', default = False )

  opts = p.parse_args()
  return opts


#-------------------------------------------------------------------------
# Bit width mutation
#-------------------------------------------------------------------------
# Randomly find and mutate an occurrence of BitsN inside construct to a
# different bit width.

class BitwidthTargetExtractor( TargetExtractor ):

  def is_int( s, name ):
    try:
      int(name)
      return True
    except ValueError:
      return False

  def is_target( s, name ):
    if not s.ctxt.is_cur_construct():
      return False
    if name.startswith('Bits') and s.is_int(name[4:]):
      return True
    elif name.startswith('b') and s.is_int(name[1:]):
      return True
    return False

  def visit_Name( s, node ):
    name = node.id
    if s.is_target(name):
      s.mutation_targets.append(node)


def mutate_bitwidth(r):
  extractor = BitwidthTargetExtractor()
  extractor.visit(r)

  if not extractor.mutation_targets:
    return False, 0, 0

  # Randomly pick one target to mutate
  target = extractor.mutation_targets[randint(0, len(extractor.mutation_targets)-1)]

  # Get new BitsN
  if target.id.startswith('Bits'):
    _N = int(target.id[4:])
  else:
    _N = int(target.id[1:])
  N = _N+1

  # Mutate
  target.id = 'Bits' + str(N)
  
  print(f"Bits{_N} -> Bits{N}")

  return True, target.lineno, target.col_offset


#-------------------------------------------------------------------------
# Component attribute mutation
#-------------------------------------------------------------------------
# Randomly find and mutate an occurrence of `s.xxxxx` to a different
# attribute.

class CompAttrTargetExtractor( TargetExtractor ):

  def is_target( s, node ):
    if not s.ctxt.is_cur_construct():
      return False
    # check for s.
    base = node.value
    if not isinstance(base, ast.Name) or base.id != 's':
      return False
    return True

  def visit_Attribute( s, node ):
    # this visit will only be called on the top level attribute
    if s.is_target(node):
      s.mutation_targets.append(node)

def mutate_comp_attr(r):
  extractor = CompAttrTargetExtractor()
  extractor.visit(r)

  if len(extractor.mutation_targets) < 2:
    return False, 0, 0

  # Sample two targets; change the attr of first target to attr of the second
  target, to = sample(extractor.mutation_targets, 2)

  print(f"s.{target.attr} -> s.{to.attr}")

  # Mutate
  target.attr = to.attr

  return True, target.lineno, target.col_offset


#-------------------------------------------------------------------------
# Component attribute mutation
#-------------------------------------------------------------------------
# Randomly find and mutate an InPort or OutPort to have a different
# direction.

class PortDirTargetExtractor( TargetExtractor ):

  def is_target( s, name ):
    if not s.ctxt.is_cur_construct():
      return False
    return name in ('InPort', 'OutPort')

  def visit_Name( s, node ):
    if s.is_target(node.id):
      s.mutation_targets.append(node)

def mutate_port_dir(r):
  extractor = PortDirTargetExtractor()
  extractor.visit(r)

  if not extractor.mutation_targets:
    return False, 0, 0

  # Randomly select a target
  target = extractor.mutation_targets[randint(0, len(extractor.mutation_targets)-1)]

  print(f"{target.id} will be flipped")

  # Mutate
  if target.id == "InPort":
    target.id = "OutPort"
  else:
    target.id = "InPort"

  return True, target.lineno, target.col_offset


#-------------------------------------------------------------------------
# Name expression mutation
#-------------------------------------------------------------------------
# Randomly find and mutate a name expression that does not contain PyMTL
# keywords to a different name expression.

class NameExprTargetExtractor( TargetExtractor ):

  pymtl_keywords = [
      'InPort', 'OutPort', 'Wire', 'Component', 'Const',
      'RoundRobinArbiter', 'RoundRobinArbiterEn',
      'Crossbar', 'RegisterFile',
      'Adder', 'And', 'Incrementer', 'LEComp', 'LTComp', 'ZeroComp',
      'Reg', 'RegEn', 'RegEnRst', 'RegRst', 'Mux', 'RShifter', 'LShifter', 'Subtractor',
      'InValRdyIfc', 'OutValRdyIfc',
      'BypassQueue1RTL', 'NormalQueue1RTL', 'NormalQueueRTL', 'PipeQueue1RTL',
      'MemoryFL', 'MemoryCL', 'PipeQueueCL',
      'DeqIfcRTL', 'EnqIfcRTL', 'GetIfcRTL', 'GiveIfcRTL',
      'MemMsgType', 'XcelMsgType',
      'RecvCL2SendRTL', 'RecvIfcRTL', 'RecvRTL2SendCL', 'SendIfcRTL',
  ]

  def is_reserved( s, name ):
    if name.startswith('Bits'):
      return True
    return name in s.pymtl_keywords

  def is_target( s, name ):
    if not s.ctxt.is_cur_construct():
      return False
    return name[0].isupper() and not s.is_reserved(name)

  def visit_Name( s, node ):
    if s.is_target(node.id) and node.id not in s.mutation_targets:
      s.mutation_targets.append(node)

def mutate_name_expr(r):
  extractor = NameExprTargetExtractor()
  extractor.visit(r)

  if len(extractor.mutation_targets) < 2:
    return False, 0, 0

  # Sample two targets and change the name of the first to name of the second
  target, to = sample(extractor.mutation_targets, 2)

  print(f"{target.id} -> {to.id}")

  # Mutate
  target.id = to.id

  return True, target.lineno, target.col_offset


#-------------------------------------------------------------------------
# Attribute base mutation
#-------------------------------------------------------------------------
# Randomly find and mutate a `s.xxxxxx` to `xxxxxx`.

class AttrBaseTargetExtractor( TargetExtractor ):

  def is_target( s, node ):
    if not s.ctxt.is_cur_construct() or not isinstance(node, ast.Attribute):
      return False
    # check for s.
    base = node.value
    if not isinstance(base, ast.Name) or base.id != 's':
      return False
    return True

  def visit_Assign( s, node ):
    if len(node.targets) == 1:
      if s.is_target(node.targets[0]):
        s.mutation_targets.append((node, 'L'))
      if s.is_target(node.value):
        s.mutation_targets.append((node, 'R'))

def mutate_attr_base(r):
  extractor = AttrBaseTargetExtractor()
  extractor.visit(r)

  if not extractor.mutation_targets:
    return False, 0, 0

  # Randomly pick one target
  target, side = extractor.mutation_targets[randint(0, len(extractor.mutation_targets)-1)]

  # Mutate
  if side == 'L':
    print(f"s.{target.targets[0].attr} -> {target.targets[0].attr}")
    target.targets[0] = ast.Name(id=target.targets[0].attr, ctx=ast.Store())
  elif side == 'R':
    print(f"s.{target.value.attr} -> {target.value.attr}")
    target.value = ast.Name(id=target.value.attr, ctx=ast.Load())

  return True, target.lineno, target.col_offset


BUG_HANDLERS =  {
    BUG_BITWIDTH  : mutate_bitwidth,
    BUG_COMP_ATTR : mutate_comp_attr,
    BUG_PORT_DIR  : mutate_port_dir,
    BUG_NAME_EXPR : mutate_name_expr,
    BUG_ATTR_BASE : mutate_attr_base,
}


# Mutate the AST located in r
def mutate(r, bug):
  assert bug in BUG_HANDLERS
  return BUG_HANDLERS[bug](r)


if __name__ == "__main__":
  n_tried = 0
  opts = parse_cmdline()
  print("===============================")

  # Randomly pick one file from the list as target
  with open( opts.input_spec, "r" ) as fd:
    targets = json.load(fd)

  # Loop until a valid bug is generated
  while True:
    if n_tried > 100:
      print(f"Failed to produce a bug after 100 trials!")
      break

    target = targets[randint(0, len(targets)-1)]

    with open( target, "r" ) as fd:
      tree = ast.parse(fd.read())

    # Pre-mutation AST dump
    if not opts.no_astdump:
      with open( target + ".pre-ast", "w" ) as fd:
        fd.write(astunparse.dump(tree))

    # Randomly pick a bug
    bug = randint(0, BUG_SENTINEL-1)
    # bug = BUG_BITWIDTH
    # bug = BUG_COMP_ATTR
    # bug = BUG_PORT_DIR
    # bug = BUG_NAME_EXPR
    # bug = BUG_ATTR_BASE
    # bug = BUG_CONST
    # bug = BUG_OPERATOR

    # Mutation here
    done, lineno, col = mutate(tree, bug)

    if done:
      print(f"Chose to mutate {target} out of {len(targets)} targets")
      print(f"Bug chosen: {BUG_STR[bug]}")
      print(f"Mutation happened on line {lineno}, col {col}")

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
      break

    n_tried += 1
