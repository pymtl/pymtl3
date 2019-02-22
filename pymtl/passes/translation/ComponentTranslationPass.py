#=========================================================================
# ComponentTranslationPass.py
#=========================================================================
# Translation pass for a single RTLComponent instance. 
#
# Author : Shunning Jiang, Peitian Pan
# Date   : Feb 13, 2019

import re, inspect

from pymtl                         import *
from pymtl.dsl                     import ComponentLevel1
from pymtl.passes                  import BasePass, PassMetadata
from pymtl.passes.Helpers          import make_indent
from pymtl.passes.rast             import get_type

from errors                        import TranslationError
from ComponentUpblkTranslationPass import ComponentUpblkTranslationPass

class ComponentTranslationPass( BasePass ):

  def __init__( s, type_env, connections_self_self,
                connections_self_child, connections_child_child ):
    """ store the connections needed in component translation """

    s.component_upblk_translator = ComponentUpblkTranslationPass( type_env )

    s._connections_self_self   = connections_self_self
    s._connections_self_child  = connections_self_child
    s._connections_child_child = connections_child_child

    s.svmodule_template =\
"""//------------------------------------------------------------------------
// PyMTL translation result for component {module_name}
//------------------------------------------------------------------------

module {module_name}
(
  // Input declarations
  {input_decls}

  // Output declarations
  {output_decls}
);

  // Local wire declarations
  {wire_decls}

  // Submodule declarations
  {child_decls}

  // Assignments due to net connection and submodule interfaces
  {assignments}

  // Logic block of {module_name}

{blk_srcs}

endmodule

"""

  def __call__( s, m ):
    """ translates a single RTLComponent instance and returns its source """

    if not '_pass_component_translation' in m.__dict__:
      m._pass_component_translation = PassMetadata()

    module_name = m.__class__.__name__

    connections_self_self   = s._connections_self_self[ m ]
    connections_self_child  = s._connections_self_child[ m ]
    connections_child_child = s._connections_child_child[ m ]

    #---------------------------------------------------------------------
    # Input, output, Wire declarations
    #---------------------------------------------------------------------

    signals = {}
    signal_decl_str = { 'input':[], 'output':[], 'wire':[] }
    signal_prefix = { 'input' : 'input', 'output' : 'output', 'wire' : '' }
    
    # First collect all input/output ports
    signals['input'] = s.collect_ports( m, InVPort )
    signals['output'] = s.collect_ports( m, OutVPort )
    signals['wire'] = s.collect_ports( m, Wire )

    # For in/out ports, generate and append their declarations to the list
    for prefix in [ 'input', 'output', 'wire' ]:
      for name, port in signals[ prefix ]:

        type_str = get_type( port ).type_str()

        signal_decl_str[ prefix ].append(
          '{prefix} {dtype} {vec_size} {name} {dim_size}'.format(
            prefix = signal_prefix[ prefix ],
            dtype = type_str[ 'dtype' ],
            vec_size = type_str[ 'vec_size' ],
            name = name,
            dim_size = type_str[ 'dim_size' ]
        ) )

    input_decls = ',\n  '.join( signal_decl_str[ 'input' ] )

    if signal_decl_str[ 'output' ]:
      input_decls += ','

    output_decls = ',\n  '.join( signal_decl_str[ 'output' ] )

    wire_decls = ';\n  '.join( signal_decl_str[ 'wire' ] )

    if wire_decls:
      wire_decls += ';'

    #---------------------------------------------------------------------
    # Instantiate child components
    #---------------------------------------------------------------------

    child_strs = []

    # TODO: only declare child signals used in the current component

    for c in m.get_child_components():
      child_name = c.get_field_name()

      ifcs = {}
      ifcs_decl_str = { 'input':[], 'output':[] }
      connection_wire = { 'input':[], 'output':[] }
      
      # First collect all input/output ports
      ifcs['input'] = s.collect_ports( c, InVPort )
      ifcs['output'] = s.collect_ports( c, OutVPort )

      # For in/out ports, generate and append their declarations to the list
      for prefix in [ 'input', 'output' ]:
        for name, port in ifcs[ prefix ]:

          fname = name

          type_str = get_type( port ).type_str()

          ifcs_decl_str[ prefix ].append(
            '{dtype} {vec_size} {fname}${name} {dim_size};'.format(
              dtype = type_str[ 'dtype' ],
              vec_size = type_str[ 'vec_size' ],
              fname = child_name,
              name = fname,
              dim_size = type_str[ 'dim_size' ]
          ) )

          connection_wire[ prefix ].append(
            '  .{0:6}( {1}${0} ),'.format( fname, child_name )
          )

      child_strs.extend( ifcs_decl_str[ 'input' ] )
      child_strs.extend( ifcs_decl_str[ 'output' ] )
      child_strs.append( '' )
      child_strs.append( c.__class__.__name__+' '+child_name )
      child_strs.append( '(' )
      child_strs.append( "  // Child component's inputs" )
      child_strs.extend( connection_wire[ 'input' ] )
      child_strs.append( "  // Child component's outputs" )
      child_strs.extend( connection_wire[ 'output' ] )
      child_strs[-2 if not connection_wire['output'] else -1] = \
        child_strs[-2 if not connection_wire['output'] else -1].rstrip(',')
      child_strs.append( ');' )

    child_decls = '\n  '.join( child_strs )

    #---------------------------------------------------------------------
    # Continuous Assignments
    #---------------------------------------------------------------------

    assign_strs = []

    for writer, reader in connections_self_self:
      assign_strs.append( 'assign {} = {};'.\
        format( reader.get_field_name(), writer.get_field_name() ) 
      )

    for writer, reader in connections_child_child:
      assign_strs.append( 'assign {}${} = {}${};'.\
        format(
          reader.get_host_component().get_field_name(),
          reader.get_field_name(), 
          writer.get_host_component().get_field_name(), 
          writer.get_field_name() 
        )
      )

    for writer, reader in connections_self_child:
      if writer.get_host_component() is m:
        assign_strs.append( 'assign {}${} = {};'.\
          format(
            reader.get_host_component().get_field_name(), 
            reader.get_field_name(), 
            writer.get_field_name() 
          )
        )

      else:
        assign_strs.append( 'assign {} = {}${};'.\
          format(
            reader.get_field_name(), 
            writer.get_host_component().get_field_name(), 
            writer.get_field_name() 
          )
        )

    assignments = '\n  '.join( assign_strs )

    #---------------------------------------------------------------------
    # Update blocks
    #---------------------------------------------------------------------

    blks = []

    # Translate all upblks in component m
    s.component_upblk_translator( m )

    # Add the source code and the translated code to blks
    for blk in m.get_update_blocks():
      py_srcs = [ '// PyMTL Upblk Source\n' ]

      inspect_srcs, _ = inspect.getsourcelines( blk )
      for idx, val in enumerate( inspect_srcs ):
        inspect_srcs[ idx ] = '// ' + val

      py_srcs.extend( inspect_srcs )

      hdl_srcs = m._pass_component_upblk_translation.blk_srcs[ blk ]

      make_indent( py_srcs, 1 )
      make_indent( hdl_srcs, 1 )

      blks.append( ''.join( py_srcs ) )
      blks.append( '\n'.join( hdl_srcs ) + '\n' )

    blk_srcs = '\n'.join( blks )


    #---------------------------------------------------------------------
    # Assemble all translated parts
    #---------------------------------------------------------------------

    ret = s.svmodule_template.format( **vars() )

    m._pass_component_translation.component_src = ret

    return ret

  #-------------------------------------------------------------------------
  # collect_ports
  #-------------------------------------------------------------------------

  def collect_ports( s, m, Type ):
    """Return a list of members of m that are or include Type ports"""

    def is_of_type( obj, Type ):
      """Is obj Type or contains Type?"""
      if isinstance( obj, Type ):
        return True
      if isinstance( obj, list ):
        return reduce( lambda x, y: x and is_of_type( y, Type ), obj, True )
      return False

    ret = []
    for name, obj in m.__dict__.iteritems():
      if isinstance( name, basestring ) and not name.startswith( '_' ):
        if is_of_type( obj, Type ):
          ret.append( ( name, obj ) )
    return ret
