
from email.mime import message
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import os
import smtplib

# Pull values from environment variables


# Safety check



def send_confirmation_email(receiver_email, verification_link, token):
    # Get Gmail credentials from environment variables
    sender_email = "samlok412@gmail.com"
    app_password = "cjgagpjteitgibya"

    # Create the email
    message = MIMEMultipart("alternative")
    message["Subject"] = "Confirm your email address"
    message["From"] = f"O'FAME Support <{sender_email}>"
    message["To"] = receiver_email

    text_content = f"Hello,\n\nThanks for signing in to O'FAME Legacy. Your confirmation code is: {token}\n\nClick this link to verify your email: {verification_link}\n\n- O'FAME Legacy Support"
    html_content = f"""\
    <html>
      <body>
        <p>Hello,</p>
        <p>Thanks for signing in to O'FAME Legacy.</p>
        <p>Your confirmation code is: <strong>{token}</strong></p>
        <p>Click <a href="{verification_link}">here</a> to confirm your login.</p>
        <p>- O'FAME Legacy Support</p>
      </body>
    </html>
    """

   
    message.attach(MIMEText(text_content, "plain"))
    message.attach(MIMEText(html_content, "html"))
    
    try:
            with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
                print(sender_email)
                print(len(app_password))
                server.login(sender_email, app_password)
                print("sending to:", receiver_email)
                server.sendmail(sender_email, receiver_email, message.as_string())
                print("The confirmation email has been sent successfully!")
    except Exception as e:
            print("Failed to send email:", e)
        
        


