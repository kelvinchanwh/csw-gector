import argparse
import json

import errant
import spacy

# Create the parser
parser = argparse.ArgumentParser(description='Process m2 and json files.')
parser.add_argument('input_json_file', type=str, help='The json file to process')
parser.add_argument('input_m2_file', type=str, help='The m2 file with edits to input')
parser.add_argument('output_m2_file', type=str, help='The m2 file to output')

args = parser.parse_args()

nlp = spacy.load('en_core_web_sm') # Or en_core_web_X for other spacy models
annotator = errant.load('en', nlp)

# Load the JSON file
with open(args.input_json_file, 'r') as f:
    data = json.load(f)

# Create a dictionary mapping original sentences to journal ids
# journal_ids = {" ".join([token.text for token in nlp(item['orig_sent'])]):item['journal_id'] for item in data}
journal_ids = {item['journal_id']:" ".join([token.text for token in nlp(item['orig_sent'])]) for item in data}

# Open the m2 file
with open(args.input_m2_file, 'r') as f:
    lines = f.readlines()

# Iterate over the lines in the m2 file
for i in range(len(lines)):
    # If the line starts with "S ", replace it with the corresponding journal id
    if lines[i].startswith('S '):
        sentence = lines[i][2:].strip()  # Remove the "S " and any trailing whitespace
        if sentence in journal_ids:
            lines[i] = 'S ' + str(journal_ids[sentence]) + '\n'
        else:
            print("Sentence not found in journal_ids:", sentence)

# Write the modified lines back to the m2 file
with open(args.output_m2_file, 'w') as f:
    f.writelines(lines)