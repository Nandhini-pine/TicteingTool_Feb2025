from django.shortcuts import render, redirect
from django.contrib import auth
from django.contrib.auth.models import User
from django.contrib import messages
from datetime import datetime, time
from .adauth import authenticate_with_ldap  # Assuming this function exists for LDAP authentication
from master.models import *
from django.contrib.sessions.models import Session
from django.views.decorators.cache import cache_control
from django.utils.timezone import now
from django.utils.timezone import localtime
import json

@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def login(request):
    context = {}

    # If the user is already authenticated, log them out
    if request.user.is_authenticated:
        auth.logout(request)
        request.session.clear()

    if request.method == 'POST':
        username_or_email = request.POST['username']
        password = request.POST['password']

        print(f"User typed: {username_or_email}")
        print(f"Password entered: {password}")

        user_obj = None  # Initialize user_obj to avoid UnboundLocalError
        user_type = None  # Initialize user_type

        # Determine if the input is a username or email
        try:
            # Attempt to retrieve the user either by username or email
            if '@' in username_or_email:  # Email format check
                user_obj = User.objects.get(email=username_or_email)
            else:
                user_obj = User.objects.get(username=username_or_email)

            if not user_obj.is_active:
                print(f"User is deactivated: {username_or_email}")
                messages.error(request, "This user is deactivated. Kindly contact the admin.")
                return redirect('login')

            user_type_obj = UserType.objects.get(user=user_obj)
            user_type = user_type_obj.user_type
        except User.DoesNotExist:
            print(f"User does not exist: {username_or_email}")
        except UserType.DoesNotExist:
            print(f"UserType not set for user: {username_or_email}")
        
        if user_obj:  # Check if user_obj was successfully assigned
            # Check if the user is already logged in
            active_sessions = Session.objects.filter(expire_date__gte=now())
            for session in active_sessions:
                session_data = session.get_decoded()
                if session_data.get('_auth_user_id') == str(user_obj.id):
                    messages.error(request, "This user is already logged in. Please log out from the other session to continue.")
                    return redirect('login')

        if user_type == 'ad':
            print("User is an AD user (LDAP authentication)")
            
            # Authenticate using LDAP
            email = user_obj.email
            user = authenticate_with_ldap(request, username_or_email, email, password)

            if user is not None:
                print(f"AD User authenticated successfully: {username_or_email}")
                # Redirect based on group
                if user.groups.filter(name='CFAPerson').exists():
                    return redirect('base')
                elif user.groups.filter(name='Manager').exists():
                    return redirect('Manager_base')
                elif user.groups.filter(name='Engineer').exists():
                    return redirect('engineer_dashboard')
                elif user.groups.filter(name='Admin').exists():
                    return redirect('admin_dashboard')
                else:
                    return redirect('base')  # Default if no specific group matches
            else:
                print(f"AD User authentication failed: {username_or_email}")
                messages.error(request, "Invalid username or password.")
                return redirect('login')

        elif user_type == 'non_ad':
            print("User is a Non-AD user (Django authentication)")

            # Authenticate using Django
            user = auth.authenticate(username=user_obj.username, password=password)

            if user is not None and user.is_active:
                print(f"Non-AD User authenticated successfully: {username_or_email}")
                
                auth.login(request, user)

                # Redirect based on group
                if user.groups.filter(name='CFAPerson').exists():
                    return redirect('base')
                elif user.groups.filter(name='Manager').exists():
                    return redirect('Manager_base')
                elif user.groups.filter(name='Engineer').exists():
                    return redirect('engineer_dashboard')
                elif user.groups.filter(name='Admin').exists():
                    return redirect('admin_dashboard')

                return redirect('base')  # Default if no specific group matches
            else:
                print(f"Non-AD User authentication failed: {username_or_email}")
                messages.error(request, "Invalid username or password.")
                return redirect('login')
        else:
            print(f"Unknown user type or user not found: {username_or_email}")
            messages.error(request, "Invalid username or password.")
            return redirect('login')

    else:
        messages.get_messages(request)

        # Time-based welcome message
        current_time = datetime.now().time()
        if current_time < time(12):
            welcome_message = "Good Morning"
            slogan = "Start your day with enthusiasm and productivity!"
        elif current_time < time(18):
            welcome_message = "Good Afternoon"
            slogan = "Stay focused and make the most of your afternoon!"
        else:
            welcome_message = "Good Evening"
            slogan = "Reflect on your day and plan for tomorrow's success."

        context['welcome_message'] = welcome_message
        context['slogan'] = slogan

        return render(request, "Login/index.html", context)



def logout(request):

    auth.logout(request)
    request.session.clear()  # Clear session data
    return redirect('login')


def logout_all(request):
    # Get all sessions that have not expired
    active_sessions = Session.objects.filter(expire_date__gte=now())
    
    
    
    # Print active sessions in the terminal (for debugging)
    print("Active Sessions to log out:")
    for session in active_sessions:
        session_data = session.get_decoded()
        user_id = session_data.get('_auth_user_id')
        print(f"Session Key: {session.session_key}, User ID: {user_id}, Expiry: {session.expire_date}")

        # Delete session only if user ID is valid
        if user_id:
            session.delete()

    messages.success(request, "All active sessions have been logged out.")
    return redirect('login')  # Redirect to the login page

    

