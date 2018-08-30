# Running Philter from the command line

## Production Mode (no ground truth annotations required)
Production mode will avoid outputting unnecessary print statements, and will skip the evaluation steps. Use the following command to run a single job:
```bash
python3 main.py -i "./data/i2b2_notes_test/" -o "./data/i2b2_results_test/" -f=./configs/ucsf_pipeline_test_map_regex_context.json --prod=True
```

To run Philter multiple jobs simultaneously, all input and output notes pertaining to a single job must be located in separate directories. For example, if you wanted to Philter 1000 notes simultaneously on two processes, the two input directories might look like:

1. ./data/batch1/500_input_notes_batch1/
2. ./data/batch2/500_input_notes_batch2/

and the output directories would be:

1. ./data/batch1/philtered_notes_batch1/
2. ./data/batch2/philtered_notes_batch2/

In this example, the following two commands would be used to start each job:
```bash
nohup python3 main.py -i "./data/batch1/500_input_notes/" -o "./data/batch1/philtered_notes/" -f=./configs/ucsf_pipeline_test_map_regex_context.json --prod=True > ./data/batch1/batch1_terminal_out.txt 2>&1 &

```
```bash
nohup python3 main.py -i "./data/batch2/500_input_notes/" -o "./data/batch2/philtered_notes/" -f=./configs/ucsf_pipeline_test_map_regex_context.json --prod=True > ./data/batch2/batch2_terminal_out.txt 2>&1 &

```


## Evaluation Mode (ground truth annotations required)
```bash
python3 main.py -i=./data/i2b2_notes/ -a=./data/i2b2_anno/ -o=./data/i2b2_results/ -f=./configs/ucsf_pipeline_test_map_regex_context.json
```

