from rest_framework import permissions
from apps.users.permissions import IsAdminUser


class IsAdmin(IsAdminUser):
    """
    Alias para IsAdminUser para claridad en el código
    """
    pass

