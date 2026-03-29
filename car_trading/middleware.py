"""
CurrentUserMiddleware
─────────────────────
Stores the current request user in a thread-local so that model signals
can retrieve it via `get_current_user()` without needing the request object.

Add to MIDDLEWARE in settings.py (after AuthenticationMiddleware):

    'car_trading.middleware.CurrentUserMiddleware',

Usage in signals:
    from car_trading.middleware import get_current_user
    user = get_current_user()
"""

import threading

_thread_local = threading.local()


def get_current_user():
    """Return the user attached to the current request thread, or None."""
    return getattr(_thread_local, "user", None)


class CurrentUserMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Stamp the authenticated user (or None) onto the thread-local.
        _thread_local.user = getattr(request, "user", None)
        try:
            response = self.get_response(request)
        finally:
            # Always clean up so the value never leaks to another request
            # served by the same thread.
            _thread_local.user = None
        return response
