
import argparse
import os
from new_plumber import process_pdf_new
from old_plumber import process_pdf_old

def main(args):
    for file_name in os.listdir(args.in_dir):
        root, ext = os.path.splitext(file_name)
        if ext.lower() != '.pdf':
            continue

        pdf_path = os.path.join(args.in_dir, file_name)

        out_name = root + '.csv'
        out_path = os.path.join(args.out_dir, out_name)

        print(f'Processing: {pdf_path}')
        # use old script if filename starts with OLD use new script if starts with NEW
        if args.format == 'old':
            process_pdf_old(pdf_path, out_path, args.password, debugLog=False)
        elif args.format == 'new':
            process_pdf_new(pdf_path, out_path, args.password, debugLog=False)
        else:
            print(f'Unknown format: {args.format}')
            continue
        print(f'Output file: {out_path}')

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--in-dir', type=str, required=True, help='directory to read statement PDFs from.')
    parser.add_argument('--out-dir', type=str, required=True, help='directory to store statement CSV to.')
    parser.add_argument('--password', type=str, default=None, help='password for the statement PDF.')
    parser.add_argument('--format', type=str, choices=['old', 'new'], default=None, help='which parser to use: old or new.')
    args = parser.parse_args()

    main(args)