from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator
from django.db.models import Sum
from django.utils.translation import ugettext_lazy as _
import datetime


def today():
    v = datetime.date.today()
    return datetime.datetime(v.year, v.month, v.day)


def next_month():
    v = datetime.date.today()
    if v.month < 12:
        return datetime.date(v.year, v.month + 1, 1)
    else:
        return datetime.date(v.year + 1, 1, 1)


class CustomerGeoState(models.Model):
    name = models.CharField(_("Name"), max_length=50)
    code = models.CharField(_("Code"), max_length=2)

    def __unicode__(self):
        return u"%s - %s" % (self.code, self.name)

    class Meta:
        ordering = ["code"]
        verbose_name = _("Customer State")
        verbose_name_plural = _("Customer States")


class CustomerCity(models.Model):
    name = models.CharField(_("Name"), max_length=50)
    state = models.ForeignKey(CustomerGeoState, verbose_name=_("State"))

    def __unicode__(self):
        return u"%s-%s" % (self.name, self.state.code)

    class Meta:
        ordering = ["name"]
        verbose_name = _("Customer City")
        verbose_name_plural = _("Customer Citys")


class Customer(models.Model):
    MONTHS = (
        (1, _("January")),
        (2, _("February")),
        (3, _("March")),
        (4, _("April")),
        (5, _("May")),
        (6, _("June")),
        (7, _("July")),
        (8, _("August")),
        (9, _("September")),
        (10, _("October")),
        (11, _("November")),
        (12, _("December")),
        )
    name = models.CharField(_("Name"), max_length=100)
    phone = models.CharField(_("Phone"), max_length=50, blank=True)
    mobile_phone = models.CharField(_("Mobile Phone"),
                                    max_length=50, blank=True)
    email = models.EmailField(_("Email"), blank=True)
    address = models.CharField(_("Address"), max_length=50, blank=True)
    neighborhood = models.CharField(_("Neighborhood"),
                                    max_length=30, blank=True)
    city = models.ForeignKey(CustomerCity, blank=True, verbose_name=_("City"))
    zip = models.CharField(_("Zip Code"), max_length=9, blank=True)
    note = models.TextField(_("Note"), blank=True)
    birth_day = models.IntegerField(_("Birth Day"), blank=True)
    birth_month = models.IntegerField(_("Birth Month"),
                                      choices=MONTHS, blank=True)

    def __unicode__(self):
        return self.name

    class Meta:
        ordering = ["name"]
        verbose_name = _("Customer")
        verbose_name_plural = _("Customers")


class Product(models.Model):
    identifier = models.CharField(_("Identifier"), max_length=50)
    description = models.CharField(_("Description"), max_length=100)
    note = models.TextField(_("Note"), blank=True)
    is_active = models.BooleanField(_("Is Active?"), default=True)
    cost = models.FloatField(_("Cost"))

    def __unicode__(self):
        return self.identifier

    class Meta:
        ordering = ["is_active", "identifier"]
        verbose_name = _("Product")
        verbose_name_plural = _("Products")


class RevenueMethod(models.Model):
    name = models.CharField(_("Name"), max_length=30, unique=True)
    operation_cost = models.FloatField(_("Operation Cost"), default=0.0)
    percentual_cost = models.FloatField(_("Percentual Cost"), default=0.0)
    is_active = models.BooleanField(_("Is Active?"), default=True)

    def __unicode__(self):
        return self.name

    class Meta:
        ordering = ["is_active", "name"]
        verbose_name = _("Revenue Method")
        verbose_name_plural = _("Revenue Methods")


class Sale(models.Model):
    datetime = models.DateTimeField(_("Date & Time"), default=today)
    seller = models.ForeignKey(User, blank=True, null=True,
                               verbose_name=_("Seller"))
    customer = models.ForeignKey(Customer, blank=True, null=True,
                                 verbose_name=_("Customer"))
    value = models.FloatField(_("Value"), default=0.0,
                              help_text=_("Updated automatically on save."))
    discount = models.FloatField(_("Discount (%)"), default=0.0)

    def recalc(self):
        v = self.salerevenue_set.aggregate(Sum("value")).get("value__sum")
        if v is None:
            v = 0.0
        self.value = v
        self.save()

    def __unicode__(self):
        if self.seller:
            return u"%s: %s (%s)" % (self.datetime.strftime("%Y-%m-%d %H:%M"),
                                     self.value, self.seller)
        else:
            return u"%s: %s" % (self.datetime.strftime("%Y-%m-%d %H:%M"),
                                self.value)

    class Meta:
        ordering = ["datetime"]
        verbose_name = _("Sale")
        verbose_name_plural = _("Sales")


class SaleProduct(models.Model):
    sale = models.ForeignKey(Sale, verbose_name=_("Sale"))
    product = models.ForeignKey(Product, limit_choices_to={"is_active": True},
                                verbose_name=_("Product"))
    count = models.IntegerField(_("Count"), validators=[MinValueValidator(1)])

    class Meta:
        verbose_name = _("Sale of Product")
        verbose_name_plural = _("Sale of Products")

    def __unicode__(self):
        return u"%d x %s" % (self.count, self.product)


class SaleRevenue(models.Model):
    sale = models.ForeignKey(Sale, verbose_name=_("Sale"))
    date_due = models.DateField(_("Due Date"), default=datetime.date.today)
    value = models.FloatField(_("Value"), validators=[MinValueValidator(1.0)])

    # method is referenced, but operation_cost and percentual_cost are
    # copied from RevenueMethod at the moment of the sale. Values
    # should not change when the reference changes.
    method = models.ForeignKey(RevenueMethod,
                               limit_choices_to={"is_active": True},
                               verbose_name=_("Revenue Method"))
    operation_cost = models.FloatField(_("Operation Cost"), default=0)
    percentual_cost = models.FloatField(_("Percentual Cost"), default=0)
    net_value = models.FloatField(_("Net Value"), default=0)

    class Meta:
        verbose_name = _("Revenue of Sale")
        verbose_name_plural = _("Revenues of Sale")

    def __unicode__(self):
        return u"%s: %s (%s)" % (self.date_due, self.value, self.method)

    def save(self):
        self.operation_cost = self.method.operation_cost
        self.percentual_cost = self.method.percentual_cost
        self.net_value = (self.value * ((100.0 - self.percentual_cost) / 100.0)
                          - self.operation_cost)
        super(SaleRevenue, self).save()
        self.sale.recalc()

    def delete(self):
        sale = self.sale
        super(SaleRevenue, self).delete()
        sale.recalc()


class NonSaleReason(models.Model):
    description = models.CharField(_("Description"), max_length=100)
    note = models.TextField(_("Note"), blank=True)

    class Meta:
        verbose_name = _("Non-Sale Reason")
        verbose_name_plural = _("Non-Sale Reasons")

    def __unicode__(self):
        return self.description


class NonSale(models.Model):
    datetime = models.DateTimeField(_("Date & Time"), default=today)
    seller = models.ForeignKey(User, verbose_name=_("Seller"))
    customer = models.ForeignKey(Customer, blank=True, null=True,
                                 verbose_name=_("Customer"))
    reason = models.ForeignKey(NonSaleReason, verbose_name=_("Reason"))
    note = models.TextField(_("Note"), blank=True)

    def __unicode__(self):
        return u"%s: %s (%s)" % (self.datetime.strftime("%Y-%m-%d %H:%M"),
                                 self.seller, self.reason)

    class Meta:
        ordering = ["datetime"]
        verbose_name = _("Non-Sale")
        verbose_name_plural = _("Non-Sales")


class MonthlyGoal(models.Model):
    start = models.DateField(_("Start Date"), default=next_month)
    seller = models.ForeignKey(User, blank=True, null=True,
                               verbose_name=_("Seller"),
                               help_text=_(
            "Leave blank to use as whole business goal."))
    total = models.FloatField(_("Total Value"))
    sales_ratio = models.FloatField(_("Sales Ratio (Percentage)"))
    products_ratio = models.FloatField(_("Products per Sale"))

    def __unicode__(self):
        if self.seller:
            return u"%s: $%0.2f (%s)" % (self.start, self.total, self.seller)
        else:
            return u"%s: $%0.2f" % (self.start, self.total)

    @classmethod
    def goals_for_period(cls, start, end, seller=None):
        queryset = cls.objects.filter(seller=seller)
        goals = list(queryset.filter(start__range=(start, end)
                                     ).order_by("start"))
        if not goals or goals[0].start != start:
            g = queryset.filter(start__lt=start).order_by("-start")[:1]
            if g:
                goals.insert(0, g[0])
        return goals

    class Meta:
        ordering = ["start"]
        verbose_name = _("Monthly Goal")
        verbose_name_plural = _("Monthly Goals")
