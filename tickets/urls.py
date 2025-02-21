from django.urls import path
from . import views

urlpatterns = [
    path('base/',views.index,name="base"),
    path('create_ticket/',views.create_ticket,name="create-ticket"),
    path('CFAPersontickets/',views.all_ticket,name="CFAPerson_alltickets"),
    path('login_new',views.login_new,name='login_new'),
    path('widget-basic/',views.test,name="widget-basic"),
    
    path('get_ticket_history/<int:ticket_id>/', views.get_ticket_history, name='get_ticket_history'),
    
    #tables
    path('CFAPerson_Table/', views.CFAPerson_Tableview, name='CFAPerson_Tables'),
    path('delete/<int:id>/', views.delete, name='delete-ticket'),
    path('get-ticket-details/<int:ticket_id>/', views.get_ticket_details, name='get-ticket-details'),
    path('edit_ticket/<int:ticket_id>/', views.edit_ticket, name="edit-ticket"),

    path('delete-attachment/<int:attachment_id>/', views.delete_attachment, name='delete-attachment'),
    path('change_ticket_status/<int:ticket_id>/', views.change_ticket_status, name='change_ticket_status'),
    path('ticket/<int:ticket_id>/clarification/', views.submit_clarification_view, name='submit_clarification'),
    path('ticket_creation',views.email_page,name='ticket_creation'),
    path('ticket_assignment',views.ticket_assign,name='ticet_assignment'),
    path('export/pdf/', views.export_to_pdf, name='export_to_pdf'),
    path('export/excel/', views.export_to_excel, name='export_to_excel'),
    path('csf/filter_tickets/', views.filter_tickets, name='csf_filter_tickets'),

]
 