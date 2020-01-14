from django.contrib import admin
from import_export import resources
from import_export.admin import ImportExportModelAdmin


from account.models import *

# Register your models here.
# @admin.register(UserProfile)
# class UserProfileAdmin(admin.ModelAdmin):
#     list_display = ['userid','role','firstname','lastname']

# Student Profiles
# class StudentResource(resources.ModelResource):
#     class Meta:
#         model = StudentProfile

# @admin.register(StudentProfile)
# class StudentProfileAdmin(ImportExportModelAdmin):
#     resource_class = StudentResource
#     list_display = ['userid','firstname','lastname','rollno','gender','section','lastupdated']


# # Faculty Profiles
# class FacultyResource(resources.ModelResource):
#     class Meta:
#         model = FacultyProfile

# @admin.register(FacultyProfile)
# class FacultyProfileAdmin(ImportExportModelAdmin):
#     resource_class = FacultyResource
#     list_display = ['userid','firstname','lastname','retired','extn','room','email','website']
#     list_filter = ['retired']


# #  Staff Profile
# class StaffResource(resources.ModelResource):
#     class Meta:
#         model = StaffProfile
#         import_id_fields = ('userid',)

# @admin.register(StaffProfile)
# class StaffProfileAdmin(ImportExportModelAdmin):
#     resource_class  = StaffResource
#     list_display = ['userid','firstname','lastname','project','guide']
#     list_filter = ['project','guide']

# @admin.register(ExternalProfile)
# class ExternalProfileAdmin(admin.ModelAdmin):
#     pass