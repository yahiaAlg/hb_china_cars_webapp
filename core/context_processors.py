"""
Context processors for the core app.

Note: Most dashboard data is now fetched in the dashboard view directly
to have better control over calculations and avoid duplication.
This context processor provides minimal global data.
"""


def global_settings(request):
    """Provide minimal global settings to all templates"""
    if not request.user.is_authenticated:
        return {}

    return {
        "app_name": "HB China Cars",
        "app_version": "1.0.0",
    }
