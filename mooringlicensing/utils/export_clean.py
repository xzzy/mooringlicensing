import csv
import os
import logging
import re

logger = logging.getLogger(__name__)

def clean(srcpath='/home/jawaidm/Documents/ML_Excel/Lotus_Notes_extracts', outpath='/var/www/mooringlicensing/mooringlicensing/utils/csv/clean'):
    '''
    from mooringlicensing.utils.export_clean import clean
    clean()
    '''
    logger.info(f'srcpath: {srcpath}')
    logger.info(f'outpath: {outpath}')

    # line = '"""aho "" baka"""'
    # temp = re.sub(r'^"*|"*$', '', line)

    isExist = os.path.exists(outpath)
    if not isExist:
        os.makedirs(outpath)

    files = []
    for file in os.listdir(srcpath):
        if file.endswith(".txt"):
            files.append(file)

    for filename in files:
        #with open('/home/jawaidm/Documents/ML_Excel/Lotus_Notes_extracts/EmergencyDets20221201-083245.txt', encoding="cp1252") as f:
        with open(srcpath + os.sep + filename, encoding="cp1252") as inf:
            lines = [line.rstrip() for line in inf]

        out_filename = filename.split('/')[-1]
        with open(outpath + os.sep + out_filename, 'w', newline='') as outf:
            logger.info(f'Processing file: [{filename}]...')
            wr = csv.writer(outf, quoting=csv.QUOTE_NONE, escapechar='\\') #, delimiter ='|', quotechar = '"')
            line_number = 0
            for line in lines:
                line_number += 1  # This is used when an error raised to specify which line raises the error.
                try:
                    if '|' not in line:
                        # No delimiter in a line, which means no cells in the line.  We are not interested in the line.  Skip the process
                        continue

                    # wr.writerow([line.strip('"')])
                    temp = re.sub(r'^"*|"*$', '', line)  # Remove double quotes at the begginging and end of a string, regardless of their quantity.
                    wr.writerow([temp])
                except Exception as e:
                    logger.error(f'Error: {e}.  filename: {filename},  line_number: {line_number},  line: {line}')
