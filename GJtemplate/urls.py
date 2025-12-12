"""
URL configuration for GJtemplate project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path

from . import views

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", views.home, name="home"),
    path("api/clients/", views.api_clients, name="api-clients"),
    path("api/clients/save/", views.api_clients_save, name="api-clients-save"),
    path("api/master-data/", views.api_master_data, name="api-master-data"),
    path(
        "api/master-data/save/",
        views.api_master_data_save,
        name="api-master-data-save",
    ),
    path("api/add_senior", views.api_add_senior),
    path("api/remove_senior", views.api_remove_senior),
    path("api/add_member", views.api_add_member),
    path("api/remove_member", views.api_remove_member),

    path("api/add_proposal_status", views.api_add_proposal_status),
    path("api/remove_proposal_status", views.api_remove_proposal_status),

    path("api/add_gstr9_status", views.api_add_gstr9_status),
    path("api/remove_gstr9_status", views.api_remove_gstr9_status),

    path("api/add_gstr9c_status", views.api_add_gstr9c_status),
    path("api/remove_gstr9c_status", views.api_remove_gstr9c_status),

    path("api/add_custom_column", views.api_add_custom_column, name="api_add_custom_column"),
    path("api/remove_custom_column", views.api_remove_custom_column, name="api_remove_custom_column"),
    path("api/upload_tracker/", views.api_upload_tracker, name = "api_upload_tracker"),
    path("api/clear_clients/",views.api_clear_clients, name = "api_clear_clients")
]
