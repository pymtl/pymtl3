#=========================================================================
# VerilogTBGenPass.py
#=========================================================================
# Author : Shunning Jiang
# Date   : Mar 18, 2020

import copy
import importlib
import json
import linecache
import os
import shutil
import subprocess
import sys
from importlib import reload
from itertools import cycle
from textwrap import indent
from collections import deque

from pymtl3 import Placeholder
from pymtl3.datatypes import get_nbits
from pymtl3.dsl import Component
from pymtl3.passes.BasePass import BasePass
from pymtl3.passes.rtlir import RTLIRDataType as rdt
from pymtl3.passes.rtlir import RTLIRType as rt
from pymtl3.passes.rtlir import get_component_ifc_rtlir

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

      dut_signal_decls = []

      task_signal_decls = []
      task_assign_strs = []
      task_check_strs = []

      pname_vname_mapping = {}

      for pname, vname, port, is_ifc in x._ports:
        if vname == "reset" or vname == "clk":
          continue
        print(self._get_direction(port), pname, vname, port, is_ifc)

        # Prepare for generating strings

        direction = self._get_direction( port )
        p_n_dim, p_rtype = get_rtype( port )
        dtype = p_rtype.get_dtype()
        if   isinstance( dtype, rdt.Vector ): nbits = dtype.get_length()
        elif isinstance( dtype, rdt.Struct ): nbits = get_nbits(dtype.get_class())

        # signal_decls
        signal_decl_indices = " ".join( [ f"[0:{d-1}]" for d in p_n_dim ] )
        signal_decls.append( f"logic [{nbits-1}:0] {vname} {signal_decl_indices}" )

        # dut_signal_decls
        dut_signal_decls.append( f".{vname}({vname})" )

        # task related strs
        prefix = "inp_" if direction == "input" else "ref_"

        Q = deque( [ (vname, vname, p_n_dim) ] )
        while Q:
          name, mangled_name, indices = Q.popleft()
          if not indices:
            if direction == "input":
              task_signal_decls.append( f"input logic [{nbits-1}:0] inp_{mangled_name}" )
              task_assign_strs.append( f"{name} = inp_{mangled_name}")
            else: # output
              task_signal_decls.append( f"input logic [{nbits-1}:0] ref_{mangled_name}" )
              task_check_strs.append( f"if ({name} != ref_{mangled_name}) $finish")
          else:
            for i in range( indices[0] ):
              Q.append( (f"{name}[{i}]", f"{mangled_name}__{i}", indices[1:]) )

      print()

      dut_name = x._ip_cfg.translated_top_module

      strs = {
        'args_strs': ",".join([f"a{i}" for i in range(len(x._ports))]),
        'harness_name': dut_name + "_tb",
        'signal_decls': ";\n  ".join(signal_decls), # logic [31:0] xxx, -- packed array
        'task_signal_decls': ",\n    ".join(task_signal_decls), # input logic [31:0] in__x;input logic [31:0] ref_y; -- unpacked ports
        'task_assign_strs': ";\n    ".join(task_assign_strs), # x = in__x; -- unpacked
        'task_check_strs': ";\n    ".join(task_check_strs), # ERR( lineno, 'x', x, ref_x ) -- unpacked
        'dut_name': dut_name,
        'dut_clk_decl': '.clk(clk)' if x._ph_cfg.has_clk else '',
        'dut_reset_decl': '.reset(reset)' if x._ph_cfg.has_reset else '',
        'dut_signal_decls': ",\n    ".join(dut_signal_decls), # logic [31:0] xxx, -- packed array, # .x(x), -- packed array
        'test_cases_file_name': '',
      }

      print()
      for x,y in strs.items():
        print(repr(x),y)

      template_name = os.path.dirname( os.path.abspath( __file__ ) ) + \
                      os.path.sep + 'verilog_tbgen.v.template'

      with open(template_name) as template:
        with open( dut_name + "_tb.v", 'w' ) as output:
          template = template.read()
          output.write( template.format( **strs ) )

  def collect_sig_func( self, top ):

    # TODO use actual nets to reduce the amount of saved signals

    # Give all ' and " characters a preceding backslash for .format
    wav_srcs = []

    # Now we create per-cycle signal value collect functions
    for x in top._dsl.all_signals:
      if x.is_top_level_signal() and ( not repr(x).endswith('.clk') or x is top.clk ):
        if is_bitstruct_class( x._dsl.Type ):
          wav_srcs.append( "wavmeta.text_sigs['{0}'].append( to_bits({0}).bin() )".format(x) )
        elif issubclass( x._dsl.Type, Bits ):
          wav_srcs.append( "wavmeta.text_sigs['{0}'].append( {0}.bin() )".format(x) )

    wavmeta.text_sigs = defaultdict(list)

    # TODO use integer index instead of dict, should be easy
    src =  """
def dump_wav():
  {}
""".format( "\n  ".join(wav_srcs) )
    s, l_dict = top, {}
    exec(compile( src, filename="temp", mode="exec"), globals().update(locals()), l_dict)
    return l_dict['dump_wav']

  def _get_direction( s, port ):
    if isinstance( port, rt.Port ):
      return port.get_direction()
    elif isinstance( port, rt.Array ):
      return port.get_sub_type().get_direction()
    raise Exception( f"unrecognized direction {d}!" )
