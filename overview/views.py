from cashflow.models import Balance as CashFlowBalance
from cashflow.models import Payment as CashFlowPayment
from suppliers.models import SupplierPayment
from sales.models import SaleRevenue
from sales.models import Sale
from sales.models import NonSale
from sales.models import MonthlyGoal
from sales.models import Customer
from django.shortcuts import render_to_response
from django.template import Context, RequestContext, loader
from django.contrib.auth.models import User
from django.db.models import Sum
from django.contrib.auth.decorators import login_required
from django.utils.translation import ugettext_lazy as _
from django.conf import settings
from django.http import Http404

import datetime

SELLERS_QUERY = User.objects.filter(is_active=True,
                                    groups__name=settings.SBA_SELLER_GROUP)

@login_required
def index(request, date=None):
    if date is None:
        date = datetime.date.today()
        is_today = True
    else:
        try:
            date = datetime.date(*(int(x) for x in date.split("-")))
            is_today = date == datetime.date.today()
        except ValueError:
            raise Http404

    period_days7 = (date, date + datetime.timedelta(7))
    period_days30 = (date, date + datetime.timedelta(30))

    if date.weekday() == 0:
        week_start = date
    else:
        week_start = date - datetime.timedelta(date.weekday())
    week = (week_start, date + datetime.timedelta(6))

    if date.month == 12:
        next_month = datetime.date(date.year + 1, 1, 1)
    else:
        next_month = datetime.date(date.year, date.month + 1, 1)
    month = (datetime.date(date.year, date.month, 1),
             next_month - datetime.timedelta(1))

    def get_sales(seller, period):
        q = Sale.objects.filter(
            datetime__range=period, seller=seller).aggregate(Sum("value"))
        return q.get("value__sum") or 0.0

    def get_sales_ratio(seller, period):
        filters = {"datetime__range": period, "seller": seller}
        sales = len(Sale.objects.filter(**filters))
        non_sales = len(NonSale.objects.filter(**filters))
        total = sales + non_sales
        if total == 0:
            return None
        else:
            return sales / float(total)

    def get_sales_goal(seller, date, period):
        goals = MonthlyGoal.goals_for_period(period[0], period[1], seller)
        if not goals:
            return None
        else:
            date_days = (date - period[0]).days + 1
            month_days = (period[1] - period[0]).days + 1
            return float(goals[-1].total * date_days) / month_days

    sellers = []
    sellers_date = 0.0
    sellers_week = 0.0
    sellers_month = 0.0
    for u in SELLERS_QUERY.order_by("first_name"):
        u_date = get_sales(u, (date, date))
        u_week = get_sales(u, week)
        u_month = get_sales(u, month)
        sellers_date += u_date
        sellers_week += u_week
        sellers_month += u_month
        sellers.append({
                "seller": u,
                "date": u_date,
                "week": u_week,
                "month": u_month,
                "ratio_month": get_sales_ratio(u, month),
                "goal": get_sales_goal(u, date, month),
                })

    def get_total_sales(period):
        q = Sale.objects.filter(datetime__range=period).aggregate(Sum("value"))
        return q.get("value__sum") or 0.0
    sales_total_date = get_total_sales((date, date))
    sales_total_week = get_total_sales(week)
    sales_total_month = get_total_sales(month)

    sales_others_date = sales_total_date - sellers_date
    sales_others_week = sales_total_week - sellers_week
    sales_others_month = sales_total_month - sellers_month

    sales_trend_week = (sales_total_week * 7) / (date.weekday() + 1)
    sales_trend_month = (sales_total_month * month[1].day) / date.day

    goals = MonthlyGoal.goals_for_period(month[0], month[1], None)
    month_days = (month[1] - month[0]).days + 1
    sales = []
    last_day = [None, None, None]
    if goals:
        last_goal = 0
        sales_ratio_goal = goals[-1].sales_ratio / 100.0
    else:
        last_goal = None
        sales_ratio_goal = None
    for o in Sale.objects.filter(datetime__range=month).order_by("datetime"):
        d = datetime.date(o.datetime.year, o.datetime.month, o.datetime.day)
        if last_day[0] != d:
            if last_goal is None:
                g = None
            else:
                idx = last_goal
                idx_max = len(goals)
                while idx + 1 < idx_max and goals[idx + 1].start < d:
                    idx += 1
                last_goal = idx
                g = goals[idx].total / month_days
                g = int(g * 100) / 100.0
            last_day = [d, 0.0, g]
            sales.append(last_day)
        last_day[1] += o.value

    date_list = {}
    date_total = 0.0
    date_debits_count = 0
    date_credits_count = 0
    date_payments_count = 0
    date_suppliers_payments_count = 0
    date_revenues_count = 0

    desc_tmpl = loader.get_template("cashflow/balance_description.html")
    for o in CashFlowBalance.objects.filter(date=date):
        c = Context(
            {"date": o.date,
             "description": o.description,
             "tags": list(o.tags.all()),
             })
        description = desc_tmpl.render(c)
        url = "/admin/cashflow/balance/%d/" % o.id
        if o.type == "C":
            date_total += o.value
            date_credits_count += 1
            date_list.setdefault(_("Other Credits"), []).append(
                (o.value, o.is_estimated, description, url))
        else:
            date_total -= o.value
            date_debits_count += 1
            date_list.setdefault(_("Other Debits"), []).append(
                (-o.value, o.is_estimated, description, url))

    desc_tmpl = loader.get_template("cashflow/payment_description.html")
    for o in CashFlowPayment.objects.filter(date=date):
        c = Context(
            {"date": o.date,
             "description": o.description,
             "tags": list(o.tags.all()),
             "cost_center": o.cost_center,
             "paid": o.was_paid,
             })
        description = desc_tmpl.render(c)
        url = "/admin/cashflow/payment/%d/" % o.id
        date_total -= o.value
        date_payments_count += 1
        date_list.setdefault(_("Payments"), []).append(
            (-o.value, o.is_estimated, description, url))

    desc_tmpl = loader.get_template("suppliers/payment_description.html")
    for o in SupplierPayment.objects.filter(date_due=date):
        status = ""
        for k, v in SupplierPayment.STATUS_CHOICES:
            if k == o.status:
                status = v
                break
        c = Context(
            {"date": o.date_due,
             "supplier": o.invoice.supplier,
             "invoice": o.invoice.identifier,
             "status": status,
             "tags": list(o.invoice.tags.all()),
             "paid": o.status == "P",
             })
        description = desc_tmpl.render(c)
        url = "/admin/suppliers/supplierpayment/%d/" % o.id
        date_total -= o.value
        date_suppliers_payments_count += 1
        date_list.setdefault(_("Suppliers Payments"), []).append(
            (-o.value, False, description, url))

    desc_tmpl = loader.get_template("sales/revenue_description.html")
    for o in SaleRevenue.objects.filter(date_due=date):
        c = Context(
            {"date": o.date_due,
             "value": o.value,
             "net_value": o.net_value,
             "method": o.method.name,
             "operation_cost": o.operation_cost,
             "percentual_cost": o.percentual_cost,
             "sale": o.sale,
             })
        description = desc_tmpl.render(c)
        url = "/admin/sales/sale/%d/" % o.sale.id
        date_total += o.value
        date_revenues_count += 1
        date_list.setdefault(_("Sales Revenue"), []).append(
            (o.value, False, description, url))

    date_list = list(date_list.iteritems())
    date_list.sort(lambda a, b: cmp(unicode(a[0]), unicode(b[0])))

    days7_total = 0.0
    q = CashFlowBalance.objects.filter(date__range=period_days7, type="C")
    days7_credits_count = len(q)
    days7_total += q.aggregate(Sum("value")).get("value__sum") or 0
    q = CashFlowBalance.objects.filter(date__range=period_days7, type="D")
    days7_debits_count = len(q)
    days7_total -= q.aggregate(Sum("value")).get("value__sum") or 0
    q = CashFlowPayment.objects.filter(date__range=period_days7)
    days7_payments_count = len(q)
    days7_total -= q.aggregate(Sum("value")).get("value__sum") or 0
    q = SupplierPayment.objects.filter(date_due__range=period_days7)
    days7_suppliers_payments_count = len(q)
    days7_total -= q.aggregate(Sum("value")).get("value__sum") or 0
    q = SaleRevenue.objects.filter(date_due__range=period_days7)
    days7_revenues_count = len(q)
    days7_total += q.aggregate(Sum("value")).get("value__sum") or 0

    days30_total = 0.0
    q = CashFlowBalance.objects.filter(date__range=period_days30, type="C")
    days30_credits_count = len(q)
    days30_total += q.aggregate(Sum("value")).get("value__sum") or 0
    q = CashFlowBalance.objects.filter(date__range=period_days30, type="D")
    days30_debits_count = len(q)
    days30_total -= q.aggregate(Sum("value")).get("value__sum") or 0
    q = CashFlowPayment.objects.filter(date__range=period_days30)
    days30_payments_count = len(q)
    days30_total -= q.aggregate(Sum("value")).get("value__sum") or 0
    q = SupplierPayment.objects.filter(date_due__range=period_days30)
    days30_suppliers_payments_count = len(q)
    days30_total -= q.aggregate(Sum("value")).get("value__sum") or 0
    q = SaleRevenue.objects.filter(date_due__range=period_days30)
    days30_revenues_count = len(q)
    days30_total += q.aggregate(Sum("value")).get("value__sum") or 0

    initial_balance = 0.0
    q = CashFlowBalance.objects.filter(date__lt=date, type="C")
    initial_balance += q.aggregate(Sum("value")).get("value__sum") or 0
    q = CashFlowBalance.objects.filter(date__lt=date, type="D")
    initial_balance -= q.aggregate(Sum("value")).get("value__sum") or 0
    q = CashFlowPayment.objects.filter(date__lt=date)
    initial_balance -= q.aggregate(Sum("value")).get("value__sum") or 0
    q = SupplierPayment.objects.filter(date_due__lt=date)
    initial_balance -= q.aggregate(Sum("value")).get("value__sum") or 0
    q = SaleRevenue.objects.filter(date_due__lt=date)
    initial_balance += q.aggregate(Sum("value")).get("value__sum") or 0

    birth_day = Customer.objects.filter(
        birth_day=date.day, birth_month=date.month).order_by("name")
    birth_month = Customer.objects.filter(
        birth_day__gt=date.day, birth_month=date.month).order_by(
        "birth_day", "name")

    ctxt = {
        "sellers": sellers,
        "sales": sales,
        "sales_total_date": sales_total_date,
        "sales_total_week": sales_total_week,
        "sales_total_month": sales_total_month,
        "sales_others_date": sales_others_date,
        "sales_others_week": sales_others_week,
        "sales_others_month": sales_others_month,
        "sales_trend_week": sales_trend_week,
        "sales_trend_month": sales_trend_month,
        "sales_ratio_goal": sales_ratio_goal,
        "date_list": date_list,
        "is_today": is_today,
        "date": date,
        "date_before": date - datetime.timedelta(1),
        "date_after": date + datetime.timedelta(1),
        "date_debits_count": date_debits_count,
        "date_credits_count": date_credits_count,
        "date_payments_count": date_payments_count,
        "date_suppliers_payments_count": date_suppliers_payments_count,
        "date_revenues_count": date_revenues_count,
        "date_total": date_total,
        "date_balance": date_total + initial_balance,
        "days7_debits_count": days7_debits_count,
        "days7_credits_count": days7_credits_count,
        "days7_payments_count": days7_payments_count,
        "days7_suppliers_payments_count": days7_suppliers_payments_count,
        "days7_revenues_count": days7_revenues_count,
        "days7_total": days7_total,
        "days7_balance": days7_total + initial_balance,
        "days30_debits_count": days30_debits_count,
        "days30_credits_count": days30_credits_count,
        "days30_payments_count": days30_payments_count,
        "days30_suppliers_payments_count": days30_suppliers_payments_count,
        "days30_revenues_count": days30_revenues_count,
        "days30_total": days30_total,
        "days30_balance": days30_total + initial_balance,
        "birth_day": birth_day,
        "birth_month": birth_month,
        }
    return render_to_response('overview/index.html', ctxt,
                              context_instance=RequestContext(request))
