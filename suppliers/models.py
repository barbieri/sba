from django.db import models
from cashflow.models import Tag as CashFlowTag
from django.core.validators import MinValueValidator
import datetime

class Supplier(models.Model):
    name = models.CharField(max_length=100)
    phone = models.CharField(max_length=50, blank=True)
    email = models.EmailField(blank=True)
    note = models.TextField(blank=True)

    def __unicode__(self):
        return self.name


class SupplierInvoice(models.Model):
    STATUS_CHOICES = (
        ("R", "Received"),
        ("W", "Waiting"),
        )
    supplier = models.ForeignKey(Supplier)
    identifier = models.CharField(max_length=50)
    date_received = models.DateField(default=datetime.date.today)
    date_issue = models.DateField()
    date_due = models.DateField()
    note = models.TextField(blank=True)
    declared_value = models.FloatField(validators=[MinValueValidator(1.0)])
    status = models.CharField(max_length=1, choices=STATUS_CHOICES,
                              default=STATUS_CHOICES[0][0])
    tags = models.ManyToManyField(CashFlowTag,
                                  limit_choices_to={"is_active": True})

    def __unicode__(self):
        return u"%s (%s)" % (self.identifier, self.supplier)

    def total_value(self):
        total = 0.0
        for p in self.supplierpayment_set.all():
            total += p.value
        return total

    def payments(self):
        return self.supplierpayment_set.count()


class SupplierPayment(models.Model):
    STATUS_CHOICES = (
        ("R", "Received"),
        ("W", "Waiting"),
        ("P", "Paid"),
        )
    invoice = models.ForeignKey(SupplierInvoice)
    value = models.FloatField(validators=[MinValueValidator(1.0)])
    date_due = models.DateField()
    note = models.TextField(blank=True)
    status = models.CharField(max_length=1, choices=STATUS_CHOICES,
                              default=STATUS_CHOICES[0][0])
