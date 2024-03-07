import argparse
import cld3
import json
import re
from rapidfuzz import fuzz

# This code uses the Compact Language Detection Module:
# https://github.com/bsolomon1124/pycld3
def main():
    # Parse command line args
    args = parse_args()
    # Output file
    out_text = open(args.out, "w", encoding="utf-8")
    # Strings to remove
    tags = ["[/BLUE]", "[/RED]", "[/f-blue]", "[f-blue]", "[/f-bold]", "[f-bold]", "[/f-red]", "[f-red]"]
    # Save list of dicts here
    out_list = []

    # Open the JSON file
    with open(args.lang8) as lang8, open(args.out, "w") as out:
        # Loop through lang8 lines
        for line in lang8:
            line = json.loads(line, strict=False)
            # We only want English L2
            if "English" not in line[2]: continue
            # Output json dict here
            out_dict = {}
            # Save some metadata
            out_dict["journal_id"] = line[0]
            out_dict["author_l1"] = line[3]
            out_dict["author_l2"] = line[2]
            out_dict["sents"] = []
            # Loop through learner sents
            for i, sent in enumerate(line[4]):
                # Ignore empty sentences
                if not sent: continue
                # Clean up the original string
                orig = clean(sent, tags)
                # Get the languages of the original string
                orig_langs = cld3.get_frequent_languages(orig, num_langs=2)
                # Only keep codeswitching with English
                if len(orig_langs) == 2 and (orig_langs[0].language == "en" or orig_langs[1].language == "en"):
                    # Save valid correct strings here
                    cors = []
                    # Loop through corrected strings (if any)
                    for cor in line[5][i]:
                        # Ignore empty sentences
                        if not cor: continue
                        # Clean the string
                        cor = clean(cor, tags)
                        # Ignore sentences that have very different lengths (5 or more token)
                        if abs(len(orig.split())-len(cor.split())) >= 5: 
                            # print("Diff Len")
                            # print (orig)
                            # print(cor)
                            continue
                        # Ignore sentences where orig is the start of cor or vice versa (usually a comment)
                        if cor.startswith(orig) or orig.startswith(cor): 
                            print("Orig Start")
                            print (orig)
                            print(cor)
                            continue
                        # Get the languages of the corrected string
                        cor_langs = cld3.get_frequent_languages(cor, num_langs=2)
                        # Only keep sentences where orig and cor langs are the same
                        if len(cor_langs) == 2 and {orig_langs[0].language, orig_langs[1].language} == {cor_langs[0].language, cor_langs[1].language}:
                            # Run a last filter to ignore sentences with dissimilar character ratios
                            if fuzz.ratio(orig, cor) < 60: continue
                            # Save the remaining corrected strings
                            cors.append(cor)
                    # If there are no cors, ignore the sentence
                    if not cors: continue
                    # Create a sent dict
                    sent_dict = {}
                    # Save the orig text
                    sent_dict["orig_sent"] = orig
                    # Save the cor sents
                    sent_dict["cor_sents"] = cors
                    # Save the orig_langs information
                    predict_dict = {"Lang1": orig_langs[0].language, 
                                    "Lang1_Prob": round(orig_langs[0].probability, 2), 
                                    "Lang1_Ratio": round(orig_langs[0].proportion, 2),
                                    "Lang2": orig_langs[1].language, 
                                    "Lang2_Prob": round(orig_langs[1].probability, 2), 
                                    "Lang2_Ratio": round(orig_langs[1].proportion, 2)}
                    # Save in the sent dict
                    sent_dict["orig_langs"] = predict_dict
                    # Save sent_dict in out_dict
                    out_dict["sents"].append(sent_dict)
            # If sents is not empty, save the dict in out_list
            if out_dict["sents"]: out_list.append(out_dict)
        # Save the out_list
        json.dump(out_list, out, ensure_ascii=False, indent=4)

# Parse command line arguments
def parse_args():
    # Define and parse program input
    parser = argparse.ArgumentParser()
    parser.add_argument("lang8", help="Multilingual lang8 file (eg. lang-8-20111007-L1-v2.dat)")
    parser.add_argument("-out", help="Output JSON file path.", required=True)
    args = parser.parse_args()
    return args
    
# Remove the markup
def clean(text, tags):
    # Delete everything between sline
    text = re.sub("\[sline\].*\[/sline\]", "", text)
    # Loop through tags and replace
    for tag in tags:
        text = text.replace(tag, "")
    # Remove excess whitespace
    text = " ".join(text.split())
    return text

if __name__ == "__main__":
    main()