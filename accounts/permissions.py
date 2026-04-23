from rest_framework.permissions import BasePermission

from .models import User


class RoleBasedPermission(BasePermission):
	allowed_roles = set()

	def has_permission(self, request, view):
		user = request.user
		if not user or not user.is_authenticated:
			return False

		if user.is_superuser:
			return True

		return getattr(user, "role", None) in self.allowed_roles


class CanManagePatientsPermission(RoleBasedPermission):
	allowed_roles = {User.RoleChoices.ADMIN, User.RoleChoices.STAFF}


class CanViewDoctorsPermission(RoleBasedPermission):
	allowed_roles = {
		User.RoleChoices.ADMIN,
		User.RoleChoices.DOCTOR,
		User.RoleChoices.STAFF,
		User.RoleChoices.OPS,
	}


class CanManageDoctorsPermission(RoleBasedPermission):
	allowed_roles = {User.RoleChoices.ADMIN, User.RoleChoices.OPS}


class CanViewMappingsPermission(RoleBasedPermission):
	allowed_roles = {
		User.RoleChoices.ADMIN,
		User.RoleChoices.DOCTOR,
		User.RoleChoices.STAFF,
		User.RoleChoices.OPS,
	}


class CanManageMappingsPermission(RoleBasedPermission):
	allowed_roles = {
		User.RoleChoices.ADMIN,
		User.RoleChoices.STAFF,
		User.RoleChoices.OPS,
	}
