# MBOX to CSV

![Platform Python](https://img.shields.io/badge/platform-python%202.7-yellow.svg)

A Python script for extracting emails from an MBOX file into a CSV file. The script also provides the ability to filter out emails from a certain name/email address.

## How to Run the Script

[1] Install Docker
    - [Windows](https://www.docker.com/docker-windows)
    - [Mac](https://www.docker.com/docker-mac)
[2] Clone the Repository, Run the Script!

```bash
~ $ git clone https://github.com/jarrodparkes/mbox-to-csv
~/mbox-to-csv $ cd mbox-to-csv/
~/mbox-to-csv $ ./run.sh
```

> **Note**: You could also download the repository directly using [this link](https://github.com/jarrodparkes/mbox-to-csv/archive/master.zip).

## An Example

I've provided an `example.mbox` file to demonstrate how the script is used. For this example, I want the script to only extract emails that *parkesfjames@gmail.com* sent:

```bash
~/mbox-to-csv $ ./run.sh
name of mbox file in current directory (ex. my_file.mbox): example.mbox
name of sender that you want to filter (ex. Jarrod Parkes):
email of sender that you want to filter (ex. parkesfjarrod@gmail.com): parkesrjames@gmail.com
generated csv file called clean_mail.csv
# clean_mail.csv only contains emails parkesfjames@gmail.com sent
```
