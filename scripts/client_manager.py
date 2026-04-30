#!/usr/bin/env python3
"""
Client and Project Manager for Claude SEO

Manages clients and projects with SQLite database backend.
Provides CRUD operations and active project tracking.

Usage:
    python client_manager.py add-client --name "Client Name"
    python client_manager.py add-project --client "client-slug" --name "Project Name" --url "https://example.com"
    python client_manager.py set-active --client "client-slug" --project "project-slug"
    python client_manager.py get-active
    python client_manager.py list-clients
    python client_manager.py list-projects [--client "client-slug"]
    python client_manager.py get-client --slug "client-slug"
    python client_manager.py get-project --client "client-slug" --project "project-slug"
"""

import argparse
import json
import os
import re
import sqlite3
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, List, Any


def slugify(text: str) -> str:
    """Convert text to URL-safe slug."""
    text = text.lower()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[-\s]+', '-', text)
    return text.strip('-')


def get_repo_root() -> Path:
    """Get repository root directory."""
    return Path(__file__).parent.parent


def get_db_path() -> Path:
    """Get database file path."""
    return get_repo_root() / 'clients' / '.clients.db'


def get_active_project_file() -> Path:
    """Get active project file path."""
    return get_repo_root() / '.active-project'


def init_database(db_path: Path) -> None:
    """Initialize database with schema."""
    db_path.parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Clients table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS clients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            slug TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
    ''')

    # Projects table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS projects (
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
        )
    ''')

    # Audits table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS audits (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id INTEGER NOT NULL,
            audit_type TEXT NOT NULL,
            audit_date TEXT NOT NULL,
            report_path TEXT NOT NULL,
            score INTEGER,
            FOREIGN KEY (project_id) REFERENCES projects(id)
        )
    ''')

    # Active project table (single row)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS active_project (
            id INTEGER PRIMARY KEY CHECK (id = 1),
            project_id INTEGER NOT NULL,
            set_at TEXT NOT NULL,
            FOREIGN KEY (project_id) REFERENCES projects(id)
        )
    ''')

    conn.commit()
    conn.close()

    # Set restrictive permissions
    os.chmod(db_path, 0o600)


def add_client(name: str) -> Dict[str, Any]:
    """Add a new client."""
    slug = slugify(name)
    db_path = get_db_path()
    init_database(db_path)

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Check if exists
    cursor.execute('SELECT id FROM clients WHERE slug = ?', (slug,))
    if cursor.fetchone():
        conn.close()
        return {
            'success': False,
            'error': f'Client "{slug}" already exists'
        }

    # Insert client
    now = datetime.utcnow().isoformat()
    cursor.execute(
        'INSERT INTO clients (slug, name, created_at, updated_at) VALUES (?, ?, ?, ?)',
        (slug, name, now, now)
    )

    conn.commit()
    conn.close()

    # Create client folder
    client_path = get_repo_root() / 'clients' / slug
    client_path.mkdir(parents=True, exist_ok=True)

    # Create CLIENT.md
    client_md_path = client_path / 'CLIENT.md'
    client_md_content = f"""# {name}

## Contact Information

- **Company:** {name}
- **Contact Person:**
- **Email:**
- **Phone:**
- **Billing Contact:**

## Business Information

- **Industry:**
- **Target Markets:**
- **Main Competitors:**

## Projects

<!-- Projects will be listed here automatically -->

## Notes

<!-- Add client-specific notes, requirements, preferences -->

---

*Created: {now}*
"""
    client_md_path.write_text(client_md_content)

    return {
        'success': True,
        'client_slug': slug,
        'client_name': name,
        'path': str(client_path)
    }


def add_project(client_slug: str, name: str, url: str,
                 industry: str = '', tone: str = '', target_audience: str = '',
                 competitors: Optional[List[str]] = None,
                 focus_keywords: Optional[List[str]] = None,
                 brand_notes: str = '') -> Dict[str, Any]:
    """Add a new project to a client with optional SEO specifications."""
    project_slug = slugify(name)
    db_path = get_db_path()
    init_database(db_path)

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Get client
    cursor.execute('SELECT id, name FROM clients WHERE slug = ?', (client_slug,))
    client = cursor.fetchone()
    if not client:
        conn.close()
        return {
            'success': False,
            'error': f'Client "{client_slug}" not found'
        }

    client_id, client_name = client

    # Check if project exists
    cursor.execute(
        'SELECT id FROM projects WHERE client_id = ? AND slug = ?',
        (client_id, project_slug)
    )
    if cursor.fetchone():
        conn.close()
        return {
            'success': False,
            'error': f'Project "{project_slug}" already exists for client "{client_slug}"'
        }

    # Insert project
    now = datetime.utcnow().isoformat()
    cursor.execute(
        'INSERT INTO projects (client_id, slug, name, url, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?)',
        (client_id, project_slug, name, url, now, now)
    )

    conn.commit()
    conn.close()

    # Create project folder structure
    project_path = get_repo_root() / 'clients' / client_slug / project_slug
    (project_path / 'reports').mkdir(parents=True, exist_ok=True)
    (project_path / 'images' / 'original').mkdir(parents=True, exist_ok=True)
    (project_path / 'images' / 'optimized').mkdir(parents=True, exist_ok=True)
    (project_path / 'data').mkdir(parents=True, exist_ok=True)
    (project_path / 'wordpress').mkdir(parents=True, exist_ok=True)

    # Create PROJECT.md
    project_md_path = project_path / 'PROJECT.md'

    # Format competitors list
    competitors_list = competitors or []
    competitors_md = '\n'.join(f'- {c}' for c in competitors_list) if competitors_list else '- <!-- Add competitor URLs -->'

    # Format focus keywords list
    keywords_list = focus_keywords or []
    keywords_md = '\n'.join(f'- {k}' for k in keywords_list) if keywords_list else '- <!-- Add focus keywords -->'

    project_md_content = f"""# {name}

## Project Information

- **Client:** {client_name}
- **URL:** {url}
- **Industry:** {industry}
- **Launch Date:**
- **CMS:**

## SEO Specifications

### Tone of Voice

{tone if tone else '<!-- Describe the brand tone: formal, friendly, technical, conversational, luxury, etc. -->'}

### Target Audience

{target_audience if target_audience else '<!-- Describe the target audience: demographics, interests, needs, buying behavior -->'}

### Brand Context

**Properties / Products / Services:**
<!-- List key offerings, unique features, differentiators -->

**Unique Selling Points (USPs):**
<!-- What makes this brand different? Certifications, awards, unique features -->

**Key Differentiators:**
<!-- Compared to competitors, what advantages does this brand have? -->

### Competitor Analysis

{competitors_md}

**Competitor Weaknesses to Exploit:**
<!-- List competitor gaps, weaknesses, or missed opportunities -->
<!-- Example: Competitor A has poor mobile experience, slow site speed -->
<!-- Example: Competitor B ranks for X but has thin content -->

**Competitor Strengths to Match:**
<!-- What are competitors doing well that we should address? -->

### Keyword Universe

**High-Priority Keywords:**
<!-- Target these first - high volume, good intent, achievable ranking -->
{keywords_md if keywords_list else '- <!-- Add high-priority keywords -->'}

**Medium-Priority Keywords:**
<!-- Secondary targets - lower volume or higher competition -->
- <!-- Add medium-priority keywords -->

**Long-Tail Keywords:**
<!-- Low competition, high intent, specific user queries -->
- <!-- Add long-tail keywords -->

### Focus Keywords

{keywords_md}

### Brand Notes

{brand_notes if brand_notes else '<!-- Additional brand guidelines, style notes, terminology to use/avoid -->'}

## Image SEO Overrides

**Note:** These override global rules in `skills/seo-images-manager/references/global-rules.md`

### Naming Convention Overrides
<!-- Example: Max 3-4 words instead of default 5-7 -->
<!-- Example: Always include brand name at end -->

### Alt Text Overrides
<!-- Example: Max 100 characters instead of default 125 -->
<!-- Example: Always include year for blog posts -->

### Language-Specific Rules
- **Primary Language:** <!-- es, it, en, fr, de, pt, nl -->
- **Secondary Language:** <!-- Optional -->
- **Tertiary Language:** <!-- Optional -->

## SEO Goals

- [ ] Goal 1
- [ ] Goal 2
- [ ] Goal 3

## WordPress Integration

- **REST API Endpoint:** {url}/wp-json
- **Authentication:** (configured separately)
- **Media Library Folder:**

## Audit History

| Date | Type | Score | Report |
|------|------|-------|--------|
| - | - | - | - |

## Notes

<!-- Add project-specific notes -->

---

*Created: {now}*
"""
    project_md_path.write_text(project_md_content)

    # Create .gitkeep files
    (project_path / 'images' / 'original' / '.gitkeep').touch()
    (project_path / 'images' / 'optimized' / '.gitkeep').touch()
    (project_path / 'data' / '.gitkeep').touch()
    (project_path / 'wordpress' / '.gitkeep').touch()

    return {
        'success': True,
        'client_slug': client_slug,
        'client_name': client_name,
        'project_slug': project_slug,
        'project_name': name,
        'url': url,
        'path': str(project_path)
    }


def set_active_project(client_slug: str, project_slug: str) -> Dict[str, Any]:
    """Set the active project."""
    db_path = get_db_path()
    init_database(db_path)

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Get project
    cursor.execute('''
        SELECT p.id, p.name, p.url, c.name, c.slug
        FROM projects p
        JOIN clients c ON p.client_id = c.id
        WHERE c.slug = ? AND p.slug = ?
    ''', (client_slug, project_slug))

    project = cursor.fetchone()
    if not project:
        conn.close()
        return {
            'success': False,
            'error': f'Project "{client_slug}/{project_slug}" not found'
        }

    project_id, project_name, url, client_name, _ = project

    # Update active project
    now = datetime.utcnow().isoformat()
    cursor.execute('DELETE FROM active_project WHERE id = 1')
    cursor.execute(
        'INSERT INTO active_project (id, project_id, set_at) VALUES (1, ?, ?)',
        (project_id, now)
    )

    conn.commit()
    conn.close()

    # Write .active-project file
    active_project_data = {
        'client': client_slug,
        'client_name': client_name,
        'project': project_slug,
        'project_name': project_name,
        'url': url,
        'path': f'clients/{client_slug}/{project_slug}',
        'set_at': now
    }

    active_project_file = get_active_project_file()
    active_project_file.write_text(json.dumps(active_project_data, indent=2))

    return {
        'success': True,
        **active_project_data
    }


def get_active_project() -> Dict[str, Any]:
    """Get the current active project."""
    active_project_file = get_active_project_file()

    if not active_project_file.exists():
        return {
            'success': False,
            'error': 'No active project set. Run: /seo-project set <client> <project>'
        }

    data = json.loads(active_project_file.read_text())
    return {
        'success': True,
        **data
    }


def list_clients() -> Dict[str, Any]:
    """List all clients."""
    db_path = get_db_path()
    init_database(db_path)

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute('''
        SELECT c.slug, c.name, COUNT(p.id) as project_count
        FROM clients c
        LEFT JOIN projects p ON c.id = p.client_id
        GROUP BY c.id
        ORDER BY c.name
    ''')

    clients = [
        {
            'slug': row[0],
            'name': row[1],
            'project_count': row[2]
        }
        for row in cursor.fetchall()
    ]

    conn.close()

    return {
        'success': True,
        'clients': clients,
        'total': len(clients)
    }


def list_projects(client_slug: Optional[str] = None) -> Dict[str, Any]:
    """List all projects, optionally filtered by client."""
    db_path = get_db_path()
    init_database(db_path)

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Get active project
    cursor.execute('''
        SELECT c.slug, p.slug
        FROM active_project ap
        JOIN projects p ON ap.project_id = p.id
        JOIN clients c ON p.client_id = c.id
        WHERE ap.id = 1
    ''')
    active = cursor.fetchone()
    active_project = f"{active[0]}/{active[1]}" if active else None

    # Get projects
    if client_slug:
        cursor.execute('''
            SELECT c.slug, c.name, p.slug, p.name, p.url, p.last_audit_at,
                   COUNT(a.id) as report_count
            FROM projects p
            JOIN clients c ON p.client_id = c.id
            LEFT JOIN audits a ON p.id = a.project_id
            WHERE c.slug = ?
            GROUP BY p.id
            ORDER BY p.name
        ''', (client_slug,))
    else:
        cursor.execute('''
            SELECT c.slug, c.name, p.slug, p.name, p.url, p.last_audit_at,
                   COUNT(a.id) as report_count
            FROM projects p
            JOIN clients c ON p.client_id = c.id
            LEFT JOIN audits a ON p.id = a.project_id
            GROUP BY p.id
            ORDER BY c.name, p.name
        ''')

    projects = [
        {
            'client_slug': row[0],
            'client_name': row[1],
            'project_slug': row[2],
            'project_name': row[3],
            'url': row[4],
            'last_audit_at': row[5],
            'report_count': row[6],
            'is_active': f"{row[0]}/{row[2]}" == active_project
        }
        for row in cursor.fetchall()
    ]

    conn.close()

    return {
        'success': True,
        'projects': projects,
        'total': len(projects),
        'active_project': active_project
    }


def get_client(slug: str) -> Dict[str, Any]:
    """Get client details."""
    db_path = get_db_path()
    init_database(db_path)

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute('SELECT id, slug, name, created_at FROM clients WHERE slug = ?', (slug,))
    client = cursor.fetchone()

    if not client:
        conn.close()
        return {
            'success': False,
            'error': f'Client "{slug}" not found'
        }

    client_id, client_slug, name, created_at = client

    # Get projects
    cursor.execute('''
        SELECT slug, name, url, last_audit_at, COUNT(a.id) as report_count
        FROM projects p
        LEFT JOIN audits a ON p.id = a.project_id
        WHERE p.client_id = ?
        GROUP BY p.id
        ORDER BY p.name
    ''', (client_id,))

    projects = [
        {
            'slug': row[0],
            'name': row[1],
            'url': row[2],
            'last_audit_at': row[3],
            'report_count': row[4]
        }
        for row in cursor.fetchall()
    ]

    conn.close()

    return {
        'success': True,
        'slug': client_slug,
        'name': name,
        'created_at': created_at,
        'projects': projects,
        'project_count': len(projects),
        'path': f'clients/{client_slug}'
    }


def get_project(client_slug: str, project_slug: str) -> Dict[str, Any]:
    """Get project details."""
    db_path = get_db_path()
    init_database(db_path)

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute('''
        SELECT p.id, p.slug, p.name, p.url, p.created_at, p.last_audit_at,
               c.slug, c.name
        FROM projects p
        JOIN clients c ON p.client_id = c.id
        WHERE c.slug = ? AND p.slug = ?
    ''', (client_slug, project_slug))

    project = cursor.fetchone()

    if not project:
        conn.close()
        return {
            'success': False,
            'error': f'Project "{client_slug}/{project_slug}" not found'
        }

    project_id, proj_slug, proj_name, url, created_at, last_audit_at, cli_slug, cli_name = project

    # Get audits
    cursor.execute('''
        SELECT audit_type, audit_date, report_path, score
        FROM audits
        WHERE project_id = ?
        ORDER BY audit_date DESC
    ''', (project_id,))

    audits = [
        {
            'type': row[0],
            'date': row[1],
            'report': row[2],
            'score': row[3]
        }
        for row in cursor.fetchall()
    ]

    conn.close()

    return {
        'success': True,
        'client_slug': cli_slug,
        'client_name': cli_name,
        'project_slug': proj_slug,
        'project_name': proj_name,
        'url': url,
        'created_at': created_at,
        'last_audit_at': last_audit_at,
        'audits': audits,
        'audit_count': len(audits),
        'path': f'clients/{cli_slug}/{proj_slug}'
    }


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description='Client and Project Manager')
    subparsers = parser.add_subparsers(dest='command', help='Command to execute')

    # add-client
    add_client_parser = subparsers.add_parser('add-client', help='Add a new client')
    add_client_parser.add_argument('--name', required=True, help='Client name')

    # add-project
    add_project_parser = subparsers.add_parser('add-project', help='Add a new project')
    add_project_parser.add_argument('--client', required=True, help='Client slug')
    add_project_parser.add_argument('--name', required=True, help='Project name')
    add_project_parser.add_argument('--url', required=True, help='Project URL')
    add_project_parser.add_argument('--industry', default='', help='Industry/sector')
    add_project_parser.add_argument('--tone', default='', help='Tone of voice description')
    add_project_parser.add_argument('--target-audience', default='', help='Target audience description')
    add_project_parser.add_argument('--competitors', default='', help='Comma-separated competitor URLs')
    add_project_parser.add_argument('--keywords', default='', help='Comma-separated focus keywords')
    add_project_parser.add_argument('--brand-notes', default='', help='Additional brand notes')

    # set-active
    set_active_parser = subparsers.add_parser('set-active', help='Set active project')
    set_active_parser.add_argument('--client', required=True, help='Client slug')
    set_active_parser.add_argument('--project', required=True, help='Project slug')

    # get-active
    subparsers.add_parser('get-active', help='Get active project')

    # list-clients
    subparsers.add_parser('list-clients', help='List all clients')

    # list-projects
    list_projects_parser = subparsers.add_parser('list-projects', help='List projects')
    list_projects_parser.add_argument('--client', help='Filter by client slug')

    # get-client
    get_client_parser = subparsers.add_parser('get-client', help='Get client details')
    get_client_parser.add_argument('--slug', required=True, help='Client slug')

    # get-project
    get_project_parser = subparsers.add_parser('get-project', help='Get project details')
    get_project_parser.add_argument('--client', required=True, help='Client slug')
    get_project_parser.add_argument('--project', required=True, help='Project slug')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    # Execute command
    try:
        if args.command == 'add-client':
            result = add_client(args.name)
        elif args.command == 'add-project':
            competitors = [c.strip() for c in args.competitors.split(',') if c.strip()] if args.competitors else None
            keywords = [k.strip() for k in args.keywords.split(',') if k.strip()] if args.keywords else None
            result = add_project(
                args.client, args.name, args.url,
                industry=args.industry,
                tone=args.tone,
                target_audience=getattr(args, 'target_audience', ''),
                competitors=competitors,
                focus_keywords=keywords,
                brand_notes=getattr(args, 'brand_notes', '')
            )
        elif args.command == 'set-active':
            result = set_active_project(args.client, args.project)
        elif args.command == 'get-active':
            result = get_active_project()
        elif args.command == 'list-clients':
            result = list_clients()
        elif args.command == 'list-projects':
            result = list_projects(args.client if hasattr(args, 'client') else None)
        elif args.command == 'get-client':
            result = get_client(args.slug)
        elif args.command == 'get-project':
            result = get_project(args.client, args.project)
        else:
            result = {'success': False, 'error': f'Unknown command: {args.command}'}

        print(json.dumps(result, indent=2))
        sys.exit(0 if result.get('success') else 1)

    except Exception as e:
        print(json.dumps({
            'success': False,
            'error': str(e)
        }), file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
