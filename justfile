set windows-shell := ["pwsh.exe", "-NoLogo", "-Command"]

# ── Project Configuration ─────────────────────────────────────────────────────

export NAME := "Yahboom MCP"
export DESC := "Industrial ROS 2 control plane"
export VER  := "1.4.0"
export PORT := "10892"
export MODE := "dual"
export HOST := "0.0.0.0"

# ── Dashboard ─────────────────────────────────────────────────────────────────

# Display the SOTA Industrial Dashboard
default:
    @$lines = Get-Content '{{justfile()}}'; \
    Write-Host " [{{NAME}}] {{DESC}} v{{VER}}" -ForegroundColor White -BackgroundColor Cyan; \
    Write-Host '' ; \
    $currentCategory = ''; \
    foreach ($line in $lines) { \
        if ($line -match '^# ── ([^─]+) ─') { \
            $currentCategory = $matches[1].Trim(); \
            Write-Host "`n  $currentCategory" -ForegroundColor Cyan; \
            Write-Host ('  ' + ('─' * 45)) -ForegroundColor Gray; \
        } elseif ($line -match '^# ([^─].+)') { \
            $desc = $matches[1].Trim(); \
            $idx = [array]::IndexOf($lines, $line); \
            if ($idx -lt $lines.Count - 1) { \
                $nextLine = $lines[$idx + 1]; \
                if ($nextLine -match '^([a-z0-9-]+):') { \
                    $recipe = $matches[1]; \
                    $pad = ' ' * [math]::Max(2, (20 - $recipe.Length)); \
                    Write-Host "    $recipe" -ForegroundColor White -NoNewline; \
                    Write-Host "$pad$desc" -ForegroundColor Gray; \
                } \
            } \
        } \
    } \
    Write-Host "`n  [System: HARDENED | Mode: {{MODE}} | Port: {{PORT}}]" -ForegroundColor DarkGray; \
    Write-Host ''

# ── Lifecycle ─────────────────────────────────────────────────────────────────

# Synchronize all dependencies and dev extras
bootstrap:
    uv sync --all-extras

# Workspace sanitization (clean caches and build artifacts)
clean:
    if (Test-Path -Path "__pycache__") { Remove-Item -Recurse -Force "__pycache__" }; \
    if (Test-Path -Path "**/__pycache__") { Get-ChildItem -Path "." -Recurse -Filter "__pycache__" | Remove-Item -Recurse -Force }; \
    if (Test-Path -Path ".pytest_cache") { Remove-Item -Recurse -Force ".pytest_cache" }; \
    if (Test-Path -Path ".coverage") { Remove-Item -Force ".coverage" }; \
    if (Test-Path -Path "htmlcov") { Remove-Item -Recurse -Force "htmlcov" }

# Complete project re-initialization
setup: clean bootstrap
    Write-Host "Project successfully re-initialized." -ForegroundColor Green

# ── Operation ─────────────────────────────────────────────────────────────────

# Start the Yahboom MCP server (Unified Gateway)
serve mode=MODE port=PORT:
    uv run python -m yahboom_mcp.server --mode {{mode}} --port {{port}}

# Start the Yahboom MCP server in stdio mode
stdio:
    uv run python -m yahboom_mcp.server --mode stdio

# Start the SOTA web dashboard
web:
    Set-Location webapp; ./start.ps1

# ── Development ───────────────────────────────────────────────────────────────

# Start server with auto-reload (backend only)
dev:
    uv run uvicorn yahboom_mcp.server:app --reload --port {{PORT}} --host {{HOST}}

# Spawn an interactive Python REPL in the project context
repl:
    uv run python

# Enter the virtual environment shell
shell:
    uv shell

# ── Quality ───────────────────────────────────────────────────────────────────

# Execute comprehensive linting (Ruff)
lint:
    uv run ruff check .
    Set-Location '{{justfile_directory()}}\webapp'
    npx @biomejs/biome ci .

# Execute auto-fixes and formatting
fix:
    uv run ruff check . --fix --unsafe-fixes
    uv run ruff format .
    Set-Location '{{justfile_directory()}}\webapp'
    npx @biomejs/biome check --write .

# Fast quality check (lint + unit tests)
check: lint test-unit

# ── Testing ───────────────────────────────────────────────────────────────────

# Run the complete test suite
test:
    uv run pytest

# Run fast unit tests (no hardware simulation)
test-unit:
    uv run pytest tests/unit/

# Run integration tests (fastapi/bridge sync)
test-integration:
    uv run pytest tests/integration/

# Execute coverage analysis with HTML report
test-cov:
    uv run pytest --cov=yahboom_mcp --cov-report=html
    Write-Host "Coverage report generated in htmlcov/index.html" -ForegroundColor Cyan

# ── Mission Logic ─────────────────────────────────────────────────────────────

# Execute autonomous patrol square mission
patrol seconds="60":
    uv run scripts/run_patrol_square.ps1 {{seconds}}

# Start the embodied AI observation loop
embodied:
    uv run scripts/embodied_loop.py

# ── Diagnosis ─────────────────────────────────────────────────────────────────

# Check robot health and telemetry
health:
    uv run scripts/check_health.py

# Inspect active ROS 2 topics
topics:
    uv run scripts/check_robot_topics.py

# Perform core hardware audit
hw-audit:
    uv run scripts/audit_hardware.py

# Perform camera system audit (v2)
cam-audit:
    uv run scripts/audit_camera_system_v2.py

# ── Discovery ─────────────────────────────────────────────────────────────────

# Execute camera discovery probe (v7)
discover-cam:
    uv run scripts/ultimate_camera_discovery_v7.py

# Discover Yahboom hardware drivers
discover-drivers:
    uv run scripts/discover_yahboom_drivers.py

# ── Deployment ─────────────────────────────────────────────────────────────────

# Deploy cognitive pack to Boomy (Raspbot v2)
deploy-cognitive:
    uv run scripts/deploy_boomy_cognitive.py

# Deploy robot system upgrades
deploy-upgrades:
    uv run scripts/deploy_robot_upgrades.py

# ── Hardening ─────────────────────────────────────────────────────────────────

# Execute Bandit security audit
check-sec:
    uv run bandit -r src/

# Execute dependency security audit
audit-deps:
    uv run safety check
