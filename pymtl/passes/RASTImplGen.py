#========================================================================
# RASTImplGen.py
#========================================================================
# This file generates (1) the implementation of the RAST ASDL defined in
# RAST.asdl which should reside in the same directory as this file and 
# (2) the implementation of RAST visualization pass.
# The generated implementation is printed to RAST.py under the same
# directory. RAST visualization pass is printed to RASTVisualizationPass.py 
# under the same directory
#
# Author : Peitian Pan
# Date   : Jan 2, 2019

class constructor( object ):
  """The class of constructors that make up the node types. name is the name
  of this constructor and should be capitalized. type_list is the list of
  node types of all parameters. field_list is the list of names of all
  parameters. If the constructor does not have any parameters, both lists
  will be None."""
  def __init__( s, name, type_list, field_list ):
    assert name[0].isupper()

    isNone = ( type_list is None ) and ( field_list is None )
    isSameLen = ( not isNone ) and ( len( type_list ) == len( field_list ) )
    assert isNone or isSameLen

    s.name = name
    s.type_list = type_list
    s.field_list = field_list

  def impl_str( s ):
    """Return the implementation of this constructor as a Python class."""
    impl_template =\
"""
class {constr_name}( BaseRAST ):
  def __init__( s{params_name} ):
    {params_assign}

  def __eq__( s, other ):
    if type( s ) != type( other ):
      return False
    {check_equal}return True

  def __ne__( s, other ):
    return not s.__eq__( other )
"""
    if s.type_list is None:
      params_name = ''
      params_assign = 'pass'
      check_equal = ''

    else: 
      # Generate statements for checking sub fields
      eq = []
      for t, f in zip( s.type_list, s.field_list ):
        if s.is_sequence( t ):
          eq.append( 'for x, y in zip( s.{field}, other.{field} ):'.format( field = f ) )
          eq.append( '  if x != y:' )
          eq.append( '    return False' )
        else:
          eq.append( 'if s.{field} != other.{field}:'.format( field = f ) )
          eq.append( '  return False' )

      params_name = ', ' + ', '.join( s.field_list )
      params_assign = '\n    '.join(
        map( lambda x: "s.{field} = {field}".format(field = x), s.field_list )
      )
      check_equal = '\n    '.join( eq ) + '\n    '

    return impl_template.format(
      constr_name = s.name,
      params_name = params_name, 
      params_assign = params_assign,
      check_equal = check_equal
    )

  def viz_impl_str( s ):
    """Return the implementation of the visualization visitor of this
    constructor as a Python function.""" 
    impl_template =\
"""
  def visit_{constr_name}( s, node ):
    s.cur += 1
    local_cur = s.cur

    table_header = '<<TABLE BORDER="0" CELLBORDER="1" CELLSPACING="0"> '
    table_body = '{table_body}'
    table_opt = ''
    table_trail = ' </TABLE>>'

    if isinstance( node.Type, RASTTypeSystem.BaseRASTType ):
      table_opt = ' <TR><TD COLSPAN="2">Type: ' + node.Type.__class__.__name__ + '</TD></TR>'
      for name, obj in node.Type.__dict__.iteritems():
        table_opt += ' <TR><TD>' + name + '</TD><TD>' + str( obj ) + '</TD></TR>'

    label = (table_header + table_body + table_opt + table_trail){label_trail}

    {body}
"""

    # Black box around the text between header and trail
    table_header = '<<TABLE BORDER="0" CELLBORDER="1" CELLSPACING="0"> '
    table_trail = ' </TABLE>>'

    body = []

    if s.type_list is None:
      # No parameter for this RAST node.
      # Just creating a single vertex is enough.

      body.append( "s.g.node( str( s.cur ), label = label )" )
      table_body = '<TR><TD COLSPAN="2">{name}</TD></TR>'.format( name = s.name )

      body_str = '\n    '.join( body )
      body_str = body_str

      label_trail = ''

    else: 
      # 1. Create a vertex corresponding to this RAST node
      # 2. Add edges between this RAST node and all child nodes

      body.append( "s.g.node( str( s.cur ), label = label )" )

      # The top string of vertex label
      table_body = '<TR><TD COLSPAN="2">{name}</TD></TR>'.format( name = s.name )

      # Templates for built-in fields
      built_in_str =\
        '<TR><TD>{type_name}</TD><TD>{{{value}}}</TD></TR>'
      built_in_trail =\
        '.format({built_in_trail_body})'
      built_in_trail_body = []

      # Template for user-defined fields
      customized_str = \
      "s.g.edge( str({s}), str({t}), label = '{edge_label}'{edge_label_trail} )"

      # Process each field of this RAST node
      for t, f in zip( s.type_list, s.field_list ):
        if s.is_built_in( t ):
          # Add this built-in type to the label string
          # Assume built-in types will never have sequence modifier
          built_in = built_in_str.format( type_name = f, value = f )
          built_in_trail_body.append( f + '=node.' + f )
          table_body += ' ' + built_in
        else:
          # Add the user-defined field to the label string
          if s.is_sequence( t ):
            # A sequence of customized types
            indented = []
            indented.append( 'for i, f in enumerate(node.{field}):'.format( 
              field = f 
            ) )
            indented.append( customized_str.format(
              s = 'local_cur',
              t = 's.cur+1',
              edge_label = f + '[{idx}]',
              edge_label_trail = '.format(idx = i)'
            ) )
            indented.append( 's.visit( f )' )
            indented = [indented[0]] + map( lambda x: '  '+x, indented[1:] )
            body = body + indented
          else:
            # A single customized type
            body.append( customized_str.format(
              s = 'local_cur',
              t = 's.cur+1',
              edge_label = f, 
              edge_label_trail = ''
            ) )
            body.append( 's.visit( node.{field} )'.format(
              field = f
            ) )

      if built_in_trail_body == []:
        label_trail = ''
      else:
        label_trail = built_in_trail.format(
          built_in_trail_body = ', '.join( built_in_trail_body )
        )

      body_str = '\n    '.join( body )

    return impl_template.format(
      constr_name = s.name,
      table_body = table_body,
      label_trail = label_trail,
      body = body_str
    )

  def is_built_in( s, type_name ):
    lst = [ 'identifier', 'int', 'object', 'bool', 'string' ]

    for t in lst:
      if type_name.startswith( t ):
        return True

    return False

  def is_sequence( s, type_name ):
    if type_name[-1] == '*':
      return True
    return False

  def __eq__( s, other ):
    if isinstance( other, constructor ):
      return s.name == other.name
    return False

  def __ne__( s, other ):
    return not s.__eq__( other )

def parse_constructor( constr_str ):
  """Return the constructor object that corresponds to the one in the given
  constructor string."""
  if constr_str.find( '(' ) != -1:
    # has parameters
    bracket_idx = constr_str.index( '(' )
    bracket_end_idx = constr_str.index( ')' )
    constr_name = constr_str[ 0 : bracket_idx ]
    params = constr_str[ bracket_idx + 1 : bracket_end_idx ].strip()
    params = params.split( ',' )
    type_list = []
    field_list = []
    for param in params:
      param_lst = param.strip().split()
      type_list.append( param_lst[0] )
      field_list.append( param_lst[1] )
  else: 
    # no parameters
    constr_name = constr_str
    type_list = None
    field_list = None

  return constructor( constr_name, type_list, field_list )

def get_type( type_name ):
  """Return the type of the given node type string (without *? modifier)."""
  if type_name[ -1 ] == '*' or type_name[ -1 ] == '?':
    return type_name[ : -1 ]
  return type_name

def get_constr( module_str, start, end ):
  """Extract and return the constructor string from module_str[start:end];
  also return the first position past the constructor string."""
  constr_start = start
  # Remove leading spaces
  while module_str[ constr_start ] == ' ':
    constr_start += 1

  if module_str.find( '(', start, end ) != -1:
    # this constructor has parameters
    bracket_idx = module_str.find( ')', start, end )
    constr = module_str[ constr_start : bracket_idx+1 ]
    l = bracket_idx + 1
  else: 
    # this constructor has no parameters
    l = constr_start
    while l < end and module_str[ l ] != ' ':
      l += 1
    constr = module_str[ constr_start : l ]

  return constr, l

def implement_module( module_str ):
  """Return a string that implements all constructors in the given module
  string."""
  start = 0
  node_type = set()
  built_in_node_type = set( ['identifier', 'int', 'string', 'bool', 'object'] )
  constr_list = set()
  header_str =\
"""#========================================================================
# RAST.py
#========================================================================
# This file contains the definition of all RAST constructs.
# This file is automatically generated by RASTImplGen.py.
"""
  base_def_str =\
"""
class BaseRAST( object ):
  def __init__( s ):
    pass
"""
  visitor_str =\
"""
#----------------------------------------
# RAST visitor
#----------------------------------------

class RASTNodeVisitor( object ):
  # This visitor uses the same code as the Python AST node visitor
  def visit( self, node, *args ):
      method = 'visit_' + node.__class__.__name__
      visitor = getattr( self, method, self.generic_visit )
      return visitor( node, *args )

  def generic_visit( self, node, *args ):
      for field, value in iter_fields( node ):
          if isinstance( value, list ):
              for item in value:
                  if isinstance( item, AST ):
                      self.visit( item, *args )
          elif isinstance( value, AST ):
              self.visit( value, *args )
"""
  impl_str = header_str + base_def_str

  viz_header_str =\
"""#========================================================================
# RASTVisualizationPass.py
#========================================================================
# Visualize RAST using Graphviz packeage. The output graph is in PDF
# format. 
# This file is automatically generated by RASTImplGen.py.

import os
import RASTTypeSystem

from pymtl import *
from RAST import *
from BasePass import BasePass

from graphviz import Digraph
"""
  viz_class_def_str =\
"""
class RASTVisualizationPass( BasePass ):
  def __call__( s, model ):
    visitor = RASTVisualizationVisitor()

    for blk in model.get_update_blocks():
      visitor.init( blk.__name__ )
      visitor.visit( model._rast[ blk ] )
      visitor.dump()

class RASTVisualizationVisitor( RASTNodeVisitor ):
  def __init__( s ):
    s.output = 'unamed'
    s.output_dir = 'rast-viz'

  def init( s, name ):
    s.g = Digraph( 
      comment = 'RAST Visualization of ' + name,
      node_attr = { 'shape' : 'plaintext' }
    )
    s.blk_name = name
    s.cur = 0

  def dump( s ):
    if not os.path.exists( s.output_dir ):
      os.makedirs( s.output_dir )
    s.g.render( s.output_dir + os.sep + s.blk_name )
"""
  viz_impl_str = viz_header_str + viz_class_def_str

  # parse one node type at a time
  while module_str.find( '=', start ) != -1:
    assign_idx = module_str.find( '=', start )
    node_type_name = module_str[ start : assign_idx ].strip()
    node_type.add( node_type_name )

    # find the boundary of this node type
    boundary = module_str.find( '=', assign_idx + 1 )
    if boundary == -1:
      boundary = len( module_str )

    constructor_start = assign_idx + 1
    # check if there are multiple constructors
    while module_str.find( '|', constructor_start ) != -1:
      constructor_end = module_str.find( '|', constructor_start )
      if constructor_end >= boundary: break

      # parse each possible constructor and move to the next
      constr_str, l = get_constr(
        module_str, constructor_start, constructor_end 
      )
      constr_list.add( parse_constructor( constr_str ) )
      constructor_start = constructor_end + 1

    # one constructor remaining
    constr_str, l = get_constr( module_str, constructor_start, boundary )
    constr_list.add( parse_constructor( constr_str ) )

    start = l
  
  # sanity check
  for constr in constr_list:
    if not constr.type_list is None:
      for constr_type in constr.type_list:
        assert get_type( constr_type ) in node_type.union( built_in_node_type )

  # generate implementation
  for constr in constr_list:
    impl_str += constr.impl_str()
    viz_impl_str += constr.viz_impl_str()

  impl_str += visitor_str

  with open( 'RAST.py', 'w' ) as output:
    output.write( impl_str )

  with open( 'RASTVisualizationPass.py', 'w' ) as output:
    output.write( viz_impl_str )

def extract_module( asdl_str ):
  """Return the module name and the module string of the given asdl 
  string."""
  module_name_start = asdl_str.index( 'module' ) + len( 'module' )
  module_name_end = asdl_str.index( '{' )
  module_str_end = asdl_str.index( '}' )

  module_name = asdl_str[ module_name_start : module_name_end ].strip()
  module_str  = asdl_str[ module_name_end + 1 : module_str_end ].strip()

  return module_name, module_str

# This file should be run first to generate the correct implementation 
# of RAST.
if __name__ == '__main__':
  with open( 'RAST.asdl', 'r') as asdl_file:
    asdl_str = ''
    for line in asdl_file:
      if line.strip().startswith( '--' ) or ( not line.strip() ):
        continue
      asdl_str += line.strip() + ' '

    # RAST module is the first one in the file
    module_name, module_str = extract_module( asdl_str )
    assert module_name == 'RAST'

    implement_module( module_str )
