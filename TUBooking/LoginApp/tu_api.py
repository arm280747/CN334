"""TU REST API client for authenticating users via the institutional endpoint."""

import requests
from django.conf import settings


class TUAPIError(Exception):
    """Raised when the TU REST API cannot be reached or returns malformed data."""


def verify_credentials(username, password, timeout=10):
    """Verify a username/password pair against the TU REST API.

    Returns a dict of user data on success, or None when the credentials are
    rejected. Raises TUAPIError for transport or configuration problems.
    """

    app_key = getattr(settings, "TU_API_APP_KEY", "")
    if not app_key:
        raise TUAPIError("TU_API_APP_KEY is not configured in settings.")

    url = getattr(
        settings,
        "TU_API_URL",
        "https://restapi.tu.ac.th/api/v1/auth/Ad/verify",
    )

    headers = {
        "Content-Type": "application/json",
        "Application-Key": app_key,
    }
    payload = {"UserName": username, "PassWord": password}

    try:
        response = requests.post(url, json=payload, headers=headers, timeout=timeout)
    except requests.RequestException as exc:
        raise TUAPIError(f"Cannot reach TU REST API: {exc}") from exc

    try:
        data = response.json()
    except ValueError as exc:
        raise TUAPIError("TU REST API returned an invalid response.") from exc

    if response.status_code != 200 or not data.get("status"):
        return None

    return {
        "username": data.get("username", username),
        "tu_status": data.get("type") or data.get("tu_status"),
        "display_name_th": data.get("displayname_th", ""),
        "display_name_en": data.get("displayname_en", ""),
        "email": data.get("email", ""),
        "department": data.get("department", ""),
        "faculty": data.get("faculty", ""),
        "organization": data.get("organization", ""),
        "raw": data,
    }
