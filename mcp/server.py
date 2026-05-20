"""FastMCP server exposing the KPI estimates data API as MCP tools.

Phase 0 stub. The five read-only tools (search_companies, list_kpis,
get_company_kpis, get_kpi_estimates, get_current_qtd) are implemented in
Phase 4. They import and reuse the backend service layer in-process
(from app.service import ...), so the MCP server never re-implements query
logic and never makes a network hop to the REST API.
"""
