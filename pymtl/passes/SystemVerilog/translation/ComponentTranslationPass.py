#=========================================================================
# ComponentTranslationPass.py
#=========================================================================
# Translation pass for a single RTLComponent instance. 
#
# Author : Shunning Jiang, Peitian Pan
# Date   : Feb 13, 2019

import re, inspect

from pymtl                             import *
from pymtl.passes                      import BasePass, PassMetadata
from pymtl.passes.utility.pass_utility import make_indent

from errors                            import TranslationError
from ComponentUpblkTranslationPass     import ComponentUpblkTranslationPass
from helpers                           import *

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
  // Localparams
  {local_params}

  // Local wire declarations
  {wire_decls}

  // Submodule declarations
  {child_decls}

  // Continuous Assignments
  {assignments}

  // Logic block of {module_name}

{blk_srcs}

endmodule

"""

  def __call__( s, m ):
    """ translates a single RTLComponent instance and returns its source """

    if not '_pass_component_translation' in m.__dict__:
      m._pass_component_translation = PassMetadata()

    module_name = generate_module_name( m )

    connections_self_self   = s._connections_self_self[ m ]
    connections_self_child  = s._connections_self_child[ m ]
    connections_child_child = s._connections_child_child[ m ]

    #---------------------------------------------------------------------
    # Input, output, Wire declarations
    #---------------------------------------------------------------------

    signals = {}
    signal_decl_str = { 'input':[], 'output':[], 'wire':[] }
    signal_prefix = { 'input' : 'input', 'output' : 'output', 'wire' : '' }
    
    # First collect all input/output ports and wires
    signals['input'] = collect_ports( m, InVPort )
    signals['output'] = collect_ports( m, OutVPort )
    signals['wire'] = collect_ports( m, Wire )

    # For in/out ports, generate and append their declarations to the list
    for prefix in [ 'input', 'output', 'wire' ]:
      for name, port in signals[ prefix ]:

        signal_decl_str[ prefix ].append(
          signal_prefix[ prefix ] + ' ' + generate_signal_decl( name, port )
        )

    input_decls = ',\n  '.join( signal_decl_str[ 'input' ] )

    if signal_decl_str[ 'output' ]:
      input_decls += ','

    output_decls = ',\n  '.join( signal_decl_str[ 'output' ] )

    #---------------------------------------------------------------------
    # Instantiate child components
    #---------------------------------------------------------------------

    child_strs = []

    # TODO: only declare child signals used in the current component

    for c in m.get_child_components():
      child_name = c.get_field_name()
      child_name = get_verilog_name( child_name )

      ifcs = {}
      ifcs_decl_str = { 'input':[], 'output':[] }
      connection_wire = { 'input':[], 'output':[] }
      
      # First collect all input/output ports
      ifcs['input'] = collect_ports( c, InVPort )
      ifcs['output'] = collect_ports( c, OutVPort )

      # For in/out ports, generate and append their declarations to the list
      for prefix in [ 'input', 'output' ]:
        for name, port in ifcs[ prefix ]:

          ifcs_decl_str[ prefix ].append(
            generate_signal_decl( child_name + '$' + name, port ) + ';'
          )

          connection_wire[ prefix ].append(
            '  .{0:6}( {1}${0} ),'.format( get_verilog_name(name), child_name )
          )

      child_strs.extend( ifcs_decl_str[ 'input' ] )
      child_strs.extend( ifcs_decl_str[ 'output' ] )
      child_strs.append( '' )
      child_strs.append( generate_module_name(c)+' '+child_name )
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
          get_verilog_name(reader.get_host_component().get_field_name()),
          reader.get_field_name(), 
          get_verilog_name(writer.get_host_component().get_field_name()),
          writer.get_field_name() 
        )
      )

    for writer, reader in connections_self_child:
      if writer.get_host_component() is m:
        assign_strs.append( 'assign {}${} = {};'.\
          format(
            get_verilog_name(reader.get_host_component().get_field_name()),
            reader.get_field_name(), 
            writer.get_field_name() 
          )
        )

      else:
        assign_strs.append( 'assign {} = {}${};'.\
          format(
            reader.get_field_name(), 
            get_verilog_name(writer.get_host_component().get_field_name()),
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
    # Free variables to localparams
    #---------------------------------------------------------------------

    freevars = m._pass_component_upblk_translation.freevars.values()

    local_params = '\n  '.join( freevars )

    #---------------------------------------------------------------------
    # Temporaray variable definitions
    #---------------------------------------------------------------------
    
    tmpvars = m._pass_component_upblk_translation.tmpvars.values()

    for tmpvar_def in tmpvars:
      signal_decl_str[ 'wire' ].append( tmpvar_def )

    wire_decls = ';\n  '.join( signal_decl_str[ 'wire' ] )

    if wire_decls:
      wire_decls += ';'

    #---------------------------------------------------------------------
    # Assemble all translated parts
    #---------------------------------------------------------------------

    ret = s.svmodule_template.format( **vars() )

    m._pass_component_translation.component_src = ret

    return ret
