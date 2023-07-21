import datetime
import resend
import time

resend.api_key = "re_X1PBTBvD_5mJfFM98AuF2278fNAGfXVNV"
from termcolor import colored


class Alerting:

  def __init__(self,
               alert_threshold=5,
               send_notifications=True,
               user_emails=set()):
    self.unhandled_errors = {
    }  # dictionary of openai errors + frequency count for that hour
    now = datetime.datetime.now()
    self.current_time_block = now.hour
    self.set_cooldown = True
    self.cooldown_start_time = time.time()
    self.send_notifications = send_notifications
    self.user_emails = user_emails

  def start_cooldown(self):
    self.set_cooldown = True
    self.cooldown_start_time = time.time()

  def send_alert(self, error_type, most_recent_error):
    print(colored("Sending alert", "magenta"))
    params = {
      "from":
      "krrish@berri.ai",
      "subject":
      """reliableGPT 💪: Unhandled Error - {}""".format(error_type),
      "html":
      """
            <p><strong>ReliableGPT Error:</strong></p>
            <p>A critical error occurred that ReliableGPT was unable to handle.</p>
            <p>This error has happened 5 times in the last hour:</p>
            <p><strong>{}</strong></p>
            <p> This was your most recent error {} </p>
            <p>Suggest a way we could cover this error with reliableGPT 💪:
        <a href="https://github.com/BerriAI/reliableGPT/issues/new">Here</a></p>

        <p>Join our Discord for Support:
        <a href=" https://discord.com/invite/WXFfTeEXRh">Here</a></p>
            """.format(error_type, most_recent_error)
    }
    for email in self.user_emails:
      params["to"] = email
      email = resend.Emails.send(params)
    return

  def add_emails(self, user_email):
    if type(user_email) == list:
      for email in user_email:
        self.user_emails.add(email)
    else:
      self.user_emails.add(user_email)
    return

  def add_error(self, openai_error=None, error_description=None, error_type=None):
    if openai_error != None:
      openai_error = openai_error.error  # index into the error attribute of the class
      if "type" in openai_error:
        error_type = openai_error['type']
    elif error_description and error_type:
      error_type = error_type
      openai_error = error_description
    now = datetime.datetime.now()
    curr_time = now.hour

    if curr_time == self.current_time_block:
      if error_type in self.unhandled_errors:
        self.unhandled_errors[error_type] += 1
      else:
        self.unhandled_errors[error_type] = 1
      if self.unhandled_errors[error_type] >= 5:
        self.unhandled_errors[error_type] = 0  # reset this to 0
        # cooldown for 15 minutes -> do this to prevent email spam.
        if self.set_cooldown and time.time() - self.cooldown_start_time > 900:
          self.send_alert(error_type, openai_error)
          self.set_cooldown()
        elif self.set_cooldown == False:
          self.send_alert(error_type, openai_error)
          self.start_cooldown()
    else:  # reset
      self.unhandled_errors[error_type] = 1
      self.current_time_block = curr_time
    return
