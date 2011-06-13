from sales.models import Sale, NonSale, MonthlyGoal

from django.shortcuts import render_to_response
from django.template import RequestContext
from django.db.models import Sum
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib.admin.widgets import AdminDateWidget
from django import forms
import datetime
from django.conf import settings
from django.utils.translation import ugettext_lazy as _

def last_month():
    now = datetime.date.today()
    if now.month == 1:
        return datetime.date(now.year - 1, 1, 1)
    else:
        return datetime.date(now.year, now.month - 1, 1)


@login_required
def index(request):
    return render_to_response("sales/index.html",
                              context_instance=RequestContext(request))


@login_required
def sellers(request):
    return render_to_response("sales/sellers/index.html",
                              context_instance=RequestContext(request))

@login_required
def total(request):
    return render_to_response("sales/total/index.html",
                              context_instance=RequestContext(request))


class PeriodForm(forms.Form):
    start = forms.DateField(label=_("start"),
                            initial=last_month, widget=AdminDateWidget())
    end = forms.DateField(label=_("end"),
                          initial=datetime.date.today, widget=AdminDateWidget())


SELLERS_QUERY = User.objects.filter(is_active=True,
                                    groups__name=settings.SBA_SELLER_GROUP)


def sales_data_get(start, end, seller_id, key, date_id_get):
    sellers = []
    t_sales_count = 0
    t_sales_total = 0.0
    t_sales_discount_total = 0.0
    t_sales_discount_count = 0
    t_sales_products_count = 0
    t_non_sales_count = 0

    q = SELLERS_QUERY
    if seller_id:
        q = q.filter(id=seller_id)

    period = (start, end)
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

            date_id = date_id_get(s.datetime)
            c_data = {
                "operations": 1,
                "non_sales": 0,
                "sales": 1,
                "value": s.value,
                "discount_count": discount_count,
                "discount_value": discount_value,
                "products": products,
                }
            d_data = u_data.get(date_id)
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
            u_data[date_id] = x = {}
            for k, cv in c_data.iteritems():
                x[k] = cv + d_data[k]

        for s in non_sales.filter(seller=u):
            u_non_sales_count += 1
            date_id = date_id_get(s.datetime)
            c_data = {
                "operations": 1,
                "non_sales": 1,
                "sales": 0,
                "value": 0.0,
                "discount_count": 0,
                "discount_value": 0.0,
                "products": 0,
                }
            d_data = u_data.get(date_id)
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
            u_data[date_id] = x = {}
            for k, cv in c_data.iteritems():
                x[k] = cv + d_data[k]

        u_data = list({key: a, "data": b}
                      for a, b in u_data.iteritems())
        u_data.sort(lambda a, b: cmp(a[key][0], b[key][0]))

        t_sales_count += u_sales_count
        t_sales_total += u_sales_total
        t_sales_discount_total += u_sales_discount_total
        t_sales_discount_count += u_sales_discount_count
        t_sales_products_count += u_sales_products_count
        t_non_sales_count += u_non_sales_count
        sellers.append({
                "name": u"%s %s." % (u.first_name, u.last_name[:1]),
                "operations": u_sales_count + u_non_sales_count,
                "non_sales": u_non_sales_count,
                "sales": u_sales_count,
                "value": u_sales_total,
                "discount_count": u_sales_discount_count,
                "discount_value": u_sales_discount_total,
                "products": u_sales_products_count,
                "data": u_data,
                })

    keys = {}
    for i, row in enumerate(sellers):
        for r in row["data"]:
            date_id = r[key]
            data = r["data"]
            d = keys.get(date_id)
            if d is None:
                d = [{"operations": 0,
                      "non_sales": 0,
                      "sales": 0,
                      "value": 0.0,
                      "discount_count": 0,
                      "discount_value": 0.0,
                      "products": 0,
                      }] * len(sellers)
                keys[date_id] = d
            d[i] = data

    keys = list(keys.iteritems())
    keys.sort(lambda a, b: cmp(a[0], b[0]))
    ctxt = {
        "sellers": sellers,
        key + "s": keys,
        "total_operations": t_sales_count + t_non_sales_count,
        "total_sales": t_sales_count,
        "total_value": t_sales_total,
        "total_non_sales": t_non_sales_count,
        "total_discount_count": t_sales_discount_count,
        "total_discount_value": t_sales_discount_total,
        "total_products": t_sales_products_count,
        }
    return ctxt


def total_report(request, key, date_id_get, goal_get, template):
    ctxt = {}
    start = None
    end = None
    if request.method != "POST":
        form = PeriodForm()
    else:
        form = PeriodForm(request.POST)
        if form.is_valid():
            start = form.cleaned_data["start"]
            end = form.cleaned_data["end"]
            ctxt = sales_data_get(start, end, None, key, date_id_get)

    old_keys = ctxt.pop(key + "s", [])
    keys = []
    for date_id, data in old_keys:
        d = {"operations": 0,
             "non_sales": 0,
             "sales": 0,
             "value": 0.0,
             "discount_count": 0,
             "discount_value": 0.0,
             "products": 0,
             }
        for s in data:
            for k, v in s.iteritems():
                d[k] += v
        d["goal"], d["goal_proportion"] = goal_get(start, end, date_id)
        keys.append((date_id, d))

    ctxt["form"] = form
    ctxt[key + "s"] = keys
    return render_to_response(template, ctxt,
                              context_instance=RequestContext(request))

_month_days_cache = {}
def month_days(year, month):
    cached = _month_days_cache.get((year, month))
    if cached is not None:
        return cached

    this = datetime.date(year, month, 1)
    if month < 12:
        next = datetime.date(year, month + 1, 1)
    else:
        next = datetime.date(year + 1, 1, 1)
    days = (next - this).days

    if len(_month_days_cache) > 1000:
        _month_days_cache.clear() # ugly!
    _month_days_cache[(year, month)] = days

    return days


@login_required
def total_daily(request):
    def date_id_get(date):
        return (date.year, date.month, date.day)

    goals = []
    goals_proportions = {}
    def goal_get(start, end, date_id):
        proportion = goals_proportions.get((date_id[0], date_id[1]))
        if proportion is None:
            proportion = 1.0 / month_days(date_id[0], date_id[1])
            goals_proportions[(date_id[0], date_id[1])] = proportion
        if not goals:
            goals.extend(MonthlyGoal.goals_for_period(start, end, None))
        goal = None
        date = datetime.date(*date_id)
        for g in goals:
            if g.start <= date:
                goal = g
            else:
                break
        return (goal, proportion)

    return total_report(request, "day", date_id_get, goal_get,
                        "sales/total/daily.html")


@login_required
def total_weekly(request):
    def date_id_get(date):
        x = datetime.date(date.year, date.month, date.day)
        x -= datetime.timedelta(x.weekday())
        return (date.year, date.isocalendar()[1], x)

    goals = []
    goals_proportions = {}
    def goal_get(start, end, date_id):
        proportion = goals_proportions.get((date_id[0], date_id[2].month))
        if proportion is None:
            proportion = 7.0 / month_days(date_id[0], date_id[2].month)
            goals_proportions[(date_id[0], date_id[2])] = proportion
        if not goals:
            goals.extend(MonthlyGoal.goals_for_period(start, end, None))
        goal = None
        date = date_id[2]
        for g in goals:
            if g.start <= date:
                goal = g
            else:
                break
        return (goal, proportion)

    return total_report(request, "week", date_id_get, goal_get,
                        "sales/total/weekly.html")

@login_required
def total_monthly(request):
    def date_id_get(date):
        return (date.year, date.month, date.strftime("%B %Y"))

    goals = []
    def goal_get(start, end, date_id):
        if not goals:
            goals.extend(MonthlyGoal.goals_for_period(start, end, None))
        goal = None
        date = datetime.date(date_id[0], date_id[1], 1)
        for g in goals:
            if g.start <= date:
                goal = g
            else:
                break
        return (goal, 1)

    return total_report(request, "month", date_id_get, goal_get,
                        "sales/total/monthly.html")


class SellerPeriodForm(PeriodForm):
    seller = forms.ChoiceField(label=_("seller"), required=False)


def sellers_report(request, key, date_id_get, goal_get, template):
    sellers_choices = [("", _("All"))] + [(o.id, o.get_full_name()) for o in
                                       SELLERS_QUERY.order_by("first_name")]
    ctxt = {}
    start = None
    end = None
    seller = None

    if request.method != "POST":
        form = SellerPeriodForm()
        form.fields["seller"].choices = sellers_choices
    else:
        form = SellerPeriodForm(request.POST)
        form.fields["seller"].choices = sellers_choices
        if form.is_valid():
            start = form.cleaned_data["start"]
            end = form.cleaned_data["end"]
            seller = form.cleaned_data["seller"]
            if not seller:
                seller = None
            ctxt = sales_data_get(start, end, seller, key, date_id_get)

    old_keys = ctxt.pop(key + "s", [])
    keys = []
    n_sellers = float(len(SELLERS_QUERY))
    goal = None
    goal_proportion = None
    for date_id, data in old_keys:
        goal, goal_proportion = goal_get(start, end, date_id, seller)
        if seller is None or goal.seller is None:
            if n_sellers:
                goal_proportion /= n_sellers
        keys.append((date_id, data, goal, goal_proportion))

    ctxt["form"] = form
    ctxt[key + "s"] = keys
    ctxt["goal"] = goal
    ctxt["goal_proportion"] = goal_proportion
    return render_to_response(template, ctxt,
                              context_instance=RequestContext(request))


@login_required
def sellers_daily(request):
    def date_id_get(date):
        return (date.year, date.month, date.day)

    goals = []
    goals_proportions = {}
    def goal_get(start, end, date_id, seller):
        proportion = goals_proportions.get((date_id[0], date_id[1]))
        if proportion is None:
            proportion = 1.0 / month_days(date_id[0], date_id[1])
            goals_proportions[(date_id[0], date_id[1])] = proportion
        if not goals:
            goals.extend(MonthlyGoal.goals_for_period(start, end, seller))
            if seller is not None and not goals:
                goals.extend(MonthlyGoal.goals_for_period(start, end, None))
        goal = None
        date = datetime.date(*date_id)
        for g in goals:
            if g.start <= date:
                goal = g
            else:
                break
        return (goal, proportion)

    return sellers_report(request, "day", date_id_get, goal_get,
                          "sales/sellers/daily.html")


@login_required
def sellers_weekly(request):
    def date_id_get(date):
        x = datetime.date(date.year, date.month, date.day)
        x -= datetime.timedelta(x.weekday())
        return (date.year, date.isocalendar()[1], x)

    goals = []
    goals_proportions = {}
    def goal_get(start, end, date_id, seller):
        proportion = goals_proportions.get((date_id[0], date_id[2].month))
        if proportion is None:
            proportion = 7.0 / month_days(date_id[0], date_id[2].month)
            goals_proportions[(date_id[0], date_id[2])] = proportion
        if not goals:
            goals.extend(MonthlyGoal.goals_for_period(start, end, seller))
            if seller is not None and not goals:
                goals.extend(MonthlyGoal.goals_for_period(start, end, None))
        goal = None
        date = date_id[2]
        for g in goals:
            if g.start <= date:
                goal = g
            else:
                break
        return (goal, proportion)

    return sellers_report(request, "week", date_id_get, goal_get,
                          "sales/sellers/weekly.html")

@login_required
def sellers_monthly(request):
    def date_id_get(date):
        return (date.year, date.month, date.strftime("%B %Y"))

    goals = []
    def goal_get(start, end, date_id, seller):
        if not goals:
            goals.extend(MonthlyGoal.goals_for_period(start, end, seller))
            if seller is not None and not goals:
                goals.extend(MonthlyGoal.goals_for_period(start, end, None))
        goal = None
        date = datetime.date(date_id[0], date_id[1], 1)
        for g in goals:
            if g.start <= date:
                goal = g
            else:
                break
        return (goal, 1)

    return sellers_report(request, "month", date_id_get, goal_get,
                          "sales/sellers/monthly.html")
