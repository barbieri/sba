from cashflow.models import Tag, Balance, CostCenter, Payment
from django.contrib import admin


class TagAdmin(admin.ModelAdmin):
    list_display = ["name", "note", "active"]
    list_filter = ["active"]
    search_fields = ["name", "note"]


class BalanceAdmin(admin.ModelAdmin):
    list_display = ["description", "date", "type", "value", "estimated",
                    "tag_list"]
    list_filter = ["date", "type", "estimated"]
    search_fields = ["description", "value"]

    def tag_list(self, o):
        return ", ".join(t.name for t in o.tags.all())


class CostCenterAdmin(admin.ModelAdmin):
    list_display = ["name", "note"]
    search_fields = ["name", "note"]


class PaymentAdmin(admin.ModelAdmin):
    list_display = ["description", "cost_center", "date", "value", "type",
                    "estimated", "paid", "tag_list"]
    list_filter = ["cost_center", "date", "type", "estimated", "paid"]
    search_fields = ["description", "value"]

    def tag_list(self, o):
        return ", ".join(t.name for t in o.tags.all())


admin.site.register(Balance, BalanceAdmin)
admin.site.register(CostCenter, CostCenterAdmin)
admin.site.register(Payment, PaymentAdmin)
admin.site.register(Tag, TagAdmin)
