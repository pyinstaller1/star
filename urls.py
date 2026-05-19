from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('kospi/', views.partial_kospi_view, name='_partial_kospi'),
    path('detail/', views.partial_detail_view, name='_partial_detail'),
    path('account/', views.account_view, name='account'),
    path('start_kospi/', views.start_kospi, name='start_kospi'),
    path('start_kospi_1day/', views.start_kospi_1day, name='start_kospi_1day'),
    path('get_ilbong_1day/', views.get_ilbong_1day_view, name='get_ilbong_1day'),





    path('add_gwansim_group/', views.add_gwansim_group_view, name='add_gwansim_group'),
    path('add_gwansim_stock/', views.add_gwansim_stock_view, name='add_gwansim_stock'),
    path('delete_gwansim_stock/', views.delete_gwansim_stock_view, name='delete_gwansim_stock'),
    path('delete_gwansim_group/', views.delete_gwansim_group_view, name='delete_gwansim_group'),
    
    path('update_gwansim_stock_order/', views.update_gwansim_stock_order_view, name='update_gwansim_stock_order'),
    path('update_gwansim_group_order/', views.update_gwansim_group_order_view, name='update_gwansim_group_order'),
    


    path('save_check_setting/', views.save_check_setting_view, name='save_check_setting'),
    path('get_check_setting/', views.get_check_setting_view, name='get_check_setting'),

    path('strategy/', views.strategy_view, name='strategy'),
    path('st_macd/', views.st_macd_view, name='st_macd'),




















    path('gwansim/', views.gwansim_view, name='gwansim'),

    
]








