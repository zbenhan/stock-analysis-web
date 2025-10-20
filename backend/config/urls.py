from django.contrib import admin
from django.urls import path, include
from stock_analysis import views
from stock_analysis.views import download_template
from django.views.generic import TemplateView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.index, name='index'),
    path('api/get-stock-data/', views.get_stock_data_api, name='get_stock_data'),
    path('api/get-random-stocks/', views.get_random_stocks_api, name='get_random_stocks'),
    path('api/download-template/', download_template, name='download_template'),
    path('', TemplateView.as_view(template_name='index.html'), name='home'),
    
    # 文章页面路由
     path('articles/poor-charlies-almanack.html', 
         TemplateView.as_view(template_name='articles/poor-charlies-almanack.html'), 
         name='poor-charlies-almanack'),

    path('articles/beat-the-street.html', 
         TemplateView.as_view(template_name='articles/beat-the-street.html'), 
         name='beat-the-street'),
 
    path('articles/mississippi-bubble.html', 
         TemplateView.as_view(template_name='articles/mississippi-bubble.html'), 
         name='mississippi-bubble'),

    path('articles/tulip-mania.html', 
         TemplateView.as_view(template_name='articles/tulip-mania.html'), 
         name='tulip-mania'),

    path('articles/great-depression-suicide-shoeshine.html', 
         TemplateView.as_view(template_name='articles/great-depression-suicide-shoeshine.html'), 
         name='great-depression-suicide-shoeshine'),

    path('articles/ew-ssecurities-ultron-finger.html', 
         TemplateView.as_view(template_name='articles/ew-ssecurities-ultron-finger.html'), 
         name='ew-ssecurities-ultron-finger'),

    path('articles/gamestop-short-squeeze.html', 
         TemplateView.as_view(template_name='articles/gamestop-short-squeeze.html'), 
         name='gamestop-short-squeeze'),
    
    # API路由保持不变
    #path('api/', include('stock_analysis.urls')),
]
