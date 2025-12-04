# HDFC Bank Credit Card Statement Parser

Extracts information from an HDFC Bank Credit Card statement. This will help copy structured data out of your statement.

> This was built for personal use and does not guarantee accuracy. Always cross check extracted data with your pdf for mistakes

## Usage
1. Setup a virtual env and activate a virtual environment (optional)
    ```
    $ sudo apt install -y python3-venv
    $ python3 -m venv env
    $ source env/bin/activate
    ```

2. Install requirements
    ```
    $ pip install -r requirements.txt
    ```

3. Copy credit card statement PDFs in old format to `input/old_format/` and new format to `input/new_format/` folders respectively

4. Update the password in `run.sh` and 

5. Run the script `./run.sh`

    Sample output:
    ```
    Processing: ./input/old_format/OLD - 2024-07-12.PDF
    Output file: ./output/OLD - 2024-07-12.csv
    Processing: ./input/new_format/NEW - 2024-08-12.pdf
    Output file: ./output/NEW - 2024-08-12.csv
    ```

    Example of the output csv is shown in `example-output.csv` in this repo.

6. Cross check the data and make sure the extracted information is correct.

## Notes
- It extracts both Indian and Foreign transactions. For Foreign transactions, the Forex Amount and Forex Rate is also extracted
- Cr/Dr column is also included
- I might have missed out testing for some types of transactions in the statement. Create a PR if you had to fix something to make it work for you
- Supports both old and new format of statements issued by HDFC Bank

