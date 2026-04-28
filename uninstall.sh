#!/usr/bin/env bash
set -euo pipefail

main() {
    echo "→ Uninstalling Claude Next SEO..."
    echo ""

    # List of all Next SEO skills (explicit names, no wildcards)
    skills=(
        "seo"
        "seo-audit"
        "seo-backlinks"
        "seo-client"
        "seo-cluster"
        "seo-competitor-pages"
        "seo-content"
        "seo-dataforseo"
        "seo-drift"
        "seo-ecommerce"
        "seo-geo"
        "seo-google"
        "seo-hreflang"
        "seo-image-gen"
        "seo-images"
        "seo-images-manager"
        "seo-local"
        "seo-maps"
        "seo-page"
        "seo-plan"
        "seo-programmatic"
        "seo-project"
        "seo-schema"
        "seo-sitemap"
        "seo-sxo"
        "seo-technical"
        "seo-wordpress"
    )

    # List of all Next SEO agents (explicit names, no wildcards)
    agents=(
        "seo-technical"
        "seo-content"
        "seo-schema"
        "seo-sitemap"
        "seo-performance"
        "seo-visual"
        "seo-geo"
        "seo-local"
        "seo-maps"
        "seo-google"
        "seo-backlinks"
        "seo-dataforseo"
        "seo-image-gen"
        "seo-cluster"
        "seo-sxo"
        "seo-drift"
        "seo-ecommerce"
    )

    # Count existing skills and agents
    skill_count=0
    for skill in "${skills[@]}"; do
        if [[ -d "${HOME}/.claude/skills/${skill}" ]]; then
            ((skill_count++))
        fi
    done

    agent_count=0
    for agent in "${agents[@]}"; do
        if [[ -f "${HOME}/.claude/agents/${agent}.md" ]]; then
            ((agent_count++))
        fi
    done

    echo "Found:"
    echo "  - ${skill_count} SEO skills"
    echo "  - ${agent_count} SEO agents"
    echo ""

    # Remove all SEO skills (explicit list)
    echo "→ Removing all SEO skills..."
    for skill in "${skills[@]}"; do
        if [[ -d "${HOME}/.claude/skills/${skill}" ]]; then
            rm -rf "${HOME}/.claude/skills/${skill}"
            echo "  ✓ Removed skill: ${skill}"
        fi
    done

    # Remove all SEO agents (explicit list)
    echo "→ Removing all SEO agents..."
    for agent in "${agents[@]}"; do
        if [[ -f "${HOME}/.claude/agents/${agent}.md" ]]; then
            rm -f "${HOME}/.claude/agents/${agent}.md"
            echo "  ✓ Removed agent: ${agent}"
        fi
    done

    echo ""
    echo "✓ Claude Next SEO uninstalled successfully!"
    echo ""
    echo "Removed:"
    echo "  - ${skill_count} skills from ~/.claude/skills/"
    echo "  - ${agent_count} agents from ~/.claude/agents/"
    echo ""
    echo "⚠️  Client data preserved in: $(pwd)/clients/"
    echo "   Contains: client databases, reports, images, WordPress credentials"
    echo ""
    echo "To remove client data:"
    echo "   rm -rf $(pwd)/clients/"
    echo ""
    echo "To backup before removing:"
    echo "   tar -czf next-seo-backup-\$(date +%Y%m%d).tar.gz clients/"
    echo ""
}

main "$@"
