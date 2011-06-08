from suppliers.models import Supplier, SupplierInvoice, SupplierPayment
from django.utils.translation import ugettext_lazy as _
from django.contrib import admin

class SupplierAdmin(admin.ModelAdmin):
    list_display = ["name", "phone", "email"]
    search_fields = ["name", "phone", "email", "note"]


class SupplierPaymentInline(admin.TabularInline):
    model = SupplierPayment
    extra = 3


class SupplierPaymentAdmin(admin.ModelAdmin):
    list_display = ["invoice_supplier", "invoice_identifier", "date_due",
                    "value", "status", "note"]
    list_filter = ["invoice__supplier__name", "date_due", "value", "status"]
    search_fields = ["invoice__supplier__name",
                     "invoice__identifier", "date_due",
                     "value", "status", "note"]
    date_hierarchy = "date_due"

    def invoice_supplier(self, o):
        return o.invoice.supplier
    invoice_supplier.short_description = _("Invoice Supplier")

    def invoice_identifier(self, o):
        return o.invoice.identifier
    invoice_identifier.short_description = _("Invoice Identifier")


class SupplierInvoiceAdmin(admin.ModelAdmin):
    inlines = [SupplierPaymentInline]
    list_display = ["identifier", "supplier", "date_due",
                    "declared_value", "total_value", "payments",
                    "status", "tag_list"]
    list_filter = ["supplier__name", "supplier", "date_due", "status"]
    search_fields = ["supplier__name", "identifier"]
    filter_horizontal = ("tags",)
    date_hierarchy = "date_due"

    def tag_list(self, o):
        return ", ".join(t.name for t in o.tags.all())
    tag_list.short_description = _("Tags")


admin.site.register(Supplier, SupplierAdmin)
admin.site.register(SupplierInvoice, SupplierInvoiceAdmin)
admin.site.register(SupplierPayment, SupplierPaymentAdmin)
