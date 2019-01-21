#------------------------------------------------------------------------
# UpblkRASTToASTPass.py
#------------------------------------------------------------------------
# This pass converts RAST back to AST nodes and compile each converted
# node into python source code.
# 
# Still under development. Will remove this line when finished.
# 
# Author : Peitian Pan
# Date   : Jan 18, 2019

import ast
import RAST

from pymtl import *

class UpblkRASTToASTPass( BasePass ):

  def __call__( s, m ):

    visitor = UpblkRASTToASTVisitor( m )

    for blk, rast in m._rast.iteritems():

      m._ast[ blk ] = visitor.enter( blk, rast )

      print ast.dump( m._ast[ blk ] )

class UpblkRASTToASTVisitor( RAST.RASTNodeVisitor ):

  comb_upblk_cnt = 0

  def enter( s, blk, rast ):

    ret = s.visit( rast )

    comb_upblk_cnt += 1

    return ret

  def visit_CombUpblk( s, node ):
    ret = ast.Module( [] )

    ret.body.append( ast.FunctionDef(
      name = ast.Name( 'comb_upblk_' + str( comb_upblk_cnt ) ),
      args = ast.arguments( [], None, None, [] ),
      body = [], 
      decorator_list = [ 
        ast.Attribute( 
          value = ast.Name( id = 's', ctx = ast.Load ),
          attr = 'update',
          ctx = ast.Load
        )
      ]
    ) )

    for stmt in node.stmts:
      ret.body[ 0 ].body.append( s.visit( stmt ) )

    return ret

  def visit_Assign( s, node ):
    ret = ast.Assign( [ s.visit( node.target ) ], s.visit( noode.value ) )

    return ret
