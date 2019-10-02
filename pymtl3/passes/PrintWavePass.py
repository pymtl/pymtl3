from __future__ import absolute_import, division, print_function

import time
from collections import defaultdict
from copy import deepcopy

import py
import sys
from pymtl3.dsl import Const
from pymtl3.passes.BasePass import BasePass, PassMetadata

from .errors import PassOrderError



class PrintWavePass( BasePass ):

  def __call__( self, top ):

    if not hasattr( top._sched, "schedule" ):
      raise PassOrderError( "schedule" )

    if hasattr( top, "_cl_trace" ):
      schedule = top._cl_trace.schedule
    else:
      schedule = top._sched.schedule

    schedule.append( self.print_wav_func( top) )

  def helpprint(self,top):
    char_length = 5
    _tick = u'\u258f'
    _up, _down = u'\u2571', u'\u2572'
    _x, _low, _high = u'\u2573', u'\u005f', u'\u203e'
    _revstart, _revstop = '\x1B[7m', '\x1B[0m'
    if True:

      print("")
      for sig in s._signals:
        if sig != "s.clk" and sig != "s.reset":

          print("")
          print(sig,end="")
          next_char_length = char_length

          prev_val = None
          for val in s._signals[sig]:

            if prev_val is not None:

              if prev_val[0][:3] == '0b0':
                print(_low*char_length,end="")
                if val[1]%5 == 0:
                  print(" ",end = "")
                if val[0][:3] == '0b1':
                  print(_up,end="")
                  next_char_length = char_length - 1
                else:
                  next_char_length = char_length
              elif prev_val[0][:3] == '0b1':
                print(_high*char_length,end="")
                if val[1]%5== 0:
                  print(" ",end="")
                if val[0][:3] == '0b0':
                  print(_down,end = "")
                  next_char_length = char_length - 1
                else:
                  next_char_length = char_length
            prev_val = val


  def print_wav_func(self, top):
    src =  """
def print_wav():



  try:
    # Type check
    {0}
    char_length = 5
    _back = '\033[F'
    _tick = u'\u258f'
    _up, _down = u'\u2571', u'\u2572'
    _x, _low, _high = u'\u2573', u'\u005f', u'\u203e'
    _revstart, _revstop = '\x1B[7m', '\x1B[0m'
    if True:

      print("")
      size=len(s._signals)
      for sig in s._signals:
        if sig != "s.clk" and sig != "s.reset":

          print("")
          print(sig,end="")
          next_char_length = char_length

          prev_val = None
          for val in s._signals[sig]:

            if prev_val is not None:

              if prev_val[0][:3] == '0b0':
                print(_low*char_length,end="")
                if val[1]%5 == 0:
                  print(" ",end = "")
                if val[0][:3] == '0b1':
                  print(_up,end="")
                  next_char_length = char_length - 1
                else:
                  next_char_length = char_length
              elif prev_val[0][:3] == '0b1':
                print(_high*char_length,end="")
                if val[1]%5== 0:
                  print(" ",end="")
                if val[0][:3] == '0b0':
                  print(_down,end = "")
                  next_char_length = char_length - 1
                else:
                  next_char_length = char_length
            prev_val = val
  except Exception:
    raise





  print(size*_back)
""".format("" )

    s, l_dict = top, {}

    exec(compile( src, filename="temp", mode="exec"), globals().update(locals()), l_dict)

    return l_dict['print_wav']
