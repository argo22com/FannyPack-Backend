from django.contrib import admin

# Register your models here.
from payments.models import Room, Payment, User

admin.site.register(User)
admin.site.register(Room)
admin.site.register(Payment)
