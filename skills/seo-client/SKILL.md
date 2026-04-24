---
name: seo-client
description: >
  Manage SEO clients for multi-client operations. Create clients, list all clients
  with project counts, and view detailed client information. Part of the client/project
  management system for organizing SEO work across multiple businesses. Use when user
  says "add client", "list clients", "client info", or "manage clients".
user-invokable: true
argument-hint: "[add|list|info] <client-name>"
license: MIT
metadata:
  author: AgriciDaniel
  version: "1.0.0"
  category: seo
---

# SEO Client Manager

## Overview

Manages clients for multi-client SEO operations. Creates organized folder structures and tracks client metadata. Works together with `/seo-project` to enable full client/project organization.

## Use Cases

- Agency managing multiple client websites
- Freelancer tracking projects for different clients
- In-house SEO managing multiple domains/brands
- Historical audit tracking per client

## Commands

### `/seo-client add <client-name>`

Creates a new client with folder structure.

**Arguments:**
- `client-name` (required): Client name (will be slugified for folder name)

**Example:**
```
/seo-client add "Example Client"
```

**Creates:**
```
clients/
  └── example-client/
      └── CLIENT.md
```

**Output:**
- Client slug
- Folder path
- Success confirmation

**Implementation:**
```bash
python scripts/client_manager.py add-client --name "Client Name"
```

---

### `/seo-client list`

Lists all clients with project counts.

**Output:**
```
Clients:
  1. example-client (2 projects)
  2. example-corp (1 project)

Total: 2 clients
```

**Implementation:**
```bash
python scripts/client_manager.py list-clients
```

---

### `/seo-client info <client-name>`

Shows detailed information about a client.

**Arguments:**
- `client-name` (required): Client name or slug

**Output:**
- Client name
- Folder path
- Projects list with URLs
- Last audit date per project
- Total reports count

**Implementation:**
```bash
python scripts/client_manager.py get-client --slug "client-slug"
```

---

## Folder Structure

### Client Level
```
clients/
  └── {client-slug}/
      ├── CLIENT.md           # Client notes, contact info
      └── {project-slug}/     # Projects (created via /seo-project)
```

### CLIENT.md Template

Created automatically when adding a new client:

```markdown
# {Client Name}

## Contact Information

- **Company:**
- **Contact Person:**
- **Email:**
- **Phone:**
- **Billing Contact:**

## Business Information

- **Industry:**
- **Target Markets:**
- **Main Competitors:**

## Projects

- [{Project Name}]({project-slug}/) - {URL}

## Notes

<!-- Add client-specific notes, requirements, preferences -->
```

---

## Database Schema

SQLite database at `clients/.clients.db`:

```sql
CREATE TABLE clients (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    slug TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
```

---

## Error Handling

| Scenario | Action |
|----------|--------|
| Client already exists | Return error, suggest using existing slug |
| Invalid client name | Validate and reject with error message |
| Database locked | Retry with exponential backoff |

---

## Best Practices

1. **Naming Convention:**
   - Use descriptive client names: "Example Client" not "Cliente 1"
   - Client names should be business entities

2. **Organization:**
   - One client = one business entity
   - Multiple projects per client are managed via `/seo-project`
   - Update CLIENT.md with relevant contact and business info

3. **Security:**
   - `clients/` folder is gitignored by default (sensitive data)
   - Database has 600 permissions (owner read/write only)

---

## Related Commands

After creating a client:
1. Add projects: `/seo-project add <client> <project> <url>`
2. Set active project: `/seo-project set <client> <project>`
3. List client projects: `/seo-project list <client>`

---

**Version:** 1.0.0
**Last Updated:** 2026-04-23
**Skill Type:** Management / Infrastructure
