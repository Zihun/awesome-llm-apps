# UV Migration Guide

This guide explains how to use the new `uv`-based setup for the awesome-llm-apps repository.

## What Changed?

The repository is now a **uv-based monorepo** with centralized dependency management. All projects can share a common virtual environment and dependencies through the root `pyproject.toml`.

## Quick Start

### 1. Install uv

```bash
# macOS and Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

# Or with pip
pip install uv
```

### 2. Set Up the Environment

From the root of the repository:

```bash
# Install core dependencies only
uv sync

# Or install with all optional dependencies
uv sync --all-extras

# Or install specific dependency groups
uv sync --extra agents --extra rag --extra web
```

This creates a `.venv` directory in the root with all dependencies installed.

### 3. Run Any Project

You can now run any project from the root directory:

```bash
# Run a Python script
uv run python rag_tutorials/agentic_rag_embedding_gemma/agentic_rag_embeddinggemma.py

# Run a Streamlit app
uv run streamlit run starter_ai_agents/ai_travel_agent/ai_travel_agent.py

# Navigate to a specific project and run
cd rag_tutorials/agentic_rag_embedding_gemma
uv run streamlit run agentic_rag_embeddinggemma.py
```

## Available Dependency Groups

The `pyproject.toml` defines several optional dependency groups:

- **agents** - AI Agent frameworks (agno, openai-agents, mcp-agent)
- **rag** - RAG and Vector Stores (lancedb, pypdf, faiss-cpu)
- **web** - Web and API tools (firecrawl-py, google-search-results, icalendar)
- **mcp** - MCP agent tools
- **local-llm** - Local LLM support (ollama)
- **dev** - Development tools (pytest, ruff, mypy)
- **all** - All dependencies combined

### Installing Specific Groups

```bash
# Install only RAG dependencies
uv sync --extra rag

# Install agents and MCP dependencies
uv sync --extra agents --extra mcp

# Install everything
uv sync --all-extras
```

## Working with Individual Projects

### Option 1: Use the Shared Environment (Recommended)

All projects can use the shared `.venv` at the root:

```bash
# From the root
uv run python <path-to-script>

# Or from within a project directory
cd starter_ai_agents/ai_travel_agent
uv run streamlit run ai_travel_agent.py
```

### Option 2: Keep Using pip (Legacy)

Individual project `requirements.txt` files are still present. If you prefer, you can still use pip:

```bash
cd starter_ai_agents/ai_travel_agent
pip install -r requirements.txt
python ai_travel_agent.py
```

## Benefits of Using uv

1. **Speed**: 10-100x faster than pip for dependency resolution and installation
2. **Reproducibility**: The `uv.lock` file ensures everyone gets the same versions
3. **Simplicity**: Single command to set up all projects
4. **Compatibility**: Works alongside existing pip/requirements.txt workflows
5. **Disk Space**: Single shared environment instead of many virtualenvs

## Common Commands

```bash
# Sync dependencies (install/update)
uv sync

# Add a new dependency
uv add package-name

# Add to a specific optional group
uv add --optional agents new-agent-framework

# Remove a dependency
uv remove package-name

# Update all dependencies
uv lock --upgrade

# Run a command in the virtual environment
uv run <command>

# Activate the virtual environment manually
source .venv/bin/activate  # Linux/macOS
.venv\Scripts\activate     # Windows
```

## Troubleshooting

### "Package not found"

If you get a package not found error, make sure you've installed the right extras:

```bash
# Check which extras you need
cat pyproject.toml | grep -A 5 "\[project.optional-dependencies\]"

# Install the missing group
uv sync --extra <group-name>
```

### "Python version mismatch"

The project requires Python >= 3.10. Check your version:

```bash
python --version
uv python list  # See Python versions managed by uv
```

### Want to use a specific Python version?

```bash
uv python install 3.11
uv sync --python 3.11
```

### Reset everything

```bash
# Remove virtual environment
rm -rf .venv

# Remove lock file
rm uv.lock

# Start fresh
uv sync
```

## For Contributors

When adding new dependencies to a project:

1. **Update the root `pyproject.toml`** instead of individual `requirements.txt`
2. Choose the appropriate optional dependency group
3. Run `uv sync` to update the lock file
4. Commit both `pyproject.toml` and `uv.lock`

Example:

```bash
# Add a new dependency to the agents group
uv add --optional agents new-package

# Or edit pyproject.toml directly and then:
uv sync
```

## Migration Checklist for Individual Projects

If you're maintaining a specific project and want to fully migrate:

- [x] Root `pyproject.toml` created
- [x] Root `uv.lock` generated
- [x] `.gitignore` updated
- [x] README updated with uv instructions
- [ ] (Optional) Remove individual `requirements.txt` if no longer needed
- [ ] (Optional) Add project-specific instructions to project README

## Resources

- [uv Documentation](https://docs.astral.sh/uv/)
- [uv GitHub Repository](https://github.com/astral-sh/uv)
- [Python Packaging Guide](https://packaging.python.org/)
