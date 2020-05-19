#=========================================================================
# VerilogTBGenPass.py
#=========================================================================
# Author : Shunning Jiang
# Date   : Mar 18, 2020

from collections import deque

import py

from pymtl3.dsl import MetadataKey
from pymtl3.extra.pypy import custom_exec
from pymtl3.passes.BasePass import BasePass
from pymtl3.passes.rtlir import RTLIRDataType as rdt
from pymtl3.passes.rtlir import RTLIRType as rt

from ..errors import VerilogImportError
from ..util.utility import get_rtype
from .verilog_tbgen_v_template import template as tb_template


class VerilogTBGenPass( BasePass ):
  """ We only generate TB if it is imported or translation-imported """

  # TBGenPass pass public pass data

  #: tbgen case name
  #:
  #: Type: ``str``; input
  #:
  #: Default value: ""
  case_name = MetadataKey(str)

  vtbgen_hooks = MetadataKey(list)

  def __call__( self, top ):
    if not top._dsl.constructed:
      raise VerilogImportError( top,
        f"please elaborate design {top} before applying the TBGen pass!" )

    assert not top.has_metadata( self.vtbgen_hooks )

    tbgen_hooks = []
    top.set_metadata( self.vtbgen_hooks, tbgen_hooks )

    tbgen_components = []

    def traverse_hierarchy( m ):
      if m.has_metadata( self.case_name ) and hasattr(m, '_ports'):
        tbgen_components.append( (m, m.get_metadata( self.case_name )) )
      else:
        for child in m.get_child_components():
          traverse_hierarchy( child )

    traverse_hierarchy( top )

    for x, case_name in tbgen_components:

      signal_decls = []
      task_assign_strs = []
      task_signal_decls = []
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
        elif isinstance( dtype, rdt.Struct ): nbits = dtype.get_class().nbits
        else:                                 raise Exception( f"unrecognized data type {d}!" )

        # signal_decls
        signal_decl_indices = " ".join( [ f"[0:{d-1}]" for d in p_n_dim ] )
        signal_decls.append( f"logic [{nbits-1}:0] {vname} {signal_decl_indices}" )

        # dut_signal_decls

        if p_n_dim:
          # https://sutherland-hdl.com/papers/2013-SNUG-SV_Synthesizable-SystemVerilog_paper.pdf
          # chapter 5.2.3
          dut_signal_decls.append( f".{vname}({{ >> {{ {vname} }} }})" )
        else:
          dut_signal_decls.append( f".{vname}({vname})" )

        Q = deque( [ (vname, vname, p_n_dim) ] )
        tot = 0 # This is to keep the same order as pname list
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

      with open( f"{dut_name}_{case_name}_tb.v", 'w' ) as output:
        output.write( tb_template.format(
          args_strs         = ",".join([f"a{i}" for i in range(len(task_signal_decls))]),
          harness_name      = dut_name + "_tb",
          signal_decls      = ";\n  ".join(signal_decls), # logic [31:0] xxx [0:3]; -- unpacked array
          task_signal_decls = ",\n    ".join(task_signal_decls), # input logic [31:0] in__x;input logic [31:0] ref_y; -- unpacked ports
          task_assign_strs  = ";\n    ".join(task_assign_strs), # x = in__x; -- unpacked
          task_check_strs   = ";\n    ".join(task_check_strs), # ERR( lineno, 'x', x, ref_x ) -- unpacked
          dut_name          = dut_name,
          dut_clk_decl      = '.clk(clk)' if x._ph_cfg.has_clk else '',
          dut_reset_decl    = '.reset(reset)' if x._ph_cfg.has_reset else '',
          dut_signal_decls  = ",\n    ".join(dut_signal_decls), # logic [31:0] xxx, -- packed array, # .x(x), -- packed array
          cases_file_name   = f"{dut_name}_{case_name}_tb.v.cases",
        ))

      case_file = open( f"{dut_name}_{case_name}_tb.v.cases", "w" )
      tbgen_hooks.append( self.gen_hook_func( top, x, py_signal_order, case_file ) )

  @staticmethod
  def gen_hook_func( top, x, ports, case_file ):
    port_srcs = [ f"'h{{str(x.{p}.to_bits())}}" for p in ports ]

    src =  """
def dump_case():
  if top.sim_cycle_count() > 2: # skip the 2 cycles of reset
    print(f"`T({});", file=case_file, flush=True)
""".format( ",".join(port_srcs) )
    _locals = {}
    custom_exec( py.code.Source(src).compile(), {'top': top, 'x': x, 'case_file': case_file}, _locals)
    return _locals['dump_case']
