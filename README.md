# MBOX to CSV

![Platform Python](https://img.shields.io/badge/platform-python%202.7-yellow.svg)

Python script for converting MBOX file to CSV.

## Overview

This script takes 3 arguments:

- mbox_fname: name of a mbox file in the executing directory
- name_of_sender: name in the FROM field that you want to filter out
- email_of_sender: email in the FROM field that you want to filter out

Example argument values:

- mbox_fname: my_file.mbox
- name_of_sender: John Doe
- email_of_sender: john@example.com
