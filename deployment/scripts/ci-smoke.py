"""Exercise HTTP tool behavior against a disposable CI container."""

import json
import os
import sys
import uuid
from urllib.request import Request, urlopen

base_url = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8000"


def request(path, payload=None):
    data = None if payload is None else json.dumps(payload).encode()
    req = Request(
        base_url + path, data=data, headers={"Content-Type": "application/json"}
    )
    with urlopen(req, timeout=10) as response:
        return json.load(response)


# HTTP health is only a response check; database state is checked separately in CI.
assert request("/health")["status"] == "healthy"
names = {tool["name"] for tool in request("/mcp/tools")["local_tools"]}
assert {"read_file", "write_file"} <= names
scratch = os.environ.get("WAYGATE_SCRATCH_DIR", "/app/tmp/tools")
path = f"{scratch}/waygate-smoke-{uuid.uuid4().hex}.txt"
written = request(
    "/mcp/execute",
    {"action": "write_file", "params": {"path": path, "content": "fixture roundtrip"}},
)
assert written["status"] == "success", written
read = request("/mcp/execute", {"action": "read_file", "params": {"path": path}})
assert read["status"] == "success", read
assert read["result"]["content"] == "fixture roundtrip", read
refused = request(
    "/mcp/execute", {"action": "read_file", "params": {"path": "/etc/passwd"}}
)
assert refused["status"] == "error", refused
assert "Path not allowed" in refused["error"], refused
for shared_path in ["/tmp/unrelated-fixture.txt", "/var/tmp/unrelated-fixture.txt"]:
    shared = request(
        "/mcp/execute", {"action": "read_file", "params": {"path": shared_path}}
    )
    assert shared["status"] == "error", shared
    assert "Path not allowed" in shared["error"], shared
unknown = request("/mcp/execute", {"action": "fixture_unknown_tool"})
assert unknown["status"] == "error", unknown
print("PASS: HTTP catalog, file roundtrip, path refusal, unknown-tool refusal")
