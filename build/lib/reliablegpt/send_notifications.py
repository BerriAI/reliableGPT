from klotty import Klotty
import time

client = Klotty(api_key="re_X1PBTBvD_5mJfFM98AuF2278fNAGfXVNV")

def send_emails_task(user_email, notification_data, should_send=False):
    body = f"""
    Unhandled Error Data
    {notification_data}
    """
    client.send_email(to=user_email,
                      sender="krrish@berri.ai",
                      subject="reliableGPT: Unhandled Error",
                      html=body)
