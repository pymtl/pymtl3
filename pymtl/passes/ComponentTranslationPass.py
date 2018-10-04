#--------------------------------------------------------------
# Translation pass for a single RTLComponent instance
# This pass will recursively translate all child components
#--------------------------------------------------------------

from pymtl        import *
from pymtl.model  import ComponentLevel1
from BasePass     import BasePass
from collections  import defaultdict, deque
from errors       import TranslationError

from UpblkTranslationPass import UpblkTranslationPass

import re

svmodule_template = """\
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
  {children_decls}

  // Assignments due to net connection and submodule interfaces
  {assignments}

  // Logic block of {module_name}
  {blk_srcs}

endmodule
"""

class ComponentTranslationPass( BasePass ):

  def __init__( s, connections_self_self, connections_self_child,
                   connections_child_child ):
    """ the connections are needed in recursive component translation """

    s._connections_self_self    = connections_self_self
    s._connections_self_child   = connections_self_child
    s._connections_child_child  = connections_child_child

  def __call__( s, m ):
    """ translates a single RTLComponent instance and returns its source """
    module_name = m.__class__.__name__

    connections_self_self    = s._connections_self_self[ m ]
    connections_self_child   = s._connections_self_child[ m ]
    connections_child_child  = s._connections_child_child[ m ]

    #-------------------------------------------------------------------
    # Input/output declarations
    #-------------------------------------------------------------------

    # Keep track of array ports
    array_port_dict = {}

    input_strs  = gen_sv_signal_name( array_port_dict, 'input ', \
        sorted( m.get_input_value_ports(), key = repr ) )

    output_strs  = gen_sv_signal_name( array_port_dict, 'output ', \
        sorted( m.get_output_value_ports(), key = repr ) )

    input_decls = ',\n  '.join( input_strs )

    if output_strs: input_decls += ','

    output_decls = ',\n  '.join( output_strs )

    #-------------------------------------------------------------------
    # Local wire declarations
    #-------------------------------------------------------------------

    # TODO: dont declare wires that are unused

    array_wire_dict = {}

    wire_strs = gen_sv_signal_name( array_wire_dict, '', \
        sorted( m.get_wires(), key = repr ) )

    wire_decls = ';\n  '.join( wire_strs )
    wire_decls += ';'

    #-------------------------------------------------------------------
    # Instantiate child components
    #-------------------------------------------------------------------

    children_strs = []

    # TODO: only declare children signals used in the current component

    for child in m.get_child_components():
      child_name = child.get_field_name()

      # Turn a child's input ports into temporary signal declaration and
      # wiring in instantiation

      sig_decls   = []
      in_wiring   = []
      out_wiring  = []

      # TODO: align all declarations
      for port in sorted( child.get_input_value_ports(), key=repr ):
        fname = port.get_field_name()
        nbits = port.Type.nbits
        width = '' if nbits == 1 else ' [{}:0]'.format(nbits-1)
        sig_decls.append('logic{} {}${};'.format( width, child_name, fname ))
        in_wiring.append('  .{0:6}( {1}${0} ),'.format( fname, child_name ))

      for port in sorted( child.get_output_value_ports(), key=repr ):
        fname = port.get_field_name()
        nbits = port.Type.nbits
        width = '' if nbits == 1 else ' [{}:0]'.format(nbits-1)
        sig_decls.append('logic{} {}${};'.format( width, child_name, fname ))
        out_wiring.append('  .{0:6}( {1}${0} ),'.format( fname, child_name ))

      children_strs.extend( sig_decls )
      children_strs.append( '' )
      children_strs.append( child.__class__.__name__+' '+child_name)
      children_strs.append( '(' )
      children_strs.append( "  // Child component's inputs" )
      children_strs.extend( in_wiring )
      children_strs.append( "  // Child component's outputs" )
      children_strs.extend( out_wiring )
      children_strs[-2 if not out_wiring else -1].rstrip(',')
      children_strs.append( ');' )

    children_decls = '\n  '.join( children_strs )

    #-------------------------------------------------------------------
    # Assignments
    #-------------------------------------------------------------------

    assign_strs = []

    for writer, reader in connections_self_self:
      assign_strs.append( 'assign {} = {};'.format( reader.get_field_name(), 
                                                    writer.get_field_name() ) 
                        )

    for writer, reader in connections_child_child:
      assign_strs.append( 'assign {}${} = {}${};'.format(
                          reader.get_host_component().get_field_name(),
                          reader.get_field_name(), 
                          writer.get_host_component().get_field_name(), 
                          writer.get_field_name() )
                        )

    for writer, reader in connections_self_child:
      if writer.get_host_component() is m:
        assign_strs.append( 'assign {}${} = {};'.format(
                            reader.get_host_component().get_field_name(), 
                            reader.get_field_name(), 
                            writer.get_field_name() )
                          )

      else:
        assign_strs.append( 'assign {} = {}${};'.format(
                            reader.get_field_name(), 
                            writer.get_host_component().get_field_name(), 
                            writer.get_field_name() )
                          )

    assignments = '\n  '.join( assign_strs )

    #-------------------------------------------------------------------
    # Update blocks
    #-------------------------------------------------------------------

    blk_srcs = UpblkTranslationPass()( m )

    #-------------------------------------------------------------------
    # Assemble all translated parts
    #-------------------------------------------------------------------

    ret =  svmodule_template.format( **vars() )

    #-------------------------------------------------------------------
    # Append the source code of child components at the end 
    #-------------------------------------------------------------------

    for obj in sorted( m.get_child_components(), key = repr ):
      ret += ComponentTranslationPass(
            s._connections_self_self, 
            s._connections_self_child, 
            s._connections_child_child
          )( obj )

    return ret

#--------------------------------------------------------------
# Helper functions
#--------------------------------------------------------------

def gen_sv_signal_name( array_dict, direction, ports ):
  """ generate in/out port declarations """
  ret = []

  # Collect all array ports
  for port in ports:
    if '[' in port._my_name:
      # Speical treatment for lists
      array_name    = get_array_name( port._my_name )
      array_idx     = get_array_idx( port._my_name )
      try: 
        array_range = array_dict[ array_name ]
      except KeyError:
        array_range = 1
      array_dict[ array_name ] = max( array_idx + 1, array_range )

  # Generate signal declarations for all ports
  for port in ports:
    name = port._my_name
    nbits = port.Type.nbits
    width = '' if nbits == 0 else ' [{}:0]'.format( nbits - 1 )
    if not '[' in name:
      # Not a list
      ret.append('{direction}logic{width} {name}'.format(**locals()))
    else:
      # Only generate 1 port declarartion for a series of array ports
      if get_array_idx( name ) == 0:    # e.g. in_[0]
        name = get_array_name( name )
        array_range = str( array_dict[ name ] )
        ret.append('{direction}logic{width} {name}[{array_range}]'.\
            format( **locals() ) )

  return ret

def to_sv_name( name ):
  if '[' in name: 
    # Special treatment for a list: in_[1] --> in_$1
    return re.sub( r'\[(\d+)\]', r'$\1', name )
  else:
    return name

def get_array_name( name ):
  return re.sub( r'\[(\d+)\]', '', name )

def get_array_idx( name ):
  m = re.search( r'\[(\d+)\]', name )
  return int( m.group( 1 ) )

