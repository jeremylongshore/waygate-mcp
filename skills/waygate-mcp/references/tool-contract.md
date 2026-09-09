# Waygate MCP Tool Contract

This reference records the behavior visible in the Waygate 2.1.0 repository.
Re-check the running server and current source before relying on it as a
deployment guarantee.

## Filesystem tools

- `list_directory` requires a directory path. It accepts a recursive flag and
  glob pattern and returns entries with file metadata.
- `search_files` requires a query. It accepts a path and a search type of
  `content`, `filename`, or `both`.
- `read_file` requires a file path, defaults to UTF-8, and rejects files above
  ten megabytes.
- `write_file` requires a path and content, creates parent directories, and
  rejects content above five megabytes.
- Paths are resolved before comparison with the handler's allowlisted roots.
- The checked-in handler defaults its base path to `/home/jeremy` and derives
  project roots from it. That is not portable configuration.

## Command tool

`execute_command` requires a command string, defaults to a 30-second timeout,
and starts an asynchronous subprocess shell. Its checked-in denylist rejects
substrings including recursive force removal, privilege elevation, permissive
mode changes, filesystem formatting, raw disk writes, common download clients,
netcat, device redirection, and `format`.

A substring denylist is not command isolation. Callers must still use fixed,
bounded commands, safely quote values, avoid destructive or privileged work,
and verify results independently.

## HTTP tool

`http_request` requires a URL. It accepts method, headers, JSON, raw data, and a
timeout. Authentication is supplied by the caller in request headers. The
checked-in handler does not establish a general destination allowlist, so the
skill applies explicit URL and network-destination boundaries.

## Example sequences

For inspection, list the target directory, search narrowly, read only matching
files, and return paths with findings. For an authorized file change, read the
current file, write the minimal replacement, then read it back. Do not use the
command tool to bypass a rejection from a narrower tool.
