from celery import shared_task
from django.conf import settings
from django.core.mail import send_mail


@shared_task
def send_otp_email_task(email, otp,forgot=False):
    """
    Task to send OTP to the tenant owner's email with HTML content.
    """
    if forgot:
        subject = "Forgot Password - OTP"
    subject = "Your Platform Registration OTP"
    from_email = 'stream8196@gmail.com'  # Use the email configured in settings
    plain_message = f'''Your OTP is {otp}. Please verify it within 2 minutes'''
                        
    html_message = f"""
        <html>
        <body>
            <h1>Your Platform Registration OTP</h1>
            <p>Your OTP is <strong>{otp}</strong>.</p>
            <p>Please verify it within Please verify it within 2 minutes.</p>
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
        <p>If you didn't request this, please contact our support team immediately.</p>
        <br>
        <p>Best regards,</p>
        <p><strong>Stream Way Team</strong></p>
    </body>
    </html>
    """
    send_mail(subject, plain_message, from_email, [email], html_message=html_message)
