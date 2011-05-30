from cashflow.models import Balance as CashFlowBalance
from cashflow.models import CostCenter as CashFlowCostCenter
from cashflow.models import Payment as CashFlowPayment
from cashflow.models import Tag as CashFlowTag
from suppliers.models import SupplierPayment
from sales.models import SaleRevenue

from django.shortcuts import render_to_response
from django.template import Context, RequestContext, loader
from django.db.models import Sum
from django.contrib.auth.decorators import login_required

import datetime


def _all_options(iterator):
    return [d[0] for d in iterator]


def _to_options(iterator, reference_set):
    result = []
    for k, v in iterator:
        if k in reference_set:
            selected = 'selected=1'
        else:
            selected = ""
        result.append((k, v, selected))
    return result


def _to_checked(value):
    if value:
        return "checked=1"
    else:
        return ""


def _get_list(query, field, reference_set, typeconversion=lambda x: x):
    result = []
    refs = set(_all_options(reference_set))
    for v in query.getlist(field):
        try:
            v = typeconversion(v)
        except:
            continue
        if v in refs:
            result.append(v)
    return result


_bool_mapping = {
    "1": True,
    "true": True,
    "yes": True,
    "on": True,
    "0": False,
    "false": False,
    "no": False,
    "off": False,
}
def _get_bool(query, field, default):
    v = query.get(field, default)
    if isinstance(v, basestring):
        return _bool_mapping.get(v, default)
    return bool(v)


def _get_date(query, field, default):
    value = query.get(field, None)
    if value is None:
        return default
    try:
        dt = datetime.datetime.strptime(value, "%Y-%m-%d")
        return datetime.date(dt.year, dt.month, dt.day)
    except ValueError:
        return default


def _filter_db(iterator, reference_set):
    result = []
    for o in iterator:
        if o.id in reference_set:
            result.append(o)
    return result

@login_required
def index(request):
    all_balances = CashFlowBalance.TYPE_CHOICES
    all_cost_centers = [(o.id, o.name) for o in
                        CashFlowCostCenter.objects.all().order_by("name")]
    all_payments = CashFlowPayment.TYPE_CHOICES
    all_tags = [(o.id, o.name) for o in
                CashFlowTag.objects.all().order_by("name")]

    default_start = datetime.date.today()
    default_end = datetime.date.today() + datetime.timedelta(60)

    if request.method != "POST":
        balances = _all_options(all_balances)
        cost_centers = _all_options(all_cost_centers)
        payments = _all_options(all_payments)
        tags = _all_options(all_tags)
        show_suppliers = True
        show_revenues = True
        show_estimateds = True
        show_details = True
        start_date = default_start
        end_date = default_end
    else:
        balances = _get_list(request.POST, "balances", all_balances)
        cost_centers = _get_list(request.POST, "cost_centers", all_cost_centers,
                                 int)
        payments = _get_list(request.POST, "payments", all_payments)
        tags = _get_list(request.POST, "tags", all_tags, int)
        show_suppliers = _get_bool(request.POST, "show_suppliers", False)
        show_revenues = request.POST.get("show_revenues", False)
        show_estimateds = _get_bool(request.POST, "show_estimateds", False)
        show_details = request.POST.get("show_details", False)
        start_date = _get_date(request.POST, "start_date", default_start)
        end_date = _get_date(request.POST, "end_date", default_end)

    flow = []
    initial_value = 0.0
    initial_estimate = 0.0

    # initial balance: cashflow.Balance
    def value_sum(type, estimated):
        if type not in balances:
            return 0.0
        if not show_estimateds and estimated:
            return 0.0
        q = CashFlowBalance.objects.filter(
            type=type, tags__id__in=tags, estimated=estimated,
            date__lt=start_date
            ).distinct()
        # note: can't use q.aggregate(Sum("value")) since it will replicate
        # due multiple tags matching
        value = sum(o.value for o in q)
        #print "balance: type=%r, tags=%r, estimated=%r, date<%s: %r" % (type, tags, estimated, start_date, value)
        return value

    initial_estimate += value_sum("C", True)
    initial_estimate -= value_sum("D", True)
    v = value_sum("C", False)
    initial_value += v
    initial_estimate += v
    v = value_sum("D", False)
    initial_value -= v
    initial_estimate -= v

    # initial payment: cashflow.Payment
    def value_sum(estimated):
        if not show_estimateds and estimated:
            return 0.0
        q = CashFlowPayment.objects.filter(
            type__in=payments, tags__id__in=tags, cost_center__in=cost_centers,
            estimated=estimated, date__lt=start_date
            ).distinct()
        # note: can't use q.aggregate(Sum("value")) since it will replicate
        # due multiple tags matching
        value = sum(o.value for o in q)
        #print "payment: types=%r, tags=%r, cost-center=%r, estimated=%r, date<%s: %r" % (payments, tags, cost_centers, estimated, start_date, value)
        return value

    initial_estimate -= value_sum(True)
    v = value_sum(False)
    initial_value -= v
    initial_estimate -= v

    # initial payment: suppliers.SupplierPayment
    if show_suppliers:
        q = SupplierPayment.objects.filter(
            invoice__tags__id__in=tags, date_due__lt=start_date).distinct()
        # note: can't use q.aggregate(Sum("value")) since it will replicate
        # due multiple tags matching
        value = sum(o.value for o in q)
        print "supplier-payment: tags=%r, date<%s: %r" % (tags, start_date, value)
        initial_estimate -= value
        initial_value -= value

    # initial revenue: sales.SaleRevenue
    if show_revenues:
        q = SaleRevenue.objects.filter(date_due__lt=start_date)
        value = q.aggregate(Sum("net_value")).get("net_value__sum")
        if value:
            initial_estimate += value
            initial_value += value
        print "sales-revenue: date<%s: %r" % (start_date, value)

    # flow: cashflow.Balance
    filters = {
        "type__in": balances,
        "date__range": (start_date, end_date),
        }
    if not show_estimateds:
        filters["estimated"] = False
    if show_details:
        desc_tmpl = loader.get_template("cashflow/balance_description.html")
    for o in CashFlowBalance.objects.filter(**filters):
        filtered_tags = _filter_db(o.tags.all(), tags)
        if not filtered_tags:
            continue

        if o.type == "C":
            value = o.value
        else:
            value = -o.value

        if not show_details:
            description = o.description
        else:
            c = Context(
                {"date": o.date,
                 "description": o.description,
                 "tags": list(o.tags.all()),
                 })
            description = desc_tmpl.render(c)

        url = "/admin/cashflow/balance/%d/" % o.id
        flow.append((o.date, value, o.estimated, description, url))

    # flow: cashflow.Payment
    filters = {
        "type__in": payments,
        "date__range": (start_date, end_date),
        "tags__id__in": tags,
        }
    if not show_estimateds:
        filters["estimated"] = False
    if show_details:
        desc_tmpl = loader.get_template("cashflow/payment_description.html")
    for o in CashFlowPayment.objects.filter(**filters).distinct():
        if o.cost_center and o.cost_center.id not in cost_centers:
            continue

        if not show_details:
            description = o.description
        else:
            c = Context(
                {"date": o.date,
                 "description": o.description,
                 "tags": list(o.tags.all()),
                 "cost_center": o.cost_center,
                 "paid": o.paid,
                 })
            description = desc_tmpl.render(c)

        url = "/admin/cashflow/payment/%d/" % o.id
        flow.append((o.date, -o.value, o.estimated, description, url))

    # flow: suppliers.SupplierPayment
    if show_suppliers:
        filters = {
            "date_due__range": (start_date, end_date),
            "invoice__tags__id__in": tags,
            }
        if show_details:
            desc_tmpl = loader.get_template(
                "suppliers/payment_description.html")
        for o in SupplierPayment.objects.filter(**filters).distinct():
            status = ""
            for k, v in SupplierPayment.STATUS_CHOICES:
                if k == o.status:
                    status = v
                    break

            if not show_details:
                description = u"%s (%s - %s)" % (o.invoice.identifier,
                                            o.invoice.supplier, status)
            else:
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
            flow.append((o.date_due, -o.value, False, description, url))

    # flow: sales.SaleRevenue
    if show_revenues:
        filters = {
            "date_due__range": (start_date, end_date),
            }
        if show_details:
            desc_tmpl = loader.get_template(
                "sales/revenue_description.html")
        for o in SaleRevenue.objects.filter(**filters):
            if not show_details:
                description = o
            else:
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
            flow.append((o.date_due, o.net_value, False, description, url))

    # report
    flow.sort(cmp=lambda a, b: cmp(a[0], b[0]))
    flow_report = []
    last_month = [None, None, None, None]
    last_week = [None, None, None, None]
    last_day = [None, None, None, None]
    total_value = initial_value
    total_estimate = initial_estimate
    for row in flow:
        month_name = row[0].strftime("%B %Y")
        if month_name != last_month[0]:
            month = [month_name, total_value, total_estimate, []]
            flow_report.append(month)
            last_month = month
            last_week = [None, None]

        week_number = row[0].isocalendar()[1]
        if week_number != last_week[0]:
            week = [week_number, total_value, total_estimate, []]
            last_month[3].append(week)
            last_week = week
            last_day = [None, None]

        day_name = row[0].strftime("%A, %d")
        if day_name != last_day[0]:
            day = [day_name, total_value, total_estimate, []]
            last_week[3].append(day)
            last_day = day

        if row[2]:
            value = 0
            estimate = row[1]
        else:
            value = row[1]
            estimate = 0
        total_value += value
        total_estimate += row[1]
        last_day[3].append((value, estimate, total_value, total_estimate,
                            row[3], row[4]))


    # cashflow.models
    balance_filters = _to_options(CashFlowBalance.TYPE_CHOICES, balances)
    cost_center_filters = _to_options(all_cost_centers, cost_centers)
    payment_filters = _to_options(CashFlowPayment.TYPE_CHOICES, payments)
    tag_filters = _to_options(all_tags, tags)

    # suppliers.models
    suppliers_filter = _to_checked(show_suppliers)
    estimateds_filter = _to_checked(show_estimateds)

    # sales.models
    revenues_filter = _to_checked(show_revenues)

    # extra
    details_filter = _to_checked(show_details)
    start_date_filter = start_date.strftime("%Y-%m-%d")
    end_date_filter = end_date.strftime("%Y-%m-%d")

    ctxt = {
        "balance_filters": balance_filters,
        "cost_center_filters": cost_center_filters,
        "payment_filters": payment_filters,
        "tag_filters": tag_filters,
        "suppliers_filter": suppliers_filter,
        "revenues_filter": revenues_filter,
        "estimateds_filter": estimateds_filter,
        "details_filter": details_filter,
        "start_date_filter": start_date_filter,
        "end_date_filter": end_date_filter,
        "flow_report": flow_report,
        "final": (total_value, total_estimate),
        "difference": (total_value - initial_value,
                       total_estimate - initial_estimate),
        "show_estimateds": show_estimateds,
        }
    return render_to_response('cashflow/index.html', ctxt,
                              context_instance=RequestContext(request))
