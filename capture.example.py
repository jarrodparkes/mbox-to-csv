from bs4 import BeautifulSoup
from email_reply_parser import EmailReplyParser
from email.utils import parsedate_tz, mktime_tz

import datetime
import mailbox
import quopri
import re
import time

# capture default content
def capture_contents(email, date_format):
    """Returns a dictionary containing the captured contents of an email.

    The contents of the dictionary should be as follows:
    {
        "date": [(str) the date the email was written],
        "sent_from": [(list) a list of email addresses the email was sent from],
        "sent_to": [(list) a list of email addresses the email was sent to],
        "cc": [(list) a list of email addresses the email was cc'ed to],
        "subject": [(str) the subject of the email],
        "contents": [(str) the contents of the email],
    }

    Args:
        email (mailbox.Message): https://docs.python.org/3.8/library/email.compat32-message.html
        date_format (str): A date format strings such as "%m/%d/%Y"

    Returns:
        dict: a dictionary containing the captured contents of an email
    """
    date = get_date(email["date"], date_format)
    sent_from = get_emails_clean(email["from"])
    sent_to = get_emails_clean(email["to"])
    cc = get_emails_clean(email["cc"])
    subject = re.sub('[\n\t\r]', ' -- ', str(email["subject"]))
    contents = get_content(email)

    return {
        "date": date,
        "sent_from": sent_from,
        "sent_to": sent_to,
        "cc": cc,
        "subject": subject,
        "contents": contents
    }

# converts seconds since epoch to mm/dd/yyyy string
def get_date(rfc2822time, date_format):
    if rfc2822time is None:
        return None
    time_tuple = parsedate_tz(rfc2822time)
    utc_seconds_since_epoch = mktime_tz(time_tuple)
    datetime_obj = datetime.datetime.fromtimestamp(utc_seconds_since_epoch)
    return datetime_obj.strftime(date_format)

# clean content
def clean_content(content):
    # decode message from "quoted printable" format
    content = quopri.decodestring(content)

    # try to strip HTML tags
    # if errors happen in BeautifulSoup (for unknown encodings), then bail
    try:
        soup = BeautifulSoup(content, "html.parser", from_encoding="iso-8859-1")
    except Exception as e:
        return ''
    return ''.join(soup.findAll(text=True))

# get contents of email
def get_content(email):
    parts = []

    for part in email.walk():
        if part.get_content_maintype() == 'multipart':
            continue

        content = part.get_payload(decode=True)

        part_contents = ""
        if content is None:
            part_contents = ""
        else:
            part_contents = EmailReplyParser.parse_reply(clean_content(content))

        parts.append(part_contents)

    return parts[0]

# get all emails in field
def get_emails_clean(field):
    # find all matches with format <user@example.com> or user@example.com
    matches = re.findall(r'\<?([a-zA-Z0-9_\-\.]+@[a-zA-Z0-9_\-\.]+\.[a-zA-Z]{2,5})\>?', str(field))
    if matches:
        emails_cleaned = []
        for match in matches:
            emails_cleaned.append(match.lower())
        unique_emails = list(set(emails_cleaned))
        return sorted(unique_emails, key=str.lower)
    else:
        return []
