import pdfplumber
import csv, os, argparse

def process(input, output, password):
    with pdfplumber.open(input, password=password) as pdf:
        pages = pdf.pages
        indian = []
        foreign = []

        for page in pages:
            text = page.extract_text() or ""
            if "Domestic Transactions" in text:
                print("Domestic")
                table = page.extract_table()
                if table:
                    for (index, row) in enumerate(table):
                        if index == 0 or not row or row[0] == "" or row[0] is None:
                            continue

                        amount_index = len(row) - 2
                        print(row)

                        amount_raw = str(row[amount_index]).replace("Cr", "").replace(" ", "").replace(",", "") if len(row) > amount_index else "0"
                        indian.append({
                            "date": str(row[0]).replace("null", ""),
                            "description": row[1] if len(row) > 1 else "",
                            "currency": "INR",
                            "forex_amount": "",
                            "forex_rate": "",
                            "amount": amount_raw,
                            "type": "Cr" if "Cr" in str(row[amount_index]) else "Dr"
                        })

            elif "International Transactions" in text:
                print("Foreign")
                table_settings = {
                    "explicit_vertical_lines": [380] # Split the currency
                }
                table = page.extract_table(table_settings=table_settings)
                if table:
                    for (index, row) in enumerate(table):
                        if index == 0 or not row or row[0] == "" or row[0] is None:
                            continue

                        amount_index = len(row) - 2
                        print(row)

                        currency = str(row[2])[0:3] if len(row) > 2 and len(str(row[2])) >= 3 else ""
                        forex_amt_raw = str(row[2])[4:].replace(",", "").strip() if len(row) > 2 and len(str(row[2])) > 4 else ""
                        amount_raw = str(row[amount_index]).replace("Cr", "").replace(" ", "").replace(",", "") if len(row) > amount_index else "0"

                        forex_rate = ""
                        if forex_amt_raw and amount_raw:
                            try:
                                f_amt = float(forex_amt_raw)
                                a_amt = float(amount_raw)
                                if f_amt != 0:
                                    forex_rate = '%.2f' % (a_amt / f_amt)
                            except (ValueError, ZeroDivisionError):
                                forex_rate = ""

                        foreign.append({
                            "date": str(row[0]).replace("null", ""),
                            "description": row[1] if len(row) > 1 else "",
                            "currency": currency,
                            "forex_amount": forex_amt_raw,
                            "forex_rate": forex_rate,
                            "amount": amount_raw,
                            "type": "Cr" if "Cr" in str(row[amount_index]) else "Dr"
                        })

        # Calculate total due accurately once across all extracted transactions
        # Domestic transactions: Credits (Cr) don't add to billable dues
        # Foreign transactions: Credits (Cr) are marked as deductions
        total_amount = sum(
            float(item["amount"].replace(",", "")) * (0 if item["type"] == "Cr" else 1)
            for item in indian if item["amount"]
        ) + sum(
            float(item["amount"].replace(",", "")) * (-1 if item["type"] == "Cr" else 1)
            for item in foreign if item["amount"]
        )

    print("Processed " + str(input) + ". Total due should be " + str(total_amount))

    # Output to CSV
    combined = []
    combined.extend(indian)
    combined.extend(foreign)

    fields = ["date", "currency", "description", "forex_amount", "forex_rate", "amount", "type"]
    if output:
        out_parent = os.path.dirname(output)
        if out_parent:
            os.makedirs(out_parent, exist_ok=True)
        with open(output, 'w', encoding='utf-8') as file:
            writer = csv.DictWriter(file, delimiter=',', lineterminator='\n', quoting=csv.QUOTE_ALL, fieldnames=fields)
            writer.writeheader()

            for row in combined:
                writer.writerow({ key: row.get(key, "") for key in fields })

    return {"total_amount": total_amount, "indian": indian, "foreign": foreign, "combined": combined}


def main(args):
    if not os.path.exists(args.in_dir):
        print(f"Error: Input directory '{args.in_dir}' does not exist.")
        return

    os.makedirs(args.out_dir, exist_ok=True)

    for file_name in os.listdir(args.in_dir):
        root, ext = os.path.splitext(file_name)
        if ext.lower() != '.pdf':
            continue

        pdf_path = os.path.join(args.in_dir, file_name)

        out_name = root + '.csv'
        out_path = os.path.join(args.out_dir, out_name)

        print(f'Processing: {pdf_path}')
        process(pdf_path, out_path, args.password)
        print(f'Output file: {out_path}')

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--in-dir', type=str, required=True, help='directory to read statement PDFs from.')
    parser.add_argument('--out-dir', type=str, required=True, help='directory to store statement CSV to.')
    parser.add_argument('--password', type=str, default=None, help='password for the statement PDF.')
    args = parser.parse_args()

    main(args)
