from rest_framework.permissions import BasePermission

class IsDataProvider(BasePermission):
    def has_permission(self, request, view):
        return request.user.groups.filter(name='DataProvider').exists()

class IsInstitutionManager(BasePermission):
    def has_permission(self, request, view):
        return request.user.groups.filter(name='InstitutionManager').exists()

class IsSeniorMoEOfficial(BasePermission):
    def has_permission(self, request, view):
        return request.user.groups.filter(name='SeniorMoEOfficial').exists()