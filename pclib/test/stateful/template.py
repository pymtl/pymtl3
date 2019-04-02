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
def update_args():
  pass
  {assign_args}

def update_rets():
  pass
  {assign_rets}

def update_rdy():
  s.{method_name}_rdy = s.model.{method_name}.rdy

def update():
  if s.{method_name}_called:  
    if s.model.{method_name}.rdy:
      s.model.{method_name}.en = 1
    else:
      s.model.{method_name}.en = 0
  else:
    s.model.{method_name}.en = 0
    s.{method_name}_rdy = 0
  s.{method_name}_called = 0


"""

method_tmpl = """

assert method_spec.args.keys() == kwargs.keys()
self.{method}_called = 1
{assign_args}
"""

arg_tmpl = """
self.{method}_{arg} = kwargs["{arg}"]
"""

cycle_tmpl = """
def cycle():
  self.model.tick()
  self.model.reset = 0
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
