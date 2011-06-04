from django.conf.urls.defaults import patterns, include, url

from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    url(r'^sales/sellers/daily/$', "sales.views.sellers_daily"),
    url(r'^cashflow/$', "cashflow.views.index"),
    url(r'^admin/', include(admin.site.urls)),
    url(r'^accounts/', include('django.contrib.auth.urls')),
)
