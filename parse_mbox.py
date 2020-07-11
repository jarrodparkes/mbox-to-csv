from html.parser import HTMLParser
from email.header import Header, decode_header
from bs4 import BeautifulSoup
import mailbox
import base64
import quopri
import re
import sys
import html2text

""" ____Format utils____ """

class MLStripper(HTMLParser):
    """
    Strip HTML from strings in Python
    https://stackoverflow.com/questions/753052/strip-html-from-strings-in-python
    """
    def __init__(self):
        super().__init__()
        self.reset()
        self.fed = []
    def handle_data(self, d):
        self.fed.append(d)
    def get_data(self):
        return ''.join(self.fed)



def strip_tags(html):
    """
    Use MLStripper class to strip HMTL from string
    """
    s = MLStripper()
    s.feed(html)
    return s.get_data()


def strip_payload(payload):
    """
    Remove carriage returns and new lines
    """
    return payload.replace('\r', ' ').replace('\n', ' ')


def encoded_words_to_text(encoded_words):
    """
    Not used, left for reference only
    https://dmorgan.info/posts/encoded-word-syntax/
    """
    encoded_word_regex = r'=\?{1}(.+)\?{1}([B|Q])\?{1}(.+)\?{1}='
    # encoded_word_regex = r'=\?{1}.+\?{1}[B|Q|b|q]\?{1}.+\?{1}='
    charset, encoding, encoded_text = re.match(encoded_word_regex, encoded_words, re.IGNORECASE).groups()
    if encoding.upper() == 'B':
        byte_string = base64.b64decode(encoded_text)
    elif encoding.upper() == 'Q':
        byte_string = quopri.decodestring(encoded_text)
    return byte_string.decode(charset)



""" ____Custom Message class____ """

class CustomMessage():
    """
    The CusomMessage class represents an email message with three fields:
    - :body:
    - :subject:
    - :content_type: (document, plain text, HTML, image...)
    """
    def __init__(self, body, subject, content_type):
        """
        Constructor
        It tries to find the subject's encoding and decode it accordingly
        It decodes the body based on the content type
        """
        self.content_type = content_type

        # Decode subject if encoded in utf-8
        if isinstance(subject, Header):
            subject = decode_header(subject)[0][0].decode('utf-8')

        # The subject can have several parts encoded in different formats
        # These parts are flagged with strings like '=?UTF-8?'
        if subject is not None and ('=?ISO-' in subject.upper() or '=?UTF-8?' in subject.upper()):
            self.subject = ''
            for subject_part in decode_header(subject):
                # Decode each part based on its encoding
                # The encoding could be returnd by the "decode_header" function
                if subject_part[1] is None:
                    self.subject += strip_payload(subject_part[0].decode())
                else:
                    self.subject += strip_payload(subject_part[0].decode(subject_part[1]))
        elif subject is None:
            # Empty subject
            self.subject = ''
        else:
            # Subject is not encoded or other corner cases that are not considered
            self.subject = strip_payload(subject)

        # Body decoding
        if 'text' in self.content_type:
            # Decode text messages
            try:
                decoded_body = body.decode('utf-8')
            except UnicodeDecodeError:
                decoded_body = body.decode('latin-1')

            if 'html' in self.content_type:

                soup = BeautifulSoup(decoded_body, features="html.parser")

                # kill all script and style elements
                for script in soup(["script", "style"]):
                    script.extract()    # rip it out

                # get text
                text = soup.get_text()

                # break into lines and remove leading and trailing space on each
                lines = (line.strip() for line in text.splitlines())
                # break multi-headlines into a line each
                chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
                # drop blank lines
                text = '\n'.join(chunk for chunk in chunks if chunk)

                self.body = text
                # # If it is an HTML message, remove HTML tags
                # h = html2text.HTML2Text()
                #
                # h.ignore_links = True
                # h.ignore_tables = True
                # h.ignore_images = True
                # h.ignore_anchors = True
                # h.ignore_emphasis = True
                #
                # self.body = strip_payload(h.handle(decoded_body))
            else:
                self.body = strip_payload(decoded_body)
        else:
            # If not text, return the body as it is
            self.body = body

    def __str__(self):
        body_length = 2000
        printed_body = self.body[:body_length]
        if 'text' in self.content_type:
            # Shorten long message bodies
            if len(self.body) > body_length:
                printed_body += "..."
        return " ---- Custom Message ---- \n  -- Content Type: {}\n  -- Subject: {}\n  -- Body --\n{}\n\n".format(self.content_type, self.subject, printed_body)

    def get_body(self):
        return self.body

    def get_subject(self):
        return self.subject

    def get_content_type(self):
        return self.content_type

    def create_vector_line(self, label):
        """
        Creates a CSV line with the message's body and given :label:
        Removes any commas from body and label
        """
        return '{body},{label}'.format(body=self.body.replace(',', ''), label=label)

    @staticmethod
    def extract_types_from_messages(messages):
        """
        Takes a list of CustomMessage and extracts all the existing values for content_type
        ['application/ics', 'application/octet-stream', 'application/pdf', 'image/gif', 'image/jpeg',
        'image/png', 'text/calendar', 'text/html', 'text/plain', 'text/x-amp-html']
        """
        types = set()
        for m in messages:
            types.add(m.get_content_type())
        return sorted(types)



""" ____Extraction utils____ """

def extract_message_payload(mes, parent_subject=None):
    """
    Extracts recursively the payload of the messages contained in :mes:
    When a message is embedded in another, it uses the parameter :parent_subject:
    to set the subject properly (it uses the parent's subject)
    """
    extracted_messages = []
    if mes.is_multipart():
        if parent_subject is None:
            subject_for_child = mes.get('Subject')
        else:
            subject_for_child = parent_subject
        for part in mes.get_payload():
            extracted_messages.extend(extract_message_payload(part, subject_for_child))
    else:
        extracted_messages.append(CustomMessage(mes.get_payload(decode=True), parent_subject,  mes.get_content_type()))
    return extracted_messages


def text_messages_to_string(mes):
    """
    Returns the email's body extracted from :mes: as a string.
    Ignores images and documents.
    :mes: should be a list of CustomMessage objects.
    """
    output = ''
    for m in mes:
        if m.get_content_type().startswith('text'):
            output += str(m.body) + "\n\n"
    return output


def create_classification_line(mes, label):
    """
    Creates CSV line(s) with two columns: the email's body extracted from :mes:
    and its classification (:label:)
    Ignores images, documents and calendar messages.
    :mes: should be a list of CustomMessage objects.
    """
    output = ''
    for m in mes:
        if m.get_content_type().startswith('text') and m.get_content_type() != 'text/calendar':
            output += m.create_vector_line(label) + '\n'
    return output


def to_file(text, file):
    """
    Writes :text: to :file:
    """
    f = open(file, 'w')
    f.write(text)
    f.close


def extract_mbox_file(file):
    """
    Extracts all the messages included in an mbox :file:
    by calling extract_message_payload
    """
    mbox = mailbox.mbox(file)
    messages = []
    for message in mbox:
        messages.extend(extract_message_payload(message))
    return messages



if __name__ == '__main__':
    argv = sys.argv
    if len(argv) != 2:
        print('Invalid arguments')
    else:
        file = argv[1]
        messages = extract_mbox_file(file)
        # to_file(create_classification_line(messages, 'label'), file + '_features.csv')
        to_file(text_messages_to_string(messages), file + '_full_extract.txt')


# Call to create a CSV file with the extracted data (body + label)
# to_file(create_classification_line(messages, 'label'), file + '_features.csv')
# Call to export all the extracted data
# to_file(text_messages_to_string(messages), file + '_full_extract')
