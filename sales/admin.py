from sales.models import CustomerGeoState, CustomerCity, Customer, \
    Product, RevenueMethod, Sale, SaleProduct, SaleRevenue, \
    NonSaleReason, NonSale

from django.utils.translation import ugettext_lazy as _
from django.contrib import admin
from django.db.models import Sum
from django import forms


class CustomerCityInline(admin.TabularInline):
    model = CustomerCity
    extra = 3


class CustomerCityAdmin(admin.ModelAdmin):
    list_display = ["name", "state"]
    list_filter = ["state"]
    search_fields = ["name", "state__name", "state__code"]


class CustomerGeoStateAdmin(admin.ModelAdmin):
    inlines = [CustomerCityInline]
    list_display = ["code", "name"]
    list_filter = ["code"]
    search_fields = ["code", "name"]


class CustomerAdmin(admin.ModelAdmin):
    list_display = ["name", "phone", "email", "city"]
    list_filter = ["city"]
    search_fields = ["name", "phone", "email", "address", "neighborhood",
                     "city__name", "zip", "note"]


class ProductAdmin(admin.ModelAdmin):
    list_display = ["identifier", "description", "is_active", "cost"]
    list_filter = ["is_active"]
    search_fields = ["identifier", "description"]
    actions = ["make_inactive"]

    def make_inactive(self, request, queryset):
        rows_updated = queryset.update(is_active=False)
        if rows_updated < 1:
            message_bit = "No product"
        elif rows_updated == 1:
            message_bit = "1 product"
        else:
            message_bit = "%d products" % rows_updated
        self.message_user(request, _("%s marked as inactive") % message_bit)
    make_inactive.short_description = _("Mark selected as inactive")


class SaleRevenueInline(admin.TabularInline):
    model = SaleRevenue
    readonly_fields = ["operation_cost", "percentual_cost", "net_value"]
    extra = 3


class SaleProductInline(admin.TabularInline):
    model = SaleProduct
    extra = 5


class SaleAdmin(admin.ModelAdmin):
    inlines = [SaleRevenueInline, SaleProductInline]
    list_display = ["datetime", "seller", "customer", "value",
                    "discount", "product_count", "revenue_count"]
    list_filter = ["datetime", "seller", "customer", "discount"]
    search_fields = ["seller__first_name", "seller__last_name",
                     "seller__username", "customer__name"]
    date_hierarchy = "datetime"
    actions = ["summary"]
    readonly_fields = ["value"]

    def product_count(self, o):
        v = o.saleproduct_set.aggregate(Sum("count")).get("count__sum")
        if v:
            return v
        return ""
    product_count.short_description = _("Products")

    def revenue_count(self, o):
        return o.salerevenue_set.count()
    revenue_count.short_description = _("Revenues")

    def summary(self, request, queryset):
        message = ""

        count = queryset.count()
        if count < 1:
            message = _("No sales selected")
        else:
            revenue = 0.0
            discount = 0.0
            products = 0
            for o in queryset.all():
                revenue += o.value
                discount += o.discount
                products += o.saleproduct_set.aggregate(Sum("count")
                                                        ).get("count__sum")
            message = _("%(sales)d sales, %(products)d products "
                        "(%(average_products)0.1f average), "
                        "%(average_discount)0.0f%% average discount, "
                        "revenue %(revenue)0.2f "
                        "(%(average_revenue)0.2f average)") % \
                        {"sales": count,
                         "products": products,
                         "average_products": products / float(count),
                         "average_discount": discount / count,
                         "revenue": revenue,
                         "average_revenue": revenue / count,
                         }

        self.message_user(request, message)
    summary.short_description = _("Summary")


class RevenueMethodAdmin(admin.ModelAdmin):
    list_display = ["name", "operation_cost", "percentual_cost", "is_active"]


class NonSaleAdmin(admin.ModelAdmin):
    list_display = ["datetime", "seller", "customer", "reason", "note"]
    list_filter = ["datetime", "seller", "customer", "reason"]
    search_fields = ["seller__first_name", "seller__last_name",
                     "seller__username", "customer__name",
                     "reason__description", "note"]
    date_hierarchy = "datetime"


admin.site.register(CustomerGeoState, CustomerGeoStateAdmin)
admin.site.register(CustomerCity, CustomerCityAdmin)
admin.site.register(Customer, CustomerAdmin)
admin.site.register(Product, ProductAdmin)
admin.site.register(Sale, SaleAdmin)
admin.site.register(RevenueMethod, RevenueMethodAdmin)
admin.site.register(NonSaleReason)
admin.site.register(NonSale, NonSaleAdmin)
