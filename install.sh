#!/usr/bin/env bash
set -euo pipefail

# Claude SEO Installer
# Wraps everything in main() to prevent partial execution on network failure

main() {
    SKILL_DIR="${HOME}/.claude/skills/seo"
    AGENT_DIR="${HOME}/.claude/agents"

    # Detect if running from local repo (Next SEO) or installing from remote (upstream)
    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    if [ -f "${SCRIPT_DIR}/CHANGELOG.md" ] && [ -d "${SCRIPT_DIR}/skills/seo-images-manager" ]; then
        # Local installation (Next SEO fork with new features)
        INSTALL_MODE="local"
        LOCAL_REPO="${SCRIPT_DIR}"
        echo "════════════════════════════════════════"
        echo "║   Claude Next SEO - Installer        ║"
        echo "║   v1.1.0 - GSC Integration           ║"
        echo "════════════════════════════════════════"
    else
        # Remote installation (upstream Claude SEO)
        INSTALL_MODE="remote"
        REPO_URL="https://github.com/AgriciDaniel/claude-seo"
        REPO_TAG="${CLAUDE_SEO_TAG:-v1.9.0}"
        echo "════════════════════════════════════════"
        echo "║   Claude SEO - Installer             ║"
        echo "║   Claude Code SEO Skill              ║"
        echo "════════════════════════════════════════"
    fi
    echo ""

    # Check prerequisites
    command -v python3 >/dev/null 2>&1 || { echo "✗ Python 3 is required but not installed."; exit 1; }
    command -v git >/dev/null 2>&1 || { echo "✗ Git is required but not installed."; exit 1; }

    # Check Python version (3.10+ required)
    PYTHON_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
    PYTHON_OK=$(python3 -c 'import sys; print(1 if sys.version_info >= (3, 10) else 0)')
    if [ "${PYTHON_OK}" = "0" ]; then
        echo "✗ Python 3.10+ is required but ${PYTHON_VERSION} was found."
        exit 1
    fi
    echo "✓ Python ${PYTHON_VERSION} detected"

    # Create directories
    mkdir -p "${SKILL_DIR}"
    mkdir -p "${AGENT_DIR}"

    # Setup source directory based on install mode
    if [ "${INSTALL_MODE}" = "local" ]; then
        echo "→ Installing from local repository (Next SEO v1.1)..."
        SOURCE_DIR="${LOCAL_REPO}"
    else
        # Clone or update from remote
        TEMP_DIR=$(mktemp -d)
        trap "rm -rf ${TEMP_DIR}" EXIT
        echo "↓ Downloading Claude SEO (${REPO_TAG})..."
        git clone --depth 1 --branch "${REPO_TAG}" "${REPO_URL}" "${TEMP_DIR}/claude-seo" 2>/dev/null
        SOURCE_DIR="${TEMP_DIR}/claude-seo"
    fi

    # Copy skill files
    echo "→ Installing skill files..."
    cp -r "${SOURCE_DIR}/skills/seo/"* "${SKILL_DIR}/"

    # Copy sub-skills (including Next SEO exclusive: seo-client, seo-project, seo-wordpress, seo-images-manager)
    if [ -d "${SOURCE_DIR}/skills" ]; then
        echo "→ Installing sub-skills..."
        skill_count=0
        for skill_dir in "${SOURCE_DIR}/skills"/*/; do
            skill_name=$(basename "${skill_dir}")
            target="${HOME}/.claude/skills/${skill_name}"
            mkdir -p "${target}"
            cp -r "${skill_dir}"* "${target}/"
            skill_count=$((skill_count + 1))
        done
        echo "  ✓ Installed ${skill_count} skills"

        # List Next SEO exclusive skills if in local mode
        if [ "${INSTALL_MODE}" = "local" ]; then
            echo ""
            echo "Next SEO Exclusive Skills:"
            [ -d "${HOME}/.claude/skills/seo-client" ] && echo "  ✓ seo-client - Multi-client management"
            [ -d "${HOME}/.claude/skills/seo-project" ] && echo "  ✓ seo-project - Project organization"
            [ -d "${HOME}/.claude/skills/seo-wordpress" ] && echo "  ✓ seo-wordpress - WordPress integration"
            [ -d "${HOME}/.claude/skills/seo-images-manager" ] && echo "  ✓ seo-images-manager - Image SEO with GSC integration (v1.1)"
            echo ""
        fi
    fi

    # Copy schema templates
    if [ -d "${SOURCE_DIR}/schema" ]; then
        mkdir -p "${SKILL_DIR}/schema"
        cp -r "${SOURCE_DIR}/schema/"* "${SKILL_DIR}/schema/"
    fi

    # Copy reference docs
    if [ -d "${SOURCE_DIR}/pdf" ]; then
        mkdir -p "${SKILL_DIR}/pdf"
        cp -r "${SOURCE_DIR}/pdf/"* "${SKILL_DIR}/pdf/"
    fi

    # Copy agents
    echo "→ Installing subagents..."
    cp -r "${SOURCE_DIR}/agents/"*.md "${AGENT_DIR}/" 2>/dev/null || true

    # Copy shared scripts
    if [ -d "${SOURCE_DIR}/scripts" ]; then
        mkdir -p "${SKILL_DIR}/scripts"
        cp -r "${SOURCE_DIR}/scripts/"* "${SKILL_DIR}/scripts/"
        chmod +x "${SKILL_DIR}/scripts/"*.py 2>/dev/null || true
    fi

    # Copy hooks
    if [ -d "${SOURCE_DIR}/hooks" ]; then
        mkdir -p "${SKILL_DIR}/hooks"
        cp -r "${SOURCE_DIR}/hooks/"* "${SKILL_DIR}/hooks/"
        chmod +x "${SKILL_DIR}/hooks/"*.sh 2>/dev/null || true
        chmod +x "${SKILL_DIR}/hooks/"*.py 2>/dev/null || true
    fi

    # Copy extensions (optional add-ons: dataforseo, banana)
    if [ -d "${SOURCE_DIR}/extensions" ]; then
        echo "=> Installing extensions..."
        for ext_dir in "${SOURCE_DIR}/extensions"/*/; do
            [ -d "${ext_dir}" ] || continue
            ext_name=$(basename "${ext_dir}")
            # Extension skills
            if [ -d "${ext_dir}skills" ]; then
                for ext_skill in "${ext_dir}skills"/*/; do
                    [ -d "${ext_skill}" ] || continue
                    ext_skill_name=$(basename "${ext_skill}")
                    target="${HOME}/.claude/skills/${ext_skill_name}"
                    mkdir -p "${target}"
                    cp -r "${ext_skill}"* "${target}/"
                done
            fi
            # Extension agents
            if [ -d "${ext_dir}agents" ]; then
                cp -r "${ext_dir}agents/"*.md "${AGENT_DIR}/" 2>/dev/null || true
            fi
            # Extension references
            if [ -d "${ext_dir}references" ]; then
                mkdir -p "${SKILL_DIR}/extensions/${ext_name}/references"
                cp -r "${ext_dir}references/"* "${SKILL_DIR}/extensions/${ext_name}/references/"
            fi
            # Extension scripts
            if [ -d "${ext_dir}scripts" ]; then
                mkdir -p "${SKILL_DIR}/extensions/${ext_name}/scripts"
                cp -r "${ext_dir}scripts/"* "${SKILL_DIR}/extensions/${ext_name}/scripts/"
            fi
        done
    fi

    # Copy requirements.txt to skill dir so users can retry later
    cp "${SOURCE_DIR}/requirements.txt" "${SKILL_DIR}/requirements.txt" 2>/dev/null || true

    # Install Python dependencies (venv preferred, --user fallback)
    echo "→ Installing Python dependencies..."
    VENV_DIR="${SKILL_DIR}/.venv"
    if python3 -m venv "${VENV_DIR}" 2>/dev/null; then
        "${VENV_DIR}/bin/pip" install --quiet -r "${SOURCE_DIR}/requirements.txt" 2>/dev/null && \
            echo "  ✓ Installed in venv at ${VENV_DIR}" || \
            echo "  ⚠  Venv pip install failed. Run: ${VENV_DIR}/bin/pip install -r ${SKILL_DIR}/requirements.txt"
    else
        pip install --quiet --user -r "${SOURCE_DIR}/requirements.txt" 2>/dev/null || \
        echo "  ⚠  Could not auto-install. Run: pip install --user -r ${SKILL_DIR}/requirements.txt"
    fi

    # Optional: Install Playwright browsers (for screenshot analysis)
    echo "→ Installing Playwright browsers (optional, for visual analysis)..."
    if [ -f "${VENV_DIR}/bin/playwright" ]; then
        "${VENV_DIR}/bin/python" -m playwright install chromium 2>/dev/null || \
        echo "  ⚠  Playwright install failed. Visual analysis will use WebFetch fallback."
    else
        python3 -m playwright install chromium 2>/dev/null || \
        echo "  ⚠  Playwright install failed. Visual analysis will use WebFetch fallback."
    fi

    echo ""
    if [ "${INSTALL_MODE}" = "local" ]; then
        echo "✓ Claude Next SEO v1.1 installed successfully!"
        echo ""
        echo "New in v1.1:"
        echo "  • Google Search Console integration for image keywords"
        echo "  • Opportunity scoring (0-100) for quick wins"
        echo "  • Intelligent 7-day cache (>90% API savings)"
        echo "  • Multi-client/project management"
        echo "  • WordPress REST API integration"
        echo ""
        echo "Usage:"
        echo "  1. Start Claude Code:    claude"
        echo "  2. Setup client:         /seo-client add \"My Client\""
        echo "  3. Setup project:        /seo-project add \"my-client\" \"Project\" https://example.com"
        echo "  4. Run SEO audit:        /seo audit https://example.com"
        echo "  5. Optimize images:      /seo-images-manager analyze"
        echo ""
        echo "Documentation:"
        echo "  • README.md: ${SOURCE_DIR}/README.md"
        echo "  • CHANGELOG.md: ${SOURCE_DIR}/CHANGELOG.md"
        echo "  • GSC Integration: ${HOME}/.claude/skills/seo-images-manager/GSC-INTEGRATION.md"
    else
        echo "✓ Claude SEO installed successfully!"
        echo ""
        echo "Usage:"
        echo "  1. Start Claude Code:  claude"
        echo "  2. Run commands:       /seo audit https://example.com"
        echo ""
        echo "To upgrade to Next SEO (multi-client + GSC):"
        echo "  git clone https://github.com/YOUR-FORK/claude-next-seo"
        echo "  cd claude-next-seo && bash install.sh"
    fi
    echo ""
    echo "Python deps location: ${SKILL_DIR}/requirements.txt"
    [ "${INSTALL_MODE}" = "remote" ] && echo "To uninstall: curl -fsSL ${REPO_URL}/raw/main/uninstall.sh | bash"
}

main "$@"
