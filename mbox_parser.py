from bs4 import BeautifulSoup
from email_reply_parser import EmailReplyParser
from email.utils import parsedate_tz, mktime_tz

import datetime
import mailbox
import quopri
import re
import sys
import time
import unicodecsv as csv

# converts seconds since epoch to mm/dd/yyyy string
def get_date(second_since_epoch, date_format):
    time_tuple = parsedate_tz(email["date"])
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
            emails_cleaned.append(match)
        return ", ".join(sorted(emails_cleaned, key=str.lower))
    else:
        return ""

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
        cant_convert_count = 0
        for email in mailbox.mbox(mbox_file):

            contents = get_content(email)

            if not contents:
                cant_convert_count += 1
                contents = "[could not convert]"

            writer.writerow([get_date(email["date"], "%m/%d/%Y"),
                            get_emails_clean(email["from"]),
                            get_emails_clean(email["to"]),
                            get_emails_clean(email["cc"]),
                            re.sub('[\n\t\r]', ' -- ', email["subject"]),
                            contents])
            row_written += 1

        print("generated " + export_file_name + " for " + str(row_written) + " messages, " + str(cant_convert_count) + " messages had issues converting their content")
        export_file.close()
