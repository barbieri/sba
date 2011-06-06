from django.db import models
from cashflow.models import Tag as CashFlowTag
from django.core.validators import MinValueValidator
from django.utils.translation import ugettext_lazy as _
import datetime

class Supplier(models.Model):
    name = models.CharField(_("Name"), max_length=100)
    phone = models.CharField(_("Phone"), max_length=50, blank=True)
    email = models.EmailField(_("Email"), blank=True)
    note = models.TextField(_("Note"), blank=True)

    class Meta:
        ordering = ["name"]
        verbose_name = _("Supplier")
        verbose_name_plural = _("Suppliers")

    def __unicode__(self):
        return self.name


class SupplierInvoice(models.Model):
    STATUS_CHOICES = (
        ("R", _("Received")),
        ("W", _("Waiting")),
        )
    supplier = models.ForeignKey(Supplier, verbose_name=_("Supplier"))
    identifier = models.CharField(_("Identifier"), max_length=50)
    date_received = models.DateField(_("Receive Date"),
                                     default=datetime.date.today)
    date_issue = models.DateField(_("Issue Date"))
    date_due = models.DateField(_("Due Date"))
    note = models.TextField(_("Note"), blank=True)
    declared_value = models.FloatField(_("Declared Value"),
                                       validators=[MinValueValidator(1.0)])
    status = models.CharField(_("Status"), max_length=1, choices=STATUS_CHOICES,
                              default=STATUS_CHOICES[0][0])
    tags = models.ManyToManyField(CashFlowTag, verbose_name=_("Tags"),
                                  limit_choices_to={"is_active": True})

    class Meta:
        ordering = ["date_due", "declared_value"]
        verbose_name = _("Supplier's Invoice")
        verbose_name_plural = _("Supplier's Invoices")

    def __unicode__(self):
        return u"%s (%s)" % (self.identifier, self.supplier)

    def total_value(self):
        total = 0.0
        for p in self.supplierpayment_set.all():
            total += p.value
        return total
    total_value.short_description = _("Total Value")

    def payments(self):
        return self.supplierpayment_set.count()
    payments.short_description = _("Payments")


class SupplierPayment(models.Model):
    STATUS_CHOICES = (
        ("R", _("Received")),
        ("W", _("Waiting")),
        ("P", _("Paid")),
        )
    invoice = models.ForeignKey(SupplierInvoice, verbose_name=_("Invoice"))
    value = models.FloatField(_("Value"), validators=[MinValueValidator(1.0)])
    date_due = models.DateField(_("Due Date"))
    note = models.TextField(_("Note"), blank=True)
    status = models.CharField(_("Status"), max_length=1, choices=STATUS_CHOICES,
                              default=STATUS_CHOICES[0][0])

    class Meta:
        ordering = ["date_due", "value"]
        verbose_name = _("Supplier's Payment")
        verbose_name_plural = _("Supplier's Payments")
