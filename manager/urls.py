from django.urls import path
from . import views

urlpatterns = [
    path('Dashboard_Manager/',views.Manager_base,name="Manager_base"),
    path('assign/<int:id>/', views.assign_ticket, name='assign_ticket'),
    path('All_tickets_Manager/',views.manager_alltickets,name="manager_alltickets"),

  #table
    path('Manager_Tables_view/', views.manager_tableview, name='manager_tables'),
    path('delete_ticket/<int:ticket_id>/', views.delete_ticket, name='delete_ticket'),
    path('get-ticket-details/<int:ticket_id>/', views.get_ticket_details, name='get-ticket-details'),
    path('manager_tables_view/export/', views.manager_export_to_pdf, name='manager_export_to_pdf'),
    path('manager_export_to_excel/', views.manager_export_to_excel, name='manager_export_to_excel'),
    path('manager/filter_tickets', views.filter_tickets, name='filter_tickets'),
    path('Manager_Tables_view/', views.manager_tableview, name='manager_tables'),
    path('engineer_count/',views.engineers_count,name="engineer_count"),
    path('get_ticket_datas/', views.get_ticket_datas, name='get_ticket_datas'),

]  