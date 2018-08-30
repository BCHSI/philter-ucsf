# Running Philter from the command line

## Production Mode (no ground truth annotations required)
Production mode will avoid outputting unnecessary print statements, and will skip the evaluation steps. Use the following command to run a single job:
```bash
python3 main.py -i "./data/i2b2_notes_test/" -o "./data/i2b2_results_test/" -f=./configs/ucsf_pipeline_test_map_regex_context.json --prod=True
```

To run Philter multiple jobs simultaneously, all input and output notes pertaining to a single job must be located in a separate directory. For example, if you wanted to Philter 1000 notes simultaneously on two processes, the split file directories would be:

1. ./data/batch1/input_notes/
2. ./data/batch2/input_notes/

and the output directories would be:

1. ./data/batch1/philtered_notes/
2. ./data/batch2/philtered_notes/

In this example, the following two commands would be used to start each job:
```bash
nohup python3 main.py -i "./data/batch1/input_notes/" -o "./data/batch1/philtered_notes/" -f=./configs/ucsf_pipeline_test_map_regex_context.json >  2>&1 &

```
```bash
nohup python3 main.py -i "./data/batch2/input_notes/" -o "./data/batch2/philtered_notes/" -f=./configs/ucsf_pipeline_test_map_regex_context.json >  2>&1 &

```


## Evaluation Mode (ground truth annotations required)
```bash
python3 main.py -i=./data/i2b2_notes/ -a=./data/i2b2_anno/ -o=./data/i2b2_results/ -f=./configs/ucsf_pipeline_test_map_regex_context.json
```

