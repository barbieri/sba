from django.db import models
from django.core.validators import MinValueValidator
from django.core.exceptions import ValidationError
import datetime


def color_validator(value):
    if value:
        if value[0] != "#":
            raise ValidationError(u"%s is not a valid #rrggbb color." %
                                  (value,))
        try:
            a = int(value[1:], 16)
        except ValueError:
            raise ValidationError(u"%s is not a valid #rrggbb color." %
                                  (value,))

class Tag(models.Model):
    name = models.CharField(max_length=30)
    color = models.CharField(max_length=7, default="#ffffff",
                             validators=[color_validator])
    note = models.TextField(blank=True)
    active = models.BooleanField(default=True)

    def __unicode__(self):
        return self.name


class Balance(models.Model):
    TYPE_CHOICES = (
        ("C", "Credit"),
        ("D", "Debit"),
        )

    description = models.CharField(max_length=30)
    date = models.DateField(default=datetime.date.today)
    type = models.CharField(max_length=1, choices=TYPE_CHOICES,
                            default=TYPE_CHOICES[0][0])
    value = models.FloatField(validators=[MinValueValidator(1.0)])
    estimated = models.BooleanField()
    note = models.TextField(blank=True)
    tags = models.ManyToManyField(Tag, limit_choices_to={"active": True})

    def __unicode__(self):
        if not self.estimated:
            return self.description
        else:
            return u"%s*" % (self.description,)


class CostCenter(models.Model):
    name = models.CharField(max_length=30)
    color = models.CharField(max_length=7, default="#ffffff",
                             validators=[color_validator])
    note = models.TextField(blank=True)
    active = models.BooleanField(default=True)

    def __unicode__(self):
        return self.name


class Payment(models.Model):
    TYPE_CHOICES = (
        ("F", "Fixed"),
        ("V", "Variable"),
        )
    cost_center = models.ForeignKey(CostCenter)
    description = models.CharField(max_length=30)
    date = models.DateField(default=datetime.date.today)
    type = models.CharField(max_length=1, choices=TYPE_CHOICES,
                            default=TYPE_CHOICES[0][0])
    value = models.FloatField(validators=[MinValueValidator(1.0)])
    estimated = models.BooleanField()
    paid = models.BooleanField()
    note = models.TextField(blank=True)
    tags = models.ManyToManyField(Tag, limit_choices_to={"active": True})

    def __unicode__(self):
        if not self.estimated:
            return self.description
        else:
            return u"%s*" % (self.description,)
