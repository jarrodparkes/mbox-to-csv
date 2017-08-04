#!/bin/bash
docker run -it --rm --name mbox-to-csv -v "$PWD":/usr/src/myapp -w /usr/src/myapp python:2 python mbox_parser.py
