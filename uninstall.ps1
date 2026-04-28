#!/usr/bin/env pwsh
# claude-seo uninstaller for Windows
# Cleanly removes all SEO skills, agents, and scripts

$ErrorActionPreference = "Stop"

function Write-Color($Color, $Text) {
    Write-Host $Text -ForegroundColor $Color
}

function Main {
    $SkillDir = Join-Path $env:USERPROFILE ".claude" "skills"
    $AgentDir = Join-Path $env:USERPROFILE ".claude" "agents"

    Write-Color Cyan "=== Uninstalling claude-seo ==="
    Write-Host ""

    # Remove main skill (includes venv, references, scripts, hooks)
    $seoDir = Join-Path $SkillDir "seo"
    if (Test-Path $seoDir) {
        Remove-Item -Recurse -Force $seoDir
        Write-Color Green "  Removed: $seoDir"
    }

    # Remove sub-skills (all 26 skills)
    $subSkills = @(
        "seo-audit", "seo-backlinks", "seo-client", "seo-cluster",
        "seo-competitor-pages", "seo-content", "seo-dataforseo", "seo-drift",
        "seo-ecommerce", "seo-geo", "seo-google", "seo-hreflang",
        "seo-image-gen", "seo-images", "seo-images-manager", "seo-local",
        "seo-maps", "seo-page", "seo-plan", "seo-programmatic",
        "seo-project", "seo-schema", "seo-sitemap", "seo-sxo",
        "seo-technical", "seo-wordpress"
    )
    foreach ($skill in $subSkills) {
        $skillPath = Join-Path $SkillDir $skill
        if (Test-Path $skillPath) {
            Remove-Item -Recurse -Force $skillPath
            Write-Color Green "  Removed: $skillPath"
        }
    }

    # Remove agents (all 17 agents)
    $agents = @(
        "seo-technical", "seo-content", "seo-schema", "seo-sitemap",
        "seo-performance", "seo-visual", "seo-geo", "seo-local",
        "seo-maps", "seo-google", "seo-backlinks", "seo-dataforseo",
        "seo-image-gen", "seo-cluster", "seo-sxo", "seo-drift",
        "seo-ecommerce"
    )
    foreach ($agent in $agents) {
        $agentPath = Join-Path $AgentDir "$agent.md"
        if (Test-Path $agentPath) {
            Remove-Item -Force $agentPath
            Write-Color Green "  Removed: $agentPath"
        }
    }

    Write-Host ""
    Write-Color Cyan "=== claude-seo uninstalled ==="
    Write-Host ""
    Write-Color Yellow "Restart Claude Code to complete removal."
}

Main
