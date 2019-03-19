import argparse
import csv
import os
import sys
print(sys.version)

parser = argparse.ArgumentParser()
parser.add_argument('--input')
parser.add_argument('--db_local')
parser.add_argument('--db_online')
parser.add_argument('--ppm')
parser.add_argument('--ppm_frag')
parser.add_argument('--fragmasstol')
parser.add_argument('--polarity')
parser.add_argument('--results')
parser.add_argument('--threads')

args = parser.parse_args()
print args

os.makedirs("tmet")

with open(args.input,"r") as infile:
    numlines = 0
    for line in infile:
        line = line.strip()
        if numlines == 0:
            if "CH$NAME:" in line:
                featid = line.split("CH$NAME: ")[1]
                featid = featid.split(" ")
                featid = featid[1] + "_" + featid[3] + "_" + featid[5] + "_" + featid[7]
            if "MS$FOCUSED_ION:" in line:
                mz = float(line.split("MS$FOCUSED_ION: PRECURSOR_M/Z ")[1])
                if args.polarity=="pos":
                    mz2 = mz-1.007276
                else:
                    mz2 = mz+1.007276
            if "PK$NUM_PEAK:" in line:
                numlines = int(line.split("PK$NUM_PEAK: ")[1])
                linesread = 0
                peaklist = []
        else:
            if linesread == numlines:
                numlines = 0
                #write spec file
                with open('./tmpspec.txt', 'w') as outfile:
                    for p in peaklist:
                        outfile.write(p[0]+"\t"+p[1]+"\n")
                #create commandline input
                cmd_command = "PeakListPath=tmpspec.txt "
                if args.db_local != "None":
                    cmd_command += "MetFragDatabaseType=LocalCSV "
                    cmd_command += "LocalDatabasePath={0} ".format(args.db_local)
                else:
                    cmd_command += "MetFragDatabaseType={0} ".format(args.db_online)
                cmd_command += "FragmentPeakMatchAbsoluteMassDeviation={0} ".format(args.fragmasstol)
                cmd_command += "FragmentPeakMatchRelativeMassDeviation={0} ".format(args.ppm_frag)
                cmd_command += "DatabaseSearchRelativeMassDeviation={0} ".format(args.ppm)
                cmd_command += "NeutralPrecursorMass={0} ".format(mz2)
                cmd_command += "SampleName={0}_metfrag ".format(featid)
                cmd_command += "ResultsPath=./tmet/ "
                if args.polarity == "pos":
                    cmd_command += "IsPositiveIonMode=True "
                else:
                    cmd_command += "IsPositiveIonMode=False "
                if args.polarity == "pos": ### Annotation information. Create a dict for the PrecurorIonModes??
                    cmd_command += "PrecursorIonMode=1 "
                else:
                    cmd_command += "PrecursorIonMode=-1 "
                cmd_command += "MetFragCandidateWriter=CSV " ## TSV not available
                cmd_command += "NumberThreads={} ".format(args.threads)
                # run Metfrag
                print "metfrag {0}".format(cmd_command)
                os.system("metfrag {0}".format(cmd_command))
            else:
                #One line not need between numpeak and peaklist
                if not "PK$PEAK:" in line:
                    line = tuple(line.split("\t"))
                    #Keep only m/z and intensity, not relative intensity
                    save_line = tuple(line[0].split("\t") + line[1].split("\t"))
                    linesread += 1
                    peaklist.append(save_line)



#outputs might have different headers. Need to get a list of all the headers before we start merging the files
outfiles = sorted(os.listdir("./tmet"))

headers = []
c = 0
for fname in outfiles:
    with open("./tmet/"+fname) as infile:
        reader = csv.reader(infile)
        headers.extend(reader.next())
        # check if file has any data rows 
        for i, row in enumerate(reader):
            c+=1
            if i==1:
                break
        
# if no data rows (e.g. matches) then do not save an output and leave the program        
if c==0:
    sys.exit()


print headers
headers = ['UID'] + sorted(list(set(headers)))
print headers

#merge outputs
with open(args.results, 'a') as merged_outfile:

    dwriter = csv.DictWriter(merged_outfile, fieldnames=headers, delimiter='\t')
    dwriter.writeheader()

    for fname in outfiles:
        fileid = os.path.basename(fname).split("_")[0]
        with open("./tmet/"+fname) as infile:
            reader = csv.DictReader(infile, delimiter=',', quotechar='"')
            for line in reader:
                line['UID'] = fileid
                dwriter.writerow(line)


