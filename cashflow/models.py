from django.db import models
from django.core.validators import MinValueValidator
from django.core.exceptions import ValidationError
from django.utils.translation import ugettext_lazy as _
import datetime


def color_validator(value):
    if value:
        if value[0] != "#":
            raise ValidationError(_(u"%s is not a valid #rrggbb color.") %
                                  (value,))
        try:
            a = int(value[1:], 16)
        except ValueError:
            raise ValidationError(_(u"%s is not a valid #rrggbb color.") %
                                  (value,))

class Tag(models.Model):
    name = models.CharField(_("Name"), max_length=30)
    color = models.CharField(_("Color"), max_length=7, default="#ffffff",
                             validators=[color_validator])
    note = models.TextField(_("Note"), blank=True)
    is_active = models.BooleanField(_("Is Active?"), default=True)

    def __unicode__(self):
        return self.name

    class Meta:
        ordering = ["is_active", "name"]
        verbose_name = _("Tag")
        verbose_name_plural = _("Tags")


class Balance(models.Model):
    TYPE_CHOICES = (
        ("C", _("Credit")),
        ("D", _("Debit")),
        )

    description = models.CharField(_("Description"), max_length=30)
    date = models.DateField(_("Date"), default=datetime.date.today)
    type = models.CharField(_("Type"), max_length=1, choices=TYPE_CHOICES,
                            default=TYPE_CHOICES[0][0])
    value = models.FloatField(_("Value"), validators=[MinValueValidator(1.0)])
    is_estimated = models.BooleanField(_("Is Estimated?"))
    note = models.TextField(_("Note"), blank=True)
    tags = models.ManyToManyField(Tag, limit_choices_to={"is_active": True},
                                  verbose_name=_("Tags"))

    def __unicode__(self):
        if not self.is_estimated:
            return self.description
        else:
            return u"%s*" % (self.description,)

    class Meta:
        ordering = ["date", "value"]
        verbose_name = _("Balance")
        verbose_name_plural = _("Balances")


class CostCenter(models.Model):
    name = models.CharField(_("Name"), max_length=30)
    color = models.CharField(_("Color"), max_length=7, default="#ffffff",
                             validators=[color_validator])
    note = models.TextField(_("Note"), blank=True)
    is_active = models.BooleanField(_("Is Active?"), default=True)

    def __unicode__(self):
        return self.name

    class Meta:
        verbose_name = _("Cost Center")
        verbose_name_plural = _("Cost Centers")


class Payment(models.Model):
    TYPE_CHOICES = (
        ("F", _("Fixed")),
        ("V", _("Variable")),
        )
    cost_center = models.ForeignKey(CostCenter, verbose_name=_("Cost Center"))
    description = models.CharField(_("Description"), max_length=30)
    date = models.DateField(_("Date"), default=datetime.date.today)
    type = models.CharField(_("Type"), max_length=1, choices=TYPE_CHOICES,
                            default=TYPE_CHOICES[0][0])
    value = models.FloatField(_("Value"), validators=[MinValueValidator(1.0)])
    is_estimated = models.BooleanField(_("Is Estimated?"))
    was_paid = models.BooleanField(_("Was Paid?"))
    note = models.TextField(_("Note"), blank=True)
    tags = models.ManyToManyField(Tag, limit_choices_to={"is_active": True},
                                  verbose_name=_("Tags"))

    def __unicode__(self):
        if not self.is_estimated:
            return self.description
        else:
            return u"%s*" % (self.description,)

    class Meta:
        ordering = ["date", "value"]
        verbose_name = _("Payment")
        verbose_name_plural = _("Payments")
