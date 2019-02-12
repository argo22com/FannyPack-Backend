from django.contrib import admin

# Register your models here.
from payments.models import Room, Payment, User, Split

admin.site.register(User)
admin.site.register(Room)


class SplitInline(admin.TabularInline):
    model = Split


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ['room', 'pledger', 'name', 'date']
    inlines = [
        SplitInline
    ]
