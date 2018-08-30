# Running Philter from the command line

## Production Mode (no ground truth annotations required)
Production mode will avoid outputting unnecessary print statements, and will skip the evaluation steps. Use the following command to run a single job:
```bash
python3 main.py -i ./data/i2b2_notes/ -o ./data/i2b2_results/ -f ./configs/ucsf_pipeline_test_map_regex_context.json --prod=True
```

To run multiple jobs simultaneously, all input notes handled by a single job must be located in separate directories. For example, if you wanted to Philter 1000 notes simultaneously on two processes, the two input directories might look like:

1. ./data/batch1/500_input_notes_batch1/
2. ./data/batch2/500_input_notes_batch2/

In this example, the following two commands would be used to start each job:
```bash
nohup python3 main.py -i ./data/batch1/500_input_notes_batch2/ -o ./data/i2b2_results_test/ -f ./configs/ucsf_pipeline_test_map_regex_context.json --prod=True > ./data/batch1/batch1_terminal_out.txt 2>&1 &

```
```bash
nohup python3 main.py -i ./data/batch2/500_input_notes_batch2/ -o ./data/i2b2_results_test/ -f ./configs/ucsf_pipeline_test_map_regex_context.json --prod=True > ./data/batch2/batch2_terminal_out.txt 2>&1 &

```

## Evaluation Mode (ground truth annotations required)
```bash
python3 main.py -i ./data/i2b2_notes/ -a ./data/i2b2_anno/ -o ./data/i2b2_results/ -x ./data/phi_notes_i2b2.json -f=./configs/ucsf_pipeline_test_map_regex_context.json
```


## Creating Philter-Compatible Input Files
Because Philter only accepts plain text files as input, the note text must be extracted from notes in xml format. Additionally, Philter requires plain text annotation files (with asterisks obscuring PHI) for evalutaion. To create these required files from notes in xml format, run the following command:

```bash
python3 ./generate_dataset/main_ucsf_updated.py -x ./data/i2b2_xml/ -o ./data/phi_notes_i2b2.json -n ./data/i2b2_notes/ -a ./data/i2b2_anno/
```
### Input and Output Description
This script expects notes in xml format, and transforms each input file into two plain text files: 1) the original note text, and 2) the note text with asterisks obscuring PHI. A properly formatted xml input can be found in ./data/i2b2_xml, and examples of the two outputs can be found in ./data/i2b2_notes and ./data/i2b2_anno, respectively. Additionally, this script creates a .json file that contains the original text from each note, followed by the PHI annotations in json format. An example of this output file can be found at ./data/phi_notes_i2b2.json.
### Flags:

-x Path to the directory file that contains the note xml files<br/>
-o Path to the json file that will contain a summary of the phi in the xml files<br/>
-n Path to the directory where you would like to store the plain text notes<br/>
-a Path to the directory where you would like to store the plain text annotations<br/>
