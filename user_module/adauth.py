# adauth.py
from django.contrib.auth import login
from ldap3 import Server, Connection, SIMPLE
from django.contrib.auth.models import User 
from datetime import timedelta


def authenticate_with_ldap(request, username, email, password):
    server = Server("ldaps://TCLBLRCORPDC04.titan.com:636")

    try:
        print(f"Attempting to authenticate {username} with email {email}")

        connection = Connection(server, user=email, password=password, authentication=SIMPLE, auto_bind=True)
        
        if connection.bind():
            print(f"Successfully authenticated {username} with email {email}")
            try:
                user = User.objects.get(email__iexact=email, is_active=True)  # Case-insensitive email match
                login(request, user)

                return user  # Return the user object on successful authentication
            except User.DoesNotExist:
                print(f"User {username} does not exist in local database.")
                return None  # Return None if the user does not exist in the local database
        else:
            print("Failed to bind to the LDAP server.")
            return None  # Return None if binding fails

    except Exception as e:
        print(f"LDAP authentication failed: {str(e)}")
        return None  # Return None if any exception occurs
