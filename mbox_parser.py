import mailbox
import csv
import html2text

# constants
export_file_name = "clean_mail.csv"

# get body of email
def get_message(message):
    if message.is_multipart():
        body = ""
        for part in message.get_payload():
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
        return message.get_payload()

if __name__ == "__main__":

    # get mbox file
    mbox_file = raw_input("name of mbox file in current directory (ex. my_file.mbox): ")

    # get name to filter
    name_filter = raw_input("name of sender that you want to filter (ex. Jarrod Parkes, * for any): ")

    # get email to filter
    email_filter = raw_input("email of sender that you want to filter (ex. parkesfjarrod@gmail.com, * for any): ")

    # create CSV file
    writer = csv.writer(open(export_file_name, "wb"))

    # create header row
    writer.writerow(["subject", "from", "date", "body"])

    # add rows based on mbox file
    for message in mailbox.mbox(mbox_file):
        contents = get_message(message)
        contents = html2text.html2text(contents)
        # does message contain name or email filter?
        if name_filter != "" and name_filter in message["from"]:
            writer.writerow([message["subject"], message["from"], message["date"], contents])
        elif email_filter != "" and email_filter in message["from"]:
            writer.writerow([message["subject"], message["from"], message["date"], contents])
        elif email_filter != "" and name_filter != "":
            writer.writerow([message["subject"], message["from"], message["date"], contents])
        else:
            continue

    # print finish message
    print "generated csv file called " + export_file_name
