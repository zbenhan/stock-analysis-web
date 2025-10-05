from django.contrib import admin
from django.urls import path
from stock_analysis import views
from stock_analysis.views import download_template

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.index, name='index'),
    path('api/get-stock-data/', views.get_stock_data_api, name='get_stock_data'),
    path('api/get-random-stocks/', views.get_random_stocks_api, name='get_random_stocks'),
    path('api/download-template/', download_template, name='download_template'),
]
