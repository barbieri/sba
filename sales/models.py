from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator
from django.db.models import Sum
import datetime


def today():
    v = datetime.date.today()
    return datetime.datetime(v.year, v.month, v.day)


class CustomerGeoState(models.Model):
    name = models.CharField(max_length=50)
    code = models.CharField(max_length=2)

    def __unicode__(self):
        return u"%s - %s" % (self.code, self.name)

    class Meta:
        ordering = ["code"]
        verbose_name = "Customer State"


class CustomerCity(models.Model):
    name = models.CharField(max_length=50)
    state = models.ForeignKey(CustomerGeoState)

    def __unicode__(self):
        return u"%s-%s" % (self.name, self.state.code)

    class Meta:
        ordering = ["name"]


class Customer(models.Model):
    name = models.CharField(max_length=100)
    phone = models.CharField(max_length=50, blank=True)
    email = models.EmailField(blank=True)
    address = models.CharField(max_length=50, blank=True)
    neighborhood = models.CharField(max_length=30, blank=True)
    city = models.ForeignKey(CustomerCity, blank=True)
    zip = models.CharField(max_length=9, blank=True)
    note = models.TextField(blank=True)

    def __unicode__(self):
        return self.name

    class Meta:
        ordering = ["name"]


class Product(models.Model):
    identifier = models.CharField(max_length=50)
    description = models.CharField(max_length=100)
    note = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    cost = models.FloatField()

    def __unicode__(self):
        return self.identifier


class RevenueMethod(models.Model):
    name = models.CharField(max_length=30, unique=True)
    operation_cost = models.FloatField(default=0.0)
    percentual_cost = models.FloatField(default=0.0)
    is_active = models.BooleanField(default=True)

    def __unicode__(self):
        return self.name

    class Meta:
        ordering = ["name"]


class Sale(models.Model):
    datetime = models.DateTimeField(default=today)
    vendor = models.ForeignKey(User, blank=True, null=True)
    customer = models.ForeignKey(Customer, blank=True, null=True)
    value = models.FloatField(default=0.0,
                              help_text="Updated automatically on save.")
    discount = models.FloatField(default=0.0)

    def recalc(self):
        v = self.salerevenue_set.aggregate(Sum("value")).get("value__sum")
        if v is None:
            v = 0.0
        self.value = v
        self.save()

    def __unicode__(self):
        if self.vendor:
            return u"%s: %s (%s)" % (self.datetime.strftime("%Y-%m-%d %H:%M"),
                                     self.value, self.vendor)
        else:
            return u"%s: %s" % (self.datetime.strftime("%Y-%m-%d %H:%M"),
                                self.value)

    class Meta:
        ordering = ["datetime"]


class SaleProduct(models.Model):
    sale = models.ForeignKey(Sale)
    product = models.ForeignKey(Product, limit_choices_to={"is_active": True})
    count = models.IntegerField(validators=[MinValueValidator(1)])


class SaleRevenue(models.Model):
    sale = models.ForeignKey(Sale)
    date_due = models.DateField(default=datetime.date.today)
    value = models.FloatField(validators=[MinValueValidator(1.0)])

    # method is referenced, but operation_cost and percentual_cost are
    # copied from RevenueMethod at the moment of the sale. Values
    # should not change when the reference changes.
    method = models.ForeignKey(RevenueMethod,
                               limit_choices_to={"is_active": True})
    operation_cost = models.FloatField(default=0)
    percentual_cost = models.FloatField(default=0)
    net_value = models.FloatField(default=0)

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
