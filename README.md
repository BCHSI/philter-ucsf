
# Running Philter: A Step-by-Step Guide

Philter is a command-line based clinical text de-identification software that removes protected health information (PHI) from any plain text file. Although the software has built-in evaluation capabilities and can compare Philter PHI-reduced notes with a corresponding set of ground truth annotations, annotations are not required to run Philter. The following steps may be used to 1) run Philter in the command line without ground truth annotations, or 2) generate Philter-compatible annotations and run Philter in evaluation mode using ground truth annotations. Although any set of notes and corresponding annotations may be used with Philter, the examples provided here will correspond to the I2B2 dataset, which Philter uses in its default configuration. 

Before running Philter either with or without evaluation, make sure to familiarize yourself with the various options that may be used for any given Philter run:

### Flags:
**-i (input):**&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Path to the directory or the file that contains the clinical note(s), the default is ./data/i2b2_notes/<br/>
**-a (anno):**&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Path to the directory or the file that contains the PHI annotation(s), the default is ./data/i2b2_anno/<br/>
**-o (output):**&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Path to the directory to save the PHI-reduced notes in, the default is ./data/i2b2_results/<br/>
**-f (filters):**&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Path to the config file, the default is ./configs/philter_delta.json<br/>
**-x (xml):**&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Path to the json file that contains all xml data, the default is ./data/phi_notes.json<br/>
**-c (coords):**&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Output path to the json file that will contain the coordinate map data, the default is ./data/coordinates.json<br/>
**-v (verbose):**&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;When verbose is true, will emit messages about script progress. The default is True<br/>
**-e (run_eval):**&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;When run_eval is true, will run our eval script and emit summarized results to terminal<br/>
**-t (freq_table):**&nbsp;&nbsp;&nbsp;&nbsp;When freqtable is true, will output a unigram/bigram frequency table of all note words and their PHI/non-PHI counts. Default is False<br/>
**-n (initials):**&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;When initials is true, will include annotated initials PHI in recall/precision calculations. The default is True<br/>
**--eval_output:**&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Path to the directory that the detailed eval files will be outputted to, the default is ./data/phi/<br/>
**--stanfordner:**&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Path to Stanford NER, the default is /usr/local/stanford-ner/<br/>
**--outputformat:**&nbsp;&nbsp;Define format of annotation, allowed values are \"asterisk\", \"i2b2\". Default is \"asterisk\"<br/>
**--ucsfformat:**&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;When ucsfformat is true, will adjust eval script for slightly different xml format. The default is False<br/>
**--prod:**&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;When prod is true, this will run the script with output in i2b2 xml format without running the eval script. The default is False<br/>
**--cachepos:**&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Path to a directoy to store/load the pos data for all notes. If no path is specified then memory caching will be used<br/>

## 0. Curating I2B2 XML Files
To remove non-HIPAA PHI annotations from the I2B2 XML files, run the following command:

**-i** Path to the directory that contains the original I2B2 xml files<br/>
**-o** Path to the directory where the curated files will be written<br/>

```bash
python improve_i2b2_notes.py -i data/i2b2_xml/ -o data/i2b2_xml_updated/
```

## 1. Running Philter WITHOUT evaluation (no ground-truth annotations required)

**a.** Make sure the input file(s) are in plain text format. If you are using the I2B2 dataset (or any other dataset in XML or other formats), the note text must be extracted from each original file and be saved in individual text files. Examples of properly formatted input files can be found in ./data/i2b2_notes/.

**b.** Store all input file(s) in the same directory, and create an output directory (if you want the PHI-reduced notes to be stored somewhere other than the default location).

**c.** Create a configuration file with specified filters (if you do not want to use the default configuration file).

**d.** Run Philter in the command line using either default or custom parameters.

Use the following command to run a single job and output files in XML format:
```bash
python3 main.py -i ./data/i2b2_notes/ -o ./data/i2b2_results/ -f ./configs/philter_delta.json --prod=True
```
If you'd like the output files to be in plain text format (with asterisks obscuring PHI), simply add the -outputformat "asterisk" option:
```bash
python3 main.py -i ./data/i2b2_notes/ -o ./data/i2b2_results/ -f ./configs/philter_delta.json --prod=True --outputformat "asterisk"
```

To run multiple jobs simultaneously, all input notes handled by a single job must be located in separate directories to avoid cross-contamination between output files. For example, if you wanted to run Philter on 1000 notes simultaneously on two processes, the two input directories might look like:

1. ./data/batch1/500_input_notes_batch1/
2. ./data/batch2/500_input_notes_batch2/

In this example, the following two commands would be used to start running each job in the background:
```bash
nohup python3 main.py -i ./data/batch1/500_input_notes_batch2/ -o ./data/i2b2_results_test/ -f ./configs/philter_delta.json --prod=True > ./data/batch1/batch1_terminal_out.txt 2>&1 &

```
```bash
nohup python3 main.py -i ./data/batch2/500_input_notes_batch2/ -o ./data/i2b2_results_test/ -f ./configs/philter_delta.json --prod=True > ./data/batch2/batch2_terminal_out.txt 2>&1 &

```

## 2. Running Philter WITH evaluation (ground truth annotations required)

**a.** Create Philter-compatible annotation files using the transformation script located in ./generate_dataset/. This script expects notes in xml format, and transforms each input file into two plain text files: 1) the original note text, and 2) the note text with asterisks obscuring PHI. A properly formatted xml input can be found in ./data/i2b2_xml, and examples of the two outputs can be found in ./data/i2b2_notes and ./data/i2b2_anno, respectively. Additionally, this script creates a .json file that contains the original text from each note, followed by the PHI annotations in json format. An example of this output file can be found at ./data/phi_notes_i2b2.json. This is the file that will be used as the -x default option. 

### Flags:

**-x** Path to the directory file that contains the note xml files<br/>
**-o** Path to the json file that will contain a summary of the phi in the xml files<br/>
**-n** Path to the directory where you would like to store the plain text notes<br/>
**-a** Path to the directory where you would like to store the plain text annotations<br/>

Use the following command to create these input files from notes in XML format:

```bash
python3 ./generate_dataset/main_ucsf_updated.py -x ./data/i2b2_xml/ -o ./data/phi_notes_i2b2.json -n ./data/i2b2_notes/ -a ./data/i2b2_anno/
```
Note: If this command produces an ElementTree.ParseError, you may need to remove .DS_Store from ./data/i2b2_xml.

**b-c.** See Step 1b-c above

**d.** Run Philter in evaluation mode using the following command:

```bash
python3 main.py -i ./data/i2b2_notes/ -a ./data/i2b2_anno/ -o ./data/i2b2_results/ -x ./data/phi_notes_i2b2.json -f=./configs/philter_delta.json
```
