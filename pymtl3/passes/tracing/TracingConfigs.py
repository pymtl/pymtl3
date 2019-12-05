#=========================================================================
# TracingConfigs.py
#=========================================================================
# Author : Shunning Jiang
# Date   : Dec 4, 2019
"""Configuration class of tracing passes"""


from pymtl3.dsl import Placeholder
from pymtl3.passes.errors import InvalidPassOptionValue
from pymtl3.passes.PassConfigs import BasePassConfigs, Checker
from ..util.utility import expand, get_component_unique_name


class TracingConfigs( BasePassConfigs ):

  Options = {
    "tracing" : 'none',
    "method_trace" : True,
  }

  Checkers = {
    'method_trace': Checker(
      condition = lambda v: isinstance(v, bool),
      error_msg = "expects a boolean"
    ),

    'tracing': (
      lambda v: v in ['none', 'vcd', 'text_ascii', 'text_fancy'],
      "expects a string in ['none', 'vcd', 'text_ascii', 'text_fancy']"
    ),

  PassName = 'passes.tracing.*'
