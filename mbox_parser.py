from bs4 import BeautifulSoup
from email_reply_parser import EmailReplyParser
import mailbox
import quopri
import re
import sys
import unicodecsv as csv

# clean content
def clean_content(content):
    # decode message from "quoted printable" format
    content = quopri.decodestring(content)

    # try to strip HTML tags
    # if errors happen in BeautifulSoup (for unknown encodings), then bail
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

# get all emails in field
def get_emails_clean(field):
    # find all matches with format <user@example.com> or user@example.com
    matches = re.findall(r'\<?([a-zA-Z0-9_\-\.]+@[a-zA-Z0-9_\-\.]+\.[a-zA-Z]{2,5})\>?', str(field))
    if matches:
        emails_cleaned = []
        for match in matches:
            emails_cleaned.append(match)
        return ", ".join(sorted(emails_cleaned, key=str.lower))
    else:
        return "n/a"

# entry point
if __name__ == '__main__':
    argv = sys.argv

    if len(argv) != 2:
        print('usage: mbox_parser.py [path_to_mbox]')
    else:
        mbox_file = argv[1]
        export_file_name = mbox_file + ".csv"
        export_file = open(export_file_name, "wb")

        writer = csv.writer(export_file, encoding='utf-8')
        writer.writerow(["date", "from", "to", "cc", "subject", "content"])

        row_written = 0
        for email in mailbox.mbox(mbox_file):
            writer.writerow([email["date"],
                            get_emails_clean(email["from"]),
                            get_emails_clean(email["to"]),
                            get_emails_clean(email["cc"]),
                            re.sub('[\n\t\r]', ' -- ', email["subject"]),
                            get_content(email)])

            row_written += 1

        print("generated CSV file called " + export_file_name + " with " + str(row_written) + " rows")
        export_file.close()
