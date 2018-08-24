# Running Philter from the command line

## Production Mode (no ground truth annotations required)
```bash
python3 main.py -i "./data/i2b2_notes_test/" -o "./data/i2b2_results_test/" -f=./configs/ucsf_pipeline_test_map_regex_context.json --prod=True
```
Notes - this production mode will avoid outputting unnecessary print statements, and will skip the evaluation steps

## Development Mode (ground truth annotations required)
```bash
python3 main.py -i=./data/i2b2_notes/ -a=./data/i2b2_anno/ -o=./data/i2b2_results/ -f=./configs/ucsf_pipeline_test_map_regex_context.json
```
