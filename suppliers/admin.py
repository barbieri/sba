from suppliers.models import Supplier, SupplierInvoice, SupplierPayment
from django.contrib import admin

class SupplierPaymentInline(admin.TabularInline):
    model = SupplierPayment
    extra = 3

class SupplierPaymentAdmin(admin.ModelAdmin):
    list_display = ["invoice_supplier", "invoice_identifier", "date_due",
                    "value", "status", "note"]
    list_filter = ["date_due", "status"]
    date_hierarchy = "date_due"

    def invoice_supplier(self, o):
        return o.invoice.supplier

    def invoice_identifier(self, o):
        return o.invoice.identifier


class SupplierInvoiceAdmin(admin.ModelAdmin):
    inlines = [SupplierPaymentInline]
    list_display = ["identifier", "supplier", "date_due",
                    "declared_value", "total_value", "payments",
                    "status", "tag_list"]
    list_filter = ["supplier", "date_due", "status"]
    search_fields = ["supplier", "identifier"]
    filter_horizontal = ("tags",)
    date_hierarchy = "date_due"

    def tag_list(self, o):
        return ", ".join(t.name for t in o.tags.all())


admin.site.register(Supplier)
admin.site.register(SupplierInvoice, SupplierInvoiceAdmin)
admin.site.register(SupplierPayment, SupplierPaymentAdmin)
