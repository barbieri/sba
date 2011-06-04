from sales.models import Sale, NonSale

from django.shortcuts import render_to_response
from django.template import RequestContext
from django.db.models import Sum
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django import forms
import datetime
import settings

def last_month():
    now = datetime.date.today()
    if now.month == 1:
        return datetime.date(now.year - 1, 1, 1)
    else:
        return datetime.date(now.year, now.month - 1, 1)


class PeriodForm(forms.Form):
    start = forms.DateField(initial=last_month)
    end = forms.DateField(initial=datetime.date.today)



SELLERS_QUERY = User.objects.filter(is_active=True,
                                    groups__name=settings.SBA_SELLER_GROUP)

class SellerPeriodForm(PeriodForm):
    seller = forms.ChoiceField(required=False)


@login_required
def sellers_daily(request):
    sellers = []
    sellers_choices = [("", "All")] + [(o.id, o.get_full_name()) for o in
                                       SELLERS_QUERY.order_by("first_name")]

    t_sales_count = 0
    t_sales_total = 0.0
    t_sales_discount_total = 0.0
    t_sales_discount_count = 0
    t_sales_products_count = 0
    t_non_sales_count = 0

    if request.method != "POST":
        form = SellerPeriodForm()
        form.fields["seller"].choices = sellers_choices
    else:
        form = SellerPeriodForm(request.POST)
        form.fields["seller"].choices = sellers_choices
        if form.is_valid():
            q = SELLERS_QUERY
            if form.cleaned_data["seller"]:
                q = q.filter(id=form.cleaned_data["seller"])

            period = (form.cleaned_data["start"], form.cleaned_data["end"])
            sales = Sale.objects.filter(datetime__range=period)
            non_sales = NonSale.objects.filter(datetime__range=period)

            for u in q:
                u_sales_count = 0
                u_sales_total = 0.0
                u_sales_discount_total = 0.0
                u_sales_discount_count = 0
                u_sales_products_count = 0
                u_non_sales_count = 0
                u_data = {}
                for s in sales.filter(seller=u):
                    products = s.saleproduct_set.aggregate(
                        Sum("count")).get("count__sum")
                    if products is None:
                        products = 0

                    if s.discount > 0:
                        discount_value = s.discount
                        discount_count = 1
                    else:
                        discount_value = 0
                        discount_count = 0

                    u_sales_count += 1
                    u_sales_total += s.value
                    u_sales_discount_total += discount_value
                    u_sales_discount_count += discount_count
                    u_sales_products_count += products

                    date = (s.datetime.year, s.datetime.month, s.datetime.day)
                    c_data = {
                        "operations": 1,
                        "non_sales": 0,
                        "sales": 1,
                        "value": s.value,
                        "discount_count": discount_count,
                        "discount_value": discount_value,
                        "products": products,
                        }
                    d_data = u_data.get(date)
                    if d_data is None:
                        d_data = {
                            "operations": 0,
                            "non_sales": 0,
                            "sales": 0,
                            "value": 0.0,
                            "discount_count": 0,
                            "discount_value": 0.0,
                            "products": 0,
                            }
                    u_data[date] = x = {}
                    for k, cv in c_data.iteritems():
                        x[k] = cv + d_data[k]

                for s in non_sales.filter(seller=u):
                    u_non_sales_count += 1
                    date = (s.datetime.year, s.datetime.month, s.datetime.day)
                    c_data = {
                        "operations": 1,
                        "non_sales": 1,
                        "sales": 0,
                        "value": 0.0,
                        "discount_count": 0,
                        "discount_value": 0.0,
                        "products": 0,
                        }
                    d_data = u_data.get(date)
                    if d_data is None:
                        d_data = {
                            "operations": 0,
                            "non_sales": 0,
                            "sales": 0,
                            "value": 0.0,
                            "discount_count": 0,
                            "discount_value": 0.0,
                            "products": 0,
                            }
                    u_data[date] = x = {}
                    for k, cv in c_data.iteritems():
                        x[k] = cv + d_data[k]

                u_data = list({"date": a, "data": b}
                              for a, b in u_data.iteritems())
                u_data.sort(lambda a, b: cmp(a["date"][0], b["date"][0]))

                t_sales_count += u_sales_count
                t_sales_total += u_sales_total
                t_sales_discount_total += u_sales_discount_total
                t_sales_discount_count += u_sales_discount_count
                t_sales_products_count += u_sales_products_count
                t_non_sales_count += u_non_sales_count
                sellers.append({
                        "name": u.get_full_name(),
                        "operations": u_sales_count + u_non_sales_count,
                        "non_sales": u_non_sales_count,
                        "sales": u_sales_count,
                        "value": u_sales_total,
                        "discount_count": u_sales_discount_count,
                        "discount_value": u_sales_discount_total,
                        "products": u_sales_products_count,
                        "data": u_data,
                        })

    days = {}
    for i, row in enumerate(sellers):
        for r in row["data"]:
            date = r["date"]
            data = r["data"]
            d = days.get(date)
            if d is None:
                d = [{"operations": 0,
                      "non_sales": 0,
                      "sales": 0,
                      "value": 0.0,
                      "discount_count": 0,
                      "discount_value": 0.0,
                      "products": 0,
                      }] * len(sellers)
                days[date] = d
            d[i] = data

    days = list(days.iteritems())
    days.sort(lambda a, b: cmp(a[0], b[0]))
    ctxt = {
        "form": form,
        "sellers": sellers,
        "days": days,
        "total_operations": t_sales_count + t_non_sales_count,
        "total_sales": t_sales_count,
        "total_value": t_sales_total,
        "total_non_sales": t_non_sales_count,
        "total_discount_count": t_sales_discount_count,
        "total_discount_value": t_sales_discount_total,
        "total_products": t_sales_products_count,
        }
    return render_to_response('sales/sellers/daily.html', ctxt,
                              context_instance=RequestContext(request))

@login_required
def sellers_weekly(request):
    sellers = []
    sellers_choices = [("", "All")] + [(o.id, o.get_full_name()) for o in
                                       SELLERS_QUERY.order_by("first_name")]

    t_sales_count = 0
    t_sales_total = 0.0
    t_sales_discount_total = 0.0
    t_sales_discount_count = 0
    t_sales_products_count = 0
    t_non_sales_count = 0

    if request.method != "POST":
        form = SellerPeriodForm()
        form.fields["seller"].choices = sellers_choices
    else:
        form = SellerPeriodForm(request.POST)
        form.fields["seller"].choices = sellers_choices
        if form.is_valid():
            q = SELLERS_QUERY
            if form.cleaned_data["seller"]:
                q = q.filter(id=form.cleaned_data["seller"])

            period = (form.cleaned_data["start"], form.cleaned_data["end"])
            sales = Sale.objects.filter(datetime__range=period)
            non_sales = NonSale.objects.filter(datetime__range=period)

            for u in q:
                u_sales_count = 0
                u_sales_total = 0.0
                u_sales_discount_total = 0.0
                u_sales_discount_count = 0
                u_sales_products_count = 0
                u_non_sales_count = 0
                u_data = {}
                for s in sales.filter(seller=u):
                    products = s.saleproduct_set.aggregate(
                        Sum("count")).get("count__sum")
                    if products is None:
                        products = 0

                    if s.discount > 0:
                        discount_value = s.discount
                        discount_count = 1
                    else:
                        discount_value = 0
                        discount_count = 0

                    u_sales_count += 1
                    u_sales_total += s.value
                    u_sales_discount_total += discount_value
                    u_sales_discount_count += discount_count
                    u_sales_products_count += products

                    week = (s.datetime.year, s.datetime.isocalendar()[1])
                    c_data = {
                        "operations": 1,
                        "non_sales": 0,
                        "sales": 1,
                        "value": s.value,
                        "discount_count": discount_count,
                        "discount_value": discount_value,
                        "products": products,
                        }
                    d_data = u_data.get(week)
                    if d_data is None:
                        d_data = {
                            "operations": 0,
                            "non_sales": 0,
                            "sales": 0,
                            "value": 0.0,
                            "discount_count": 0,
                            "discount_value": 0.0,
                            "products": 0,
                            }
                    u_data[week] = x = {}
                    for k, cv in c_data.iteritems():
                        x[k] = cv + d_data[k]

                for s in non_sales.filter(seller=u):
                    u_non_sales_count += 1
                    week = (s.datetime.year, s.datetime.isocalendar()[1])
                    c_data = {
                        "operations": 1,
                        "non_sales": 1,
                        "sales": 0,
                        "value": 0.0,
                        "discount_count": 0,
                        "discount_value": 0.0,
                        "products": 0,
                        }
                    d_data = u_data.get(week)
                    if d_data is None:
                        d_data = {
                            "operations": 0,
                            "non_sales": 0,
                            "sales": 0,
                            "value": 0.0,
                            "discount_count": 0,
                            "discount_value": 0.0,
                            "products": 0,
                            }
                    u_data[week] = x = {}
                    for k, cv in c_data.iteritems():
                        x[k] = cv + d_data[k]

                u_data = list({"week": a, "data": b}
                              for a, b in u_data.iteritems())
                u_data.sort(lambda a, b: cmp(a["week"][0], b["week"][0]))

                t_sales_count += u_sales_count
                t_sales_total += u_sales_total
                t_sales_discount_total += u_sales_discount_total
                t_sales_discount_count += u_sales_discount_count
                t_sales_products_count += u_sales_products_count
                t_non_sales_count += u_non_sales_count
                sellers.append({
                        "name": u.get_full_name(),
                        "operations": u_sales_count + u_non_sales_count,
                        "non_sales": u_non_sales_count,
                        "sales": u_sales_count,
                        "value": u_sales_total,
                        "discount_count": u_sales_discount_count,
                        "discount_value": u_sales_discount_total,
                        "products": u_sales_products_count,
                        "data": u_data,
                        })

    weeks = {}
    for i, row in enumerate(sellers):
        for r in row["data"]:
            week = r["week"]
            data = r["data"]
            d = weeks.get(week)
            if d is None:
                d = [{"operations": 0,
                      "non_sales": 0,
                      "sales": 0,
                      "value": 0.0,
                      "discount_count": 0,
                      "discount_value": 0.0,
                      "products": 0,
                      }] * len(sellers)
                weeks[week] = d
            d[i] = data

    weeks = list(weeks.iteritems())
    weeks.sort(lambda a, b: cmp(a[0], b[0]))
    ctxt = {
        "form": form,
        "sellers": sellers,
        "weeks": weeks,
        "total_operations": t_sales_count + t_non_sales_count,
        "total_sales": t_sales_count,
        "total_value": t_sales_total,
        "total_non_sales": t_non_sales_count,
        "total_discount_count": t_sales_discount_count,
        "total_discount_value": t_sales_discount_total,
        "total_products": t_sales_products_count,
        }
    return render_to_response('sales/sellers/weekly.html', ctxt,
                              context_instance=RequestContext(request))

@login_required
def sellers_monthly(request):
    sellers = []
    sellers_choices = [("", "All")] + [(o.id, o.get_full_name()) for o in
                                       SELLERS_QUERY.order_by("first_name")]

    t_sales_count = 0
    t_sales_total = 0.0
    t_sales_discount_total = 0.0
    t_sales_discount_count = 0
    t_sales_products_count = 0
    t_non_sales_count = 0

    if request.method != "POST":
        form = SellerPeriodForm()
        form.fields["seller"].choices = sellers_choices
    else:
        form = SellerPeriodForm(request.POST)
        form.fields["seller"].choices = sellers_choices
        if form.is_valid():
            q = SELLERS_QUERY
            if form.cleaned_data["seller"]:
                q = q.filter(id=form.cleaned_data["seller"])

            period = (form.cleaned_data["start"], form.cleaned_data["end"])
            sales = Sale.objects.filter(datetime__range=period)
            non_sales = NonSale.objects.filter(datetime__range=period)

            for u in q:
                u_sales_count = 0
                u_sales_total = 0.0
                u_sales_discount_total = 0.0
                u_sales_discount_count = 0
                u_sales_products_count = 0
                u_non_sales_count = 0
                u_data = {}
                for s in sales.filter(seller=u):
                    products = s.saleproduct_set.aggregate(
                        Sum("count")).get("count__sum")
                    if products is None:
                        products = 0

                    if s.discount > 0:
                        discount_value = s.discount
                        discount_count = 1
                    else:
                        discount_value = 0
                        discount_count = 0

                    u_sales_count += 1
                    u_sales_total += s.value
                    u_sales_discount_total += discount_value
                    u_sales_discount_count += discount_count
                    u_sales_products_count += products

                    month = (s.datetime.year, s.datetime.month,
                             s.datetime.strftime("%B %Y"))
                    c_data = {
                        "operations": 1,
                        "non_sales": 0,
                        "sales": 1,
                        "value": s.value,
                        "discount_count": discount_count,
                        "discount_value": discount_value,
                        "products": products,
                        }
                    d_data = u_data.get(month)
                    if d_data is None:
                        d_data = {
                            "operations": 0,
                            "non_sales": 0,
                            "sales": 0,
                            "value": 0.0,
                            "discount_count": 0,
                            "discount_value": 0.0,
                            "products": 0,
                            }
                    u_data[month] = x = {}
                    for k, cv in c_data.iteritems():
                        x[k] = cv + d_data[k]

                for s in non_sales.filter(seller=u):
                    u_non_sales_count += 1
                    month = (s.datetime.year, s.datetime.month,
                             s.datetime.strftime("%B %Y"))
                    c_data = {
                        "operations": 1,
                        "non_sales": 1,
                        "sales": 0,
                        "value": 0.0,
                        "discount_count": 0,
                        "discount_value": 0.0,
                        "products": 0,
                        }
                    d_data = u_data.get(month)
                    if d_data is None:
                        d_data = {
                            "operations": 0,
                            "non_sales": 0,
                            "sales": 0,
                            "value": 0.0,
                            "discount_count": 0,
                            "discount_value": 0.0,
                            "products": 0,
                            }
                    u_data[month] = x = {}
                    for k, cv in c_data.iteritems():
                        x[k] = cv + d_data[k]

                u_data = list({"month": a, "data": b}
                              for a, b in u_data.iteritems())
                u_data.sort(lambda a, b: cmp(a["month"][0], b["month"][0]))

                t_sales_count += u_sales_count
                t_sales_total += u_sales_total
                t_sales_discount_total += u_sales_discount_total
                t_sales_discount_count += u_sales_discount_count
                t_sales_products_count += u_sales_products_count
                t_non_sales_count += u_non_sales_count
                sellers.append({
                        "name": u.get_full_name(),
                        "operations": u_sales_count + u_non_sales_count,
                        "non_sales": u_non_sales_count,
                        "sales": u_sales_count,
                        "value": u_sales_total,
                        "discount_count": u_sales_discount_count,
                        "discount_value": u_sales_discount_total,
                        "products": u_sales_products_count,
                        "data": u_data,
                        })

    months = {}
    for i, row in enumerate(sellers):
        for r in row["data"]:
            month = r["month"]
            data = r["data"]
            d = months.get(month)
            if d is None:
                d = [{"operations": 0,
                      "non_sales": 0,
                      "sales": 0,
                      "value": 0.0,
                      "discount_count": 0,
                      "discount_value": 0.0,
                      "products": 0,
                      }] * len(sellers)
                months[month] = d
            d[i] = data

    months = list(months.iteritems())
    months.sort(lambda a, b: cmp(a[0], b[0]))
    import pprint; pprint.pprint(sellers)
    ctxt = {
        "form": form,
        "sellers": sellers,
        "months": months,
        "total_operations": t_sales_count + t_non_sales_count,
        "total_sales": t_sales_count,
        "total_value": t_sales_total,
        "total_non_sales": t_non_sales_count,
        "total_discount_count": t_sales_discount_count,
        "total_discount_value": t_sales_discount_total,
        "total_products": t_sales_products_count,
        }
    return render_to_response('sales/sellers/monthly.html', ctxt,
                              context_instance=RequestContext(request))
