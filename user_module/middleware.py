from django.http import HttpResponse
from django.utils.crypto import get_random_string
import base64
from django.contrib.auth import logout
from django.utils.timezone import now, make_aware, is_naive
from django.shortcuts import redirect
import datetime
# myapp/middleware.py

from django.http import HttpResponse

class ContentTypeNosniffMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        response['X-Content-Type-Options'] = 'nosniff'
        return response


class SessionTimeoutMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            # Retrieve last activity from the session
            last_activity = request.session.get('last_activity')

            if last_activity:
                try:
                    last_activity = datetime.datetime.fromisoformat(last_activity)
                    # Convert to timezone-aware if naive
                    if is_naive(last_activity):
                        last_activity = make_aware(last_activity)
                except ValueError:
                    last_activity = None  # Reset if invalid

            # Check elapsed time
            if last_activity:
                elapsed_time = (now() - last_activity).total_seconds()

                # Debugging information
                print(f"Last activity time: {last_activity}")
                print(f"Current time: {now()}")
                print(f"Elapsed time since last activity: {elapsed_time} seconds")

                # Auto logout after timeout (15 minutes)
                if elapsed_time > 900:
                    print("Auto-logout: Timeout reached.")
                    logout(request)
                    return redirect('login')  # Redirect to login page after timeout
            # Update or initialize the last_activity timestamp
            request.session['last_activity'] = now().isoformat()

        return self.get_response(request)



from django.utils.deprecation import MiddlewareMixin

class CustomSecurityHeadersMiddleware(MiddlewareMixin):
    def process_response(self, request, response):
        response['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        response['X-Content-Type-Options'] = 'nosniff'
        response['X-Frame-Options'] = 'DENY'
        response['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains; preload'
        response['Permissions-Policy'] = 'geolocation=(self), microphone=()'  # Example Permissions-Policy header
        return response


class CSPNonceMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
 
    def __call__(self, request):
        nonce = base64.b64encode(get_random_string(16).encode()).decode()
        request.csp_nonce = nonce
        response = self.get_response(request)
       
        csp_parts = [
            "default-src 'self'",
            f"script-src  'nonce-{nonce}'",
            f"style-src 'self' 'unsafe-inline' https://fonts.googleapis.com https://cdn.jsdelivr.net https://cdnjs.cloudflare.com https://cdn.datatables.net https://cdnjs.cloudflare.com/ajax/libs/font-awesome/5.15.3/css/all.min.css https://maxcdn.bootstrapcdn.com/font-awesome/4.7.0/css/font-awesome.min.css https://cdn.jsdelivr.net/npm/sweetalert2@10.15.7/dist/sweetalert2.min.css https://cdnjs.cloudflare.com/ajax/libs/viewerjs/1.10.0/viewer.min.css",
            "font-src 'self' https://fonts.gstatic.com https://cdnjs.cloudflare.com https://maxcdn.bootstrapcdn.com https://cdn.jsdelivr.net https://cdn.datatables.net https://cdnjs.cloudflare.com https://cdn.jsdelivr.net/npm/sweetalert2@10.15.7/dist/sweetalert2.min.css https://cdnjs.cloudflare.com/ajax/libs/viewerjs/1.10.0/viewer.min.css https://flaticon.com",
            "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com https://cdn.jsdelivr.net https://cdnjs.cloudflare.com https://cdn.datatables.net https://cdnjs.cloudflare.com/ajax/libs/font-awesome/5.15.3/css/all.min.css https://maxcdn.bootstrapcdn.com/font-awesome/4.7.0/css/font-awesome.min.css https://cdn.jsdelivr.net/npm/sweetalert2@10.15.7/dist/sweetalert2.min.css https://cdnjs.cloudflare.com/ajax/libs/viewerjs/1.10.0/viewer.min.css https://flaticon.com",
            "img-src 'self' data: https://flaticon.com",
            "connect-src 'self'",
            "base-uri 'self'",
            "form-action 'self'",
        ]

        response['Content-Security-Policy'] = "; ".join(csp_parts)
        return response


class XPermittedCrossDomainPoliciesMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
 
    def __call__(self, request):
        response = self.get_response(request)
        response['X-Permitted-Cross-Domain-Policies'] = 'none'
        return response