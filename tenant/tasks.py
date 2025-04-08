from celery import shared_task
from django.conf import settings
from django.core.mail import send_mail


@shared_task
def send_otp_email_task(email, otp):
    print(settings.EMAIL_HOST_USER)
    """
    Task to send OTP to the tenant owner's email with HTML content.
    """
    subject = "Your Platform Registration OTP"
    from_email = 'stream8196@gmail.com'  # Use the email configured in settings
    plain_message = f'''Your OTP is {otp}. Please verify it within 5 minutes to 
                        complete your registration.'''
    html_message = f"""
        <html>
        <body>
            <h1>Your Platform Registration OTP</h1>
            <p>Your OTP is <strong>{otp}</strong>.</p>
            <p>Please verify it within 5 minutes to complete your registration.</p>
        </body>
        </html>
    """

    # Using the send_mail method from Django for sending the email
    send_mail(
        subject,
        plain_message,
        from_email,
        [email],
        html_message=html_message,
        fail_silently=False,
    )

    print("OTP sent successfully!")

# import logging
# from django.conf import settings
# from django.core.mail import send_mail
# from django.template.loader import render_to_string
# from django.utils.html import strip_tags
# from celery import shared_task

# logger = logging.getLogger(__name__)

# @shared_task(bind=True, max_retries=3)
# def send_otp_email_task(self, email, otp):
#     """
#     Task to send OTP to the tenant owner's email with a professionally designed HTML template.
    
#     Args:
#         email (str): Recipient email address
#         otp (str): One-Time Password to be sent
    
#     Returns:
#         bool: True if email sent successfully, False otherwise
#     """
#     try:
#         # Prepare email context
#         email_context = {
#             'otp': otp,
#             'platform_name': 'StreamWay',
#             'support_email': 'support@streamway.com',
#             'expiry_minutes': 5
#         }
        
#         # Render HTML email template
#         html_message = render_to_string('templates/otp_verification.html', email_context)
#         plain_message = strip_tags(html_message)
        
#         # Email configuration
#         subject = f"Your {email_context['platform_name']} Verification Code"
#         from_email = settings.DEFAULT_FROM_EMAIL
        
#         # Send email
#         send_mail(
#             subject,
#             plain_message,
#             from_email,
#             [email],
#             html_message=html_message,
#             fail_silently=False,
#         )
        
#         logger.info(f"OTP email sent successfully to {email}")
#         return True
    
#     except Exception as exc:
#         # Log the error and retry the task
#         logger.error(f"Failed to send OTP email to {email}: {str(exc)}")
        
#         # Retry mechanism with exponential backoff
#         try:
#             self.retry(exc=exc, countdown=2 ** self.request.retries)
#         except Exception as retry_exc:
#             logger.critical(f"Permanent failure sending OTP email to {email}: {str(retry_exc)}")
#             return False


@shared_task
def send_login_credential(email, password):
    """
    Task to send login credentials (username and password) to the tenant owner's email.
    """
    subject = "Your Login Credentials for Stream Way"
    from_email = 'stream8196@gmail.com'  # Use the email configured in settings
    plain_message = f"""Hello, 

Your account has been successfully created. 

Your login credentials are:
Username: {email}
Password: {password}

Please use these credentials to log in and start managing your business.

If you didn't request this, please contact support immediately.

Best regards,  
Stream Way Team
"""
    html_message = f"""
    <html>
    <body>
        <h2>Welcome to Stream Way!</h2>
        <p>Your account has been successfully created. Below are your login credentials:</p>
        <p><strong>Username:</strong> {email}</p>
        <p><strong>Password:</strong> {password}</p>
        <p>Please use these credentials to <a href="http://yourplatform.com/login">log in</a> and start managing your business.</p>
        <p>If you didn't request this, please contact our support team immediately.</p>
        <br>
        <p>Best regards,</p>
        <p><strong>Stream Way Team</strong></p>
    </body>
    </html>
    """
    send_mail(subject, plain_message, from_email, [email], html_message=html_message)
