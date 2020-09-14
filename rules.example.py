# external counts
cant_convert_count = 0
blacklist_count = 0

def apply_rules(date, sent_from, sent_to, cc, subject, contents, owners, blacklist_domains):
    """Returns a list to be written to a CSV after applying domain-specific rules to its contents.

    The list format is as follows:
    ["flagged", "date", "description", "from", "to", "cc", "subject", "content", "time (minutes)"]

    Args:
        date (str): The date the email was written.
        sent_from (list): A list of email addresses the email was sent from.
        sent_to (list): A list of email addresses the email was sent to.
        cc (list): A list of email addresses the email was cc'ed to.
        subject (str): The subject of the email.
        contents (str): The contents of the email.
        owners (list): A list of email addresses representing the "owners" of the MBOX.
        blacklist_domains (list): A list of domains that can be used for omission rules.

    Returns:
        list: a list to be written to a CSV after applying domain-specific rules to its contents
    """
    return [
        "",
        date,
        "",
        ", ".join(sent_from),
        ", ".join(sent_to),
        ", ".join(cc),
        subject,
        contents,
        "0"
    ]
