from django.conf.urls.defaults import patterns, include, url

from django.shortcuts import render_to_response
from django.contrib.auth.decorators import login_required
from django.contrib import admin
admin.autodiscover()


@login_required
def report(request):
    return render_to_response("report.html")


urlpatterns = patterns('',
    url(r'^report/$', report),
    url(r'^report/sales/$', "sales.views.index"),
    url(r'^report/sales/$', "sales.views.index"),
    url(r'^report/sales/sellers/$', "sales.views.sellers"),
    url(r'^report/sales/sellers/daily/$', "sales.views.sellers_daily"),
    url(r'^report/sales/sellers/weekly/$', "sales.views.sellers_weekly"),
    url(r'^report/sales/sellers/monthly/$', "sales.views.sellers_monthly"),
    url(r'^report/cashflow/$', "cashflow.views.index"),
    url(r'^admin/', include(admin.site.urls)),
    url(r'^accounts/', include('django.contrib.auth.urls')),
)
