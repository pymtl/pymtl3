#=========================================================================
# TracingConfigs.py
#=========================================================================
# Author : Shunning Jiang
# Date   : Dec 4, 2019
"""Configuration class of tracing passes"""


from pymtl3.passes.PassConfigs import BasePassConfigs, Checker


class TracingConfigs( BasePassConfigs ):

  Options = {
    "tracing" : 'none',
    "vcd_file_name" : "",
    "method_trace" : True,
  }

  Checkers = {
    'tracing': Checker(
      lambda v: v in ['none', 'vcd', 'text_ascii', 'text_fancy' ],
      "expects a string in ['none', 'vcd', 'text_ascii', 'text_fancy']"
    ),

    'vcd_file_name': Checker(
      condition = lambda v: isinstance(v, str),
      error_msg = "expects a string"
    ),

    'method_trace': Checker(
      condition = lambda v: isinstance(v, bool),
      error_msg = "expects a boolean"
    ),
  }

  PassName = 'passes.tracing.*'
