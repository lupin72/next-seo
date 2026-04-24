# SEO WordPress Connection Manager

## Overview

Manages WordPress REST API connection for SEO projects. Checks for `.env` file in the active project directory, prompts for credentials if missing, validates connection, and enables WordPress integration for image optimization, content publishing, and metadata updates.

## Use Cases

- Initial WordPress connection setup for new projects
- Testing WordPress REST API connectivity
- Managing WordPress credentials securely
- Uploading optimized images to WordPress Media Library (future)
- Publishing SEO recommendations directly to WordPress (future)

## Commands

### `/seo-wordpress setup`

Sets up WordPress connection for the active project.

**Workflow:**
1. Checks if active project is set (via `/seo-project set`)
2. Looks for `.env` file in project directory: `clients/{client}/{project}/.env`
3. If `.env` exists, validates connection
4. If `.env` missing, prompts for credentials
5. Saves credentials to `.env` file
6. Tests connection with WordPress REST API
7. Creates `wordpress/config.json` with connection metadata

**Output:**
- Connection status (✅ Connected / ❌ Failed)
- WordPress site info (site title, version, REST API version)
- Available endpoints
- Confirmation of credential storage

---

### `/seo-wordpress test`

Tests existing WordPress connection.

**Actions:**
- Reads `.env` from active project directory
- Validates credentials
- Fetches site info via REST API
- Reports connection status

**Output:**
```
✅ WordPress Connection: OK

Site: Example WordPress Site
URL: https://example.com
Version: WordPress 6.5.2
REST API: /wp-json/wp/v2/

Endpoints Available:
  - /wp-json/wp/v2/posts
  - /wp-json/wp/v2/media
  - /wp-json/wp/v2/pages
```

---

### `/seo-wordpress info`

Displays current WordPress connection configuration.

**Output:**
- WordPress URL
- Username (masked)
- Connection status
- Last tested timestamp
- Configured endpoints

---

## WordPress Connection Parameters

### Required Parameters

**WP_URL** (Required)
- Full WordPress site URL
- Example: `https://example.com`
- Must include protocol (`https://` or `http://`)
- Do NOT include trailing slash

**WP_USERNAME** (Required)
- WordPress admin or editor username
- Example: `admin` or `editor@example.com`
- User must have permissions to:
  - Upload media (`upload_files` capability)
  - Edit posts/pages (`edit_posts` capability)

**WP_APP_PASSWORD** (Required)
- WordPress Application Password (NOT regular password)
- **How to generate:**
  1. WordPress Dashboard → Users → Your Profile
  2. Scroll to "Application Passwords" section
  3. Enter name: "Claude SEO Tools"
  4. Click "Add New Application Password"
  5. Copy the generated password (format: `xxxx xxxx xxxx xxxx xxxx xxxx`)
  6. Paste here (spaces will be removed automatically)

### Optional Parameters

**WP_MEDIA_FOLDER** (Optional)
- Custom folder for SEO-optimized images
- Default: `seo-optimized`
- Creates folder in WordPress Media Library

**WP_VERIFY_SSL** (Optional)
- Verify SSL certificate on HTTPS requests
- Default: `true`
- Set to `false` for local development with self-signed certificates

---

## .env File Format

**Location:** `clients/{client-slug}/{project-slug}/.env`

**Format:**
```bash
# WordPress REST API Connection
WP_URL=https://example.com
WP_USERNAME=admin
WP_APP_PASSWORD=xxxx xxxx xxxx xxxx xxxx xxxx

# Optional Configuration
WP_MEDIA_FOLDER=seo-optimized
WP_VERIFY_SSL=true
```

**Security:**
- ✅ `.env` files are gitignored by default
- ✅ File permissions set to `600` (owner read/write only)
- ✅ Never commit `.env` to version control
- ✅ Application passwords can be revoked anytime in WordPress

---

## WordPress config.json Format

**Location:** `clients/{client-slug}/{project-slug}/wordpress/config.json`

**Purpose:** Stores connection metadata and usage logs (NOT credentials)

**Format:**
```json
{
  "site_url": "https://example.com",
  "site_title": "Example WordPress Site",
  "wordpress_version": "6.5.2",
  "rest_api_version": "wp/v2",
  "connection_tested_at": "2026-04-23T18:30:00Z",
  "connection_status": "active",
  "endpoints": {
    "posts": "/wp-json/wp/v2/posts",
    "pages": "/wp-json/wp/v2/pages",
    "media": "/wp-json/wp/v2/media",
    "users": "/wp-json/wp/v2/users"
  },
  "capabilities": {
    "upload_media": true,
    "edit_posts": true,
    "publish_posts": true
  },
  "media_folder": "seo-optimized",
  "last_upload_at": null,
  "total_uploads": 0
}
```

---

## Implementation

### Python Script: `scripts/wordpress_connect.py`

**Purpose:** Manage WordPress connection, validate credentials, test endpoints

**Functions:**
1. `setup_connection(project_path, credentials)` - Create `.env` and test connection
2. `test_connection(project_path)` - Validate existing connection
3. `get_site_info(project_path)` - Fetch WordPress site metadata
4. `validate_credentials(url, username, app_password)` - Test REST API auth

**Dependencies:**
- `requests` - HTTP client for REST API
- `python-dotenv` - Parse `.env` files
- `json` - Config file management

**Usage:**
```bash
# Setup new connection
python scripts/wordpress_connect.py setup \
  --project clients/prova/test \
  --url https://example.com \
  --username admin \
  --password "xxxx xxxx xxxx xxxx"

# Test existing connection
python scripts/wordpress_connect.py test \
  --project clients/prova/test

# Get site info
python scripts/wordpress_connect.py info \
  --project clients/prova/test
```

---

## User Flow Example

**Scenario:** User runs `/seo-wordpress setup` for the first time

**Step 1: Check Active Project**
```
Checking active project...
✅ Active project: prova / test
   Path: clients/prova/test
```

**Step 2: Check for .env**
```
Checking for WordPress configuration...
❌ No .env file found in clients/prova/test/

Let's set up your WordPress connection.
```

**Step 3: Prompt for Credentials**

Use `AskUserQuestion` to collect credentials:

**Question 1: WordPress URL**
```
What is your WordPress site URL?

Example: https://example.com

⚠️ Important:
- Include protocol (https:// or http://)
- Do NOT include trailing slash
- Must be publicly accessible
```

**Question 2: WordPress Username**
```
What is your WordPress admin username?

Example: admin or your-email@example.com

This user must have:
✓ Media upload permissions
✓ Post/page editing permissions
```

**Question 3: Application Password**
```
WordPress Application Password:

⚠️ This is NOT your regular WordPress password!

How to generate an Application Password:
1. Log into WordPress Dashboard
2. Go to: Users → Your Profile
3. Scroll to "Application Passwords"
4. Name: "Claude SEO Tools"
5. Click "Add New Application Password"
6. Copy the generated password (format: xxxx xxxx xxxx xxxx)

Paste the password here:
```

**Step 4: Save & Test**
```
Saving credentials to clients/prova/test/.env...
✅ Credentials saved (file permissions: 600)

Testing connection...
Connecting to https://example.com/wp-json/...

✅ Connection successful!

Site Information:
  Title: Example WordPress Site
  Version: WordPress 6.5.2
  REST API: /wp-json/wp/v2/

Available Endpoints:
  ✓ Posts (/wp-json/wp/v2/posts)
  ✓ Pages (/wp-json/wp/v2/pages)
  ✓ Media (/wp-json/wp/v2/media)

Configuration saved to:
  clients/prova/test/wordpress/config.json

✅ WordPress connection ready!

Next steps:
  - Upload optimized images: /seo-wordpress upload
  - Sync content updates: /seo-wordpress sync
```

---

## Error Handling

### No Active Project Set

**Error:**
```
❌ No active project set.

Please set an active project first:
  /seo-project set "client-name" "project-name"

Or list available projects:
  /seo-project list
```

### Invalid WordPress URL

**Error:**
```
❌ Cannot connect to https://example.com

Possible issues:
  - URL is incorrect or unreachable
  - Site is not WordPress
  - REST API is disabled
  - Firewall blocking connection

Please verify:
  1. Site is accessible in browser
  2. WordPress REST API enabled
  3. URL format: https://example.com (no trailing slash)
```

### Invalid Credentials

**Error:**
```
❌ Authentication failed

HTTP 401: Unauthorized

Possible issues:
  - Username is incorrect
  - Application Password is incorrect or expired
  - Application Passwords not enabled in WordPress

Please verify:
  1. Username matches WordPress user
  2. Using Application Password (not regular password)
  3. Application Password is active (check Users → Your Profile)
```

### Insufficient Permissions

**Error:**
```
❌ User does not have required permissions

Missing capabilities:
  ✗ upload_files
  ✗ edit_posts

Please ensure your WordPress user has:
  - Editor or Administrator role
  - Media upload permissions
  - Post editing permissions
```

### REST API Disabled

**Error:**
```
❌ WordPress REST API is disabled

The WordPress REST API is required for this integration.

To enable:
  1. Check if security plugin is blocking REST API
  2. Disable "Disable REST API" plugins
  3. Add to wp-config.php:
     add_filter('rest_authentication_errors', '__return_true');
```

---

## Security Best Practices

### 1. Application Passwords (Not Regular Passwords)

**Always use Application Passwords**, never regular WordPress passwords:
- ✅ Can be revoked without changing main password
- ✅ Granular control (can revoke specific app access)
- ✅ Doesn't expose main password
- ✅ WordPress tracks usage per application

**How Users Generate Application Passwords:**
1. WordPress Dashboard → Users → Profile
2. Scroll to "Application Passwords" section
3. Enter name: "Claude SEO Tools"
4. Click "Add New Application Password"
5. Copy generated password immediately (shown only once)

### 2. File Permissions

**Automatically set `.env` file permissions to `600`:**
```bash
chmod 600 clients/prova/test/.env
```
- Owner: read + write
- Group: no access
- Others: no access

### 3. .gitignore

**Ensure `.env` is gitignored:**

Add to `.gitignore` (should already be present):
```
# WordPress credentials
**/.env
clients/**/.env

# WordPress config (contains site metadata, NOT credentials)
# This is safe to commit if you want to track connection metadata
# clients/**/wordpress/config.json
```

### 4. Credential Rotation

**Recommend rotating Application Passwords:**
- Every 90 days for production sites
- Immediately if credentials are exposed
- When team members leave

**How to rotate:**
1. Revoke old Application Password in WordPress
2. Generate new Application Password
3. Run `/seo-wordpress setup` again
4. Update `.env` with new password

### 5. HTTPS Only

**Require HTTPS for WordPress connections:**
- Credentials transmitted in Base64 encoding (not encrypted)
- HTTPS ensures credentials aren't intercepted
- Reject HTTP connections by default (warn user)

---

## Future Features (Planned)

### Phase 2: Image Upload
```
/seo-wordpress upload
```
- Upload optimized images from `images/optimized/` to WordPress Media Library
- Create custom folder in Media Library
- Track uploads in `wordpress/publish-log.json`
- Return WordPress Media IDs for use in content

### Phase 3: Content Sync
```
/seo-wordpress sync
```
- Sync SEO recommendations to WordPress posts/pages
- Update meta titles, descriptions
- Add/update schema markup
- Update alt text on images

### Phase 4: Metadata Management
```
/seo-wordpress metadata <post-id>
```
- Update Yoast SEO metadata via REST API
- Set focus keywords
- Configure social previews (Open Graph, Twitter Cards)
- Manage canonical URLs

---

## Integration with Other Skills

**This skill enables:**

1. **`/seo-images optimize`** (Phase 2)
   - Optimize images in `images/original/`
   - Upload to WordPress via `/seo-wordpress upload`

2. **`/seo-schema`**
   - Generate schema markup
   - Inject into WordPress pages via API

3. **`/seo-content`**
   - Analyze WordPress content remotely
   - Suggest improvements
   - Update content via API (with approval)

4. **`/seo-audit`**
   - Fetch live site data via WordPress API
   - Access unpublished drafts for review
   - Generate reports and post to WordPress as drafts

---

## WordPress API Reference

### Authentication

**Base64 Encoding:**
```
Authorization: Basic base64(username:application_password)
```

**Example Request:**
```bash
curl -X GET https://example.com/wp-json/wp/v2/posts \
  -H "Authorization: Basic $(echo -n 'admin:xxxx xxxx xxxx xxxx' | base64)"
```

### Common Endpoints

**Get Site Info:**
```
GET /wp-json/
```

**List Posts:**
```
GET /wp-json/wp/v2/posts
GET /wp-json/wp/v2/posts?per_page=100
GET /wp-json/wp/v2/posts?status=draft
```

**Upload Media:**
```
POST /wp-json/wp/v2/media
Content-Type: image/jpeg
Content-Disposition: attachment; filename="image.jpg"

[binary image data]
```

**Update Post Metadata (Yoast):**
```
PUT /wp-json/wp/v2/posts/{id}
{
  "meta": {
    "_yoast_wpseo_title": "SEO Title",
    "_yoast_wpseo_metadesc": "SEO Description",
    "_yoast_wpseo_focuskw": "keyword"
  }
}
```

---

## Testing Checklist

Before releasing to user:

- [ ] Can detect active project correctly
- [ ] Prompts for credentials if `.env` missing
- [ ] Validates WordPress URL format
- [ ] Tests connection successfully
- [ ] Creates `.env` with correct permissions (600)
- [ ] Creates `wordpress/config.json` with metadata
- [ ] Handles authentication errors gracefully
- [ ] Handles connection errors gracefully
- [ ] Masks password in terminal output
- [ ] Works with WordPress 6.0+
- [ ] Works with Application Passwords
- [ ] Detects disabled REST API and provides guidance

---

**Version:** 1.0.0
**Last Updated:** 2026-04-23
**Skill Type:** Integration / Infrastructure
**Dependencies:** `requests`, `python-dotenv`, `json`
