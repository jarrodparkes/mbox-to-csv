import sys
import mailbox
import email
import quopri
import json
import time
from bs4 import BeautifulSoup
from email_reply_parser import EmailReplyParser
# from dateutil.parser import parse

MBOX = '/Users/jarrodparkes/Downloads/little.mbox'
OUT_FILE = '/Users/jarrodparkes/Downloads/little.mbox.json'

def cleanContent(msg):

    # Decode message from "quoted printable" format
    msg = quopri.decodestring(msg)

    # Strip out HTML tags, if any are present.
    # Bail on unknown encodings if errors happen in BeautifulSoup.
    try:
        soup = BeautifulSoup(msg, features="html.parser")
    except:
        return ''
    return ''.join(soup.findAll(text=True))

# There's a lot of data to process, and the Pythonic way to do it is with a
# generator. See http://wiki.python.org/moin/Generators.
# Using a generator requires a trivial encoder to be passed to json for object
# serialization.

class Encoder(json.JSONEncoder):
    def default(self, o): return  list(o)

# The generator itself...
def gen_json_msgs(mb):
    while 1:
        msg = mb.next()
        if msg is None:
            break
        yield jsonifyMessage(msg)

def jsonifyMessage(msg):
    json_msg = {'parts': []}
    for (k, v) in msg.items():
        json_msg[k] = v

    # The To, Cc, and Bcc fields, if present, could have multiple items.
    # Note that not all of these fields are necessarily defined.

    for k in ['To', 'Cc', 'Bcc']:
        if not json_msg.get(k):
            continue
        json_msg[k] = json_msg[k].replace('\n', '').replace('\t', '').replace('\r', '')\
                                 .replace(' ', '').split(',')

    for part in msg.walk():
        json_part = {}
        if part.get_content_maintype() == 'multipart':
            continue

        json_part['contentType'] = part.get_content_type()
        content = part.get_payload(decode=True)

        if content is None:
            json_part['content'] = 'n/a'
        else:
            json_part['content'] = cleanContent(content)
            json_part['content'] = EmailReplyParser.parse_reply(json_part['content'])

        json_msg['parts'].append(json_part)

    # Finally, convert date from asctime to milliseconds since epoch using the
    # $date descriptor so it imports "natively" as an ISODate object in MongoDB
    #then = parse(json_msg['Date'])
    #millis = int(time.mktime(then.timetuple())*1000 + then.microsecond/1000)
    json_msg['Date'] = {'$date' : json_msg['Date']}

    return json_msg

mbox = mailbox.mbox(MBOX)

# Write each message out as a JSON object on a separate line
# for easy import into MongoDB via mongoimport

f = open(OUT_FILE, 'w')
messages_json = []

for email in mbox:
    if email is None:
        continue
    else:
        msg = jsonifyMessage(email)
        if msg != None:
            messages_json.append(msg)

f.write(json.dumps(messages_json, cls=Encoder))

f.close()
