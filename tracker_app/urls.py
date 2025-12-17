from django.urls import path
from . import views
urlpatterns = [
    path("", views.tracker_home, name="tracker-home"),
    path("clients/", views.api_clients, name="api-clients"),
    path("clients/save/", views.api_clients_save, name="api-clients-save"),
    path("master-data/", views.api_master_data, name="api-master-data"),
    path(
        "master-data/save/",
        views.api_master_data_save,
        name="api-master-data-save",
    ),
    path("add_senior", views.api_add_senior),
    path("remove_senior", views.api_remove_senior),
    path("add_member", views.api_add_member),
    path("remove_member", views.api_remove_member),

    path("add_proposal_status", views.api_add_proposal_status),
    path("remove_proposal_status", views.api_remove_proposal_status),

    path("add_gstr9_status", views.api_add_gstr9_status),
    path("remove_gstr9_status", views.api_remove_gstr9_status),

    path("add_gstr9c_status", views.api_add_gstr9c_status),
    path("remove_gstr9c_status", views.api_remove_gstr9c_status),

    path("add_custom_column", views.api_add_custom_column, name="api_add_custom_column"),
    path("remove_custom_column", views.api_remove_custom_column, name="api_remove_custom_column"),
    path("upload_tracker/", views.api_upload_tracker, name = "api_upload_tracker"),
    path("clear_clients/",views.api_clear_clients, name = "api_clear_clients")
]