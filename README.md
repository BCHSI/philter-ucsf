# Running Philter

## Production mode
```bash
python3 main.py -i "./data/i2b2_notes_test/" -o "./data/i2b2_results_test/" --prod=True
```
Notes - this production mode will avoid outputting unnecessary print statements, and will skip the evaluation steps

## Running from command line
```bash
python3 main.py -i=./data/i2b2_notes/ -a=./data/i2b2_anno/ -o=./data/i2b2_results/ -f=./configs/example.json
```


### Run a Stanford NER Taggger  (Warning, very slow)
#### Remove 'PERSON' configs/remove_person_tags.json
```json
python3 main.py -i=./data/i2b2_notes/ -a=./data/i2b2_anno/ -o=./data/i2b2_results/ -f=./configs/test_ner.json
```


### Run a Whitelist
#### Remove 'PERSON' configs/remove_person_tags.json
```json
python3 main.py -i=./data/i2b2_notes/ -a=./data/i2b2_anno/ -o=./data/i2b2_results/ -f=./configs/test_whitelist.json
```


### Run a Blacklist
#### Remove 'PERSON' configs/remove_person_tags.json
```json
python3 main.py -i=./data/i2b2_notes/ -a=./data/i2b2_anno/ -o=./data/i2b2_results/ -f=./configs/test_blacklist.json
```


### Run a Regex
#### Remove 'PERSON' configs/remove_person_tags.json
```json
python3 main.py -i=./data/i2b2_notes/ -a=./data/i2b2_anno/ -o=./data/i2b2_results/ -f=./configs/just_digits.json
```

### Run Multiple patterns
#### Remove PHI configs/example.json
```json
python3 main.py -i=./data/i2b2_notes/ -a=./data/i2b2_anno/ -o=./data/i2b2_results/ -f=./configs/example.json
```
