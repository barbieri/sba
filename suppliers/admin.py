from suppliers.models import Supplier, SupplierInvoice, SupplierPayment
from django.contrib import admin

class SupplierPaymentInline(admin.TabularInline):
    model = SupplierPayment
    extra = 3

class SupplierPaymentAdmin(admin.ModelAdmin):
    list_display = ["invoice_supplier", "invoice_identifier", "date_due",
                    "value", "status"]
    list_filter = ["date_due", "status"]

    def invoice_supplier(self, o):
        return o.invoice.supplier

    def invoice_identifier(self, o):
        return o.invoice.identifier


class SupplierInvoiceAdmin(admin.ModelAdmin):
    inlines = [SupplierPaymentInline]
    list_display = ["identifier", "supplier", "date_due",
                    "declared_value", "total_value", "payments",
                    "status"]
    list_filter = ["supplier", "date_due", "status"]
    search_fields = ["supplier", "identifier"]


admin.site.register(Supplier)
admin.site.register(SupplierInvoice, SupplierInvoiceAdmin)
admin.site.register(SupplierPayment, SupplierPaymentAdmin)
