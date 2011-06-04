from cashflow.models import Tag, Balance, CostCenter, Payment
from django.contrib import admin

def tag2html(t):
    return '<span class="sba-tag" style="background-color: %s;">%s</span>' % \
        (t.color, t.name)


class TagAdmin(admin.ModelAdmin):
    list_display = ["name", "view_color", "is_active", "note"]
    list_filter = ["is_active"]
    search_fields = ["name", "note"]

    def view_color(self, o):
        return ('<span class="sba-tag" style="background-color: %s;">'
                '%s</span>') % \
                (o.color, o.color)
    view_color.allow_tags = True
    view_color.short_description = "Color"


class BalanceAdmin(admin.ModelAdmin):
    list_display = ["description", "date", "type", "value", "is_estimated",
                    "tag_list"]
    list_filter = ["date", "type", "is_estimated", "tags"]
    search_fields = ["description", "value"]
    filter_horizontal = ("tags",)

    def tag_list(self, o):
        return ", ".join(tag2html(t) for t in o.tags.all())
    tag_list.allow_tags = True
    tag_list.short_description = "Tags"


class CostCenterAdmin(admin.ModelAdmin):
    list_display = ["name", "view_color", "note"]
    search_fields = ["name", "note"]

    def view_color(self, o):
        return ('<span class="sba-tag" style="background-color: %s;">'
                '%s</span>') % \
                (o.color, o.color)
    view_color.allow_tags = True
    view_color.short_description = "Color"


class PaymentAdmin(admin.ModelAdmin):
    list_display = ["description", "cost_center", "date", "value", "type",
                    "is_estimated", "was_paid", "tag_list"]
    list_filter = ["cost_center", "date", "type", "is_estimated", "was_paid",
                   "tags"]
    search_fields = ["description", "value"]
    filter_horizontal = ("tags",)

    def tag_list(self, o):
        return ", ".join(tag2html(t) for t in o.tags.all())
    tag_list.allow_tags = True
    tag_list.short_description = "Tags"


admin.site.register(Balance, BalanceAdmin)
admin.site.register(CostCenter, CostCenterAdmin)
admin.site.register(Payment, PaymentAdmin)
admin.site.register(Tag, TagAdmin)
