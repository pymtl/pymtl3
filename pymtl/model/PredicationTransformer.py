import ast

class TransformationAbort( Exception ):
  pass

class PredicationTransformer( ast.NodeTransformer ):

  def get_and_verify_target_from_assign( self, node ):
    """Given an assign node, verifies the format is s.XXX = YYY, returns
    the target (lvalue), or None if it doesn't fit that format."""

    assert isinstance( node, ast.Assign )
    if len( node.targets ) != 1:
      return None

    target = node.targets[0]
    return target

  def visit_If( self, node ):
    # On an if statement, go through statements

    predications = {}
    predication_targets = {}

    def process_stmt( stmt, predication_key ):
      # Visit the statement.
      transformed_stmt = self.visit( stmt )

      # Ignore pass.
      if isinstance( transformed_stmt, ast.Pass ):
        return

      # After the transformation, there might be multiple statements
      # returned. In that case, just recurse.
      if isinstance( transformed_stmt, list ):
        for transformed_s in transformed_stmt:
          process_stmt( transformed_s, predication_key )
        return

      # Abort if not an assignment or have more than one targets.
      if not isinstance( transformed_stmt, ast.Assign ):
        raise TransformationAbort()

      if len( transformed_stmt.targets ) != 1:
        raise TransformationAbort()

      target = transformed_stmt.targets[0]
      target_dump = ast.dump( target )

      #assert target_dump not in predications
      predication_dict = predications.get( target_dump, {} )

      # If this predication key is already in the predication dict, we
      # abort. As an optimization, we might be able to use value
      # propagation of the old assignment to the new user.
      if predication_key in predication_dict:
        raise TransformationAbort()

      predication_dict[ predication_key ] = transformed_stmt.value
      predications[ target_dump ] = predication_dict
      predication_targets[ target_dump ] = target

      #predications[ target_dump ] = { predication_key : transformed_stmt.value }

    try:
      for stmt in node.body:
        process_stmt( stmt, node.test )

      for stmt in node.orelse:
        # The else clause has the predication key of None.
        process_stmt( stmt, None )

    except TransformationAbort as e:
      # Transformation failed, return the original node.
      return node

    def create_load_attr( node ):
      """Creates an ast.Attr with load context."""
      if not isinstance( node, ast.Attribute ):
        raise TransformationAbort( "create_load_attr can't convert non attributes" )

      return ast.Attribute( value=node.value, attr=node.attr, ctx=ast.Load() )

    stmts = []
    for target_dump, predication_dict in predications.items():

      def add_predication_stmt( body, orelse ):
        target = predication_targets[ target_dump ]

        # The elts are the elements of the list, orelse first because
        # False evaluates to 0.
        elts = [ orelse, body ]

        true = ast.Name( id="True", ctx=ast.Load() )

        slice_ = ast.Index( value=ast.Compare( left=node.test,
                                               ops=[ ast.Eq() ],
                                               comparators=[ true ] ) )
        value = ast.Subscript( value=ast.List( elts=elts, ctx=ast.Load()),
                               slice=slice_,
                               ctx=ast.Load() )
        stmts.append( ast.copy_location( ast.Assign( targets=[target],
                                                     value=value ),
                                         node ) )

      if node.test in predication_dict and None in predication_dict:
        # The first case is where we have both the iftrue and orelse
        # parts. Simply use the appropriate expressions.
        add_predication_stmt( predication_dict[ node.test ],
                              predication_dict[ None ] )

      elif node.test in predication_dict and None not in predication_dict:
        # The second case is we have the iftrue part, but not orelse. In
        # this case orelse can be the target.
        target = predication_targets[ target_dump ]
        add_predication_stmt( predication_dict[ node.test ],
                              create_load_attr( target ) )

      elif node.test not in predication_dict and None in predication_dict:
        # The third case is we only have the orelse part. Then it looks
        # like above.
        target = predication_targets[ target_dump ]
        add_predication_stmt( create_load_attr( target ),
                              predication_dict[ None ] )

      else:
        raise TransformationAbort(
            "Neither node.test nor None is in predication_dict" )

    if len( stmts ) == 0:
      return None
    elif len( stmts ) == 1:
      return stmts[0]
    else:
      return stmts



