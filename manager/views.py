from django.shortcuts import render,redirect,get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import cache_control
from user_module.decorators import allowed_users
from tickets.models import *
from django.contrib.auth.models import User,Group
from django.http import JsonResponse
from django.db.models import Q 
from django.contrib import messages
import json
from django.http import HttpResponse
from django.core.paginator import Paginator
from tickets.templatetags.custom_filters import dynamic_zfill  # Import the custom filter
from django.utils.timezone import localtime
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.lib.pagesizes import landscape, A4
from reportlab.platypus import PageBreak
from django.template.loader import get_template
from xhtml2pdf import pisa
import pandas as pd
from datetime import datetime, timezone as dt_timezone
from django.utils.dateparse import parse_date
from io import BytesIO
from django.utils.timezone import localtime
from django.utils import timezone

# Create your views here.

@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@login_required
@allowed_users(allowed_roles=['Manager'])
def Manager_base(request):
    all_tickets = Item.objects.all()
    recent_all_tickets = Item.objects.all().order_by('-status_changed_date')[:5]

    all_tickets_count = Item.objects.all().count()
    open_tickets = Item.objects.filter(status='open')
    
    closed_tickets = Item.objects.filter(status='closed').count()
    pending_tickets = Item.objects.filter(status='pending').count()
    assigned_tickets = Item.objects.filter(status='assigned').count()
    inprogress_tickets = Item.objects.filter(status='inprogress').count()
    resolved_tickets = Item.objects.filter(status='Resolved').count()
    reopen_tickets = Item.objects.filter(status='reopen').count()
    seekclarity_tickets = Item.objects.filter(status='seek-clarification').count()
    open_tickets_count = Item.objects.filter(status='open').count()
    engineer_group = Group.objects.get(name='Engineer')  # Get the 'Engineer' group
    engineers = User.objects.filter(groups=engineer_group) # Filter engineers by group

    open_tickets_progress = (open_tickets_count / all_tickets_count) * 100 if all_tickets_count > 0 else 0
    closed_tickets_progress = (closed_tickets / all_tickets_count) * 100 if all_tickets_count > 0 else 0
    pending_tickets_progress = (pending_tickets / all_tickets_count) * 100 if all_tickets_count > 0 else 0
    assigned_tickets_progress = (assigned_tickets / all_tickets_count) * 100 if all_tickets_count > 0 else 0
    inprogress_tickets_progress = (inprogress_tickets / all_tickets_count) * 100 if all_tickets_count > 0 else 0
    resolved_tickets_progress = (resolved_tickets / all_tickets_count) * 100 if all_tickets_count > 0 else 0
    reopen_tickets_progress = (reopen_tickets / all_tickets_count) * 100 if all_tickets_count > 0 else 0
    seekclarity_tickets_progress = (seekclarity_tickets / all_tickets_count) * 100 if all_tickets_count > 0 else 0
    all_tickets_progress = (all_tickets_count / all_tickets_count) * 100 if all_tickets_count > 0 else 0

    current_datetime = datetime.now(dt_timezone.utc)

    current_day = current_datetime.day
    current_month = current_datetime.month
    current_year = current_datetime.year

    context = {
        'current_day': current_day,
        'current_month': current_month,
        'current_year': current_year,
        'open_tickets_count': open_tickets_count,
        'all_tickets_progress':all_tickets_progress,
        'inprogress_tickets_progress':inprogress_tickets_progress,
        'open_tickets_progress':open_tickets_progress,
        'closed_tickets_progress':closed_tickets_progress,
        'pending_tickets_progress':pending_tickets_progress,
        'assigned_tickets_progress':assigned_tickets_progress,
        'open_tickets':open_tickets,
        'reopen_tickets':reopen_tickets,
        'engineers': engineers,
        'closed_tickets':closed_tickets,
        'inprogress_tickets':inprogress_tickets,
        'all_tickets':all_tickets,
        'assigned_tickets':assigned_tickets,
        'resolved_tickets':resolved_tickets,
        'pending_tickets':pending_tickets,
        'all_tickets_count':all_tickets_count,
        'resolved_tickets_progress':resolved_tickets_progress,
        'reopen_tickets_progress':reopen_tickets_progress,
        'recent_all_tickets':recent_all_tickets,
        'seekclarity_tickets':seekclarity_tickets,
        'seekclarity_tickets_progress':seekclarity_tickets_progress,
         # Pass the selected ticket to the template
    }
    return render(request, 'Manager/Manager-base.html', context)



@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@login_required
@allowed_users(allowed_roles=['Manager'])
def assign_ticket(request, id):
    item = get_object_or_404(Item, id=id)

    if request.method == 'POST':
        assignee_id = request.POST.get('assignee')

        if assignee_id:
            assignee = User.objects.get(pk=assignee_id)
            item.assignee = assignee
            item.status = 'assigned'
            item.assigned_date = timezone.now()
            item.status_changed_by_manager = request.user

            item.save(user=request.user)
            
            # Generate the ticket text
            ticket_text = dynamic_zfill(item.id, item.store_code)
            success_message = json.dumps({'type': 'success', 'ticket_id': item.id, 'text': ticket_text})
            
            messages.success(request, success_message)
        else:
            error_message = json.dumps({'type': 'error', 'text': 'No assignee selected.'})
            messages.error(request, error_message)

    return redirect('manager_alltickets')

@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@login_required
@allowed_users(allowed_roles=['Manager'])
def manager_alltickets(request):
    engineers = User.objects.filter(groups__name='Engineer')
    engineers_count = engineers.count()  # Count the number of engineers
    status = request.GET.get('status', 'all')

    # Filter tickets based on status
    if status == 'open':
        filtered_tickets = Item.objects.filter(status='open')
    elif status == 'assigned':
        filtered_tickets = Item.objects.filter(status='assigned')
    elif status == 'seek-clarification':
        filtered_tickets = Item.objects.filter(status='seek-clarification')
    elif status == 'inprogress':
        filtered_tickets = Item.objects.filter(status='inprogress')
    elif status == 'pending':
        filtered_tickets = Item.objects.filter(status='pending')
    elif status == 'Resolved':
        filtered_tickets = Item.objects.filter(status='Resolved')
    elif status == 'closed':
        filtered_tickets = Item.objects.filter(status='closed')
    elif status == 'reopen':
        filtered_tickets = Item.objects.filter(status='reopen')
    else:
        filtered_tickets = Item.objects.all()
        
    all_items = Item.objects.all()
    total_item_count = Item.objects.all().count()
    all_tickets = Item.objects.all()
    success_param = request.GET.get('success', False)
    success_message = success_param == 'True'
    latest_ticket = None  # Initialize latest_ticket to None
    topic = "Ticket Created Successfully"  # Set the topic here

    search_query = request.GET.get('search_query', '')
 
    # Initialize the error_messages variable to None
    error_messages = None  # Changed from error_message (singular) to error_messages (plural)

    if search_query:
        filtered_tickets = filtered_tickets.filter(
            Q(store_code__icontains=search_query) |  # Search by ticket code (case-insensitive, partial match)
            Q(id__icontains=search_query) |  # Search by ticket number
            Q(status__iexact=search_query) |  # Search by status (case-insensitive)
            Q(category__name__icontains=search_query) |  # Search by category name (case-insensitive)
            Q(subcategory__name__icontains=search_query)
        )

       

        # Check if the search result is empty
        if not filtered_tickets:
            error_messages = "No matching tickets found."  # Changed to error_messages (plural)
        else:
            # Reset error_messages when search results are found
            error_messages = None

    statuses = [
        "Open",
        "Assigned",
        "Seek-clarification",
        "Assigned",
        "Inprogress",
        "Pending",
        "Resolved",
        "Closed"
    ]

   
    if success_message:
        latest_ticket = Item.objects.latest('id')  # Fetch the latest created ticket
    else:
        text = ""

      # Get the search query from the request's GET parameters
   

   # Status order mapping for custom sorting
    status_order = {
        'open': 1,
        'reopen': 2,
        'seek-clarification': 3,
        'assigned': 4,
        'inprogress': 5, 
        'pending':6,
        'closed':7,
        'Resolved':8
    }

    

    # Apply sorting logic
    filtered_tickets = sorted(
        filtered_tickets,
        key=lambda ticket: status_order.get(ticket.status, 7)  # Default to 7 if status not found
    )

    # Rename the dictionary to seek_attachments
    seek_attachments = {}
    clarification_histories = {}
    status_histories = {}  # Dictionary to store status history for each ticket
    tickets_status_history = {}

    for ticket in all_tickets:
        # Fetch attachments for each ticket
        attachments = SeekAttachment.objects.filter(item=ticket.id)
        seek_attachments[ticket.id] = attachments
        
        # Fetch clarification history for each ticket
        clarifications = SeekClarificationHistory.objects.filter(item=ticket)  # Use 'item' instead of 'ticket'
        clarification_histories[ticket.id] = clarifications

        status_histories = StatusHistory.objects.filter(item=ticket).order_by('changed_at')
        tickets_status_history[ticket.id] = status_histories
        

    engineer_data = []
    for engineer in engineers:
        assigned_tickets_count = Item.objects.filter(assignee=engineer).count()
        engineer_data.append({'engineer': engineer, 'assigned_tickets_count': assigned_tickets_count})



    # If a search query is provided, filter the tickets by ticket number or status
    

    # Fetch attachments for each ticket
    ticket_attachments = {}
    for ticket in all_tickets:
        attachments = FileUpload.objects.filter(item=ticket.id)
        ticket_attachments[ticket.id] = attachments
    
    context = {
        'all_items': all_items,  # Update the variable name
        'engineer_data': engineer_data,  # Pass engineer data to the template

        'total_item_count': total_item_count,  # Update the variable name
        'engineers': engineers,
        'all_tickets': all_tickets,
        'success_message': {
            'topic': topic,
            'text': text,
        },
        'statuses': statuses,
        
        'latest_ticket': latest_ticket,
        'ticket_attachments': ticket_attachments,  # Pass ticket attachments to the template
        'error_messages':error_messages,
        'seek_attachments': seek_attachments,  # Pass seek attachments to the template
        'clarification_histories': clarification_histories,  # Pass clarification histories to the template
        'tickets_status_history': tickets_status_history,
        'engineers_count': engineers_count,  # Pass the engineers count to the template
        'tickets': filtered_tickets,


    }
    return render(request, 'Manager/manager_alltickets.html', context)

@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@login_required
@allowed_users(allowed_roles=['Manager'])
def manager_tableview(request):
    # Order the queryset by the 'created' field in descending order
    all_tickets = Item.objects.all().order_by('id')

    # Configure the number of items per page
    #items_per_page = 10
    #paginator = Paginator(all_tickets, items_per_page)
    
    #page_number = request.GET.get('page')
    #page = paginator.get_page(page_number)
    for ticket in all_tickets:
        ticket.created_date_formatted = ticket.created.strftime('%Y-%m-%d')  # Format date
    
    # Calculate the range of items being displayed
    #start_index = (page.number - 1) * items_per_page + 1
    #end_index = min(start_index + items_per_page - 1, paginator.count)
    context = {
        'all_tickets': all_tickets,  # Use the paginated queryset
        #'page': page,
        #'start_index': start_index,
        #'end_index': end_index,
        #'total_items': paginator.count,
    }
    
    return render(request, 'Manager/manager_tables.html', context)

def parse_frontend_date(date_str):
    """Helper function to parse the date in 'Dec. 23, 2024' format."""
    try:
        # Try parsing the date using the format "Dec. 23, 2024"
        return datetime.strptime(date_str, "%b. %d, %Y").date()
    except ValueError:
        # If the date format is invalid, return None
        return None

@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@login_required
@allowed_users(allowed_roles=['Manager'])
def filter_tickets(request):
    all_tickets = Item.objects.all().order_by('id')
                       
    # Filters from the request
    from_date = request.GET.get('from_date')
    to_date = request.GET.get('to_date')
    statuses = request.GET.getlist('status')
    short_description = request.GET.get('short_description')
    detailed_description = request.GET.get('detailed_description')
    assignee = request.GET.get('assignee')
    raised_code = request.GET.get('raised_code')
    closed_date = request.GET.get('closed_date')
    ageing_days = request.GET.get('ageing_days')

    # In your filter_tickets view
    if from_date and to_date:
        # Convert strings to datetime objects
        from_date = datetime.strptime(from_date, '%Y-%m-%d')
        to_date = datetime.strptime(to_date, '%Y-%m-%d')
        # Add time component to include full last day
        to_date = to_date.replace(hour=23, minute=59, second=59, microsecond=999999)
        
        # Filter using the complete date range
        all_tickets = all_tickets.filter(created__range=(from_date, to_date))
    if statuses:
        all_tickets = all_tickets.filter(status__in=statuses)

    if short_description:
        all_tickets = all_tickets.filter(short_description__icontains=short_description)

    if detailed_description:
        all_tickets = all_tickets.filter(detailed_description__icontains=detailed_description)

    if assignee:
        all_tickets = all_tickets.filter(assignee__username__icontains=assignee)

    if raised_code:
        all_tickets = all_tickets.filter(store_code__icontains=raised_code)

    if closed_date:
        try:
            closed_date = datetime.strptime(closed_date, '%Y-%m-%d').date()
            all_tickets = all_tickets.filter(closed_date=closed_date)
        except ValueError:
            pass

    if ageing_days:
        try:
            ageing_days = int(ageing_days)
            all_tickets = all_tickets.filter(ageing_days=ageing_days)
        except ValueError:
            pass

    # Serialize tickets data
    tickets_data = [
        {
            "ticket_no": ticket.id,
            "tickets_no": ticket.ticket_no,
            "category": str(ticket.category),
            "subcategory": str(ticket.subcategory),
            "short_description": ticket.short_description,
            "detailed_description": ticket.detailed_description,
            "assignee": ticket.assignee.username if ticket.assignee else "Unassigned",
            "status": ticket.status,
            "store_code": ticket.store_code,
            "created_date": ticket.created.strftime('%Y-%m-%d %H:%M:%S'),
            "closed_date": ticket.closed_date.strftime('%Y-%m-%d %H:%M:%S') if ticket.closed_date else None,
            "ageing_days": ticket.ageing_days,
        }
        for ticket in all_tickets
    ]

    return JsonResponse({"tickets": tickets_data})

from reportlab.platypus import Spacer

def manager_export_to_pdf(request):
    authenticated_user = request.user
    statuses = request.GET.get('statuses', '').split(',')
    search_query = request.GET.get('search_query', '')
    filters = request.GET.get('filters', '').split(',')
    ticket_no = request.GET.get('ticket_no', None)
    store_code = request.GET.get('store_code', None)
    from_date = request.GET.get('from_date')
    to_date = request.GET.get('to_date')

    # Fetch all tickets
    all_tickets = Item.objects.all().order_by('-created_date')

    # Apply date range filter
    if from_date and to_date:
        from_date = datetime.strptime(from_date, '%Y-%m-%d')
        to_date = datetime.strptime(to_date, '%Y-%m-%d')
        # Add time component to include full last day
        to_date = to_date.replace(hour=23, minute=59, second=59, microsecond=999999)
        
        all_tickets = all_tickets.filter(created__range=(from_date, to_date))

    # Apply ticket number filter
    if ticket_no:
        all_tickets = all_tickets.filter(ticket_no=ticket_no)

    # Apply status filter
    if statuses and statuses[0]:
            if 'resolved' not in statuses:
                all_tickets = all_tickets.filter(Q(status__in=statuses))
            else:
                all_tickets = all_tickets.filter(Q(status__in=statuses) | Q(status='Resolved'))


    # Apply search query filter
    if search_query:
        all_tickets = all_tickets.filter(
            Q(id__icontains=search_query) |
            Q(status__iexact=search_query) |
            Q(category__name__icontains=search_query) |
            Q(subcategory__name__icontains=search_query)
        )


    filter_fields = [
        'id', 'category__name', 'subcategory__name', 'ticket_no', 'created_date',
        'short_description', 'detailed_description', 'assignee__username', 'status', 'store_code',
        'filterclosedDate', 'filterageingDays'
    ]

    for i, filter_value in enumerate(filters):
        if filter_value:
            if i < len(filter_fields):
                if filter_fields[i] == 'id':
                    all_tickets = all_tickets.filter(id=filter_value)
                elif filter_fields[i] == 'created_date':
                    try:
                        parsed_date = datetime.strptime(filter_value, '%Y-%m-%d').date()
                        all_tickets = all_tickets.filter(created__date=parsed_date)
                    except ValueError:
                        pass
                elif filter_fields[i] == 'filterclosedDate':
                    try:
                        closed_date = datetime.strptime(filter_value, '%Y-%m-%d').date()
                        all_tickets = all_tickets.filter(closed_date__date=closed_date)
                    except ValueError:
                        pass
                elif filter_fields[i] == 'filterageingDays':
                    try:
                        ageing_days = int(filter_value)
                        all_tickets = all_tickets.filter(ageing_days=ageing_days)
                    except ValueError:
                        pass
                else:
                    all_tickets = all_tickets.filter(**{f"{filter_fields[i]}__icontains": filter_value})

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="ticket_data.pdf"'

    doc = SimpleDocTemplate(response, pagesize=landscape(A4))
    elements = []

    style = getSampleStyleSheet()['BodyText']
    spacer = Spacer(1, 20)
    elements.append(spacer)

    data = [[Paragraph("Ticket Number", style), Paragraph("Category", style), Paragraph("Subcategory", style),
             Paragraph("Short Description", style), Paragraph("Detailed Description", style), Paragraph("Date", style),
             Paragraph("Status", style), Paragraph("Raised Code", style), Paragraph("Assigned To", style),
             Paragraph("Assigned Date", style), Paragraph("Closed Date", style), Paragraph("Ageing Days", style),
             Paragraph("Closure Comments", style)]]

    for ticket in all_tickets:
        data.append([
            Paragraph(dynamic_zfill(ticket.id, ticket.store_code), style),
            Paragraph(str(ticket.category), style),
            Paragraph(str(ticket.subcategory), style),
            Paragraph(ticket.short_description or '', style),
            Paragraph(ticket.detailed_description or '', style),
            Paragraph(ticket.created.strftime('%Y-%m-%d %H:%M:%S'), style),
            Paragraph(ticket.status, style),
            Paragraph(ticket.store_code, style),
            Paragraph(ticket.assignee.username if ticket.assignee else 'Unassigned', style),
            Paragraph(ticket.assigned_date.strftime('%Y-%m-%d %H:%M:%S') if ticket.assigned_date else '', style),
            Paragraph(ticket.closed_date.strftime('%Y-%m-%d %H:%M:%S') if ticket.closed_date else '', style),
            Paragraph(str(ticket.ageing_days), style),
            Paragraph(ticket.closure_comments or '', style),
        ])

    table = Table(data, repeatRows=1, colWidths=[60] * 12)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ]))

    elements.append(table)
    elements.append(spacer)
    doc.build(elements)
    return response

def manager_export_to_excel(request):
    statuses = request.GET.get('statuses', '').split(',')
    search_query = request.GET.get('search_query', '')
    filters = request.GET.get('filters', '').split(',')
    ticket_no = request.GET.get('ticket_no', None)  # Get the ticket_no from the query parameters
    all_tickets = Item.objects.all().order_by('-created_date')
    store_code = request.GET.get('store_code', None)  # Get the store_code from the query parameters
    from_date = request.GET.get('from_date')
    to_date = request.GET.get('to_date')

    if from_date and to_date:
        from_date = datetime.strptime(from_date, '%Y-%m-%d')
        to_date = datetime.strptime(to_date, '%Y-%m-%d')
        # Add time component to include full last day
        to_date = to_date.replace(hour=23, minute=59, second=59, microsecond=999999)
        
        all_tickets = all_tickets.filter(created__range=(from_date, to_date))

    # If a ticket number is provided, filter by that ticket number
    if ticket_no:
        all_tickets = all_tickets.filter(ticket_no=ticket_no)

    # Apply status filtering
    if statuses and statuses[0]:
        if 'resolved' not in statuses:
            all_tickets = all_tickets.filter(Q(status__in=statuses))
        else:
            all_tickets = all_tickets.filter(Q(status__in=statuses) | Q(status='Resolved'))

    # Apply search query filtering
    if search_query:
        all_tickets = all_tickets.filter(
            Q(id__icontains=search_query) |
            Q(status__iexact=search_query) |
            Q(category__name__icontains=search_query) |
            Q(subcategory__name__icontains=search_query)
        )

    # Map filters to fields
    filter_fields = [
        'id', 'category__name', 'subcategory__name', 'ticket_no', 'created_date',
        'short_description', 'detailed_description', 'assignee__username', 'status', 'store_code',
        'filterclosedDate', 'filterageingDays'
    ]

    # Fetch dynamic filters
    for i, filter_value in enumerate(filters):
        if filter_value:
            if i < len(filter_fields):
                if filter_fields[i] == 'id':
                    all_tickets = all_tickets.filter(id=filter_value)
                elif filter_fields[i] == 'created_date':
                    try:
                        parsed_date = datetime.strptime(filter_value, '%Y-%m-%d').date()
                        all_tickets = all_tickets.filter(created__date=parsed_date)
                    except ValueError:
                        pass
                elif filter_fields[i] == 'filterclosedDate':
                    try:
                        closed_date = datetime.strptime(filter_value, '%Y-%m-%d').date()
                        all_tickets = all_tickets.filter(closed_date__date=closed_date)
                    except ValueError:
                        pass
                elif filter_fields[i] == 'filterageingDays':
                    try:
                        ageing_days = int(filter_value)
                        all_tickets = all_tickets.filter(ageing_days=ageing_days)
                    except ValueError:
                        pass
                else:
                    all_tickets = all_tickets.filter(**{f"{filter_fields[i]}__icontains": filter_value})


    # Export to Excel
    data = {
        'Ticket Number': [dynamic_zfill(ticket.id, ticket.store_code) for ticket in all_tickets],
        'Category': [ticket.category.name for ticket in all_tickets],
        'Subcategory': [ticket.subcategory.name for ticket in all_tickets],
        'Date': [ticket.created.strftime('%Y-%m-%d %H:%M:%S') for ticket in all_tickets],
        'Short Description': [ticket.short_description or '' for ticket in all_tickets],
        'Detailed Description': [ticket.detailed_description or '' for ticket in all_tickets],
        'Status': [ticket.status for ticket in all_tickets],
        'Assigned To': [ticket.assignee.username if ticket.assignee else 'Unassigned' for ticket in all_tickets],
        'Raised Code': [ticket.store_code for ticket in all_tickets],
    }
    df = pd.DataFrame(data)

    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename="filtered_tickets.xlsx"'

    with pd.ExcelWriter(response, engine='openpyxl') as writer:
        df.to_excel(writer, index=False)

    return response

def delete_ticket(request, ticket_id):
    try:
        ticket = Item.objects.get(pk=ticket_id)
        ticket.delete()
    except Item.DoesNotExist:
        pass  # Handle the case where the ticket does not exist

    return redirect('manager_tables')

def get_ticket_details(request, ticket_id):
    try:
        ticket = Item.objects.get(id=ticket_id)
        ticket_details = {

            'category': ticket.category,

            'assignee': ticket.assignee,

            'subcategory': ticket.subcategory,

            'created': ticket.created.strftime('%Y-%m-%d %H:%M:%S'),

            'status': ticket.status,

            'raised_code':ticket.raised_code,

            'id': ticket.id,  # Include the ticket ID in the response'
            # Add more details as needed

        }

        return JsonResponse(ticket_details)

    except Item.DoesNotExist:

        return JsonResponse({'error': 'Ticket not found'}, status=404)
    

@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@login_required
@allowed_users(allowed_roles=['Manager'])
def engineers_count(request):
    engineers = User.objects.filter(groups__name='Engineer')

    # Calculate the assigned tickets count for each engineer
    engineer_data = []
    for engineer in engineers:
        assigned_tickets_count = Item.objects.filter(assignee=engineer).count()
        engineer_data.append({'engineer': engineer, 'assigned_tickets_count': assigned_tickets_count})

    context = {
        'engineers_data': engineer_data,  # Pass the list of engineer data to the template
    }

    return render(request, 'Manager/engineers_count.html', context)



def get_ticket_datas(request):
    # Fetch the dynamic data from your database or any other source
    all_tickets = Item.objects.all()
    auto_tickets_count = all_tickets.filter(approval__approval='auto').count()
    manual_tickets_count = all_tickets.filter(approval__approval='manual').count()
    data = {
        'auto_tickets_count': auto_tickets_count,
        'manual_tickets_count': manual_tickets_count,
    }
    return JsonResponse(data)











