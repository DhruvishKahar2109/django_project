from django.contrib.auth import get_user_model

class EmailBackend:
    def authenticate(self, request, email=None, password=None, **kwargs):

        User  = get_user_model()

        if email is None or password is None:
            return None

        email = email.strip()

        try:
            user = User.objects.get(email__iexact=email)
        except User.DoesNotExist:
            return None
        except User.MultipleObjectsReturned:
            return None

        if user.check_password(password) and user.is_active:
            return user

        return None

    def get_user(self, user_id):

        User = get_user_model()

        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None