# Claude SEO Installer for Windows
# PowerShell installation script

$ErrorActionPreference = "Stop"

# Detect if running from local repo (Next SEO) or installing from remote (upstream)
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$IsLocalInstall = (Test-Path "$ScriptDir\CHANGELOG.md") -and (Test-Path "$ScriptDir\skills\seo-images-manager")

if ($IsLocalInstall) {
    $InstallMode = "local"
    $LocalRepo = $ScriptDir
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host "|   Claude Next SEO - Installer        |" -ForegroundColor Cyan
    Write-Host "|   v1.1.0 - GSC Integration           |" -ForegroundColor Cyan
    Write-Host "========================================" -ForegroundColor Cyan
} else {
    $InstallMode = "remote"
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host "|   Claude SEO - Installer             |" -ForegroundColor Cyan
    Write-Host "|   Claude Code SEO Skill              |" -ForegroundColor Cyan
    Write-Host "========================================" -ForegroundColor Cyan
}
Write-Host ""

function Resolve-Python {
    $pythonCmd = Get-Command -Name python -ErrorAction SilentlyContinue
    if ($null -ne $pythonCmd) {
        return @{ Exe = 'python'; Args = @() }
    }

    $pyCmd = Get-Command -Name py -ErrorAction SilentlyContinue
    if ($null -ne $pyCmd) {
        return @{ Exe = 'py'; Args = @('-3') }
    }

    return $null
}

function Invoke-External {
    param(
        [Parameter(Mandatory = $true)][string]$Exe,
        [Parameter(Mandatory = $true)][string[]]$Args,
        [switch]$Quiet
    )

    $previousErrorActionPreference = $ErrorActionPreference
    $hasNativePreference = $null -ne (Get-Variable -Name PSNativeCommandUseErrorActionPreference -ErrorAction SilentlyContinue)
    if ($hasNativePreference) {
        $previousNativePreference = $PSNativeCommandUseErrorActionPreference
    }

    try {
        $ErrorActionPreference = 'Continue'
        if ($hasNativePreference) {
            $PSNativeCommandUseErrorActionPreference = $false
        }

        $output = & $Exe @Args 2>&1 | ForEach-Object { $_.ToString() }
        $exitCode = $LASTEXITCODE
    } finally {
        $ErrorActionPreference = $previousErrorActionPreference
        if ($hasNativePreference) {
            $PSNativeCommandUseErrorActionPreference = $previousNativePreference
        }
    }

    if (-not $Quiet -and $null -ne $output -and $output.Count -gt 0) {
        $output | ForEach-Object { Write-Host $_ }
    }

    return @{ ExitCode = $exitCode; Output = $output }
}

# Check prerequisites
$python = Resolve-Python
if ($null -eq $python) {
    Write-Host "[x] Python is required but was not found (tried 'python' and 'py')." -ForegroundColor Red
    exit 1
}

try {
    $pythonVersion = & $python.Exe @($python.Args + @('--version')) 2>&1
    Write-Host "[+] $pythonVersion detected" -ForegroundColor Green
} catch {
    Write-Host "[x] Python is installed but could not be executed." -ForegroundColor Red
    exit 1
}

try {
    git --version | Out-Null
    Write-Host "[+] Git detected" -ForegroundColor Green
} catch {
    Write-Host "[x] Git is required but not installed." -ForegroundColor Red
    exit 1
}

# Set paths
$SkillDir = "$env:USERPROFILE\.claude\skills\seo"
$AgentDir = "$env:USERPROFILE\.claude\agents"

# Create directories
New-Item -ItemType Directory -Force -Path $SkillDir | Out-Null
New-Item -ItemType Directory -Force -Path $AgentDir | Out-Null

# Setup source directory based on install mode
if ($InstallMode -eq "local") {
    Write-Host "=> Installing from local repository (Next SEO v1.1)..." -ForegroundColor Yellow
    $SourceDir = $LocalRepo
} else {
    # Remote installation from upstream
    $RepoUrl = "https://github.com/AgriciDaniel/claude-seo"
    $RepoTag = if ($env:CLAUDE_SEO_TAG) { $env:CLAUDE_SEO_TAG } else { 'v1.9.0' }

    $TempDir = Join-Path $env:TEMP "claude-seo-install"
    if (Test-Path $TempDir) {
        Remove-Item -Recurse -Force $TempDir
    }

    Write-Host ">> Downloading Claude SEO ($RepoTag)..." -ForegroundColor Yellow
    $clone = Invoke-External -Exe 'git' -Args @('clone','--depth','1','--branch',$RepoTag,$RepoUrl,$TempDir) -Quiet
    if ($clone.ExitCode -ne 0) {
        throw "git clone failed. Output:`n$($clone.Output -join "`n")"
    }

    $SourceDir = $TempDir
}

$keepTemp = ($env:CLAUDE_SEO_KEEP_TEMP -eq '1')

try {
    # Copy skill files
    Write-Host "=> Installing skill files..." -ForegroundColor Yellow
    $skillSource = Join-Path $SourceDir 'skills\seo'
    if (-not (Test-Path $skillSource)) {
        throw "Could not find skill source folder in repo clone."
    }
    Copy-Item -Recurse -Force (Join-Path $skillSource '*') $SkillDir

    # Copy sub-skills (including Next SEO exclusive: seo-client, seo-project, seo-wordpress, seo-images-manager)
    $SkillsPath = "$SourceDir\skills"
    if (Test-Path $SkillsPath) {
        Write-Host "=> Installing sub-skills..." -ForegroundColor Yellow
        $skillCount = 0
        Get-ChildItem -Directory $SkillsPath | ForEach-Object {
            $target = "$env:USERPROFILE\.claude\skills\$($_.Name)"
            New-Item -ItemType Directory -Force -Path $target | Out-Null
            Copy-Item -Recurse -Force "$($_.FullName)\*" $target
            $skillCount++
        }
        Write-Host "  [+] Installed $skillCount skills" -ForegroundColor Green

        # List Next SEO exclusive skills if in local mode
        if ($InstallMode -eq "local") {
            Write-Host ""
            Write-Host "Next SEO Exclusive Skills:" -ForegroundColor Cyan
            if (Test-Path "$env:USERPROFILE\.claude\skills\seo-client") {
                Write-Host "  [+] seo-client - Multi-client management" -ForegroundColor Green
            }
            if (Test-Path "$env:USERPROFILE\.claude\skills\seo-project") {
                Write-Host "  [+] seo-project - Project organization" -ForegroundColor Green
            }
            if (Test-Path "$env:USERPROFILE\.claude\skills\seo-wordpress") {
                Write-Host "  [+] seo-wordpress - WordPress integration" -ForegroundColor Green
            }
            if (Test-Path "$env:USERPROFILE\.claude\skills\seo-images-manager") {
                Write-Host "  [+] seo-images-manager - Image SEO with GSC integration (v1.1)" -ForegroundColor Green
            }
            Write-Host ""
        }
    }

    # Copy schema templates
    $SchemaPath = "$SourceDir\schema"
    if (Test-Path $SchemaPath) {
        $SkillSchema = "$SkillDir\schema"
        New-Item -ItemType Directory -Force -Path $SkillSchema | Out-Null
        Copy-Item -Recurse -Force "$SchemaPath\*" $SkillSchema
    }

    # Copy reference docs
    $PdfPath = "$SourceDir\pdf"
    if (Test-Path $PdfPath) {
        $SkillPdf = "$SkillDir\pdf"
        New-Item -ItemType Directory -Force -Path $SkillPdf | Out-Null
        Copy-Item -Recurse -Force "$PdfPath\*" $SkillPdf
    }

    # Copy agents
    Write-Host "=> Installing subagents..." -ForegroundColor Yellow
    $AgentsPath = Join-Path $SourceDir 'agents'
    if (Test-Path $AgentsPath) {
        Copy-Item -Force (Join-Path $AgentsPath '*.md') $AgentDir -ErrorAction SilentlyContinue
    }

    # Copy shared scripts
    $ScriptsPath = "$SourceDir\scripts"
    if (Test-Path $ScriptsPath) {
        $SkillScripts = "$SkillDir\scripts"
        New-Item -ItemType Directory -Force -Path $SkillScripts | Out-Null
        Copy-Item -Recurse -Force "$ScriptsPath\*" $SkillScripts
    }

    # Copy hooks
    $HooksPath = "$SourceDir\hooks"
    if (Test-Path $HooksPath) {
        $SkillHooks = "$SkillDir\hooks"
        New-Item -ItemType Directory -Force -Path $SkillHooks | Out-Null
        Copy-Item -Recurse -Force "$HooksPath\*" $SkillHooks
    }

    # Copy extensions (optional add-ons: dataforseo, banana)
    $ExtensionsPath = Join-Path $SourceDir 'extensions'
    if (Test-Path $ExtensionsPath) {
        Write-Host "=> Installing extensions..." -ForegroundColor Yellow
        Get-ChildItem -Directory $ExtensionsPath | ForEach-Object {
            $extName = $_.Name
            $extDir = $_.FullName
            # Extension skills
            $extSkills = Join-Path $extDir 'skills'
            if (Test-Path $extSkills) {
                Get-ChildItem -Directory $extSkills | ForEach-Object {
                    $target = "$env:USERPROFILE\.claude\skills\$($_.Name)"
                    New-Item -ItemType Directory -Force -Path $target | Out-Null
                    Copy-Item -Recurse -Force "$($_.FullName)\*" $target
                }
            }
            # Extension agents
            $extAgents = Join-Path $extDir 'agents'
            if (Test-Path $extAgents) {
                Copy-Item -Force (Join-Path $extAgents '*.md') $AgentDir -ErrorAction SilentlyContinue
            }
            # Extension references
            $extRefs = Join-Path $extDir 'references'
            if (Test-Path $extRefs) {
                $refTarget = "$SkillDir\extensions\$extName\references"
                New-Item -ItemType Directory -Force -Path $refTarget | Out-Null
                Copy-Item -Recurse -Force "$extRefs\*" $refTarget
            }
            # Extension scripts
            $extScripts = Join-Path $extDir 'scripts'
            if (Test-Path $extScripts) {
                $scriptTarget = "$SkillDir\extensions\$extName\scripts"
                New-Item -ItemType Directory -Force -Path $scriptTarget | Out-Null
                Copy-Item -Recurse -Force "$extScripts\*" $scriptTarget
            }
        }
    }

    # Copy requirements.txt to skill dir for retry
    $reqFile = Join-Path $SourceDir 'requirements.txt'
    $installedReqFile = Join-Path $SkillDir 'requirements.txt'
    if (Test-Path $reqFile) {
        Copy-Item -Force $reqFile $installedReqFile
    }

    # Install Python dependencies
    Write-Host "=> Installing Python dependencies..." -ForegroundColor Yellow
    if (Test-Path $reqFile) {
        try {
            $pip = Invoke-External -Exe $python.Exe -Args @($python.Args + @('-m','pip','install','-q','-r',$reqFile)) -Quiet
            if ($pip.ExitCode -ne 0) {
                throw ($pip.Output -join "`n")
            }
        } catch {
            Write-Host "  [!]  Could not auto-install Python packages." -ForegroundColor Yellow
            Write-Host "  Try: $($python.Exe) $($python.Args -join ' ') -m pip install -r `"$installedReqFile`"" -ForegroundColor Yellow
        }
    } else {
        Write-Host "  [!]  No requirements.txt found; skipping Python dependency install." -ForegroundColor Yellow
    }

    # Optional: Install Playwright browsers
    Write-Host "=> Installing Playwright browsers (optional, for visual analysis)..." -ForegroundColor Yellow
    try {
        $pw = Invoke-External -Exe $python.Exe -Args @($python.Args + @('-m','playwright','install','chromium')) -Quiet
        if ($pw.ExitCode -ne 0) {
            throw ($pw.Output -join "`n")
        }
    } catch {
        Write-Host "  [!]  Playwright install failed. Visual analysis will use WebFetch fallback." -ForegroundColor Yellow
    }
} catch {
    Write-Host ""
    Write-Host "[x] Installation failed: $($_.Exception.Message)" -ForegroundColor Red
    if ($InstallMode -eq "remote" -and $keepTemp -and (Test-Path $TempDir)) {
        Write-Host "Temp dir kept at: $TempDir" -ForegroundColor Yellow
    }
    throw
} finally {
    if ($InstallMode -eq "remote" -and -not $keepTemp -and (Test-Path $TempDir)) {
        Remove-Item -Recurse -Force $TempDir
    }
}

Write-Host ""
if ($InstallMode -eq "local") {
    Write-Host "[+] Claude Next SEO v1.1 installed successfully!" -ForegroundColor Green
    Write-Host ""
    Write-Host "New in v1.1:" -ForegroundColor Cyan
    Write-Host "  • Google Search Console integration for image keywords"
    Write-Host "  • Opportunity scoring (0-100) for quick wins"
    Write-Host "  • Intelligent 7-day cache (>90% API savings)"
    Write-Host "  • Multi-client/project management"
    Write-Host "  • WordPress REST API integration"
    Write-Host ""
    Write-Host "Usage:" -ForegroundColor Cyan
    Write-Host "  1. Start Claude Code:    claude"
    Write-Host "  2. Setup client:         /seo-client add `"My Client`""
    Write-Host "  3. Setup project:        /seo-project add `"my-client`" `"Project`" https://example.com"
    Write-Host "  4. Run SEO audit:        /seo audit https://example.com"
    Write-Host "  5. Optimize images:      /seo-images-manager analyze"
    Write-Host ""
    Write-Host "Documentation:" -ForegroundColor Cyan
    Write-Host "  • README.md: $LocalRepo\README.md"
    Write-Host "  • CHANGELOG.md: $LocalRepo\CHANGELOG.md"
    Write-Host "  • GSC Integration: $env:USERPROFILE\.claude\skills\seo-images-manager\GSC-INTEGRATION.md"
} else {
    Write-Host "[+] Claude SEO installed successfully!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Usage:" -ForegroundColor Cyan
    Write-Host "  1. Start Claude Code:  claude"
    Write-Host "  2. Run commands:       /seo audit https://example.com"
    Write-Host ""
    Write-Host "To upgrade to Next SEO (multi-client + GSC):" -ForegroundColor Yellow
    Write-Host "  git clone https://github.com/YOUR-FORK/claude-next-seo"
    Write-Host "  cd claude-next-seo"
    Write-Host "  .\install.ps1"
}
Write-Host ""
Write-Host "Python deps location: $installedReqFile" -ForegroundColor Gray
