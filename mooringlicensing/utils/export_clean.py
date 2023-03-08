import csv
import os

def clean(srcpath='/home/jawaidm/Documents/ML_Excel/Lotus_Notes_extracts', outpath='/var/www/mooringlicensing/mooringlicensing/utils/csv/clean'):
    '''
    from mooringlicensing.utils.export_clean import clean
    clean()
    '''

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
        with open(outpath + os.sep + out_filename, 'w') as outf:
            wr = csv.writer(outf) #, delimiter ='|', quotechar = '"')
            for line in lines:
                #import ipdb; ipdb.set_trace()
                #wr.writerow(line.strip('"').split('|'))
                wr.writerow([line.strip('"')])
