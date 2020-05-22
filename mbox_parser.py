import mailbox
import unicodecsv as csv
import html2text

# constants
export_file_name = "clean_mail.csv"

# get body of email
def get_contents(email):
    if email.is_multipart():
        body = ""
        for part in email.get_payload():
            if part.is_multipart():
                for subpart in part.walk():
                    if subpart.get_content_type() == "text/html":
                        body += str(subpart)
                    elif subpart.get_content_type() == "text/plain":
                        body += str(subpart)
            else:
                body += str(part)
        return body
    else:
        return email.get_payload()

if __name__ == "__main__":

    # get mbox file
    mbox_file = raw_input("path to MBOX file: ")

    # create CSV file    
    writer = csv.writer(open(export_file_name, "wb"), encoding='utf-8')

    # create header row
    writer.writerow(["subject", "from", "date", "body"])

    # add rows based on mbox file
    for email in mailbox.mbox(mbox_file):
        contents = get_contents(email)
        contents = html2text.html2text(contents)
        writer.writerow([email["subject"], email["from"], email["date"], contents])

    # print finish message
    print "generated CSV file called " + export_file_name
