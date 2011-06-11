from suppliers.models import Supplier, SupplierInvoice, SupplierPayment
from django.utils.translation import ugettext_lazy as _
from django.db.models import Sum
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
    actions = ["summary"]

    def invoice_supplier(self, o):
        return o.invoice.supplier
    invoice_supplier.short_description = _("Invoice Supplier")

    def invoice_identifier(self, o):
        return o.invoice.identifier
    invoice_identifier.short_description = _("Invoice Identifier")

    def summary(self, request, queryset):
        message = ""

        count = queryset.count()
        if count < 1:
            message = _("No payment selected")
        else:
            value = queryset.aggregate(Sum("value")).get("value__sum") or 0.0
            message = _(
                    "%(count)d payments ($%(value)0.2f)") % \
                    {"count": count, "value": value}

        self.message_user(request, message)
    summary.short_description = _("Summary")


class SupplierInvoiceAdmin(admin.ModelAdmin):
    inlines = [SupplierPaymentInline]
    list_display = ["identifier", "supplier", "date_due",
                    "declared_value", "total_value", "payments",
                    "status", "tag_list"]
    list_filter = ["supplier__name", "supplier", "date_due", "status"]
    search_fields = ["supplier__name", "identifier"]
    filter_horizontal = ("tags",)
    date_hierarchy = "date_due"
    actions = ["summary"]

    def tag_list(self, o):
        return ", ".join(t.name for t in o.tags.all())
    tag_list.short_description = _("Tags")

    def summary(self, request, queryset):
        message = ""

        count = queryset.count()
        if count < 1:
            message = _("No invoice selected")
        else:
            declared_value = queryset.aggregate(
                Sum("declared_value")).get("declared_value__sum") or 0.0
            payments_count = 0
            payments_value = 0.0
            for i in queryset:
                for p in i.supplierpayment_set.all():
                    payments_count += 1
                    payments_value += p.value
            message = _(
                    "%(invoices_count)d invoices declaring "
                    "$%(declared_value)0.2f, "
                    "%(payments_count)d payments ($%(payments_value)0.2f)") % \
                    {"invoices_count": count,
                     "declared_value": declared_value,
                     "payments_count": payments_count,
                     "payments_value": payments_value,
                     }

        self.message_user(request, message)
    summary.short_description = _("Summary")


admin.site.register(Supplier, SupplierAdmin)
admin.site.register(SupplierInvoice, SupplierInvoiceAdmin)
admin.site.register(SupplierPayment, SupplierPaymentAdmin)
