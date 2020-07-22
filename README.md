# MBOX to CSV

![Python 3.8.3](https://img.shields.io/badge/python-3.8.3-yellow.svg)

Extract emails from an MBOX file into a CSV file.

## Example

```bash
# rename rules.example.py to rules.py
mv rules.examples.py rules.py

# launch virtual environment with included dependencies
source env/bin/activate

# run tool using example file
python3 mbox_parser.py example.mbox

# deactivate virtual environment
deactivate
```

## References

- [Python Virtual Environments](https://packaging.python.org/guides/installing-using-pip-and-virtual-environments/)
- [Email Address and MIME Parsing](https://github.com/mailgun/flanker)
- [Signature Stripping Solution](https://github.com/mailgun/talon)
- [MBOX Parsing Example: Mining the Social](https://www.oreilly.com/library/view/mining-the-social/9781449368180/ch06.html)
- [Gmail MBOX Parser](https://github.com/alejandro-g-m/Gmail-MBOX-email-parser)
- [Mail Parser Package](https://pypi.org/project/mail-parser/)
