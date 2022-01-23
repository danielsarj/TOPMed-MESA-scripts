#!/usr/bin/python
'''This python script takes one TOPMed WGS vcf.gz as input, and makes one dosage file per chromosome,
as well as a sample file ready to run PrediXcan. 

For usage, type from command line:
python TOPMed_vcf2dosage_b.py -h
dose allele is Allele2, see https://github.com/hakyimlab/PrediXcan/blob/master/Software/HOWTO-beta.md

NOTE: this is a modified version of the script found in https://github.com/WheelerLab/DivPop/blob/85100c2a41e2022e1e684e165980c3e9868db925/GWAS_QC/03_UMich_vcf2px_noambig_singlesnp.py'''

import gzip
import sys
import argparse
import os

def check_arg(args=None):
    parser = argparse.ArgumentParser(description='Script to make a dosage file from VCF')
    parser.add_argument('-i', '--inputdir',
                        help='directory containing VCF',
                        required='True')
    parser.add_argument('-f', '--file',
                        help='VCF name',
                        required='True')
    parser.add_argument('-o', '--output',
                        help='output file prefix',
                        required='True')
    return parser.parse_args()

#retrieve command line arguments
args = check_arg(sys.argv[1:])
chrpath = args.inputdir
f = args.file
o = args.output
chrfile = chrpath + "/" + f

alleles = {'A':'T', 'T':'A', 'G':'C', 'C':'G'}

#get dosage file data
if(os.path.exists(chrpath + '/dosages/') == False): #check if dosage subfolder exists
    os.mkdir(chrpath + '/dosages/')

for line in gzip.open(chrfile): #reading input file line by line
    if(line.startswith(b'##')): #check if current line is a VCF header line
        continue

    arr = line.strip().split()
    arr = map(lambda x : x.decode("utf-8"), arr)
    arr = list(arr)

    if(line.startswith(b'#CHROM')): #only one line should match #CHROM
        #makes sample file for PrediXcan
        ids = arr[9:]
        ids = map(lambda x : x + " " + x, ids)
        ids = list(ids)
        outsamples = open(chrpath + "/dosages/"+o+".samples.txt","w")
        outsamples.write("\n".join(ids))
        outsamples.close()
        continue

    (chr, pos, id, ref, alt, qual, filter, info, format) = arr[0:9]
    if len(ref) > 1 or len(alt) > 1: #skips indels
        continue
    if alleles[ref] == alt: #skips ambiguous snps
        continue

    if str(chr).find("chr") == -1: #updates chrID to the format "chr#" if necessary 
        chr = "chr" + str(chr)

    ## updates chrX, chrXY, chrY, and chrM to their numeric versions. this section can be commented out  
    if chr == "chrX":
        if int(pos)>2781479 and int(pos)<155701383: #hg38 positions
            chr = "chr23"
        else:
            chr = "chr25"
    if chr == "chrY":
        chr = "chr24"
    if chr == "chrXY":
        chr = "chr25"
    if chr == "chrM":
        chr = "chr26"
    ##

    varid = chr + ":" + str(pos) + ":" + str(ref) + ":" + str(alt) #name SNPs in chr:pos:ref:alt format

    #getting dosages
    gt_dosagerow = arr[9:]
    dosagerow = [i.split("/") for i in gt_dosagerow] #splits genotypes by "/". if genotypes are phased, change to "|"
    dosagerow = [int(i[0])+int(i[1]) for i in dosagerow]

    freqalt = round(sum(dosagerow)/(len(dosagerow)*2),4) #calc ALT allele frequency
    dosages = " ".join(map(str,dosagerow))
    output = chr + " " + str(varid) + " " + str(pos) + " " + str(ref) + " " + str(alt) + " " + str(freqalt) + " " + str(dosages) + "\n"

    with gzip.open(chrpath + "/dosages/" + o + "." + chr + ".dosage.txt.gz", "ab") as outdosage:
        outdosage.write(output.encode("utf-8"))