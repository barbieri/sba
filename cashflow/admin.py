from cashflow.models import Tag, Balance, CostCenter, Payment
from django.contrib import admin
from django.db.models import Sum
from django.utils.translation import ugettext_lazy as _

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
    view_color.short_description = _("Color")


class BalanceAdmin(admin.ModelAdmin):
    list_display = ["description", "date", "type", "value", "is_estimated",
                    "tag_list"]
    list_filter = ["date", "type", "is_estimated", "tags"]
    search_fields = ["description", "value"]
    filter_horizontal = ("tags",)
    date_hierarchy = "date"
    actions = ["summary"]

    def tag_list(self, o):
        return ", ".join(tag2html(t) for t in o.tags.all())
    tag_list.allow_tags = True
    tag_list.short_description = _("Tags")

    def summary(self, request, queryset):
        message = ""

        count = queryset.count()
        if count < 1:
            message = _("No balance selected")
        else:
            q = queryset.filter(type="C")
            credits_count = len(q)
            credits_value = q.aggregate(Sum("value")).get("value__sum") or 0.0

            q = queryset.filter(type="D")
            debits_count = len(q)
            debits_value = q.aggregate(Sum("value")).get("value__sum") or 0.0

            if credits_count and debits_count:
                message = _(
                    "%(credits_count)d credits ($%(credits_value)0.2f), "
                    "%(debits_count)d debits ($%(debits_value)0.2f), "
                    "difference is $%(diff_value)0.2f") % \
                    {"credits_count": credits_count,
                     "credits_value": credits_value,
                     "debits_count": debits_count,
                     "debits_value": debits_value,
                     "diff_value": credits_value - debits_value,
                     }
            elif credits_count:
                message = _(
                    "%(credits_count)d credits ($%(credits_value)0.2f)") % \
                    {"credits_count": credits_count,
                     "credits_value": credits_value,
                     }
            elif debits_count:
                message = _(
                    "%(debits_count)d debits ($%(debits_value)0.2f)") % \
                    {"debits_count": debits_count,
                     "debits_value": debits_value,
                     }

        self.message_user(request, message)
    summary.short_description = _("Summary")


class CostCenterAdmin(admin.ModelAdmin):
    list_display = ["name", "view_color", "note"]
    search_fields = ["name", "note"]

    def view_color(self, o):
        return ('<span class="sba-tag" style="background-color: %s;">'
                '%s</span>') % \
                (o.color, o.color)
    view_color.allow_tags = True
    view_color.short_description = _("Color")


class PaymentAdmin(admin.ModelAdmin):
    list_display = ["description", "cost_center", "date", "value", "type",
                    "is_estimated", "was_paid", "tag_list"]
    list_filter = ["cost_center", "date", "type", "is_estimated", "was_paid",
                   "tags"]
    search_fields = ["description", "value"]
    filter_horizontal = ("tags",)
    date_hierarchy = "date"
    actions = ["summary"]

    def tag_list(self, o):
        return ", ".join(tag2html(t) for t in o.tags.all())
    tag_list.allow_tags = True
    tag_list.short_description = _("Tags")

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


admin.site.register(Balance, BalanceAdmin)
admin.site.register(CostCenter, CostCenterAdmin)
admin.site.register(Payment, PaymentAdmin)
admin.site.register(Tag, TagAdmin)
