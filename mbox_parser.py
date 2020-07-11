from bs4 import BeautifulSoup
from email_reply_parser import EmailReplyParser
import mailbox
import re
import unicodecsv as csv
import quopri

# constants
export_file_name = "clean_mail.csv"

# get body of email
# def get_contents(email):
#     if email.is_multipart():
#         body = ""
#         parts = email.get_payload(decode=True)
#         if parts is not None:
#             for part in parts:
#                 if part.is_multipart():
#                     for subpart in part.walk():
#                         if subpart.get_content_type() == "text/html":
#                             body += str(subpart)
#                         elif subpart.get_content_type() == "text/plain":
#                             body += str(subpart)
#                 else:
#                     body += str(part)
#         return body
#     else:
#         return email.get_payload()

def clean_content(content):

    # Decode message from "quoted printable" format
    content = quopri.decodestring(content)

    # Strip out HTML tags, if any are present.
    # Bail on unknown encodings if errors happen in BeautifulSoup.
    try:
        soup = BeautifulSoup(content, features="html.parser")
    except:
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
            part_contents = 'n/a'
        else:
            part_contents = EmailReplyParser.parse_reply(clean_content(content))

        parts.append(part_contents)

    return parts[0]

def get_emails_clean(field_contents):
    # regex finds all matches for <user@example.com> and user@example.com
    matches = re.findall(r'\<?([a-zA-Z0-9_\-\.]+@[a-zA-Z0-9_\-\.]+\.[a-zA-Z]{2,5})\>?', str(field_contents))
    if matches:
        emails_cleaned = []
        for match in matches:
            emails_cleaned.append(match)
        return ", ".join(sorted(emails_cleaned, key=str.lower))
    else:
        return "n/a"

if __name__ == "__main__":

    # get mbox file
    mbox_file = input("path to MBOX file: ")

    # create CSV file
    writer = csv.writer(open(export_file_name, "wb"), encoding='utf-8')

    # create header row
    writer.writerow(["date", "from", "to", "cc", "subject", "content"])

    # add rows based on mbox file
    row_written = 0

    for email in mailbox.mbox(mbox_file):
        writer.writerow([email["date"],
                        get_emails_clean(email["from"]),
                        get_emails_clean(email["to"]),
                        get_emails_clean(email["cc"]),
                        re.sub('[\n\t\r]', ' -- ', email["subject"]),
                        get_content(email)])

        row_written += 1

    # print finish message
    print("generated CSV file called " + export_file_name + " with " + str(row_written) + " rows")
