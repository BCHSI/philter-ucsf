import nltk
import re
import os
import json
import pickle
import difflib
from difflib import SequenceMatcher
from chardet.universaldetector import UniversalDetector
from coordinate_map import CoordinateMap
import xml.etree.ElementTree as ET
import sys
import argparse


def isolate_phi(xml_folder):
    #isolate all phi and data with coordinates
    #turn them into a json representation
    phi = {} #fn --> {"text":"...", "phi":[{"type":"DATE"...}]}
    for root_dir, dirs, files in os.walk(xml_folder):
        for f in files:
            with open(root_dir+f, 'r', encoding='latin1') as file:
                tree = ET.parse(file)
                root = tree.getroot()

                text = ""
                phi_list = []

                for child in root:
                    if child.tag == "TEXT":
                        text = child.text
                        # if f == '167937985.txt.xml':
                        #     print(text)
                        #print (child.tag, child.attrib, child.text)
                    if child.tag == "TAGS":
                        for t in child:
                            phi_list.append(t.attrib)
                            #print(t.tag, t.attrib, t.text)
                phi[f] = {"text":text, "phi":phi_list}
    return phi

def main():
    # get input/output/filename

    ap = argparse.ArgumentParser()
    ap.add_argument("-x", "--xml", default="../data/ucsf_xml/",
                    help="Path to the directory or the file that contains the note xml files, the default is ../data/ucsf_xml/",
                    type=str)
    ap.add_argument("-o", "--output", default="../data/phi_notes_ucsf.json",
                    help="Path to the file that contains a summary of the phi in the xml files, the default is ../data/phi_notes_ucsf.json",
                    type=str)
    ap.add_argument("-n", "--notes", default="../data/ucsf_notes/",
                    help="Path to the directory or the file that contains the PHI note, the default is ../data/ucsf_notes/",
                    type=str)
    ap.add_argument("-a", "--anno", default="../data/ucsf_anno/",
                    help="Path to the directory or the file that contains the PHI annotation, the default is ../data/ucsf_anno/",
                    type=str)
    ap.add_argument("-s", "--phi", default="../data/ucsf_phi/",
                    help="Path to the directory to save the PHI summary in, the default is ../data/ucsf_phi/",
                    type=str)
    ap.add_argument("-c", "--context", default="../data/ucsf_phi_context",
                    help="Path to the directory to save the PHI context summary in, the default is ../data/ucsf_phi_context",
                    type=str)
    ap.add_argument("-p", "--pos", default="../data/ucsf_phi_pos",
                    help="Path to the directory to save the PHI pos summary in, the default is ../data/ucsf_phi_pos",
                    type=str)

    args = ap.parse_args()

    xml_folder = args.xml
    outpath = args.output
    
    # Run main function
    phi = isolate_phi(xml_folder)

    #save our data
    json.dump(phi, open(outpath, "w"), indent=4)

    NOTES_FOLDER = args.notes
    ANNO_FOLDER = args.anno

    
    #save our phi notes 
    for fn in phi:

        #get text and remove any initial *'s from the raw notes
        txt = phi[fn]["text"].replace("*", " ")

        #save our notes file
        with open(NOTES_FOLDER+fn.split(".")[0]+".txt", "w",encoding='utf-8') as note_file:
            note_file.write(txt)

        #create a coordinate mapping of all phi
        c = CoordinateMap()
        for p in phi[fn]["phi"]:
            try:
                start = int(p['start'])
                end = int(p['end'])
            except KeyError:
                start = int(p['spans'].split('~')[0])
                end = int(p['spans'].split('~')[1])
            c.add_extend(fn, start, end)

        contents = []
        last_marker = 0
        for start,stop in c.filecoords(fn):
            contents.append(txt[last_marker:start])
            
            #add a * for each letter preserving shape
            phi_hidden = re.sub(r"[a-zA-Z0-9]", "*", txt[start:stop])
            contents.append(phi_hidden)
            last_marker = stop

        #wrap it up by adding on the remaining values if we haven't hit eof
        if last_marker < len(txt):
            contents.append(txt[last_marker:len(txt)])

        with open(ANNO_FOLDER+fn.split(".")[0]+".txt", "w", encoding='utf-8') as anno_file:
            anno_file.write("".join(contents))


if __name__ == "__main__":
    main()
