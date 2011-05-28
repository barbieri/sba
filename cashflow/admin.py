from cashflow.models import Balance, CostCenter, Payment
from django.contrib import admin

class BalanceAdmin(admin.ModelAdmin):
    list_display = ["description", "date", "type", "value", "estimated"]
    list_filter = ["date", "type", "estimated"]
    search_fields = ["description", "value"]


class CostCenterAdmin(admin.ModelAdmin):
    list_display = ["name", "note"]
    search_fields = ["name", "note"]


class PaymentAdmin(admin.ModelAdmin):
    list_display = ["description", "cost_center", "date", "value", "type",
                    "estimated", "paid"]
    list_filter = ["cost_center", "date", "type", "estimated", "paid"]
    search_fields = ["description", "value"]


admin.site.register(Balance, BalanceAdmin)
admin.site.register(CostCenter, CostCenterAdmin)
admin.site.register(Payment, PaymentAdmin)
