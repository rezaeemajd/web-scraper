from rest_framework.permissions import IsAuthenticatedOrReadOnly


class StaffWritePermission(IsAuthenticatedOrReadOnly):
    """Allow public reads; require staff users for API mutations."""

    def has_permission(self, request, view):
        if request.method in ("GET", "HEAD", "OPTIONS"):
            return True
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.is_staff
        )
