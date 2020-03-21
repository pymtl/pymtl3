#=========================================================================
# VerilogTBGenPass.py
#=========================================================================
# Author : Shunning Jiang
# Date   : Mar 18, 2020

import os
import py
import sys
from collections import deque

from pymtl3.datatypes import to_bits, get_nbits
from pymtl3.passes.BasePass import BasePass, PassMetadata
from pymtl3.passes.rtlir import RTLIRDataType as rdt
from pymtl3.passes.rtlir import RTLIRType as rt
from pymtl3.utils import custom_exec

from ..errors import VerilogImportError
from ..util.utility import (
    expand,
    gen_mapped_ports,
    get_component_unique_name,
    get_rtype,
    make_indent,
    wrap,
)

class VerilogTBGenPass( BasePass ):
  """ We only generate TB if it is imported or translation-imported """

  def __call__( self, top ):
    if not top._dsl.constructed:
      raise VerilogImportError( top,
        f"please elaborate design {top} before applying the import pass!" )

    top._tbgen = PassMetadata()
    top._tbgen.tbgen_hooks = []

    tbgen_components = []

    def traverse_hierarchy( m ):
      if hasattr(m, 'verilog_tbgen') and hasattr(m, '_ports'):
        tbgen_components.append(m)
      else:
        for child in m.get_child_components():
          self.traverse_hierarchy( child )

    traverse_hierarchy( top )

    for x in tbgen_components:

      signal_decls = []
      task_signal_decls = []
      task_assign_strs = []
      task_check_strs = []
      dut_signal_decls = []

      py_signal_order = []

      for pname, vname, port, is_ifc in x._ports:
        if vname == "reset" or vname == "clk":
          continue

        # Prepare for generating strings
        if   isinstance( port, rt.Port ):  direction = port.get_direction()
        elif isinstance( port, rt.Array ): direction = port.get_sub_type().get_direction()
        else:                              raise Exception( f"unrecognized direction {d}!" )

        p_n_dim, p_rtype = get_rtype( port )
        dtype = p_rtype.get_dtype()
        if   isinstance( dtype, rdt.Vector ): nbits = dtype.get_length()
        elif isinstance( dtype, rdt.Struct ): nbits = get_nbits(dtype.get_class())
        else:                                 raise Exception( f"unrecognized data type {d}!" )

        # signal_decls
        signal_decl_indices = " ".join( [ f"[0:{d-1}]" for d in p_n_dim ] )
        signal_decls.append( f"logic [{nbits-1}:0] {vname} {signal_decl_indices}" )

        # dut_signal_decls
        dut_signal_decls.append( f".{vname}({vname})" )

        Q = deque( [ (vname, vname, p_n_dim) ] )
        tot = 0
        while Q:
          name, mangled_name, indices = Q.popleft()
          if not indices:
            pyname = pname[tot]
            if direction == "input":
              task_signal_decls.append( f"input logic [{nbits-1}:0] inp_{mangled_name}" )
              task_assign_strs.append( f"{name} = inp_{mangled_name}")
            else: # output
              task_signal_decls.append( f"input logic [{nbits-1}:0] ref_{mangled_name}" )
              task_check_strs.append( f"`CHECK(lineno, {name}, ref_{mangled_name}, \"{pyname} ({name} in Verilog)\")")
            tot += 1
            py_signal_order.append(pyname)
          else:
            for i in range( indices[0] ):
              Q.append( (f"{name}[{i}]", f"{mangled_name}__{i}", indices[1:]) )

      dut_name = x._ip_cfg.translated_top_module

      strs = {
        'args_strs': ",".join([f"a{i}" for i in range(len(task_signal_decls))]),
        'harness_name': dut_name + "_tb",
        'signal_decls': ";\n  ".join(signal_decls), # logic [31:0] xxx, -- packed array
        'task_signal_decls': ",\n    ".join(task_signal_decls), # input logic [31:0] in__x;input logic [31:0] ref_y; -- unpacked ports
        'task_assign_strs': ";\n    ".join(task_assign_strs), # x = in__x; -- unpacked
        'task_check_strs': ";\n    ".join(task_check_strs), # ERR( lineno, 'x', x, ref_x ) -- unpacked
        'dut_name': dut_name,
        'dut_clk_decl': '.clk(clk)' if x._ph_cfg.has_clk else '',
        'dut_reset_decl': '.reset(reset)' if x._ph_cfg.has_reset else '',
        'dut_signal_decls': ",\n    ".join(dut_signal_decls), # logic [31:0] xxx, -- packed array, # .x(x), -- packed array
        'test_cases_file_name': dut_name+"_tb.v.cases",
      }
      template_name = os.path.dirname( os.path.abspath( __file__ ) ) + \
                      os.path.sep + 'verilog_tbgen.v.template'

      with open(template_name) as template:
        with open( dut_name + "_tb.v", 'w' ) as output:
          template = template.read()
          output.write( template.format( **strs ) )

      case_file = open( dut_name + "_tb.v.cases", "w" )
      top._tbgen.tbgen_hooks.append( self.gen_hook_func( top, py_signal_order, case_file ) )

  @staticmethod
  def gen_hook_func( top, ports, case_file ):
    port_srcs = [ f"{{hex(int(to_bits(top.{p})))}}" for p in ports ]

    src =  """
def dump_case():
  print(f"`T({});", file=case_file)
""".format( ",".join(port_srcs) )
    _locals = {}
    custom_exec( py.code.Source(src).compile(), {'top': top, 'to_bits': to_bits, 'case_file':case_file}, _locals)
    return _locals['dump_case']

