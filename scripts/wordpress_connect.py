#!/usr/bin/env python3
"""
WordPress REST API Connection Manager

Manages WordPress connection credentials, validates authentication,
and tests REST API endpoints for SEO integration.

Usage:
    python wordpress_connect.py setup --project PATH --url URL --username USER --password PASS
    python wordpress_connect.py test --project PATH
    python wordpress_connect.py info --project PATH

Dependencies:
    pip install requests python-dotenv

Security:
    - Uses WordPress Application Passwords (not regular passwords)
    - Stores credentials in .env with 600 permissions
    - Credentials never logged or printed
    - HTTPS required for production connections
"""

import argparse
import base64
import json
import os
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional, Tuple

try:
    import requests
except ImportError:
    print(json.dumps({
        "success": False,
        "error": "requests library required. Install with: pip install requests"
    }))
    sys.exit(1)

try:
    from dotenv import load_dotenv, set_key
except ImportError:
    print(json.dumps({
        "success": False,
        "error": "python-dotenv library required. Install with: pip install python-dotenv"
    }))
    sys.exit(1)


class WordPressConnector:
    """Manages WordPress REST API connections for SEO projects."""

    def __init__(self, project_path: str):
        """
        Initialize WordPress connector for a project.

        Args:
            project_path: Path to project directory (e.g., clients/prova/test)
        """
        self.project_path = Path(project_path)
        self.env_path = self.project_path / ".env"
        self.config_path = self.project_path / "wordpress" / "config.json"

        # Ensure wordpress directory exists
        self.config_path.parent.mkdir(parents=True, exist_ok=True)

    def setup_connection(
        self,
        url: str,
        username: str,
        app_password: str,
        media_folder: str = "seo-optimized",
        verify_ssl: bool = True
    ) -> Dict:
        """
        Setup WordPress connection with credentials.

        Args:
            url: WordPress site URL (e.g., https://example.com)
            username: WordPress username
            app_password: WordPress Application Password
            media_folder: Custom media folder name
            verify_ssl: Verify SSL certificates

        Returns:
            Dict with success status and connection details
        """
        # Validate URL format
        if not url.startswith(('http://', 'https://')):
            return {
                "success": False,
                "error": "URL must include protocol (https:// or http://)"
            }

        # Remove trailing slash
        url = url.rstrip('/')

        # Warn about HTTP (insecure)
        if url.startswith('http://') and not url.startswith('http://localhost'):
            return {
                "success": False,
                "error": "HTTP connections are insecure. Please use HTTPS for production sites.",
                "warning": "HTTP is only allowed for localhost development"
            }

        # Clean up app password (remove spaces)
        app_password = app_password.replace(' ', '').strip()

        # Test connection before saving
        connection_test = self._test_auth(url, username, app_password, verify_ssl)

        if not connection_test["success"]:
            return connection_test

        # Save credentials to .env
        env_data = {
            "WP_URL": url,
            "WP_USERNAME": username,
            "WP_APP_PASSWORD": app_password,
            "WP_MEDIA_FOLDER": media_folder,
            "WP_VERIFY_SSL": str(verify_ssl).lower()
        }

        # Create .env file
        with open(self.env_path, 'w') as f:
            for key, value in env_data.items():
                f.write(f"{key}={value}\n")

        # Set secure permissions (owner read/write only)
        os.chmod(self.env_path, 0o600)

        # Get site info and save config
        site_info = self._get_site_info(url, username, app_password, verify_ssl)

        config_data = {
            "site_url": url,
            "site_title": site_info.get("name", "Unknown"),
            "site_description": site_info.get("description", ""),
            "wordpress_version": site_info.get("version", "Unknown"),
            "rest_api_version": "wp/v2",
            "connection_tested_at": datetime.now().isoformat(),
            "connection_status": "active",
            "endpoints": {
                "posts": f"{url}/wp-json/wp/v2/posts",
                "pages": f"{url}/wp-json/wp/v2/pages",
                "media": f"{url}/wp-json/wp/v2/media",
                "users": f"{url}/wp-json/wp/v2/users"
            },
            "media_folder": media_folder,
            "last_upload_at": None,
            "total_uploads": 0
        }

        # Save config
        with open(self.config_path, 'w') as f:
            json.dump(config_data, f, indent=2)

        return {
            "success": True,
            "message": "WordPress connection configured successfully",
            "site_title": site_info.get("name"),
            "site_url": url,
            "wordpress_version": site_info.get("version"),
            "env_path": str(self.env_path),
            "config_path": str(self.config_path),
            "endpoints": config_data["endpoints"]
        }

    def test_connection(self) -> Dict:
        """
        Test existing WordPress connection.

        Returns:
            Dict with connection status and site info
        """
        if not self.env_path.exists():
            return {
                "success": False,
                "error": ".env file not found",
                "path": str(self.env_path),
                "suggestion": "Run setup command first"
            }

        # Load credentials from .env
        load_dotenv(self.env_path)
        url = os.getenv("WP_URL")
        username = os.getenv("WP_USERNAME")
        app_password = os.getenv("WP_APP_PASSWORD")
        verify_ssl = os.getenv("WP_VERIFY_SSL", "true").lower() == "true"

        if not all([url, username, app_password]):
            return {
                "success": False,
                "error": "Incomplete credentials in .env file",
                "missing": [
                    k for k, v in {
                        "WP_URL": url,
                        "WP_USERNAME": username,
                        "WP_APP_PASSWORD": app_password
                    }.items() if not v
                ]
            }

        # Test authentication
        auth_result = self._test_auth(url, username, app_password, verify_ssl)

        if not auth_result["success"]:
            return auth_result

        # Get site info
        site_info = self._get_site_info(url, username, app_password, verify_ssl)

        # Update config with latest test
        if self.config_path.exists():
            with open(self.config_path, 'r') as f:
                config = json.load(f)
            config["connection_tested_at"] = datetime.now().isoformat()
            config["connection_status"] = "active"
            with open(self.config_path, 'w') as f:
                json.dump(config, f, indent=2)

        return {
            "success": True,
            "status": "connected",
            "site_title": site_info.get("name"),
            "site_url": url,
            "wordpress_version": site_info.get("version"),
            "rest_api": f"{url}/wp-json/",
            "tested_at": datetime.now().isoformat()
        }

    def get_info(self) -> Dict:
        """
        Get WordPress connection info.

        Returns:
            Dict with connection configuration
        """
        if not self.config_path.exists():
            return {
                "success": False,
                "error": "No WordPress configuration found",
                "suggestion": "Run setup command first"
            }

        with open(self.config_path, 'r') as f:
            config = json.load(f)

        # Load username from .env (mask password)
        if self.env_path.exists():
            load_dotenv(self.env_path)
            username = os.getenv("WP_USERNAME", "Unknown")
            config["username"] = username
            config["password"] = "********" + os.getenv("WP_APP_PASSWORD", "")[-4:]

        return {
            "success": True,
            **config
        }

    def _test_auth(
        self,
        url: str,
        username: str,
        app_password: str,
        verify_ssl: bool
    ) -> Dict:
        """
        Test WordPress authentication.

        Args:
            url: WordPress site URL
            username: WordPress username
            app_password: Application password
            verify_ssl: Verify SSL certificate

        Returns:
            Dict with authentication result
        """
        # Create auth header
        credentials = f"{username}:{app_password}"
        token = base64.b64encode(credentials.encode()).decode()
        headers = {"Authorization": f"Basic {token}"}

        # Test with /wp-json/wp/v2/users/me endpoint
        test_url = f"{url}/wp-json/wp/v2/users/me"

        try:
            response = requests.get(
                test_url,
                headers=headers,
                verify=verify_ssl,
                timeout=10
            )

            if response.status_code == 200:
                user_data = response.json()
                return {
                    "success": True,
                    "authenticated": True,
                    "user_id": user_data.get("id"),
                    "user_name": user_data.get("name"),
                    "capabilities": user_data.get("capabilities", {})
                }
            elif response.status_code == 401:
                return {
                    "success": False,
                    "error": "Authentication failed (401 Unauthorized)",
                    "details": "Invalid username or application password",
                    "suggestion": "Verify credentials and ensure Application Password is active"
                }
            elif response.status_code == 403:
                return {
                    "success": False,
                    "error": "Access forbidden (403 Forbidden)",
                    "details": "User does not have required permissions",
                    "suggestion": "Ensure user has Editor or Administrator role"
                }
            elif response.status_code == 404:
                return {
                    "success": False,
                    "error": "REST API not found (404)",
                    "details": "WordPress REST API may be disabled or URL is incorrect",
                    "suggestion": "Check if REST API is enabled and URL is correct"
                }
            else:
                return {
                    "success": False,
                    "error": f"Unexpected response (HTTP {response.status_code})",
                    "details": response.text[:200]
                }

        except requests.exceptions.SSLError:
            return {
                "success": False,
                "error": "SSL certificate verification failed",
                "suggestion": "Use --no-verify-ssl for self-signed certificates (development only)"
            }
        except requests.exceptions.ConnectionError:
            return {
                "success": False,
                "error": "Connection failed",
                "details": f"Cannot connect to {url}",
                "suggestion": "Verify URL is correct and site is accessible"
            }
        except requests.exceptions.Timeout:
            return {
                "success": False,
                "error": "Connection timeout",
                "details": "Server took too long to respond",
                "suggestion": "Check server performance or increase timeout"
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Unexpected error: {str(e)}"
            }

    def _get_site_info(
        self,
        url: str,
        username: str,
        app_password: str,
        verify_ssl: bool
    ) -> Dict:
        """
        Get WordPress site information.

        Args:
            url: WordPress site URL
            username: WordPress username
            app_password: Application password
            verify_ssl: Verify SSL certificate

        Returns:
            Dict with site information
        """
        credentials = f"{username}:{app_password}"
        token = base64.b64encode(credentials.encode()).decode()
        headers = {"Authorization": f"Basic {token}"}

        try:
            response = requests.get(
                f"{url}/wp-json/",
                headers=headers,
                verify=verify_ssl,
                timeout=10
            )

            if response.status_code == 200:
                return response.json()
            else:
                return {}

        except Exception:
            return {}


def main():
    """CLI interface for WordPress connection manager."""
    parser = argparse.ArgumentParser(
        description="WordPress REST API Connection Manager"
    )
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")

    # Setup command
    setup_parser = subparsers.add_parser("setup", help="Setup WordPress connection")
    setup_parser.add_argument("--project", required=True, help="Project path")
    setup_parser.add_argument("--url", required=True, help="WordPress site URL")
    setup_parser.add_argument("--username", required=True, help="WordPress username")
    setup_parser.add_argument("--password", required=True, help="Application password")
    setup_parser.add_argument("--media-folder", default="seo-optimized", help="Media folder name")
    setup_parser.add_argument("--no-verify-ssl", action="store_true", help="Disable SSL verification")

    # Test command
    test_parser = subparsers.add_parser("test", help="Test WordPress connection")
    test_parser.add_argument("--project", required=True, help="Project path")

    # Info command
    info_parser = subparsers.add_parser("info", help="Get connection info")
    info_parser.add_argument("--project", required=True, help="Project path")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    connector = WordPressConnector(args.project)

    if args.command == "setup":
        result = connector.setup_connection(
            url=args.url,
            username=args.username,
            app_password=args.password,
            media_folder=args.media_folder,
            verify_ssl=not args.no_verify_ssl
        )
    elif args.command == "test":
        result = connector.test_connection()
    elif args.command == "info":
        result = connector.get_info()
    else:
        result = {"success": False, "error": "Unknown command"}

    print(json.dumps(result, indent=2))
    sys.exit(0 if result.get("success") else 1)


if __name__ == "__main__":
    main()
