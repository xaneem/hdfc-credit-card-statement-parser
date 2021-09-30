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

3. Copy credit card statement PDFs to `./input/` folder

4. Update the password in `run.sh`

5. Run the script `./run.sh`

    Sample output:
    ```
    Processing: ./input/2021-09-10.PDF
    Processed ./input/2021-09-10.PDF. Total due should be 39432.229999999996
    Output file: ./output/2021-09-10.csv
    ```

    Example of the output csv is shown in `example-output.csv` in this repo.

6. Cross check the data and make sure the extracted information is correct.

## Notes
- It extracts both Indian and Foreign transactions. For Foreign transactions, the Forex Amount and Forex Rate is also extracted
- Cr/Dr column is also included
- I might have missed out testing for some types of transactions in the statement. Create a PR if you had to fix something to make it work for you

