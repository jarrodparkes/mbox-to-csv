import mailbox
import csv

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
    mbox_file = raw_input("mbox file (ex. my_file.mbox): ")
    name_of_sender = raw_input("name of sender to filter (ex. Jarrod Parkes): ")
    email_of_sender = raw_input("email of sender to filter (ex. jarrod@udacity.com): ")

    # create FROM filter
    from_filter = name_of_sender + " <" + email_of_sender + ">"

    # create CSV file
    writer = csv.writer(open(export_file_name, "wb"))

    # create header row
    writer.writerow(["subject", "from", "date", "body"])

    # add rows based on mbox file
    for message in mailbox.mbox(mbox_file):
        contents = get_message(message)
        clip_idx = contents.find('<jarrod@udacity.com>')
        if clip_idx != -1:
            contents = contents[:clip_idx]
        if message["subject"].find('A Personal Request') != -1 and message["from"] != from_filter:
        	writer.writerow([message["subject"], message["from"], message["date"], contents])

    # print finish message
    print "generated csv file called " + export_file_name