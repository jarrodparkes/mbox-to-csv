#!/usr/bin/env python3

from dotenv import load_dotenv

import ast
import capture
import mailbox
import ntpath
import os
import rules
import sys
import unicodecsv as csv

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
            # capture email content
            email_contents = capture.capture_contents(email, os.getenv("DATE_FORMAT"))

            # apply rules to the email content
            row = rules.apply_rules(email_contents["date"],
                                    email_contents["sent_from"],
                                    email_contents["sent_to"],
                                    email_contents["cc"],
                                    email_contents["subject"],
                                    email_contents["contents"],
                                    owners,
                                    blacklist_domains)

            # write the row
            writer.writerow(row)
            row_written += 1

        # report
        report = "generated " + export_file_name + " for " + str(row_written) + " messages"
        report += " (" + str(rules.cant_convert_count) + " could not convert; "
        report += str(rules.blacklist_count) + " blacklisted)"
        print(report)

        export_file.close()
