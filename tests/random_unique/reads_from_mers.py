#!/usr/bin/env python
# encoding: utf-8
"""
untitled.py

Created by Cole Trapnell on 2008-06-24.
Copyright (c) 2008 Cole Trapnell. All rights reserved.
"""

import sys
import getopt
import random


help_message = '''
This tool takes mummer output and generates a set of short reads from 
the hits.  

Usage:
    reads_from_mers.py <ref.fna> <mummer-mer-hits.out>
'''


class Usage(Exception):
    def __init__(self, msg):
        self.msg = msg


def main(argv=None):
    if argv is None:
        argv = sys.argv
    try:
        try:
            opts, args = getopt.getopt(argv[1:], "ho:ve:rq:m", 
                                        ["help", 
                                        "output=", 
                                        "extension",
                                        "reverse-complement",
                                        "low-qual-mismatches",
                                        "maq-fastq"])
        except getopt.error, msg:
            raise Usage(msg)
    
        extension = 10
        rc = False
        low_qual_mismatches = 0
        fastq = False
        
        # option processing
        for option, value in opts:
            if option == "-v":
                verbose = True
            if option in ("-h", "--help"):
                raise Usage(help_message)
            if option in ("-o", "--output"):
                output = value
            if option in ("-e", "--extension"):
                extension = int(value)
            if option in ("-r", "--reverse-complement"):
                rc = True
            if option in ("-q", "--low-qual-mismatches"):
                low_qual_mismatches  = int(value)
            if option in ("-m", "--maq-fastq"):
                fastq = True
                
        ref = open(args[0])
        mummer_out = open(args[1])
        
        seq = None
        for line in ref.readlines():
            if line[0] == '>':
                if seq != None:
                    raise Usage("Multi-fasta not supported")
                else:
                    seq = []
            else:
                line = line.strip()
                seq.extend(list(line))
        
        rid = None
        (ref_pos, mer_start, mer_end) = (None, None, None)

        reads_fna = open(args[2],'w')
        ebwt_expect_out = open(args[3], 'w')

        read_num = 0
        
        complement = { "A" : "T", "C" : "G", "T":"A", "G" : "C" }
        mismatch = { "A" : "C", "C" : "G", "G": "T", "T" : "C"}
        
        for line in mummer_out.readlines():
            if line[0] == '>':
                rid = line[1:].strip()
            else:
                (ref_pos, mer_start, mer_end) = line.split()
                ref_pos = int(ref_pos) - 1
                mer_start = int(mer_start) - 1
                mer_end = int(mer_end) - 1
                
                mer_len = (mer_end -  mer_start + 1)
                
                # Skip mers that occur too close to the 5' or 3' end of the
                # reference
                if (ref_pos + mer_len + extension >= len(seq) or 
                    ref_pos - extension < 0):
                    print >> sys.stderr, "Skipping", rid
                    continue
                
                if fastq:
                    defline = "@%s" % rid
                else:
                    defline = ">%s" % rid
                
                if rc:
                    rc_ref_start = ref_pos - extension + 1 
                    rc_ref_end = rc_ref_start + mer_len + extension
                    read_seq = seq[rc_ref_start : rc_ref_end]
                    read_seq.reverse()
                    read_seq = [complement[a] for a in read_seq]
                    
                    read_out = "%d-:<0,%d,%d>" % (read_num, rc_ref_start, low_qual_mismatches)
                else:
                    read_seq = seq[ref_pos:ref_pos + mer_len + extension]
                    
                    #read_seq = ''.join(read_seq)
                    read_out = "%d+:<0,%d,%d>" % (read_num, ref_pos, low_qual_mismatches)
                        
                if low_qual_mismatches > 0:
                    mis_pos = set([])
                    while len(mis_pos) < low_qual_mismatches:
                        mis_pos.add(random.choice(range(mer_len, mer_len + extension)))
                    for pos in mis_pos:
                        read_seq[pos] = mismatch[read_seq[pos]]        
                
                read_seq = ''.join(read_seq)        
                print >> reads_fna, defline
                print >> reads_fna, read_seq
                if fastq:
                    print >> reads_fna, "+"
                    print >> reads_fna, (";" * len(read_seq))
                print >> ebwt_expect_out, read_out
                
                read_num += 1
        
        
    
    except Usage, err:
        print >> sys.stderr, sys.argv[0].split("/")[-1] + ": " + str(err.msg)
        print >> sys.stderr, "\t for help use --help"
        return 2


if __name__ == "__main__":
    sys.exit(main())