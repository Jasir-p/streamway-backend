from celery import shared_task
from django.conf import settings
from django.core.mail import send_mail


@shared_task
def employee_login_credential(email, tenant_name, subdomain, password="12345678"):
    # Send an email to the employee with their login credentials
    """
    Task to send employee login credentials (username, password, tenant name, and login URL).
    """
    subject = "Your Employee Login Credentials for Stream Way"
    from_email = 'stream8196@gmail.com' 
    access_url = f"https://streamway.solutions/{subdomain}/signin"

    plain_message = f"""Hello,

    Your employee account has been successfully created under {tenant_name}.

    Your login credentials are:
    Username: {email}
    Password: {password}

    You can log in using the following link:
    {access_url}

    Please use these credentials to access your account and start managing your business.

    If you didn't request this, please contact support immediately.

    Best regards,  
    Stream Way Team
    """

    html_message = f"""
    <html>
    <body>
        <h2>Welcome to Stream Way!</h2>
        <p>Your employee account has been successfully created under <strong>{tenant_name}</strong>.</p>
        <p><strong>Username:</strong> {email}</p>
        <p><strong>Password:</strong> {password}</p>
        <p>You can log in using the following link: <a href="{access_url}">{access_url}</a></p>
        <p>Please use these credentials to log in and start managing your business.</p>
        <p>If you didn't request this, please contact our support team immediately.</p>
        <br>
        <p>Best regards,</p>
        <p><strong>Stream Way Team</strong></p>
    </body>
    </html>
    """
    send_mail(subject, plain_message, from_email, [email], html_message=html_message)




@shared_task
def employee_password_change(email, otp, tenant_name):
    # Send an email to the employee with the OTP for password change
    subject = f"Your OTP for Password Change - {tenant_name}"
    from_email = 'stream8196@gmail.com'
    

    plain_message = f"""Hello,

    You have requested a password change for your account at {tenant_name}.

    Your One-Time Password (OTP) for verification is: {otp}

    Please use this OTP to proceed with your password change.


    If you didn't request this, please contact support immediately.

    Best regards,  
    {tenant_name} Team
    """

    html_message = f"""
    <html>
    <body>
        <h2>Password Change Request</h2>
        <p>You have requested a password change for your account at <strong>{tenant_name}</strong>.</p>
        <p>Your One-Time Password (OTP) for verification is: <strong>{otp}</strong></p>
        <p>If you didn't request this, please contact our support team immediately.</p>
        <br>
        <p>Best regards,</p>
        <p><strong>{tenant_name} Team</strong></p>
    </body>
    </html>
    """

    send_mail(subject, plain_message, from_email, [email], html_message=html_message)
