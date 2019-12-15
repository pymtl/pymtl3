"""
========================================================================
AutoEvalPass.py
========================================================================
Wrap every top-level value port with @property that calls
eval_combinational automatically.

Author : Shunning Jiang
Date   : Dec 14, 2019
"""
from pymtl3.dsl import MethodPort
from pymtl3.dsl.errors import UpblkCyclicError
from pymtl3.passes.BasePass import BasePass, PassMetadata
from pymtl3.passes.errors import PassOrderError


class AutoEvalPass( BasePass ):

  def __call__( self, top ):
    if not hasattr( top, "eval_combinational" ):
      print("No eval_combinational detected, cannot add auto-eval")
      return

    if len(top.get_input_value_ports()) == 2: # only clock and reset
      print("No top-level ports, no need to add auto-eval")
      return

    top._autoeval = PassMetadata()
    top._autoeval.need_eval_comb = False

    def gen_outport_property( name ):

      def gen_getter( top ):
        # if no eval_comb, we don't do anything
        if not hasattr( top, "eval_combinational" ) or \
           top is not top._dsl.elaborate_top:
          try:
            return getattr( top._dsl, "_"+name )
          except AttributeError:
            return None

        if top._autoeval.need_eval_comb:
          top.eval_combinational()
          top._autoeval.need_eval_comb = False
        return getattr( top._autoeval, name )

      def gen_setter( top, v ):
        if not hasattr( top, "eval_combinational" ) or \
           top is not top._dsl.elaborate_top:
          setattr( top._dsl, "_"+name, v )
        else:
          setattr( top._autoeval, name, v )

      return property(gen_getter).setter(gen_setter)

    def gen_inport_property( name ):

      def gen_getter( top ):
        if not hasattr( top, "eval_combinational" ) or \
           top is not top._dsl.elaborate_top:
          try:
            return getattr( top._dsl, "_"+name )
          except AttributeError:
            return None

        return getattr( top._autoeval, name )

      def gen_setter( top, v ):
        if not hasattr( top, "eval_combinational" ) or \
           top is not top._dsl.elaborate_top:
          setattr( top._dsl, "_"+name, v )
        else:
          setattr( top._autoeval, name, v )
          top._autoeval.need_eval_comb = True

      return property(gen_getter).setter(gen_setter)

    # Has to add @property to class ...
    # # https://stackoverflow.com/a/1355444/6470797

    cls = top.__class__

    # For output value ports, we only need an enhanced property getter

    for p in top.get_output_value_ports():
      field_name = p._dsl.my_name

      setattr( cls, field_name, gen_outport_property( p._dsl.my_name ) )

    for p in top.get_input_value_ports():
      field_name = p._dsl.my_name

      setattr( cls, field_name, gen_inport_property( p._dsl.my_name ) )

    def gen_wrapped_tick( top ):
      tick = top.tick
      def wrapped_tick():
        if top._autoeval.need_eval_comb:
          top._autoeval.need_eval_comb = False
          top.eval_combinational()
        tick()
      return wrapped_tick

    top.tick = gen_wrapped_tick( top )
