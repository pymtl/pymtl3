#=========================================================================
# RedundantClkResetRemovalPass.py
#=========================================================================
# Remove unused clk and reset ports in the given component hierarchy.
#
# Author : Peitian Pan
# Date   : Mar 23, 2020

from pymtl3 import Placeholder
from pymtl3.passes.BasePass import BasePass


class RedundantClkResetRemovalPass( BasePass ):

  def __call__( s, top ):

    s.is_clk_used, s.is_reset_used = {}, {}
    s.mark_used( top )
    s.remove_unused( top )

  def mark_used( s, m ):

    subcomps     = m.get_child_components()
    update_ffs   = m.get_update_ff()
    update_mdata = m.get_upblk_metadata()

    if isinstance( m, Placeholder ):
      # We don't deal with placeholder. It should be configured through
      # placeholder configurations.
      s.is_clk_used[m], s.is_reset_used[m] = False, False

    else:
      for child in subcomps:
        s.mark_used( child )

      is_child_clk_used   = any(s.is_clk_used[x] for x in subcomps)
      is_child_reset_used = any(s.is_reset_used[x] for x in subcomps)

      # Component m uses clk if there is an update_ff in m
      is_self_clk_used    = bool( update_ffs )

      # Component m uses reset if there is a read of s.reset
      rd_signals          = update_mdata[0].values()
      is_self_reset_used  = any(m.reset in rd_set for rd_set in rd_signals)

      s.is_clk_used[m]    = is_child_clk_used or is_self_clk_used
      s.is_reset_used[m]  = is_child_reset_used or is_self_reset_used

  def remove_unused( s, m ):

    if not s.is_clk_used[m]:
      del m.clk

    if not s.is_reset_used[m]:
      del m.reset

    for child in m.get_child_components():
      s.remove_unused( child )
