from django.shortcuts import render,redirect,get_object_or_404
from tickets.models import *
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import cache_control
from django.db.models import Q
from django.http import JsonResponse
import json
from django.http import HttpResponse, HttpResponseRedirect
from django.core.paginator import Paginator
from tickets.templatetags.custom_filters import dynamic_zfill  # Import the custom filter
from django.utils.timezone import localtime
from tickets.templatetags.custom_filters import dynamic_zfill  # Import the filter function
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.lib.pagesizes import landscape, A4
from reportlab.platypus import PageBreak
from django.template.loader import get_template
from xhtml2pdf import pisa
import pandas as pd
from django.template.loader import render_to_string
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders

from django.utils import timezone


from user_module.decorators import allowed_users

@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@login_required()
@allowed_users(allowed_roles=['Engineer'])
def engineer_dashboard(request):
    engineer = request.user  # Get the currently logged-in engineer user
    engineer_tickets = Item.objects.filter(assignee=engineer)
    recent_engineer_tickets = Item.objects.filter(assignee=engineer).order_by('-status_changed_date')[:5]

    total_engineer_tickets = engineer_tickets.count()

    open_tickets = Item.objects.filter(status='open', assignee=engineer)
    assigned_tickets = Item.objects.filter(status='assigned', assignee=engineer)
    closed_tickets = Item.objects.filter(status='closed', assignee=engineer)
    resolved_tickets = Item.objects.filter(status='Resolved', assignee=engineer)
    seekclarify_tickets = Item.objects.filter(status='seek-clarification', assignee=engineer)

    pending_tickets = Item.objects.filter(status='pending', assignee=engineer)
    inprogress_tickets = Item.objects.filter(status='inprogress', assignee=engineer)

    all_tickets = engineer_tickets
    tickets = all_tickets.count()
   
    open_tickets_count = open_tickets.count()
    assigned_tickets_count = assigned_tickets.count()
    closed_tickets_count = closed_tickets.count()
    resolved_tickets_count = resolved_tickets.count()

    pending_tickets_count = pending_tickets.count()
    inprogress_tickets_count = inprogress_tickets.count()

    open_count = all_tickets.filter(status='open').count()
    assigned_count = assigned_tickets.filter(status='assigned').count()
    pending_count = all_tickets.filter(status='pending').count()
    closed_count = all_tickets.filter(status='closed').count()
    resolved_count = all_tickets.filter(status='Resolved').count()
    seekclarify_tickets_count = seekclarify_tickets.count()
    inprogress_count = all_tickets.filter(status='inprogress').count()
    
    if total_engineer_tickets > 0:
        open_percentage = (open_count / total_engineer_tickets) * 100
        assigned_percentage = (assigned_count / total_engineer_tickets) * 100
        pending_percentage = (pending_tickets_count / total_engineer_tickets) * 100
        closed_percentage = (closed_count / total_engineer_tickets) * 100
        resolved_percentage = (resolved_count / total_engineer_tickets) * 100
        ticket_percentage = (tickets / tickets) * 100
        inprogress_percentage = (inprogress_count / total_engineer_tickets) * 100
        engineer_tickets_percentage = (total_engineer_tickets / total_engineer_tickets) * 100
        seekclarify_tickets_percentage = (seekclarify_tickets_count / total_engineer_tickets) * 100
    else:
        assigned_percentage = 0
        pending_percentage = 0
        closed_percentage = 0
        inprogress_percentage = 0
        open_percentage=0
        open_count=0
        closed_count = 0
        ticket_percentage = 0
        inprogress_count = 0
        assigned_count=0
        pending_count=0
        resolved_percentage=0
        engineer_tickets_percentage=0
        seekclarify_tickets_percentage=0
    
    context = {
        'assigned_tickets_count': assigned_tickets_count,
        'assigned_tickets': assigned_tickets,
        'assigned_percentage':assigned_percentage,
        'pending_percentage':pending_percentage,
        'closed_percentage':closed_percentage,
        'resolved_percentage':resolved_percentage,
        'seekclarify_tickets_percentage':seekclarify_tickets_percentage,

        'ticket_percentage':ticket_percentage,
        'inprogress_percentage':inprogress_percentage,
        'pending_tickets_count':pending_tickets_count,
        'closed_tickets_count':closed_tickets_count,
        'resolved_tickets_count':resolved_tickets_count,
        'seekclarify_tickets_count':seekclarify_tickets_count,
        'inprogress_tickets_count':inprogress_tickets_count,
        'all_tickets':all_tickets,
        'pending_count':pending_count,
        'open_percentage':open_percentage,
        'resolved_percentage':resolved_percentage,
        'recent_engineer_tickets':recent_engineer_tickets,
        'tickets':tickets,

        'total_engineer_tickets': total_engineer_tickets,  # Add the total engineer's tickets to the context
        'engineer_tickets_percentage':engineer_tickets_percentage,

    }
    
    return render(request, 'Engineer/engineer_dashboard.html', context)

@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@login_required()
@allowed_users(allowed_roles=['Engineer'])
def all_tickets(request):
    seekmodule=SeekClarificationHistory.objects.all()
    engineer = request.user  # Get the currently logged-in engineer user
    assigned_tickets = Item.objects.filter( assignee=engineer)
    all_tickets = Item.objects.all()
    
    status = request.GET.get('status', 'all')

    # Filter tickets based on status
    if status == 'open':
        filtered_tickets = Item.objects.filter(status='open',assignee=engineer)
    elif status == 'assigned':
        filtered_tickets = Item.objects.filter(status='assigned',assignee=engineer)
    elif status == 'seek-clarification':
        filtered_tickets = Item.objects.filter(status='seek-clarification',assignee=engineer)
    elif status == 'inprogress':
        filtered_tickets = Item.objects.filter(status='inprogress',assignee=engineer)
    elif status == 'pending':
        filtered_tickets = Item.objects.filter(status='pending',assignee=engineer)
    elif status == 'Resolved':
        filtered_tickets = Item.objects.filter(status='Resolved',assignee=engineer)
    elif status == 'closed':
        filtered_tickets = Item.objects.filter(status='closed',assignee=engineer)
    elif status == 'reopen':
        filtered_tickets = Item.objects.filter(status='reopen',assignee=engineer)
    else:
        filtered_tickets = Item.objects.filter( assignee=engineer)
        
    search_query = request.GET.get('search_query', '')  
    success_param = request.GET.get('success', False)
    success_message = success_param == 'True'
    latest_ticket = None  
    topic = "Ticket Created Successfully" 
    error_message = None  

    # If a search query is provided, filter the tickets by ticket number or status
    if search_query:
        filtered_tickets = filtered_tickets.filter(
            Q(store_code__icontains=search_query) |  # Search by ticket code (case-insensitive, partial match)
            Q(id__icontains=search_query) |  # Search by ticket number
            Q(status__iexact=search_query) |  # Search by status (case-insensitive)
            Q(category__name__icontains=search_query) |  # Search by category name (case-insensitive)
            Q(subcategory__name__icontains=search_query)
        )

        # Check if the search result is empty
        if not filtered_tickets.exists():
            error_message = "No matching tickets found."

    if success_message:
        latest_ticket = Item.objects.latest('id')  # Fetch the latest created ticket
        text = f'TicketAWO1200000{latest_ticket.id}' if latest_ticket else ""
    else:
        text = ""

  
    # Fetch attachments for each ticket
    ticket_attachments = {}
    for ticket in all_tickets:
        attachments = FileUpload.objects.filter(item=ticket.id)
        ticket_attachments[ticket.id] = attachments
    # Debugging: Print ticket IDs and the number of attachments
    
    # Rename the dictionary to seek_attachments
    seek_attachments = {} 
    clarification_histories = {}
    
    for ticket in assigned_tickets:
        # Fetch attachments for each ticket
        attachments = SeekAttachment.objects.filter(item=ticket.id)
        seek_attachments[ticket.id] = attachments
        
        # Fetch clarification history for each ticket
        clarifications = SeekClarificationHistory.objects.filter(item=ticket)  # Use 'item' instead of 'ticket'
        clarification_histories[ticket.id] = clarifications
    user=request.user
    print("logged_user:",user)
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

    context = {
        'assigned_tickets': assigned_tickets,
        'filtered_tickets': filtered_tickets,
        'ticket_attachments': ticket_attachments,  # Pass ticket attachments to the template
        'error_message':error_message,
        'success_message': {
            'topic': topic,
            'text': text,
        },
        'latest_ticket': latest_ticket,
        'messages': messages.get_messages(request) , # Include the messages here
        'seek_attachments': seek_attachments,  # Pass seek attachments to the template
        'clarification_histories': clarification_histories,  # Pass clarification histories to the template
        'seekmodule':seekmodule
        }
    
    return render(request, 'Engineer/engineer_alltickets.html', context)

 
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@login_required
@allowed_users(allowed_roles=['Engineer'])
def update_status(request, item_id):

    if request.method == 'POST':
        engineer = request.user  # Get the currently logged-in engineer user

        try:
            item = Item.objects.get(pk=item_id)
            

            # Check if the engineer is assigned to the ticket
            if item.assignee == engineer:
                new_status = request.POST.get('status')
                print(f"New Status: {new_status}")  # Debugging line

                # Validate the new status against allowed values
                allowed_statuses = ['inprogress', 'pending', 'Resolved','seek-clarification']

                if new_status in allowed_statuses:
                    # Update the item status
                    item.status = new_status

                    # Set the resolved_date field to the current time when status is set to 'Resolved'
                    if new_status == 'Resolved':
                        item.resolved_date = timezone.localtime(timezone.now())  # Ensure it's timezone-aware

                    # Save resolver_comments if provided in the form
                    resolver_comments = request.POST.get('resolver_comments', '').strip()
                    if resolver_comments:
                        current_time = timezone.now().strftime('%Y-%m-%d %H:%M:%S')
                        resolver_name = engineer.username
                        formatted_comment = f"Comment by {resolver_name} on {current_time}: {resolver_comments}"
                        # Append the new comment to the existing comments
                        if item.resolver_comments and formatted_comment not in item.resolver_comments:
                            item.resolver_comments += "\n" + formatted_comment
                        else:
                            item.resolver_comments = formatted_comment
                                                
                    # Save seek clarification comments and attachments if the status is 'seek-clarification'
                 
                    if new_status == 'seek-clarification':
                        seek_comments = request.POST.get('seek_comments', '').strip()
                        seek_attachments = request.FILES.getlist('attachments')  # Get uploaded files as a list
                        print(f"Seek Attachments: {seek_attachments}")  # Debugging line

                        if not seek_comments:  # If seek_comments is empty or whitespace
                            messages.error(request, json.dumps({
                                'type': 'error',
                                'text': 'Seek clarification comments are required when changing status to seek-clarification.'
                            }))
                            return redirect('engineer_alltickets')

                        # Log the seek clarification comment with timestamp in SeekClarificationHistory model
                        clarification_history = SeekClarificationHistory.objects.create(
                            item=item,
                            seek_comment=seek_comments,
                            created_by=engineer  # Engineer who is updating the status
                        )

                        # Save each attachment with the created clarification_history
                        for file in seek_attachments:
                            SeekAttachment.objects.create(
                                item=item,
                                clarification_image=file,
                                created_by=engineer,
                                clarification_history=clarification_history  # Associate attachment with clarification history
                            )

                    # Save the updated item
                    item.save(user=request.user)
                    messages.success(request, json.dumps({
                        'type': 'success',
                        'text': dynamic_zfill(item.id, item.store_code)
                    }))
                else:
                    messages.error(request, 'Invalid status value.')
            else:
                messages.error(request, 'You are not assigned to this ticket.')

        except Item.DoesNotExist:
            messages.error(request, 'Ticket not found.')
        except Exception as e:
            # Print the exception in the command line for debugging
            print(f"Error: {e}")

    return redirect('engineer_alltickets')


@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@login_required()
@allowed_users(allowed_roles=['Engineer'])
def table_view(request):
    engineer = request.user  # Get the currently logged-in engineer user

    all_tickets = Item.objects.filter(assignee=engineer).order_by('id')

    # Configure the number of items per page
   #items_per_page = 10
   #paginator = Paginator(all_tickets, items_per_page)
    
   #page_number = request.GET.get('page')
   #page = paginator.get_page(page_number)
    
    # Calculate the range of items being displayed
   #start_index = (page.number - 1) * items_per_page + 1
   #end_index = min(start_index + items_per_page - 1, paginator.count)
    context = {
        'all_tickets': all_tickets,
        #page': page,
        #start_index': start_index,
        #end_index': end_index,
        #total_items': paginator.count,
    }
    
    return render(request, 'Engineer/engineer_tables.html', context)

from django.http import JsonResponse
from datetime import datetime
def filter_tickets(request):
    engineer = request.user  # Get the currently logged-in engineer user
    all_tickets = Item.objects.filter(assignee=engineer).order_by('id')
    
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

        # Apply status filter
    # Apply status filter
    if statuses and statuses[0]:
        if 'resolved' not in statuses:
            all_tickets = all_tickets.filter(Q(status__in=statuses))
        else:
            all_tickets = all_tickets.filter(Q(status__in=statuses) | Q(status='Resolved'))
       
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


def parse_frontend_date(date_str):
    """Helper function to parse the date in 'Dec. 23, 2024' format."""
    try:
        # Try parsing the date using the format "Dec. 23, 2024"
        return datetime.strptime(date_str, "%b. %d, %Y").date()
    except ValueError:
        # If the date format is invalid, return None
        return None
 
def engineer_export_to_pdf(request):
    current_user = request.user
    
    statuses = request.GET.get('statuses', '').split(',')
    search_query = request.GET.get('search_query', '')
    filters = request.GET.get('filters', '').split(',')
    ticket_no = request.GET.get('ticket_no', None)
    store_code = request.GET.get('store_code', None)
    from_date = request.GET.get('from_date')
    to_date = request.GET.get('to_date')
    # Sanitize the text
    def sanitize_text(text):
        if text is None:
            return ''
        return strip_tags(text)

    all_tickets = Item.objects.filter(assignee=current_user).order_by('-created_date')
 
    # Apply date range filter
    if from_date and to_date:
        # Convert strings to datetime objects
        from_date = datetime.strptime(from_date, '%Y-%m-%d')
        to_date = datetime.strptime(to_date, '%Y-%m-%d')
        # Add time component to include full last day
        to_date = to_date.replace(hour=23, minute=59, second=59, microsecond=999999)
        
        # Filter using the complete date range
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


    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="ticket_data.pdf"'

    doc = SimpleDocTemplate(response, pagesize=landscape(A4))
    elements = []

    style = getSampleStyleSheet()['BodyText']

    data = [
        [Paragraph("Ticket Number", style), Paragraph("Category", style), Paragraph("Subcategory", style), 
         Paragraph("Short Description", style), Paragraph("Detailed Description", style), Paragraph("Date", style), 
         Paragraph("Status", style), Paragraph("Assigned To", style), Paragraph("Assigned Date", style), 
         Paragraph("Closed Date", style), Paragraph("Closure Comments", style)]
    ]

    for ticket in all_tickets:
        data.append([
            Paragraph(dynamic_zfill(ticket.id, ticket.store_code), style),
            Paragraph(str(ticket.category), style),
            Paragraph(str(ticket.subcategory), style),
            Paragraph(sanitize_text(ticket.short_description), style),
            Paragraph(sanitize_text(ticket.detailed_description), style),
            Paragraph(ticket.created.strftime('%Y-%m-%d %H:%M:%S'), style),
            Paragraph(ticket.status, style),
            Paragraph(ticket.assignee.username if ticket.assignee else 'Unassigned', style),
            Paragraph(ticket.assigned_date.strftime('%Y-%m-%d %H:%M:%S') if ticket.assigned_date else '', style),
            Paragraph(ticket.closed_date.strftime('%Y-%m-%d %H:%M:%S') if ticket.closed_date else '', style),
            Paragraph(ticket.closure_comments or '', style)
        ])

    table = Table(data, repeatRows=1, colWidths=[50, 50, 50, 80, 80, 60, 60, 60, 60, 60, 80])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.white),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('WORDWRAP', (0, 0), (-1, -1), 'CJK'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP')
    ]))

    elements.append(table)
    elements.append(PageBreak())
    doc.build(elements)
 
    return response

def engineer_export_to_excel(request):
    current_user = request.user
    
    statuses = request.GET.get('statuses', '').split(',')
    search_query = request.GET.get('search_query', '')
    filters = request.GET.get('filters', '').split(',')
    ticket_no = request.GET.get('ticket_no', None)
    store_code = request.GET.get('store_code', None)
    from_date = request.GET.get('from_date')
    to_date = request.GET.get('to_date')

    all_tickets = Item.objects.filter(assignee=current_user).order_by('-created_date')
 
    # Apply date range filter
    if from_date and to_date:
        # Convert strings to datetime objects
        from_date = datetime.strptime(from_date, '%Y-%m-%d')
        to_date = datetime.strptime(to_date, '%Y-%m-%d')
        # Add time component to include full last day
        to_date = to_date.replace(hour=23, minute=59, second=59, microsecond=999999)
        
        # Filter using the complete date range
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
                    
    data = {
        'Ticket Number': [
            dynamic_zfill(ticket.id, ticket.store_code) for ticket in all_tickets
        ], 
        'Created By': [
            ticket.created_by.username if ticket.created_by else 'Unknown' 
            for ticket in all_tickets
        ],        
        'Category': [ticket.category for ticket in all_tickets],
        'Subcategory': [ticket.subcategory for ticket in all_tickets],
        'Date': [ticket.created.strftime('%Y-%m-%d %H:%M:%S') for ticket in all_tickets],
        'Short Description':[ticket.short_description for ticket in all_tickets],
        'Detailed Description':[ticket.detailed_description for ticket in all_tickets],
        'Status': [ticket.status for ticket in all_tickets],
        'Assigned_to':[ticket.assignee for ticket in all_tickets],
        'Ticket Assigned Date': [
            localtime(ticket.assigned_date).strftime('%Y-%m-%d %H:%M:%S') if ticket.assigned_date else '' 
            for ticket in all_tickets
        ],
        'Ticket Closed Date': [
            localtime(ticket.closed_date).strftime('%Y-%m-%d %H:%M:%S') if ticket.closed_date else '' 
            for ticket in all_tickets
        ],
        'Closure Comments':[ticket.closure_comments for ticket in all_tickets],      
    }
    df = pd.DataFrame(data)

    response = HttpResponse(content_type='application/ms-excel')
    response['Content-Disposition'] = 'attachment; filename="ticket_data.xlsx"'
    df.to_excel(response, index=False)

    return response

def get_ticket_details(request, ticket_id):
    try:
        ticket = Item.objects.gets(id=ticket_id)
        ticket_details = {

            'category': ticket.category,

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
    
# Email configuration
from_email = "wwdsupport_noreply@titan.co.in"
smtp_server = 'titan-co-in.mail.protection.outlook.com'
smtp_port = 25

# Function to validate email format (optional)
def validate_email(email):
    import re
    email_regex = r"(^[a-z0-9]+[.-_]?[a-z0-9]+@[a-z0-9.-]+\.[a-z]{2,6}$)"
    return bool(re.match(email_regex, email))

from email.mime.base import MIMEBase
from email import encoders
from django.db import transaction

def forward_mail_pending(request, ticket_id):
    print("forward_mail_pending view has been called.")

    if request.method == "POST":
        print("Request method is POST.")

        ticket = Item.objects.get(id=ticket_id)
        email_input = request.POST.get('email')
        resolver_comments = request.POST.get('resolver_comments', '').strip()
        print(f"Email input received: {email_input}")
        print(f"Resolver comments received: {resolver_comments}")

        if email_input:
            recipient_list = [email.strip() for email in email_input.split(',')]
            print(f"Recipient list: {recipient_list}")

            invalid_emails = [email for email in recipient_list if not validate_email(email)]
            if invalid_emails:
                print(f"Invalid email addresses: {invalid_emails}")
                messages.error(request, f"Invalid email address(es): {', '.join(invalid_emails)}")
                return redirect('engineer_alltickets')

            # **Use a transaction to ensure database updates are atomic**
            try:
                with transaction.atomic():  # Now email sending is inside the transaction
                    # **Update ticket fields before sending email**
                    if resolver_comments:
                        ticket.resolver_comments = resolver_comments  
                    ticket.status = 'pending'
                    ticket.status_changed_date = timezone.now()  # Update status change date
                    ticket.save()

                    print(f"Updated Ticket Status: {ticket.status}, Resolver Comments: {ticket.resolver_comments}")
                    print(f"Updated Status Changed Date: {ticket.status_changed_date}")

                    # **Render the email template with updated details**
                    subject = 'Ticket Forwarded'
                    cc_list = ["Nandhini.V@titan.co.in"]  # CC list

                    html_message = render_to_string('Engineer/ticket_forward_email.html', {
                        'ticket': ticket,  
                        'resolver_comments': resolver_comments if resolver_comments else "No comments provided",
                    })

                    # **Create the email message object**
                    msg = MIMEMultipart()
                    msg['From'] = from_email
                    msg['To'] = ", ".join(recipient_list)
                    msg['Cc'] = ", ".join(cc_list)  # Add CC recipients
                    msg['Subject'] = subject
                    msg.attach(MIMEText(html_message, 'html'))

                    # **Attach files to the email**
                    attachment_files = ticket.uploads.all()
                    for file_upload in attachment_files:
                        file_path = file_upload.file.path
                        file_name = file_upload.file.name
                        print(f"Attaching file: {file_name}")

                        with open(file_path, 'rb') as file:
                            part = MIMEBase('application', 'octet-stream')
                            part.set_payload(file.read())
                            encoders.encode_base64(part)
                            part.add_header('Content-Disposition', f'attachment; filename={file_name}')
                            msg.attach(part)

                    # **Send the email including CC recipients**
                    with smtplib.SMTP(smtp_server, smtp_port) as server:
                        server.starttls()
                        server.sendmail(from_email, recipient_list + cc_list, msg.as_string())  # Include CCs
                        print("Ticket Forward Email Sent Successfully")

                # If we reach here, email and DB updates are successful
                messages.success(request, "Ticket forwarded successfully!", extra_tags='forward_mail_pending')
                print("Email sent successfully.")

            except Exception as e:
                print(f"An error occurred: {e}")

                error_message = f"An error occurred while sending the email: {e}"
                messages.error(request, error_message, extra_tags='forward_mail_pending')
                return redirect('engineer_alltickets')

        else:
            print("No email input provided.")
            messages.error(request, "Please enter a valid email address.", extra_tags='forward_mail_pending')

    return redirect('engineer_alltickets')
