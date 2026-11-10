"""Local tool microbenchmarks; no provider, network, or subprocess execution."""

from source.mcp_tools import MCPToolsHandler, get_available_tools


def test_tool_catalog(benchmark):
    tools = benchmark(get_available_tools)
    names = {tool["name"] for tool in tools}
    assert {"read_file", "write_file", "execute_command"} <= names
    assert len(names) == len(tools)
    assert all(isinstance(tool["parameters"], dict) for tool in tools)


def test_allowed_path(benchmark, tmp_path):
    handler = MCPToolsHandler(base_path=str(tmp_path))
    target = tmp_path / "projects" / "example.txt"
    result = benchmark(handler._validate_path, str(target))
    assert result == target.resolve()
