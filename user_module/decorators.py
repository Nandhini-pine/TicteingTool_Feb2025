from django.http import HttpResponseRedirect
from functools import wraps
from django.contrib.auth import logout
from django.urls import reverse

def allowed_users(allowed_roles=[]):
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if request.user.groups.filter(name__in=allowed_roles).exists():
                return view_func(request, *args, **kwargs)
            else:
                logout(request)
                # Redirect to login page (or any other page you prefer)
                return HttpResponseRedirect(reverse('login')) 
        return wrapper
    return decorator
