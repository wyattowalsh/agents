# mcp-audit Delta

## ADDED Requirements

### Requirement: Jupyter MCP opt-in registry integration

The MCP registry SHALL register `jupyter-mcp-server` as an enabled stdio MCP server launched through `scripts/mcphub/jupyter-mcp-server-stdio.sh` with a pinned `jupyter-mcp-server` package, and SHALL expose it only through opt-in MCPHub groups while excluding default `harness`, `tunnel`, and `shared-read` profiles.

#### Scenario: Jupyter MCP launches through fleet wrapper

- **GIVEN** MCPHub renders `jupyter-mcp-server` from `config/mcp-registry.json`
- **WHEN** the server process starts
- **THEN** the launch command SHALL be `bash ${REPO_ROOT}/scripts/mcphub/jupyter-mcp-server-stdio.sh`
- **AND** the wrapper SHALL exec `uvx --from jupyter-mcp-server==<pinned> jupyter-mcp-server`
- **AND** tracked config SHALL reference `JUPYTER_URL` and `JUPYTER_TOKEN` only as env_var placeholders.

#### Scenario: Jupyter MCP group membership is bounded by default exposure

- **GIVEN** managed harness clients default to the `harness` group
- **WHEN** `jupyter-mcp-server` is added to the registry
- **THEN** `jupyter-mcp-server` SHALL be absent from `harness`, `tunnel`, and `shared-read` groups
- **AND** `jupyter-mcp-server` SHALL be present in `notebooks`, `coding`, `heavy`, `credentialed`, and `experimental` as a full server
- **AND** `research` and `review` SHALL expose only bounded read tools (`list_files`, `list_kernels`, `list_notebooks`, `read_notebook`, `read_cell`).

#### Scenario: Jupyter notebook content and kernel execution are high-trust surfaces

- **GIVEN** an agent invokes Jupyter MCP tools against a user-owned JupyterLab
- **WHEN** notebook cells are read or executed
- **THEN** maintainers SHALL document kernel execution tools as arbitrary code execution
- **AND** notebook cell sources and outputs SHALL be treated as untrusted external evidence
- **AND** `JUPYTER_TOKEN` SHALL remain user-owned in `.env.mcphub` only.