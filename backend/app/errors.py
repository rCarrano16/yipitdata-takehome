"""Domain exceptions for the service layer.

The service layer is consumer-agnostic: it does not know whether a REST router
or the MCP server called it. It signals failure with a plain exception, and each
consumer maps that exception to its own protocol (an HTTP status, an MCP error
string).

There is one exception, and on purpose. Field and value validation lives in the
Pydantic request schemas, which raise pydantic.ValidationError on their own, so
the service layer never needs a separate ValidationError. The only failure the
service itself originates is "you asked for something that does not exist".
"""


class NotFoundError(Exception):
    """A requested company or KPI does not exist.

    REST maps this to 404; the MCP tools catch it and return a readable string.
    """
