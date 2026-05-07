#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from typing import Any, Dict, List


API_ROOT = "https://api.cloudflare.com/client/v4"


def required_env(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        print(f"Missing {name}.", file=sys.stderr)
        sys.exit(2)
    return value


def request(method: str, path: str, token: str, payload: Dict[str, Any] | None = None) -> Dict[str, Any]:
    body = json.dumps(payload).encode("utf-8") if payload is not None else None
    req = urllib.request.Request(
        f"{API_ROOT}{path}",
        data=body,
        method=method,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            data = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Cloudflare API {method} {path} failed: {detail}") from exc

    if not data.get("success"):
        raise RuntimeError(f"Cloudflare API {method} {path} failed: {data}")
    return data


def find_application(apps: List[Dict[str, Any]], domain: str) -> Dict[str, Any] | None:
    for app in apps:
        if app.get("domain") == domain:
            return app
        if domain in app.get("self_hosted_domains", []):
            return app
    return None


def main() -> None:
    token = required_env("CLOUDFLARE_API_TOKEN")
    account_id = required_env("CLOUDFLARE_ACCOUNT_ID")
    domain = os.getenv("PARALLAX_ACCESS_DOMAIN", "parallax.lunarchain.net").strip()
    app_name = os.getenv("PARALLAX_ACCESS_APP_NAME", "Parallax").strip()
    emails = [
        email.strip().lower()
        for email in required_env("PARALLAX_ALLOWED_EMAILS").split(",")
        if email.strip()
    ]
    if not emails:
        print("PARALLAX_ALLOWED_EMAILS must include at least one email.", file=sys.stderr)
        sys.exit(2)

    apps_path = f"/accounts/{account_id}/access/apps"
    search = urllib.parse.urlencode({"search": app_name})
    apps = request("GET", f"{apps_path}?{search}", token).get("result", [])
    app = find_application(apps, domain)
    app_payload = {
        "name": app_name,
        "type": "self_hosted",
        "domain": domain,
        "session_duration": os.getenv("PARALLAX_ACCESS_SESSION", "8h"),
        "auto_redirect_to_identity": True,
    }

    if app:
        app_id = app["id"]
        request("PUT", f"{apps_path}/{app_id}", token, app_payload)
        action = "updated"
    else:
        app = request("POST", apps_path, token, app_payload).get("result", {})
        app_id = app["id"]
        action = "created"

    policies_path = f"{apps_path}/{app_id}/policies"
    policies = request("GET", policies_path, token).get("result", [])
    policy = next((item for item in policies if item.get("name") == "Allow Parallax emails"), None)
    policy_payload = {
        "name": "Allow Parallax emails",
        "decision": "allow",
        "precedence": 1,
        "include": [{"email": {"email": email}} for email in emails],
        "session_duration": os.getenv("PARALLAX_ACCESS_SESSION", "8h"),
    }
    if policy:
        request("PUT", f"{policies_path}/{policy['id']}", token, policy_payload)
    else:
        request("POST", policies_path, token, policy_payload)

    print(f"Cloudflare Access {action} for {domain}; allowed emails: {', '.join(emails)}")


if __name__ == "__main__":
    main()
