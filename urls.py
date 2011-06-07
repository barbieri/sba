from django.conf.urls.defaults import patterns, include, url

from django.views.generic.simple import redirect_to
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.contrib.auth.decorators import login_required
from django.contrib import admin
admin.autodiscover()


@login_required
def report(request):
    return render_to_response("report.html",
                              context_instance=RequestContext(request))


urlpatterns = patterns('',
    url(r'^$', "overview.views.index"),
    url(r'^overview/$', "overview.views.index"),
    url(r'^overview/(?P<date>20\d{2}-\d{2}-\d{2})/$', "overview.views.index"),
    url(r'^report/$', report),
    url(r'^report/sales/$', "sales.views.index"),
    url(r'^report/sales/sellers/$', "sales.views.sellers"),
    url(r'^report/sales/sellers/daily/$', "sales.views.sellers_daily"),
    url(r'^report/sales/sellers/weekly/$', "sales.views.sellers_weekly"),
    url(r'^report/sales/sellers/monthly/$', "sales.views.sellers_monthly"),
    url(r'^report/sales/total/$', "sales.views.total"),
    url(r'^report/sales/total/daily/$', "sales.views.total_daily"),
    url(r'^report/sales/total/weekly/$', "sales.views.total_weekly"),
    url(r'^report/sales/total/monthly/$', "sales.views.total_monthly"),
    url(r'^report/cashflow/$', "cashflow.views.index"),
    url(r'^admin/', include(admin.site.urls)),
    url(r'^accounts/profile/$', redirect_to, {"url": "/report"}),
    url(r'^accounts/', include('django.contrib.auth.urls')),
)
