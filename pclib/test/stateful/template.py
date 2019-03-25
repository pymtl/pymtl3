#=========================================================================
# template
#=========================================================================
# Code templates for generating rtl wrappers
#
# Author : Yixiao Zhang
#   Date : March 24, 2019

assign_args_tmpl = """
  s.model.{method_name}.{arg} = s.{method_name}_{arg}
"""

assign_rets_tmpl = """
  s.{method_name}_{ret} = s.model.{method_name}.{ret}
"""

update_tmpl = """
def update():
  {assign_args}
  {assign_rets}
  if s.{method_name}:
    s.{method_name}_rdy = s.model.{method_name}.rdy
    if s.model.{method_name}.rdy:
      s.model.{method_name}.en = 1
    else:
      s.model.{method_name}.en = 0
  else:
    s.model.{method_name}.en = 0
    s.{method_name}_rdy = 0
"""

method_tmpl = """
def method(**kwargs):
  assert method_spec.args.keys() == kwargs.keys()
  self.model.{method} = 1
  {assign_args}
  return result
"""

arg_tmpl = """
  self.model.{method}_{arg} = kwargs["{arg}"]
"""

cycle_tmpl = """
def cycle():
  self.model.tick()
  {assign_rets}
"""

rdy_tmpl = """
  self.results["{method}"].rdy = self.model.{method}_rdy
"""
ret_tmpl = """
  self.results["{method}"].{ret} = self.model.{method}_{ret}
"""

clear_tmpl = """
  self.model.{method} = 0
"""
