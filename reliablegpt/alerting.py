import datetime
import resend
resend.api_key = "re_X1PBTBvD_5mJfFM98AuF2278fNAGfXVNV"

class Alerting:

  def __init__(self,
               alert_threshold=5,
               send_notifications=True,
               user_emails=set()):
    self.unhandled_errors = {
    }  # dictionary of openai errors + frequency count for that hour
    now = datetime.datetime.now()
    self.current_time_block = now.hour
    self.send_notifications = send_notifications
    self.user_emails = user_emails

  def send_alert(self, error_type):
    if self.send_notifications:
      params = {
      "from": "krrish@berri.ai",
      "subject": """reliableGPT 💪: Unhandled Error - {}""".format(error_type),
      "html": """
              <p><strong>ReliableGPT Error:</strong></p>
              <p>A critical error occurred that ReliableGPT was unable to handle.</p>
              <p>This error has happened 5 times in the last hour:</p>
              <p><strong>{}</strong></p>
              <p>Suggest a way we could cover this error with reliableGPT 💪: 
            <a href="https://github.com/BerriAI/reliableGPT/issues/new">Here</a></p>
              """.format(error_type)
      }
      for email in self.user_emails:
        params["to"] = email
        email = resend.Emails.send(params)
    return 
  
  def add_emails(self, user_email):
    self.user_emails.add(user_email)
    return 

  def add_error(self, openai_error):
    if openai_error != None:
      openai_error = openai_error.error  # index into the error attribute of the class
    error_type = None  # defalt to being None
    if openai_error != None and 'type' in openai_error:
      error_type = openai_error['type']

    now = datetime.datetime.now()
    curr_time = now.hour()
    if curr_time == self.current_time_block:
      if error_type in self.unhandled_errors:
        self.unhandled_errors[error_type] += 1
      else:
        self.unhandled_errors[error_type] = 1
      if self.unhandled_errors[error_type] >= 5:
        self.send_alerts(error_type)
    else:  # reset
      self.unhandled_errors[error_type] = 1
      self.current_time_block = curr_time

    return