from django.db import models
from model_utils import Choices
from django.db.models.signals import post_save
from django.dispatch import receiver
# Create your models here.
from django_auth_ldap.backend import LDAPBackend
from django.contrib.auth.models import User


def name_email(self):
    return '{} {} ({})'.format(self.first_name,self.last_name,self.email)

User.add_to_class("__str__",name_email)


# class UserProfile(models.Model):
#     user = models.OneToOneField(User,on_delete=models.CASCADE)
#     userid = models.CharField(max_length=16)
#     role = models.CharField(max_length=16,null=True,blank=True)
#     firstname = models.CharField(max_length=64,null=True,blank=True)
#     lastname = models.CharField(max_length=64, blank=True, null=True)

#     # @property
#     # def is_faculty(self):
#     #     return self.role=='faculty'

#     # @property
#     # def is_student(self):
#     #     return self.role == 'student'

#     # @property
#     # def is_staff(self):
#     #     return self.role == 'staff'

#     # @property
#     # def is_others(self):
#     #     return self.role == 'others'


#     # def save(self,**kwargs):
#     #     return super().save(**kwargs)

    
#     # @receiver(post_save, sender=User)
#     # def create_user_profile(sender, instance, created, **kwargs):
#     #     if created:
#     #         UserProfile.objects.create(user=instance)

#     # @receiver(post_save, sender=User)
#     # def save_user_profile(sender, instance, **kwargs):
#     #     instance.profile.save()
#     class Meta:
#         app_label = 'account'

#     def __str__(self):
#         return self.user.username

# # class Profile(models.Model/

# class StudentProfile(models.Model):
#     # user = models.OneToOneField(User,on_delete=models.DO_NOTHING)
#     SECTION_CHOICES = (
#     ('ug1', 'BTech1'),
#     ('ug2', 'BTech2'),
#     ('ug3', 'BTech3'),
#     ('ug4', 'BTech4'),
#     ('dd', 'DualDegree'),
#     ('pg1', 'MTech1'),
#     ('pg2', 'Mtech2'),
#     ('pg3', 'MTech3'),
#     ('phd', 'PHD')
#     )

#     GENDER_CHOICES = (
#         ('f','Female'),
#         ('m','Male'),
#         ('o','Other')
#     )
#     userid = models.CharField(verbose_name="cse username", max_length=50,primary_key=True)
#     rollno = models.CharField(verbose_name="Roll No",max_length=16,null=True,blank=True)
#     firstname = models.CharField(verbose_name="Firstname",max_length=64,null=True,blank=True)
#     lastname = models.CharField(verbose_name="Lastname",max_length=64, blank=True, null=True)
#     interests = models.CharField(verbose_name="Academic Interests",max_length=500,null=True,blank=True)
#     gender = models.CharField(verbose_name="Gender", choices=GENDER_CHOICES,default='m',max_length=50)
#     section = models.CharField(verbose_name="Section", choices=SECTION_CHOICES,default='ug1',max_length=50)
#     ldap_section = models.CharField(verbose_name='Ldap_section', max_length=50,blank=True)
#     advisor  = models.CharField(verbose_name="Advisor", max_length=50,blank=True,null=True)
#     lastupdated = models.DateTimeField(auto_now=True)    

# class FacultyProfile(models.Model):
#     RETIRED_CHOICES = (
#         ('y','Retired Faculty'),
#         ('n','Current Faculty'),
#         ('v','Visiting Faculty'),
#         ('fv','Former Visiting'),
#         ('ca','Current Adjunct'),
#         ('fa','Former Adjunct'),
#         ('em','Emeritus')
#     )
#     userid =  models.CharField(verbose_name="cse username", max_length=50,blank=True,null=True)
#     firstname = models.CharField(verbose_name='Firstname', max_length=50,blank=True,null=True)
#     lastname = models.CharField(verbose_name='Lastname', max_length=50,blank=True,null=True)
#     interests = models.CharField(verbose_name='Research Interests', max_length=2048,blank=True,null=True)
#     extn = models.CharField(verbose_name='Office Extension Number', max_length=4,blank=True,null=True)
#     room  = models.CharField(verbose_name='Office ', max_length=50,blank=True,null=True)
#     retired = models.CharField(verbose_name='Category', choices=RETIRED_CHOICES, default='pythony',max_length=50,blank=True,null=True)
#     email =  models.EmailField(verbose_name='Email', max_length=254,blank=True,null=True)
#     extn_residence = models.CharField(verbose_name='Residence Extension', max_length=4,blank=True,null=True)
#     website = models.URLField(verbose_name='Website', max_length=200,blank=True,null=True)
#     dblp = models.URLField(verbose_name='DBLP Profile Link', max_length=200,blank=True,null=True)
#     lastupdated = models.DateTimeField(auto_now=True)

 
    

#     # def is_owner(self,request):
#     #     default = False
#     #     if request.user is not None:
#     #         default = (self.username == request.user.username)
#     #     return default

# class StaffProfile(models.Model):
#     TYPE_CHOICES = (
#         ('TS','Technical Staff'),
#         ('PS','Project Staff'),
#         ('NS(R)','Unknown'),
#         ('PE','Project Engineer'),
#         ('NS','Unknown')
#     )
#     userid = models.CharField(verbose_name='cse username', max_length=50,primary_key=True)
#     firstname = models.CharField(verbose_name='Firstname', max_length=50,blank=True,null=True)
#     lastname = models.CharField(verbose_name='Lastname', max_length=50,blank=True,null=True)
#     project = models.CharField(verbose_name='Role', choices=TYPE_CHOICES,max_length=50,blank=True,null=True)
#     guide = models.CharField(verbose_name='Guide', max_length=50,blank=True,null=True)

#     def __str__(self):
#         return self.userid
    

    

# class ExternalProfile(models.Model):
#     # TYPE_CHOICES = (
#     #     ('IN','Interns'),
#     #     ('PS','Project Staff')
#     # )
#     # username = models.CharField(verbose_name='cse username', max_length=50,blank=True,null=True)
#     # firstname = models.CharField(verbsoe_name='Firstname', max_length=50)
#     # lastname = models.CharField(verbose_name='Lastname', max_length=50)
#     # type = models.CharField(verbose_name='Type', max_length=50)
#     # # guide = models.ForeignKey("account.FacultyProfile", verbose_name='Guide', on_delete=models.)
#     # joindate = models.DateField(verbose_name='Joining Date', auto_now=False, auto_now_add=False,blank=True,null=True)
#     # guide = models.CharField(, max_length=50)

#     # def __str__(self):
#     #     return self.username
#     pass
