from rest_framework.permissions import BasePermission

from accounts.models import User


class IsOwner(BasePermission):
	"""Allow access only to resources owned by the current user."""

	def has_object_permission(self, request, view, obj):
		if getattr(request.user, "role", None) == User.RoleChoices.ADMIN:
			return True

		return obj.created_by_id == request.user.id
