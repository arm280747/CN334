def session_role(request):
    """Expose session-scoped identity to every template."""
    return {
        "session_username": request.session.get("username"),
        "session_role": request.session.get("role"),
        "session_display_name": request.session.get("display_name"),
    }
