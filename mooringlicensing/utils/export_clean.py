import csv
import os
import logging
import re

logger = logging.getLogger(__name__)

def clean(srcpath='/data/data/projects/mooringlicensing/tmp/ml_export', outpath='/data/data/projects/mooringlicensing/tmp/clean'):
    '''
    from mooringlicensing.utils.export_clean import clean
    clean()

    or

    clean(srcpath='/var/www/ml_seg/mooringlicensing/utils/csv/clean_06Feb2024', outpath='/data/data/projects/mooringlicensing/tmp/clean')
    '''
    logger.info(f'srcpath: {srcpath}')
    logger.info(f'outpath: {outpath}')

    isExist = os.path.exists(outpath)
    if not isExist:
        os.makedirs(outpath)

    files = []
    for file in os.listdir(srcpath):
        if file.endswith(".txt"):
            files.append(file)

    for filename in files:
        with open(srcpath + os.sep + filename, encoding="cp1252") as inf:
            lines = [line.rstrip() for line in inf]

        col_count = 0
        out_filename = filename.split('/')[-1]
        with open(outpath + os.sep + out_filename, 'w', newline='') as outf:
            logger.info(f'Processing file: [{filename}]...')
            wr = csv.writer(outf, quoting=csv.QUOTE_NONE, escapechar='\\') #, delimiter ='|', quotechar = '"')
            line_number = 0
            header_line = ""
            for line in lines:
                if line_number == 0:
                    col_count = line.count('|')
                    header_line = re.sub(r'^"*|"*$', '', line)
                line_number += 1  # This is used when an error raised to specify which line raises the error.
                try:
                    if '|' not in line:
                        # No delimiter in a line, which means no cells in the line.  Skip the process
                        continue

                    temp = re.sub(r'^"*|"*$', '', line)  # Remove double quotes at the beginning and end of a string, regardless of their quantity.

                    line_col_count = temp.count('|')
                    if line_col_count > col_count:
                        print("\n___Line",line_number,"has the wrong number of | -", line_col_count, "when it should be",col_count,"___")
                        print("\n",header_line,"\n")
                        print(temp, "\n")
                        print("__________________________________________________\n")

                    wr.writerow([temp])
                except Exception as e:
                    logger.error(f'Error: {e}.  filename: {filename},  line_number: {line_number},  line: {line}')
