from bs4 import BeautifulSoup
from email_reply_parser import EmailReplyParser
from email.utils import parsedate_tz, mktime_tz

import ast
import datetime
import mailbox
import ntpath
import quopri
import re
import sys
import time
import unicodecsv as csv

import os.path
from os import path

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
        return sorted(emails_cleaned, key=str.lower)
    else:
        return []

# is there a blacklisted domain in this list of emails?
def blacklisted_email_domain(emails):
    for email in emails:
        domain = email.split('@')[1]
        if domain in blacklist_domains:
            return domain
    return None

def blacklist_row(date, subject, blacklist_domain):
    blacklist_content = "[" + blacklist_domain + " blacklisted]"
    return [
        "x",
        date,
        "",
        blacklist_content,
        blacklist_content,
        blacklist_content,
        subject,
        blacklist_content,
        "0"
    ]

# entry point
if __name__ == '__main__':
    argv = sys.argv

    if len(argv) != 2:
        print('usage: mbox_parser.py [path_to_mbox]')
    else:
        mbox_file = argv[1]
        file_name = ntpath.basename(mbox_file)
        export_file_name = mbox_file + ".csv"
        export_file = open(export_file_name, "wb")

        # get email of owner
        owner = ""
        owners = []
        if path.exists(".owners"):
            with open('.owners', 'r') as ownerlist:
                contents = ownerlist.read()
                owner_dict = ast.literal_eval(contents)

            for owner_key in owner_dict:
                if owner_key in file_name:
                    owner = owner_dict[owner_key]
                    break

        # get domain blacklist
        blacklist_domains = []
        if path.exists(".blacklist"):
            with open('.blacklist', 'r') as blacklist:
                blacklist_domains = [domain.rstrip() for domain in blacklist.readlines()]

        # create CSV with header row
        writer = csv.writer(export_file, encoding='utf-8')
        writer.writerow(["flagged", "date", "description", "from", "to", "cc", "subject", "content", "time (minutes)"])

        # create row counts
        row_written = 0
        cant_convert_count = 0
        blacklist_count = 0

        for email in mailbox.mbox(mbox_file):

            # capture default content
            date = get_date(email["date"], "%m/%d/%Y")
            sent_from = get_emails_clean(email["from"])
            sent_to = get_emails_clean(email["to"])
            cc = get_emails_clean(email["cc"])
            subject = re.sub('[\n\t\r]', ' -- ', email["subject"])
            contents = get_content(email)
            content_length = len(contents)

            # get description/code
            description = ""
            if owner in sent_from:
                description = "DR Correspondence"
            elif owner in sent_to:
                description = "RV Correspondence"

            # get time calculation

            if content_length < 40:
                time = "0"
            elif content_length >= 40 and content_length < 120:
                time = "1"
            elif content_length >= 120 and content_length < 400:
                time = "6"
            else:
                time = "12"

            # check blacklist
            sent_blacklisted = blacklisted_email_domain(sent_from)
            to_blacklisted = blacklisted_email_domain(sent_to)
            cc_blacklisted = blacklisted_email_domain(cc)

            row = []
            if sent_blacklisted is not None:
                blacklist_count += 1
                row = blacklist_row(date, subject, sent_blacklisted)
            elif to_blacklisted is not None:
                blacklist_count += 1
                row = blacklist_row(date, subject, to_blacklisted)
            elif cc_blacklisted is not None:
                blacklist_count += 1
                row = blacklist_row(date, subject, cc_blacklisted)
            elif not contents:
                cant_convert_count += 1
                row = [
                    "x",
                    date,
                    description,
                    ", ".join(sent_from),
                    ", ".join(sent_to),
                    ", ".join(cc),
                    subject,
                    "[could not convert]",
                    "0"
                ]
            else:
                flagged = "x" if time == "12" else ""
                row = [
                    flagged,
                    date,
                    description,
                    ", ".join(sent_from),
                    ", ".join(sent_to),
                    ", ".join(cc),
                    subject,
                    contents,
                    time
                ]

            writer.writerow(row)

            row_written += 1

        print("generated " + export_file_name + " for " + str(row_written) + " messages (" + str(cant_convert_count) + " could not convert; " + str(blacklist_count) + " blacklisted)")
        export_file.close()
