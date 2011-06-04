from sales.models import CustomerGeoState, CustomerCity, Customer, \
    Product, RevenueMethod, Sale, SaleProduct, SaleRevenue
from django.contrib import admin
from django.db.models import Sum
from django import forms


class CustomerCityInline(admin.TabularInline):
    model = CustomerCity
    extra = 3


class CustomerCityAdmin(admin.ModelAdmin):
    list_display = ["name", "state"]
    list_filter = ["state"]
    search_fields = ["name", "state"]


class CustomerGeoStateAdmin(admin.ModelAdmin):
    inlines = [CustomerCityInline]
    list_display = ["code", "name"]
    list_filter = ["code"]
    search_fields = ["code", "name"]


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
        self.message_user(request, "%s marked as inactive" % message_bit)
    make_inactive.short_description = "Mark selected as inactive"


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
    search_fields = ["seller", "customer"]
    date_hierarchy = "datetime"
    actions = ["summary"]
    readonly_fields = ["value"]

    def product_count(self, o):
        v = o.saleproduct_set.aggregate(Sum("count")).get("count__sum")
        if v:
            return v
        return ""
    product_count.short_description = "Products"

    def revenue_count(self, o):
        return o.salerevenue_set.count()
    revenue_count.short_description = "Revenues"

    def summary(self, request, queryset):
        message = ""

        count = queryset.count()
        if count < 1:
            message = "No sales selected"
        else:
            revenue = 0.0
            discount = 0.0
            products = 0
            for o in queryset.all():
                revenue += o.value
                discount += o.discount
                products += o.saleproduct_set.aggregate(Sum("count")
                                                        ).get("count__sum")
            message = ("%d sales, %d products (%0.1f average), "
                       "%0.0f%% average discount, "
                       "revenue %0.2f (%0.2f average)") % \
                       (count, products, products / float(count),
                        discount / count,
                        revenue, revenue / count)

        self.message_user(request, message)
    summary.short_description = "Summary"


admin.site.register(CustomerGeoState, CustomerGeoStateAdmin)
admin.site.register(CustomerCity, CustomerCityAdmin)
admin.site.register(Customer)
admin.site.register(Product, ProductAdmin)
admin.site.register(Sale, SaleAdmin)
admin.site.register(RevenueMethod)
