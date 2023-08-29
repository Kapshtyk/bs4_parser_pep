# Parser PEP Documentation

## Introduction

This script allows you to collect information from the Python Enhancement Proposals (PEP) documentation site. It provides detailed information about PEPs, their status, titles, etc. It also allows you to download documentation.

## Features

- Fetches PEP details from the PEP documentation website.
- Provides information about PEP numbers, titles, statuses, and more.
- Supports different output formats: pretty table, CSV file or ZIP archive.

## Getting Started

1. Clone the repository:

   ```bash
   git clone https://github.com/Kapshtyk/bs4_parser_pep.git
   cd bs4_parser_pep
   ```

2. Install the required dependencies:

  ```bash
  pip install -r requirements.txt
  ```

3. Run the script with the desired mode:

  ```bash
  python main.py <mode>
  ```

  - positional arguments: __whats-new__, __latest-versions__, __download__ or __pep__ - parser modes

  - optional arguments:
  ```
  -h, --help - show help message and exit
  -c, --clear-cache - clear cache
  -o {pretty,file}, --output {pretty,file} - additional data output methods
  ```

## Output Options

The parser supports different output options:

- __pretty__ (default): display the results in a formatted table.
- __file__: save the results to a CSV file.

## Main dependencies

- BeautifulSoup
- requests
- requests-cache
- prettytable

## Author
- LinkedIn - [Arseny Kapshtyk](https://www.linkedin.com/in/kapshtyk/)
- Github - [@kapshtyk](https://github.com/Kapshtyk)
