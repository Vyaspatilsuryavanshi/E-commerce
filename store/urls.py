from django.urls import path
from . import views

app_name = "store"

urlpatterns = [
    path("", views.home, name="home"),
    path("catalog/", views.catalog, name="catalog"),
    path("catalog/dept/<slug:department_slug>/", views.catalog, name="catalog_department"),
    path("catalog/dept/<slug:department_slug>/<slug:category_slug>/", views.catalog, name="catalog_category"),
    path("product/<slug:slug>/", views.product_detail, name="product_detail"),
    path("product/<int:product_id>/review/", views.submit_review, name="submit_review"),
    path("visual-search/", views.visual_search_view, name="visual_search"),
    path("api/nearby-stores/", views.api_nearby_stores, name="api_nearby_stores"),
    path("api/set-location/", views.api_set_user_location, name="api_set_location"),
    path("newsletter/subscribe/", views.newsletter_subscribe, name="newsletter_subscribe"),
    path("newsletter/confirm/<str:token>/", views.newsletter_confirm, name="newsletter_confirm"),
]
