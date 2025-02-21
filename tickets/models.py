from django.db import models
from django.contrib.auth.models import User, Group
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.db.models import Count, Min
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import date
from datetime import datetime
from django.utils.timezone import now

from django.core.validators import RegexValidator


no_special_characters_validator = RegexValidator(
    r'^[a-zA-Z0-9\s\-\_,\.\(\):;\'"%]*$',
    'Only letters, numbers, spaces, -, _, ,, ., (, ), :, ;, \', ", and % are allowed in the description.'
)

class Store(models.Model):
    store_code = models.CharField(max_length=10)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, related_name='stores')

    def __str__(self):
        if self.user:
            return f"{self.store_code} - {self.user.username}"
        else:
            return self.store_code

    def save(self, *args, **kwargs):
        # Check if the user is in the "CFAPerson" group
        store_person_group = Group.objects.get(name='CFAPerson')
        
        if self.user.groups.filter(pk=store_person_group.pk).exists():
            # CFAPerson can have only one store
            existing_store = Store.objects.filter(user=self.user).exclude(pk=self.pk).first()
            if existing_store:
                raise ValidationError("CFAPersons can have only one store.")
        
        super().save(*args, **kwargs)


class TicketFileTotalSize(models.Model):
    ticket = models.ForeignKey('Item', on_delete=models.CASCADE)
    total_file_size_kb = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    def calculate_total_file_size(self):
        # Calculate the total file size for this ticket by summing the file sizes of associated FileUpload instances
        total_size_bytes = self.ticket.uploads.aggregate(total_size_bytes=models.Sum('file_size'))['total_size_bytes']
        total_size_kb = total_size_bytes / 1024 if total_size_bytes else 0  # Convert to KB
        self.total_file_size_kb = total_size_kb  # Update the total_file_size_kb field
        self.save()  # Save the instance to store the calculated total size
        return total_size_kb

    def __str__(self):
        return f"Total File Size for Ticket ID: {self.ticket.id}"

    class Meta:
        verbose_name_plural = 'Ticket File Total Sizes'


class FileUpload(models.Model):
    item = models.ForeignKey('Item', related_name='uploads', on_delete=models.CASCADE)
    file = models.FileField(upload_to='media/uploads/')  # Remove 'uploads/' from here
    file_size = models.PositiveIntegerField()

    def __str__(self):
        return f"{self.item.id} - {self.item.category} "

class Category(models.Model):
    name = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.name

class Subcategory(models.Model):
    
    # Define choices for the category field
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)  # Increase the max_length to 50

    # Define choices for the functionality and technically fields
    APPROVAL_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('other', 'Other'),  # Add 'other' option

    ]

    functionality = models.CharField(max_length=7, choices=APPROVAL_CHOICES, default='')
    technically = models.CharField(max_length=7, choices=APPROVAL_CHOICES, default='')

    def __str__(self):
        return self.name
    

class ApprovalMatrix(models.Model):
    FUNCTIONALITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('other', 'Other'),
    ]

    TECHNICALITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('other', 'Other'),
    ]

    functionally = models.CharField(max_length=7, choices=FUNCTIONALITY_CHOICES, default='')
    technically = models.CharField(max_length=7, choices=TECHNICALITY_CHOICES, default='')
    is_active = models.BooleanField(default=True, help_text="Indicates if the approval matrix is active")

    APPROVAL_CHOICES = [
        ('auto', 'Auto'),
        ('manual', 'Manual'),
    ]
    
    approval = models.CharField(max_length=6, choices=APPROVAL_CHOICES)

    class Meta:
        unique_together = ('functionally', 'technically')

    def __str__(self):
        return self.approval


class Item(models.Model):
    STATUS_CHOICES = (
        ('open', 'Open'),
        ('assigned', 'Assigned'),
        ('inprogress', 'In Progress'),
        ('pending', 'Pending'),
        ('Resolved', 'Resolved'),
        ('closed', 'Closed'),
        ('reopen', 'Re-Open'),
        ('seek-clarification', 'seek-clarification'),  # Added new choice
    )

    id = models.AutoField(primary_key=True)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    subcategory = models.ForeignKey(Subcategory, on_delete=models.CASCADE)
    short_description = models.CharField(
        max_length=255,
        help_text="A brief description of the item."
    )
    detailed_description = models.TextField(
        help_text="A detailed description of the item."
    )

    created = models.DateTimeField(default=timezone.now)
    created_date = models.DateField(default=date.today, editable=False)  # Stores only the date
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='open')
    assignee = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_items')
    created_by = models.ForeignKey(User, related_name='created_items', on_delete=models.SET_NULL, null=True, blank=True)
    assigned_date = models.DateTimeField(null=True, blank=True)
    resolved_date = models.DateTimeField(null=True, blank=True)
    closed_date = models.DateTimeField(null=True, blank=True)
    store_code = models.CharField(max_length=10, null=True, blank=True)
    resolver_comments = models.TextField(blank=True, null=True)
    status_changed_by_manager = models.ForeignKey(User, related_name='status_changed_items', on_delete=models.SET_NULL, null=True, blank=True)
    functionality = models.CharField(max_length=7, choices=Subcategory.APPROVAL_CHOICES, null=True, blank=True)
    technically = models.CharField(max_length=7, choices=Subcategory.APPROVAL_CHOICES, null=True, blank=True)
    approval = models.ForeignKey(ApprovalMatrix, on_delete=models.SET_NULL, null=True, blank=True)
    status_changed_date = models.DateTimeField(null=True, blank=True)  # New field to track status changes
    reopen_date = models.DateTimeField(null=True, blank=True)  # Field to track reopen date
    reopen_comments = models.TextField(blank=True, null=True)
    closure_comments = models.TextField(blank=True, null=True)
    ticket_no = models.CharField(max_length=50, unique=True, blank=True, null=True)

    ageing_days = models.IntegerField(default=0)  # New field to store ageing days

    @staticmethod
    def assign_ticket_to_engineer():
        # Find engineers and their assigned ticket counts
        engineers = User.objects.filter(groups__name='Engineer')
        engineer_counts = engineers.annotate(ticket_count=Count('assigned_items'))

        # Find the engineer with the fewest assigned tickets
        min_count = engineer_counts.aggregate(min_count=Min('ticket_count'))['min_count']
        available_engineers = engineer_counts.filter(ticket_count=min_count)

        if available_engineers.exists():
            # Assign the ticket to the engineer with the fewest assigned tickets
            engineer_to_assign = available_engineers.first()
            return engineer_to_assign
        else:
            return None

    def calculate_ageing_days(self):  # New field to store ageing days
        """Calculate the number of days between creation and closure."""
        if self.closed_date:
            return (self.closed_date - self.created).days
        return (now() - self.created).days

    def save(self, *args, user=None, **kwargs):
        
        self.ageing_days = self.calculate_ageing_days()

        if not self.pk:
            self.created = timezone.now()
            self.created_date = self.created.date()  # Store only the date part of created

            # Check if there is a matching subcategory for the selected category
            try:
                subcategory = Subcategory.objects.get(category=self.category, name=self.subcategory.name)
                self.functionality = subcategory.functionality
                self.technically = subcategory.technically
            except Subcategory.DoesNotExist:
                self.functionality = 'other'  # Set to 'other' when there's no matching subcategory
                self.technically = 'other'  # Set to 'other' when there's no matching subcategory
                # When both category and subcategory don't match, set approval to 'manual'
                self.approval, _ = ApprovalMatrix.objects.get_or_create(
                    functionally='other',
                    technically='other',
                    approval='manual'
                )

            if self.approval and self.approval.approval == 'auto':
                # Automatically assign the ticket to an engineer
                engineer = self.assign_ticket_to_engineer()
                if engineer:
                    self.assignee = engineer
                    self.assigned_date = timezone.now()  # Set the assigned date
                    self.status = 'assigned'  # Set the status to 'assigned'
                else:
                    self.status = 'pending'  # No engineers available, set to pending
        else:
            # This block is executed when updating an existing item
            previous_item = Item.objects.get(pk=self.pk)  # Fetch the previous instance
            
            # Check if the status has changed
            if self.status != previous_item.status:
                
                self.status_changed_date = timezone.now()

                # Create a new status history entry
                StatusHistory.objects.create(
                    item=self,
                    status=self.status,
                    changed_by=user,  # Set the user who changed the status
                    changed_at=timezone.now()
                )


        if self.created_by and self.store_code is None:
            self.store_code = self.created_by.stores.first().store_code
            
        # Generate and save the ticket number
        if not self.ticket_no:
            if not self.id:
                super().save(*args, **kwargs)  # Save to generate the `id` first.

            ticket_id_str = str(self.id)
            zeros_count = max(6 - len(ticket_id_str), 0)

            today = datetime.now()
            if today.month >= 4:  # April or later
                current_year = today.year % 100
                next_year = (today.year + 1) % 100
            else:  # January to March
                current_year = (today.year - 1) % 100
                next_year = today.year % 100

            self.ticket_no = f'{self.store_code}{current_year:02}{next_year:02}{ticket_id_str.zfill(zeros_count + len(ticket_id_str))}'

        super().save(*args, **kwargs)

    def is_touched(self):
        return self.status in ['Assigned', 'Seek-clarification', 'Inprogress', 'Pending', 'Resolved', 'Closed']
class StatusHistory(models.Model):
    item = models.ForeignKey(Item, on_delete=models.CASCADE, related_name='status_history')
    status = models.CharField(max_length=20, choices=Item.STATUS_CHOICES)
    changed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    changed_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.item} - {self.status} by {self.changed_by} on {self.changed_at}"

class SeekClarificationHistory(models.Model):
    STATUS_CHOICES = [
        ('clarified', 'clarified'),
        ('unclarified', 'unclarified'),
    ]

    item = models.ForeignKey('Item', related_name='clarification_history', on_delete=models.CASCADE)
    seek_comment = models.TextField(help_text="Seek clarification comment.", blank=False, null=False)
    clarified_comment = models.TextField(help_text="Clarified comment.", blank=True, null=True)
    created_at = models.DateTimeField(default=timezone.now)
    created_by = models.ForeignKey('auth.User', on_delete=models.SET_NULL, null=True, blank=True)
    status_check = models.CharField(max_length=20, choices=STATUS_CHOICES, default='unclarified')

    def __str__(self):
        return f"Clarification Comment for {self.item} on {self.created_at}"

class SeekAttachment(models.Model):
    item = models.ForeignKey(Item, related_name='attachments', on_delete=models.CASCADE)
    clarification_image = models.FileField(upload_to='media/clarification_uploads/', blank=True, null=True)  # Image for clarification
    clarified_image = models.FileField(upload_to='media/clarified_uploads/', blank=True, null=True)  # Image for clarified response
    created_at = models.DateTimeField(default=timezone.now)
    created_by = models.ForeignKey('auth.User', on_delete=models.SET_NULL, null=True, blank=True)
    clarification_history = models.ForeignKey(SeekClarificationHistory, related_name='attachments', on_delete=models.CASCADE)

    def __str__(self):
        return f"Attachment for {self.clarification_history} by {self.created_by}"



# Email configuration
from_email = "wwdsupport_noreply@titan.co.in"  # Use Titan server address
smtp_server = 'titan-co-in.mail.protection.outlook.com'
smtp_port = 25 

@receiver(post_save, sender=Item)
def send_email_on_ticket_creation(sender, instance, created, **kwargs):
    if created and instance.created_by:
        subject = 'New Ticket Created'

        # Get the "Manager" group
        try:
            manager_group = Group.objects.get(name='Manager')
        except Group.DoesNotExist:
            manager_group = None

        # Create a recipient list with the created_by user's email
        recipient_list = [instance.created_by.email]

        # Create a CC list (e.g., add support team)
        cc_list = ["Nandhini.V@titan.co.in"] 

        if manager_group:
            # Get all users in the "Manager" group
            managers = manager_group.user_set.all()
            
            # Add the email addresses of all managers to the recipient list
            recipient_list.extend([manager.email for manager in managers])

        # Render the HTML template with ticket details
        html_message = render_to_string(
            'ticket_created_email.html',  # Replace with the correct path to your HTML template
            {
                'ticket_id': instance.id,
                'ticket_status': instance.status,
                'store_code': instance.store_code,
                'created_date': instance.created,
                'created_by': instance.created_by,
                'short_description': instance.short_description,
                'detailed_description': instance.detailed_description,
                'category': instance.category,
                'subcategory': instance.subcategory,
                'website_link': 'https://wwdsupport.titan.in/',  # Add website link as a dictionary item

            }
        )

        # Create a plain text version of the email
        plain_message = strip_tags(html_message).encode('utf-8') 

        # Create the email message object
        msg = MIMEMultipart()
        msg['From'] = from_email
        msg['To'] = ", ".join(recipient_list)  # Join recipients with commas
        msg['Subject'] = subject
        msg['Cc'] = ", ".join(cc_list)  # Join CC recipients with commas
        msg.attach(MIMEText(html_message, 'html'))

        # Send the email using Titan server
        try:
            with smtplib.SMTP(smtp_server, smtp_port) as server:
                server.starttls()  # Start TLS for encryption
                server.sendmail(from_email, recipient_list + cc_list, msg.as_string())  # Send to recipients and CCs
                print("Ticket Creation Email Sent Successfully")
        except Exception as e:
            print(f"Failed to send Ticket Creation Email: {e}")

from django.contrib.auth.models import User, Group
from django.template.loader import render_to_string
from django.core.mail import EmailMessage
from django.utils.html import strip_tags

@receiver(post_save, sender=Item)
def send_email_on_assignment(sender, instance, **kwargs):
    if instance.assignee and instance.status == 'assigned':
        subject = 'Ticket Assignment'
        created_by_user = instance.created_by if instance.created_by else None
        created_by_username = created_by_user.username if created_by_user else "Unknown User"        
        message = (
            f'Ticket ID: {instance.id}\n'
            f'Created By: {instance.created_by.username}\n'
            f'Assigned To: {instance.assignee.username}\n'
            f'CFA Code: {instance.store_code}\n'
            f'Changed To: {instance.status}\n'
            f'Category: {instance.category.name}\n'
            f'Subcategory: {instance.subcategory.name}\n'
            f'Comments: {instance.resolver_comments}\n'
            f'Assigned Date: {instance.assigned_date}\n'
            f'\n'  # Add an empty line for better formatting
            f'Visit Website: https://wwdsupport.titan.in/'
        )

        # Create a recipient list with the assigned engineer
        recipient_list = [instance.assignee.email] 

        # Create a CC list (e.g., add support team)
        cc_list = ["Nandhini.V@titan.co.in"] 

        # Get the "Manager" group
        try:
            manager_group = Group.objects.get(name='Manager')
        except Group.DoesNotExist:
            manager_group = None

        if manager_group:
            # Get all users in the "Manager" group
            managers = manager_group.user_set.all()
            
            # Add the email addresses of all managers to the recipient list
            recipient_list.extend([manager.email for manager in managers])

        # Add the email address of the created_by user to the recipient list
        if created_by_user:
            recipient_list.append(created_by_user.email)
        # Render the HTML content from the template
        html_message = render_to_string('ticket_assignment_email.html', {'instance': instance})

        # Create the email message object
        msg = MIMEMultipart()
        msg['From'] = from_email
        msg['To'] = ", ".join(recipient_list)  # Join recipients with commas
        msg['Subject'] = subject
        msg['Cc'] = ", ".join(cc_list)  # Join CC recipients with commas
        msg.attach(MIMEText(html_message, 'html'))

        # Send the email using Titan server
        try:
            with smtplib.SMTP(smtp_server, smtp_port) as server:
                server.starttls()  # Start TLS for encryption
                server.sendmail(from_email, recipient_list + cc_list, msg.as_string())
                print("Ticket Assignment Email Sent Successfully")
        except Exception as e:
            print(f"Failed to send Ticket Assignment Email: {e}")
            print(f"Error details: {e}") 
            
@receiver(post_save, sender=Item)
def send_email_on_status_change(sender, instance, **kwargs):
    if instance.status in ['inprogress', 'pending', 'closed','Resolved']:
        subject = 'Ticket Status Change'
        message = (
            f'Ticket ID: {instance.id}\n'
            f'Changed To: {instance.status}\n'
            f'CFA Code: {instance.store_code}\n'
            f'Category: {instance.category.name}\n'
            f'Subcategory: {instance.subcategory.name}\n'
            f'Comments: {instance.resolver_comments}\n'
            f'Created By: {instance.created_by.username}\n'
            f'Change Date: {instance.status_changed_date}\n'
            f'Visit Website: https://wwdsupport.titan.in/'

        )

        # Create a recipient list
        recipient_list = [instance.created_by.email] 

        # Add the email address of the assignee (engineer) to the recipient list
        recipient_list.append(instance.assignee.email)
        cc_list = ["Nandhini.V@titan.co.in"] 

        # If there is a status_changed_by_manager, add their email to the recipient list
        if instance.status_changed_by_manager:
            recipient_list.append(instance.status_changed_by_manager.email)

        # Render the HTML content from the template
        html_message = render_to_string('ticket_status_change_email.html', {'instance': instance})

        # Create the email message object
        msg = MIMEMultipart()
        msg['From'] = from_email
        msg['To'] = ", ".join(recipient_list)  # Join recipients with commas
        msg['Subject'] = subject
        msg['Cc'] = ", ".join(cc_list)  # Join CC recipients with commas
        msg.attach(MIMEText(html_message, 'html'))

        # Send the email using Titan server
        try:
            with smtplib.SMTP(smtp_server, smtp_port) as server:
                server.starttls()  # Start TLS for encryption
                server.sendmail(from_email, recipient_list, msg.as_string())
                print("Ticket Status Change Email Sent Successfully")
        except Exception as e:
            print(f"Failed to send Ticket Status Change Email: {e}")
            print(f"Error details: {e}") 


@receiver(post_save, sender=SeekClarificationHistory)
def send_email_on_clarification_change(sender, instance, created, **kwargs):
    subject = ''
    recipient_list = [instance.item.created_by.email]  # Send to the person who created the item
    cc_list = ["Nandhini.V@titan.co.in"] 

    # Debugging
    print(f'Created by: {instance.created_by.username}')
    print(f'Seek comment: {instance.seek_comment}')
    print(f'Clarified comment: {instance.clarified_comment}')
    print(f'Clarified by: {instance.item.created_by.username}')

    if created and instance.seek_comment:
        # Email for Seek Clarification Requested
        subject = 'New Clarification Requested'
        message = (
            f'A clarification has been requested on the item ID: {instance.item.id}\n'
            f'CFA Code: {instance.item.store_code}\n'
            f'Category: {instance.item.category.name}\n'
            f'Comment: {instance.seek_comment}\n'
            f'Created By: {instance.item.assignee}\n'
            f'Created At: {instance.created_at}\n'
            f'Visit Website: https://wwdsupport.titan.in/'

        )
    elif instance.status_check == 'clarified' and instance.clarified_comment:
        # Email for Clarification Provided
        subject = 'Clarification Provided'
        message = (
            f'A clarification has been provided for the item ID: {instance.item.id}\n'
            f'CFA Code: {instance.item.store_code}\n'
            f'Category: {instance.item.category.name}\n'
            f'Clarified Comment: {instance.clarified_comment}\n'
            f'Clarified By: {instance.item.created_by.username}\n'
            f'Created At: {instance.created_at}\n'
            f'Visit Website: https://wwdsupport.titan.in/'

        )

    if subject:
        # Render the HTML content from a template (optional)
        html_message = render_to_string('seek_clarification_email.html', {'instance': instance})

        # Create the email message object
        msg = MIMEMultipart()
        msg['From'] = from_email
        msg['To'] = ", ".join(recipient_list)  # Join recipients with commas
        msg['Subject'] = subject
        msg['Cc'] = ", ".join(cc_list)  # Join CC recipients with commas
        msg.attach(MIMEText(html_message, 'html'))

        # Send the email using Titan server
        try:
            with smtplib.SMTP(smtp_server, smtp_port) as server:
                server.starttls()  # Start TLS for encryption
                server.sendmail(from_email, recipient_list, msg.as_string())
                print("Clarification Email Sent Successfully")
        except Exception as e:
            print(f"Failed to send Clarification Email: {e}")
            print(f"Error details: {e}")