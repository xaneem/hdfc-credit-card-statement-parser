import re
import pdfplumber
import csv
import os
from typing import List, Dict, Optional

# Regex patterns
DATE_TIME_RE = re.compile(r'^\s*(\d{2}/\d{2}/\d{4})\s*\|\s*(\d{2}:\d{2})\s*(.*)$')

# Forex currency and amount e.g. "USD 20.00"
FOREX_RE = re.compile(
    r'\b(?P<currency>[A-Z]{3})\b\s+(?P<amount>[\d,]+(?:\.\d{1,2})?)\s*$'
    )

DEFAULT_LOCAL_CURRENCY = "INR"

def clean_amount_str(s: Optional[str]) -> Optional[float]:
    m = re.search(r'([\d,]+(?:\.\d{1,2})?)', s)
    if not m:
        return None
    
    num_str = m.group(1)
    return float(num_str.replace(",", ""))

def parse_lines(text: str) -> List[Dict]:
    rows: List[Dict] = []
    for raw_line in text.splitlines():
        if not raw_line.strip():
            continue

        # Attempt full date|time style first
        m = DATE_TIME_RE.match(raw_line)
        if m:
            date_part, time_part, rest = m.groups()
        else:
            # try to find a date anywhere
            dm = re.search(r'(\d{2}/\d{2}/\d{4})', raw_line)
            if not dm:
                continue
            date_part = dm.group(1)
            # everything after date taken as rest
            rest = raw_line[dm.end():].strip()
            # try to get time if present
            tm = re.search(r'(\d{2}:\d{2})', raw_line)
            time_part = tm.group(1) if tm else None
            
        txn_type = "Dr"
            
        # split amount and and rest
        # try to find index of + C
        index_plus_c = rest.rfind('+ C')
        if index_plus_c != -1:
            txn_type = "Cr"
            amount_str = rest[index_plus_c + 3:].strip()
            rest = rest[:index_plus_c].strip()
        else:
            index_c = rest.rfind(' C')
            if index_c != -1:
                amount_str = rest[index_c + 2:].strip()
                rest = rest[:index_c].strip()
        amount = clean_amount_str(amount_str)

        forex_currency = None
        forex_amount = None
        description = rest
        # check for forex pattern in rest
        forex_match = FOREX_RE.search(rest)
        if forex_match:
            forex_currency = forex_match.group('currency')
            forex_amount = clean_amount_str(forex_match.group('amount'))
            # remove forex fragment from rest
            start, end = forex_match.span()
            description = (rest[:start] + rest[end:]).strip()

        # # compute forex rate if applicable
        forex_rate = None
        if forex_amount and amount:
            try:
                forex_rate = '%.4f' % float(amount / forex_amount) if forex_amount != 0 else None
            except Exception:
                forex_rate = None

        rows.append({
            "date": date_part,
            "time": time_part,
            "description": description,
            "amount": amount,
            "currency": forex_currency or DEFAULT_LOCAL_CURRENCY,
            "forex_amount": forex_amount,
            "forex_rate": forex_rate,
            "type": txn_type,
        })
    return rows

def extract_rows_from_pdf(pdf_path: str, password: Optional[str], debugLog: bool=False) -> List[Dict]:
    all_rows: List[Dict] = []
    with pdfplumber.open(pdf_path, password=password) as pdf:
        for i, page in enumerate(pdf.pages, start=1):
            page_text = page.extract_text() or ""

            # Heuristic: skip pages that don't look like statements
            if "Domestic Transactions" not in page_text and "International Transactions" not in page_text:
                if not re.search(r'\d{2}/\d{2}/\d{4}', page_text):
                    if debugLog:
                        print(f"  skip page {i} (no transaction indicator)")
                    continue

            # Try table extraction first
            try:
                tables = page.extract_tables()
            except Exception as e:
                if debugLog:
                    print(f"page {i} extract_tables() error: {e}")
                tables = []

            if tables:
                if debugLog:
                    print(f"page {i} found {len(tables)} table(s)")
                for table in tables:
                    for row in table:
                        if not row:
                            continue
                        joined = " ".join([str(c).strip() for c in row if c is not None]).strip()
                        lines = joined.splitlines()
                        # only consider lines with dates
                        for line in lines:
                            if not re.search(r'\d{2}/\d{2}/\d{4}', line):
                                continue
                            parsed_row = parse_lines(line)
                            if parsed_row:
                                all_rows.extend(parsed_row)

    return all_rows

def process_pdf_new(input: str, output: str, password: Optional[str] = None, debugLog: bool=False):
    # Ensure output directory exists
    out_dir = os.path.dirname(os.path.abspath(output))
    if out_dir and not os.path.exists(out_dir):
        os.makedirs(out_dir, exist_ok=True)
        if debugLog:
            print("Created output directory:", out_dir)

    rows = extract_rows_from_pdf(input, password=password, debugLog=debugLog)

    # Prepare output CSV columns
    cols = ["date","time","currency","description","forex_amount","forex_rate","amount","type"]
    with open(output, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, delimiter=',', lineterminator='\n', quoting=csv.QUOTE_ALL, fieldnames=cols)
        writer.writeheader()
        
        for row in rows:
            writer.writerow({ key: row.get(key, "") for key in cols })