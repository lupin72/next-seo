---
name: seo-project
description: >
  Manage SEO projects within clients. Create projects, set active project context,
  list projects with audit history, and view project details. All SEO audit reports
  automatically save to the active project folder. Use when user says "add project",
  "set active project", "list projects", "project info", or "switch project".
user-invokable: true
argument-hint: "[add|set|list|info] ..."
license: MIT
metadata:
  author: AgriciDaniel
  version: "1.0.0"
  category: seo
---

# SEO Project Manager

## Overview

Manages projects within clients for multi-client SEO operations. Creates organized folder structures, tracks active project context, and enables all SEO skills to save reports in the correct client/project directories.

## Use Cases

- Organizing multiple websites per client
- Switching between projects quickly
- Automatic report saving to project folders
- Historical audit tracking per project

## Commands

### `/seo-project add <client-name> <project-name> <url>`

Creates a new project under a client with **interactive SEO specification gathering**.

**Arguments:**
- `client-name` (required): Existing client name or slug
- `project-name` (required): Project name (will be slugified)
- `url` (required): Primary project URL

**Interactive Workflow:**

After receiving the 3 required arguments, the system **MUST** use `AskUserQuestion` to gather SEO specifications before creating the project:

**Step 1 - Ask industry and tone:**
```
AskUserQuestion:
  Q1: "What industry does the project operate in?"
      Options: Hospitality, E-commerce, SaaS, Local Business
  Q2: "What is the brand's tone of voice?"
      Options: Professional and formal, Friendly and conversational,
               Technical and specialized, Luxury and exclusive
```

**Step 2 - Ask competitors and keywords:**
```
AskUserQuestion:
  Q1: "Who are the main competitors? (enter URLs separated by commas)"
      Free text input via "Other"
  Q2: "What are the main focus keywords? (separated by commas)"
      Free text input via "Other"
```

**Step 3 - Ask target audience:**
```
AskUserQuestion:
  Q1: "Who is the primary target audience?"
      Free text input via "Other"
  Q2: "Additional brand notes? (terminology, style, restrictions)"
      Free text input via "Other"
```

After gathering all responses, call the script with all parameters:

**Implementation:**
```bash
python scripts/client_manager.py add-project \
  --client "client-slug" \
  --name "Project Name" \
  --url "https://example.com" \
  --industry "Hospitality" \
  --tone "Professional and formal, luxury-oriented" \
  --target-audience "Couples 30-55 years old, high purchasing power" \
  --competitors "https://competitor1.com,https://competitor2.com" \
  --keywords "hotel rome center,luxury hotel rome" \
  --brand-notes "Avoid colloquial terms. Always use formal language."
```

**Creates:**
```
clients/
  └── example-client/
      └── main-site/
          ├── PROJECT.md           # With all SEO specifications filled in
          ├── reports/
          ├── images/
          │   ├── original/
          │   └── optimized/
          ├── data/
          └── wordpress/
```

**PROJECT.md includes:**
- Project information (client, URL, industry)
- SEO Specifications section with:
  - Tone of Voice
  - Target Audience
  - Competitors (listed)
  - Focus Keywords (listed)
  - Brand Notes

**Output:**
- Project slug
- Full folder path
- Summary of SEO specifications saved
- Confirmation with next steps

---

### `/seo-project set <client-name> <project-name>`

Sets the active project. **All SEO commands will save reports to this project folder.**

**Arguments:**
- `client-name` (required): Client name or slug
- `project-name` (required): Project name or slug

**Example:**
```
/seo-project set "Example Client" "Main Site"
```

**Output:**
- Active project confirmation
- Project URL
- Folder path

**Behavior:**
- Creates `.active-project` file in repo root with project context
- All SEO skills read this file to know where to save reports

**Implementation:**
```bash
python scripts/client_manager.py set-active \
  --client "client-slug" \
  --project "project-slug"
```

---

### `/seo-project list [client-name]`

Lists projects, optionally filtered by client.

**Arguments:**
- `client-name` (optional): Filter by client

**Example:**
```
/seo-project list
/seo-project list "Example Client"
```

**Output:**
```
Active Project: ★ example-client / main-site

Projects:
  example-client / main-site
    URL: https://example.com
    Reports: 3
    Last audit: 2026-04-23

  example-corp / main-site
    URL: https://example.com
    Reports: 1
    Last audit: 2026-04-20
```

**Implementation:**
```bash
python scripts/client_manager.py list-projects [--client "client-slug"]
```

---

### `/seo-project info`

Shows detailed information about the currently active project.

**Output:**
- Client name
- Project name
- URL
- Folder structure
- Reports count by type
- Last audit dates
- WordPress configuration (if set)

**Implementation:**
```bash
python scripts/client_manager.py get-active
```

---

## Active Project Context

When a project is set as active via `/seo-project set`, the system creates:

**`.active-project` (repo root):**
```json
{
  "client": "example-client",
  "client_name": "Example Client",
  "project": "main-site",
  "project_name": "Main Site",
  "url": "https://example.com",
  "path": "clients/example-client/main-site",
  "set_at": "2026-04-23T14:30:00Z"
}
```

**All SEO skills check this file** to determine where to save reports.

---

## Folder Structure

### Project Level
```
clients/{client-slug}/{project-slug}/
  ├── PROJECT.md              # Project config (URL, WordPress API, etc)
  ├── reports/                # SEO audit reports
  │   ├── YYYY-MM-DD_technical-audit.md
  │   ├── YYYY-MM-DD_technical-audit.pdf
  │   ├── YYYY-MM-DD_content-audit.md
  │   └── YYYY-MM-DD_full-audit.md
  ├── images/
  │   ├── original/           # Original images before optimization
  │   ├── optimized/          # Optimized images ready for upload
  │   └── metadata.json       # Image metadata and optimization history
  ├── data/
  │   ├── baseline.json       # SEO drift baseline
  │   ├── audit-history.json  # Historical audit results
  │   ├── crux-history.json   # Core Web Vitals trends
  │   └── backlinks.json      # Backlink profile snapshots
  └── wordpress/
      ├── config.json         # WP REST API credentials
      └── publish-log.json    # Publishing history
```

### PROJECT.md Template

Created automatically when adding a new project. SEO specifications are filled during interactive creation:

```markdown
# {Project Name}

## Project Information

- **Client:** {Client Name}
- **URL:** {URL}
- **Industry:** {Industry}
- **Launch Date:**
- **CMS:**

## SEO Specifications

### Tone of Voice

{Tone description from interactive setup}

### Target Audience

{Target audience from interactive setup}

### Competitors

- {Competitor 1 URL}
- {Competitor 2 URL}

### Focus Keywords

- {Keyword 1}
- {Keyword 2}

### Brand Notes

{Brand notes from interactive setup}

## SEO Goals

- [ ] Goal 1
- [ ] Goal 2
- [ ] Goal 3

## WordPress Integration

- **REST API Endpoint:** {URL}/wp-json
- **Authentication:** (configured separately)
- **Media Library Folder:**

## Audit History

| Date | Type | Score | Report |
|------|------|-------|--------|
| YYYY-MM-DD | Technical | 85/100 | [View](reports/YYYY-MM-DD_technical-audit.md) |

## Notes

<!-- Add project-specific notes -->
```

**The SEO Specifications section is read by `seo-images-manager`** during image planning to:
- Match alt text style to the brand's tone of voice
- Filter GSC keywords by relevance to focus keywords
- Differentiate from competitor keyword strategies
- Use appropriate language for the target audience

---

## Integration with SEO Skills

All SEO skills automatically save reports to the active project folder:

**Before (without active project):**
```
/seo-technical https://example.com
# Saves to: reports/technical-audit-2026-04-23.md (repo root)
```

**After (with active project):**
```
/seo-project set "Client A" "Project 1"
/seo-technical https://example.com
# Saves to: clients/client-a/project-1/reports/2026-04-23_technical-audit.md
```

**Skills that integrate:**
- `/seo-technical` → `reports/YYYY-MM-DD_technical-audit.md`
- `/seo-page` → `reports/YYYY-MM-DD_page-audit.md`
- `/seo-audit` → `reports/YYYY-MM-DD_full-audit.md`
- `/seo-content` → `reports/YYYY-MM-DD_content-audit.md`
- `/seo-schema` → `reports/YYYY-MM-DD_schema-audit.md`
- `/seo-local` → `reports/YYYY-MM-DD_local-audit.md`
- `/seo-drift baseline` → `data/baseline.json`
- `/seo-drift compare` → `reports/YYYY-MM-DD_drift-report.md`
- `/seo-google crux` → `data/crux-history.json`
- `/seo-backlinks` → `data/backlinks.json`

---

## Database Schema

SQLite database at `clients/.clients.db`:

```sql
CREATE TABLE projects (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    client_id INTEGER NOT NULL,
    slug TEXT NOT NULL,
    name TEXT NOT NULL,
    url TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    last_audit_at TEXT,
    FOREIGN KEY (client_id) REFERENCES clients(id),
    UNIQUE(client_id, slug)
);

CREATE TABLE audits (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER NOT NULL,
    audit_type TEXT NOT NULL,
    audit_date TEXT NOT NULL,
    report_path TEXT NOT NULL,
    score INTEGER,
    FOREIGN KEY (project_id) REFERENCES projects(id)
);

CREATE TABLE active_project (
    id INTEGER PRIMARY KEY CHECK (id = 1),
    project_id INTEGER NOT NULL,
    set_at TEXT NOT NULL,
    FOREIGN KEY (project_id) REFERENCES projects(id)
);
```

---

## Error Handling

| Scenario | Action |
|----------|--------|
| Project already exists | Return error, suggest using different name |
| Client not found | List available clients |
| No active project set | Prompt user to run `/seo-project set` |
| Invalid URL format | Validate and reject with error message |
| Database locked | Retry with exponential backoff |

---

## Best Practices

1. **Naming Convention:**
   - Use descriptive project names: "Main Site" not "Project A"
   - Project names should describe the website/domain

2. **Active Project:**
   - Always set active project before running SEO commands
   - Verify with `/seo-project info` before audits
   - Switch projects with `/seo-project set` when working on different sites

3. **Organization:**
   - One project = one domain/website
   - Multiple projects can belong to the same client
   - Update PROJECT.md with relevant SEO goals and configurations

4. **Security:**
   - `clients/` folder is gitignored by default (sensitive data)
   - WordPress credentials stored encrypted in `wordpress/config.json`

---

## Workflow Example

```bash
# Setup
/seo-client add "Example Client"
/seo-project add "example-client" "Main Site" https://example.com
/seo-project set "example-client" "main-site"

# Run audits (saves to clients/example-client/main-site/reports/)
/seo-technical https://example.com
/seo-page https://example.com
/seo-audit https://example.com

# Switch to another project
/seo-project set "other-client" "other-project"
```

---

## Next Steps

After setting up a project:

1. Set as active: `/seo-project set <client> <project>`
2. Run initial audit: `/seo-audit <url>`
3. Set up WordPress integration: `/seo-wordpress setup` (future)
4. Configure baseline: `/seo-drift baseline <url>`

---

**Version:** 1.1.0
**Last Updated:** 2026-04-30
**Skill Type:** Management / Infrastructure
