import mailbox
import csv
import html2text

# constants
export_file_name = "clean_mail.csv"

# get body of email
def get_message(message):
    if not message.is_multipart():
        return message.get_payload()
    contents = ""
    for msg in message.get_payload():
        contents = contents + str(msg.get_payload()) + '\n'
    return contents

if __name__ == "__main__":

    # get command line arguments
    mbox_file = raw_input("mbox file (ex. my_file.mbox, in same directory): ")

    # create CSV file
    writer = csv.writer(open(export_file_name, "wb"))

    # create header row
    writer.writerow(["subject", "from", "date", "body"])

    # add rows based on mbox file
    for message in mailbox.mbox(mbox_file):
        contents = get_message(message)
        contents = html2text.html2text(contents)
        writer.writerow([message["subject"], message["from"], message["date"], contents])

    # print finish message
    print "generated csv file called " + export_file_name
