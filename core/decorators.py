from functools import wraps
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect
from django.contrib import messages

def role_required(roles):
    """Decorator to require specific user roles"""
    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def wrapped_view(request, *args, **kwargs):
            if not hasattr(request.user, 'userprofile'):
                messages.error(request, "Profile non configuré. Contactez l'administrateur.")
                return redirect('core:dashboard')
            
            user_role = request.user.userprofile.role
            if user_role not in roles:
                messages.error(request, "Vous n'avez pas l'autorisation d'accéder à cette page.")
                return redirect('core:dashboard')
            
            return view_func(request, *args, **kwargs)
        return wrapped_view
    return decorator

def manager_required(view_func):
    """Decorator for manager-only views"""
    return role_required(['manager'])(view_func)

def finance_required(view_func):
    """Decorator for finance/manager views"""
    return role_required(['manager', 'finance'])(view_func)

def trader_required(view_func):
    """Decorator for trader/manager views"""
    return role_required(['manager', 'trader'])(view_func)