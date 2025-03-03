from django.shortcuts import render,redirect,get_object_or_404
from django.contrib.auth.models import User,Group
from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required, user_passes_test
from django.views.decorators.cache import cache_control
from user_module.decorators import allowed_users
from django.db.models import Q
from django.core.exceptions import ObjectDoesNotExist  
from django.http import  HttpResponseRedirect, HttpResponse
from django.contrib import messages
from django.urls import reverse
from django.template.loader import get_template
from xhtml2pdf import pisa
from django.db import IntegrityError
import pandas as pd
from django.http import HttpResponseNotFound
from tickets.templatetags.custom_filters import dynamic_zfill  # Import the custom filter
from django.utils.timezone import localtime
from tickets.templatetags.custom_filters import dynamic_zfill  # Import the filter function
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.lib.pagesizes import landscape, A4
from reportlab.platypus import PageBreak
from .forms import *
from tickets.models import *
from tickets.forms import *


@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@login_required()
@allowed_users(allowed_roles=['Admin'])
def master_dashboard(request):
    # Count auto tickets
    auto_tickets_count = Item.objects.filter(approval__approval='auto').count()
    
    # Count manual tickets
    manual_tickets = Item.objects.filter(approval__approval='manual')
    open_tickets = Item.objects.filter(status='open').count()
    assigned_tickets = Item.objects.filter(status='assigned').count()
    pending_tickets = Item.objects.filter(status='pending').count()
    inprogress_tickets = Item.objects.filter(status='inprogress').count()
    resolved_tickets = Item.objects.filter(status='Resolved').count()
    closed_tickets = Item.objects.filter(status='closed').count()
    seek_clarification_tickets = Item.objects.filter(status='seek-clarification').count()
    reopen_tickets = Item.objects.filter(status='reopen').count()
    manual_tickets_count = Item.objects.filter(approval__approval='manual').count()

    # Count overall tickets
    overall_tickets_count = Item.objects.count()
    recent_tickets = Item.objects.all().order_by('-status_changed_date')[:10]
    # Count engineers
    engineers_count = User.objects.filter(groups__name='Engineer').count()

    # Create a context dictionary with the counts
    context = {
        'auto_tickets_count': auto_tickets_count,
        'manual_tickets_count': manual_tickets_count,
        'overall_tickets_count': overall_tickets_count,
        'engineers_count': engineers_count,
        'manual_tickets':manual_tickets,
        'recent_tickets':recent_tickets,
        'open_tickets':open_tickets,
        'assigned_tickets':assigned_tickets,
        'pending_tickets':pending_tickets,
        'inprogress_tickets':inprogress_tickets,
        'resolved_tickets':resolved_tickets,
        'closed_tickets':closed_tickets,
        'seek_clarification_tickets':seek_clarification_tickets,
        'reopen_tickets':reopen_tickets
    }

    return render(request, 'Admin/admin_dashboard.html', context)

@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@login_required()
@allowed_users(allowed_roles=['Admin'])
def category_subcategory_view(request):
    categories = Category.objects.all().order_by('-id')
    subcategories = Subcategory.objects.all().order_by('-id')
    approvalmatrix = ApprovalMatrix.objects.all()

    paginator = Paginator(categories, 8)  
    page = request.GET.get('page')  
    categories = paginator.get_page(page)

    error_message = None  
    form_has_errors = False  # Flag to track form errors

    if request.method == 'POST':
        category_form = CategoryForm(request.POST)
        if category_form.is_valid():
            category_name = category_form.cleaned_data['name']
            if Category.objects.filter(name=category_name).exists():
                error_message = f"Category '{category_name}' already exists."
                form_has_errors = True
            else:
                category_form.save()
                return redirect('create_page')  
        else:
            error_message = "Invalid form submission. Please try again."
            form_has_errors = True
    else:
        category_form = CategoryForm()

    return render(request, 'Admin/createpage.html', {
        'categories': categories,
        'subcategories': subcategories,
        'approvalmatrix': approvalmatrix,
        'category_form': category_form,
        'error_message': error_message,
        'form_has_errors': form_has_errors  # Pass the error flag
    })


@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@login_required()
@allowed_users(allowed_roles=['Admin'])
def create_subcategory(request):
    if request.method == 'POST':
        subcategory_form = SubcategoryForm(request.POST)
        if subcategory_form.is_valid():
            subcategory_form.save()
            return JsonResponse({'success': True})
        else:
            print(subcategory_form.errors)  # Debugging: Print form errors
            return JsonResponse({'success': False, 'errors': subcategory_form.errors})
    else:
        subcategory_form = SubcategoryForm()

    return render(request, 'Admin/createpage.html', {'subcategory_form': subcategory_form})

@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@login_required()
@allowed_users(allowed_roles=['Admin'])
def create_approval_matrix(request):
    if request.method == 'POST':
        form = ApprovalMatrixForm(request.POST)
        if form.is_valid():
            cleaned_data = form.cleaned_data
            if ApprovalMatrix.objects.filter(functionally=cleaned_data['functionally'], technically=cleaned_data['technically']).exists():
                form.add_error(None, 'An approval matrix with this combination of functionality and technicality already exists.') 
            else:
                instance = form.save(commit=False)
                instance.save()
                return redirect('create_page') 
        else:
            print("Form errors:", form.errors.as_json())
    else:
        form = ApprovalMatrixForm()

    # Get existing records
    existing_records = ApprovalMatrix.objects.all().order_by('approval') 
    print("exiting:",existing_records)

    return render(request, 'Admin/createpage.html', {'form': form, 'existing_records': existing_records})

@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@login_required()
@allowed_users(allowed_roles=['Admin'])
def admin_all_tickets(request):
    engineers = User.objects.filter(groups__name='Engineer')
    all_items = Item.objects.all()
    total_item_count = Item.objects.all().count()
    all_tickets = Item.objects.all()
    
    
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

    search_query = request.GET.get('search_query', '')

    # Initialize the error_message variable to None
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
        if not filtered_tickets:
            error_message = "No matching tickets found."
    # Define a custom sorting function to order the statuses
    def custom_sort(ticket):
        status_order = {
            'open': 0,
            'assigned': 1,
            'inprogress': 2,
            'pending': 3,
            'Resolved': 4,
            'closed': 5,
        }
        return status_order.get(ticket.status, 5)  # Default to a high number for other statuses

    # Sort the tickets based on the custom sorting function
    filtered_tickets = sorted(filtered_tickets, key=custom_sort)


    success_param = request.GET.get('success', False)
    success_message = success_param == 'True'
    latest_ticket = None  # Initialize latest_ticket to None
    topic = "Ticket Created Successfully"  # Set the topic here

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
    for ticket_id, attachments in ticket_attachments.items():
        print(f"Ticket ID: {ticket_id}, Number of Attachments: {attachments.count()}")

    context = {
        'all_items': all_items,  # Update the variable name
        'total_item_count': total_item_count,  # Update the variable name
        'engineers': engineers,
        'all_tickets': all_tickets,
        'success_message': {
            'topic': topic,
            'text': text,
        },
        'latest_ticket': latest_ticket,
        'ticket_attachments': ticket_attachments,  # Pass ticket attachments to the template
        'error_message':error_message,
        'filtered_tickets':filtered_tickets,

    }
    return render(request, 'Admin/admin_alltickets.html', context)


@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@login_required()
@allowed_users(allowed_roles=['Admin'])
def admin_create_ticket(request):
    categories = Category.objects.all()
    subcategories = Subcategory.objects.all()
    approval_matrix = ApprovalMatrix.objects.all()  # Fetch all approval matrix entries
    
    context = {
        'categories': categories,
        'subcategories': subcategories,
    }

    if request.method == 'POST':
        category_id = request.POST.get('category')
        subcategory_id = request.POST.get('subcategory')
        description = request.POST.get('description')
        files = request.FILES.getlist('fileUpload[]')  # Get a list of uploaded files

        # Check if the user selected 'Please select' for category or subcategory
        if category_id == 'Please select':
            messages.error(request, 'Please select a valid category.')
        elif subcategory_id == 'Please select':
            messages.error(request, 'Please select a valid subcategory.')
        elif not description:
            messages.error(request, 'Description is required.')
        else:
            try:
                category = Category.objects.get(pk=int(category_id))
                subcategory = Subcategory.objects.get(pk=int(subcategory_id))
                
                # Fetch the functionality and technically values from the selected subcategory
                functionality = subcategory.functionality
                technically = subcategory.technically

            except (ValueError, Category.DoesNotExist, Subcategory.DoesNotExist):
                messages.error(request, 'Invalid category or subcategory selected.')
            else:
                total_file_size = sum(file.size for file in files)
                # Check if the total file size exceeds 30KB (30 * 1024 bytes)
                if total_file_size > 30 * 1024:
                    messages.error(request, 'Total file size exceeds 30KB. Please reduce the file sizes.')
                else:
                    # Find the matching ApprovalMatrix entry based on functionality and technically
                    try:
                        approval_entry = approval_matrix.get(functionally=functionality, technically=technically)
                    except ApprovalMatrix.DoesNotExist:
                        messages.error(request, 'No matching approval matrix entry found.')
                    else:
                        item = Item(category=category, subcategory=subcategory, description=description)
                        item.functionality = functionality  # Set the functionality value
                        item.technically = technically  # Set the technically value
                        item.approval = approval_entry  # Set the approval value from the ApprovalMatrix
                        item.created_by = request.user

                        if request.user.stores.exists():
                            item.store_code = request.user.stores.first().store_code
                        else:
                            item.store_code = None

                        item.save()

                        for file in files:
                            file_size = file.size
                            file_upload = FileUpload(
                                item=item,
                                file=file,
                                file_size=file_size,
                                # ... (other fields if needed)
                            )
                            file_upload.save()

                        return redirect(reverse('admin_all_tickets')+ '?success=True')

    return render(request, 'Admin/admin_create_ticket.html', context)





@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@login_required()
def delete_catagory(request, id):
  categories = Category.objects.get(id=id)
  categories.delete()
  return HttpResponseRedirect(reverse('create_page')) 

def delete_sub(request, id):
    subcategory = get_object_or_404(Subcategory, id=id)
    subcategory.delete()
    return redirect('create_page')  # Ensure 'create_page' is defined in your URLs

from django.http import JsonResponse
from django.db.models import Q

def update_category(request, category_id):
    if request.method == "POST":
        value = request.POST.get("value")
        field = request.POST.get("field")
        category = Category.objects.get(pk=category_id)

        # Check for duplicate category name
        if field == "name":
            if Category.objects.filter(name=value).exclude(id=category_id).exists():
                return JsonResponse({"success": False, "error": "Category name already exists."})

            category.name = value
        elif field == "technically":
            category.technically = value
        elif field == "functionality":
            category.functionality = value

        category.save()

        return JsonResponse({"success": True})

    return JsonResponse({"success": False})



def get_subcategory_data(request, subcategory_id):
    try:
        subcategory = Subcategory.objects.get(pk=subcategory_id)
        subcategories = Subcategory.objects.filter(category=subcategory.category).values("id", "name","functionality","technically")

        data = list(subcategories)
        return JsonResponse({"success": True, "data": data})
    except Subcategory.DoesNotExist:
        return JsonResponse({"success": False})


from django.shortcuts import get_object_or_404

def edit_subcategory(request):
    if request.method == 'POST':
        subcategory_id = request.POST['subcategory_id']
        try:
            subcategory = Subcategory.objects.get(pk=subcategory_id)
            
            # Fetch the Category instance based on the selected category's ID
            category_id = request.POST['category']
            category = get_object_or_404(Category, pk=category_id)
            
            subcategory.category = category
            subcategory.name = request.POST['name']
            subcategory.functionality = request.POST['functionality']
            subcategory.technically = request.POST['technically']
            subcategory.save()
            return redirect('create_page')  # Replace 'category_list' with your actual URL pattern name
        except Subcategory.DoesNotExist:
            # Handle the case where the Subcategory doesn't exist
            pass
    # Handle other cases here or return an error response


@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@login_required()
@allowed_users(allowed_roles=['Admin'])
def admin_engineers_count(request):
    engineers = User.objects.filter(groups__name='Engineer')

    # Calculate the assigned tickets count for each engineer
    engineer_data = []
    for engineer in engineers:
        assigned_tickets_count = Item.objects.filter(assignee=engineer).count()
        engineer_data.append({'engineer': engineer, 'assigned_tickets_count': assigned_tickets_count})

    context = {
        'engineers_data': engineer_data,  # Pass the list of engineer data to the template
    }

    return render(request, 'Admin/engineers_ticket.html', context)

@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@login_required()
@allowed_users(allowed_roles=['Admin'])
def admin_reports(request):
    # Order the queryset by the 'created' field in descending order
    all_tickets = Item.objects.all().order_by('id')
    for ticket in all_tickets:
        ticket.created_date_formatted = ticket.created.strftime('%Y-%m-%d')
    # Configure the number of items per page
    #items_per_page = 10
    #paginator = Paginator(all_tickets, items_per_page)
    
    #page_number = request.GET.get('page')
    #page = paginator.get_page(page_number)
    
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
    
    return render(request, 'Admin/admin_tables.html', context)
def admin_filter_tickets(request):
    all_tickets = Item.objects.all()

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

from reportlab.platypus import Spacer

def admin_export_to_pdf(request):
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
    if statuses and statuses[0]:
        if 'resolved' not in statuses:
            all_tickets = all_tickets.filter(Q(status__in=statuses))
        else:
            all_tickets = all_tickets.filter(Q(status__in=statuses) | Q(status='Resolved'))
       
    # Apply ticket number filter
    if ticket_no:
        all_tickets = all_tickets.filter(ticket_no=ticket_no)

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


def admin_export_to_excel(request):
    statuses = request.GET.get('statuses', '').split(',')
    search_query = request.GET.get('search_query', '')
    filters = request.GET.get('filters', '').split(',')
    ticket_no = request.GET.get('ticket_no', None)
    store_code = request.GET.get('store_code', None)
    from_date = request.GET.get('from_date')
    to_date = request.GET.get('to_date')

    # Fetch all tickets
    all_tickets = Item.objects.all().order_by('-created_date')

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
       
    # Apply ticket number filter
    if ticket_no:
        all_tickets = all_tickets.filter(ticket_no=ticket_no)

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
        'Category': [ticket.category.name for ticket in all_tickets],
        'Subcategory': [ticket.subcategory.name for ticket in all_tickets],
        'Date': [ticket.created.strftime('%Y-%m-%d %H:%M:%S') for ticket in all_tickets],
        'Short Description':[ticket.short_description for ticket in all_tickets],
        'Detailed Description':[ticket.detailed_description for ticket in all_tickets],
        'Status': [ticket.status for ticket in all_tickets],
        'Assigned_to':[ticket.assignee.username if ticket.assignee else 'Unassigned' for ticket in all_tickets],
        'Ticket Assigned Date': [
            localtime(ticket.assigned_date).strftime('%Y-%m-%d %H:%M:%S') if ticket.assigned_date else '' 
            for ticket in all_tickets
        ],
        'Ticket Closed Date': [
            localtime(ticket.closed_date).strftime('%Y-%m-%d %H:%M:%S') if ticket.closed_date else '' 
            for ticket in all_tickets
        ],
        'Ticket Ageing Days': [ticket.ageing_days for ticket in all_tickets],

        'Closure Comments':[ticket.closure_comments for ticket in all_tickets],    
    }
    df = pd.DataFrame(data)

    response = HttpResponse(content_type='application/ms-excel')
    response['Content-Disposition'] = 'attachment; filename="ticket_data.xlsx"'

    df.to_excel(response, index=False)

    return response

def admin_delete_ticket(request, ticket_id):
    try:
        ticket = Item.objects.get(pk=ticket_id)
        ticket.delete()
    except Item.DoesNotExist:
        pass  # Handle the case where the ticket does not exist

    return redirect('admin_reports')

def admin_get_ticket_details(request, ticket_id):
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
@login_required()
@allowed_users(allowed_roles=['Admin'])
def Non_Ad_user_creation(request, user_id=None):
    if request.method == 'POST':
        if user_id:
            try:
                user = User.objects.get(id=user_id)
            except User.DoesNotExist:
                return HttpResponseNotFound("User not found.") 
            form = CustomUserChangeForm(request.POST, instance=user)
        else:
            form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save() 
            return redirect('user_list')
        else:
            return render(request, 'Admin/user_create.html', {'form': form, 'user_id': user_id})  # Remove 'user' from the context 
    else:
        if user_id:
            try:
                user = User.objects.get(id=user_id)
            except User.DoesNotExist:
                return HttpResponseNotFound("User not found.") 
            form = CustomUserChangeForm(instance=user)
        else:
            form = CustomUserCreationForm()
        return render(request, 'Admin/user_create.html', {'form': form, 'user_id': user_id})


@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@login_required()
@allowed_users(allowed_roles=['Admin'])
def Ad_user_creation(request, user_id=None):
    if request.method == 'POST':
        if user_id: 
            user = User.objects.get(id=user_id)
            form = AdUserCreationForm(request.POST, instance=user)
        else:
            form = AdUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save() 
            return redirect('user_list') 
        else:
            user = None 
    else:
        if user_id:
            user = User.objects.get(id=user_id)
            form = AdUserCreationForm(instance=user)
        else:
            form = AdUserCreationForm()
            user = None 

    return render(request, 'Admin/ad_user_create.html', {'form': form, 'user_id': user_id, 'user': user})


@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@login_required()
@allowed_users(allowed_roles=['Admin'])
def user_list(request):
    users = User.objects.all().select_related('usertype') 
    storecode=Store.objects.all()
    context = {
        'users': users,  # Pass the user data to the template
        'storecode':storecode,
    }
    return render(request, 'Admin/user_list.html',context)




@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@login_required()
@allowed_users(allowed_roles=['Admin'])
def add_storecode(request):
    if request.method == 'POST':
        form = AddStoreCodeForm(request.POST)

        if form.is_valid():
            selected_username = form.cleaned_data['username']
            store_code = form.cleaned_data['store_code']

            # Find the user by the selected username
            selected_user = User.objects.get(username=selected_username)

            # Check if the user is in the "CFAPerson" group
            store_person_group = Group.objects.get(name='CFAPerson')

            if selected_user.groups.filter(pk=store_person_group.pk).exists():
                # CFAPerson can have only one store
                existing_store = Store.objects.filter(user=selected_user).first()
                if existing_store:
                    form.add_error(None, "CFAPersons can have only one store.")
                else:
                    # Create a new Store object and save it
                    store = Store(store_code=store_code, user=selected_user)
                    store.save()

                    return redirect('storecode_list')  # Redirect to a success page
            else:
                form.add_error(None, "The selected user is not in the 'CFAPerson' group.")
        else:
            print(form.errors)  # Print the validation errors to the console
    else:
        form = AddStoreCodeForm()

    # Fetch a list of usernames
    usernames = User.objects.filter(groups__name='CFAPerson').values_list('username', flat=True)

    return render(request, 'Admin/add_storecode.html', {'form': form, 'usernames': usernames})

@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@login_required()
@allowed_users(allowed_roles=['Admin'])
def storecode_list(request):
    stores=Store.objects.all()
    context={
        'stores':stores,
    }
    return render(request,'Admin/storecode_list.html',context)



def user_delete(request, user_id):
    try:
        # Retrieve the user using the provided user_id
        user = get_object_or_404(User, id=user_id)
        
        # Deactivate the user by setting is_active to False
        user.is_active = False
        user.save()  # Save the change to the database
        
    except User.DoesNotExist:
        pass  # Handle the case where the user does not exist
    
    # Redirect to the user list page or any other page as required
    return redirect('user_list')


@login_required
@allowed_users(allowed_roles=['Admin'])
def edit_approval_matrix(request, approval_id):
    if request.method == 'POST':
        # Get the ApprovalMatrix instance to edit
        approval_matrix = ApprovalMatrix.objects.get(pk=approval_id)
        
        form = ApprovalMatrixForm(request.POST, instance=approval_matrix)
        if form.is_valid():
            # Print the values of the three fields for debugging
            print("Functionally:", form.cleaned_data['functionally'])
            print("Technically:", form.cleaned_data['technically'])
            print("Approval:", form.cleaned_data['approval'])
            
            # Update the instance with the edited data
            approval_matrix.functionally = form.cleaned_data['functionally']
            approval_matrix.technically = form.cleaned_data['technically']
            approval_matrix.approval = form.cleaned_data['approval']
            
            # Save the edited instance
            approval_matrix.save()

            # You can add a success message or redirect to another page here
            return redirect('create_page')  # Replace 'success_view_name' with the name of your success view
    else:
        form = ApprovalMatrixForm()

    return render(request, 'Admin/createpage.html', {'form': form})



def delete_approval_matrix(request, approval_id):
    approval = get_object_or_404(ApprovalMatrix, id=approval_id)
    approval.delete()
    return redirect('create_page')