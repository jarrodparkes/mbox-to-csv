#!/usr/bin/env python3
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from email_reply_parser import EmailReplyParser
from email.utils import parsedate_tz, mktime_tz

import ast
import datetime
import mailbox
import ntpath
import os
import quopri
import re
import rules
import sys
import time
import unicodecsv as csv

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

# entry point
if __name__ == '__main__':
    argv = sys.argv

    if len(argv) != 2:
        print('usage: mbox_parser.py [path_to_mbox]')
    else:
        # load environment settings
        load_dotenv(verbose=True)

        mbox_file = argv[1]
        file_name = ntpath.basename(mbox_file).lower()
        export_file_name = mbox_file + ".csv"
        export_file = open(export_file_name, "wb")

        # get owner(s) of the mbox
        owners = []
        if os.path.exists(".owners"):
            with open('.owners', 'r') as ownerlist:
                contents = ownerlist.read()
                owner_dict = ast.literal_eval(contents)
            # find owners
            for owners_array_key in owner_dict:
                if owners_array_key in file_name:
                    for owner_key in owner_dict[owners_array_key]:
                        owners.append(owner_key)

        # get domain blacklist
        blacklist_domains = []
        if os.path.exists(".blacklist"):
            with open('.blacklist', 'r') as blacklist:
                blacklist_domains = [domain.rstrip() for domain in blacklist.readlines()]

        # create CSV with header row
        writer = csv.writer(export_file, encoding='utf-8')
        writer.writerow(["flagged", "date", "description", "from", "to", "cc", "subject", "content", "time (minutes)"])

        # create row count
        row_written = 0

        for email in mailbox.mbox(mbox_file):
            # capture default content
            try:
                date = get_date(email["date"] or " ".join(email._from.rstrip().split(" ")[-6:]), os.getenv("DATE_FORMAT"))
            except:
                date = None
            sent_from = get_emails_clean(email["from"])
            sent_to = get_emails_clean(email["to"]) or [ email.get("X-GM-THRID"), ]
            cc = get_emails_clean(email["cc"])
            subject = re.sub('[\n\t\r]', ' -- ', str(email["subject"]))
            contents = get_content(email)

            # apply rules to default content
            row = rules.apply_rules(date, sent_from, sent_to, cc, subject, contents, owners, blacklist_domains)

            # write the row
            writer.writerow(row)
            row_written += 1

        # report
        report = "generated " + export_file_name + " for " + str(row_written) + " messages"
        report += " (" + str(rules.cant_convert_count) + " could not convert; "
        report += str(rules.blacklist_count) + " blacklisted)"
        print(report)

        export_file.close()
