from typing import Literal

from posthog.hogql import ast
from posthog.hogql.context import HogQLContext
from posthog.hogql.database import database
from posthog.hogql.parser import parse_expr, parse_select
from posthog.hogql.printer import print_ast
from posthog.hogql.resolver import resolve_symbols


def translate_hogql(query: str, context: HogQLContext, dialect: Literal["hogql", "clickhouse"] = "clickhouse") -> str:
    """Translate a HogQL expression into a Clickhouse expression. Raises if any placeholders found."""
    if query == "":
        raise ValueError("Empty query")

    try:
        if context.select_team_id:
            node = parse_select(query, no_placeholders=True)
            resolve_symbols(node)
            return print_ast(node, context, dialect, stack=[])
        else:
            node = parse_expr(query, no_placeholders=True)
            symbol = ast.SelectQuerySymbol(
                tables={"events": ast.TableSymbol(table=database.events)},
            )
            resolve_symbols(node, symbol)
            return print_ast(node, context, dialect, stack=[ast.SelectQuery(select=[], symbol=symbol)])

    except SyntaxError as err:
        raise ValueError(f"SyntaxError: {err.msg}")
    except NotImplementedError as err:
        raise ValueError(f"NotImplementedError: {err}")
