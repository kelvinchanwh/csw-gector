import argparse
import errant
import json

# This code uses the Compact Language Detection Module:
# https://github.com/bsolomon1124/pycld3
def main():
    # Parse command line args
    args = parse_args()
    # Load errant
    annotator = errant.load("en")

    # Open the json file and output m2 file
    with open(args.json_file) as jfile, open(args.out, "w") as out:
        jfile = json.load(jfile)
        # Loop through sent_dicts
        for sent_dict in jfile:
            # Get the orig sent
            orig = sent_dict["orig_sent"]
            # Parse with errant
            orig = annotator.parse(orig, tokenise=True)
            # WRite the orig tokens to output m2
            out.write(" ".join(["S"]+[tok.text for tok in orig])+"\n")
            # Loop through cor sents
            for i, cor in enumerate(sent_dict["cor_sents"]):
                # Parse with errant
                cor = annotator.parse(cor, tokenise=True)
                # Get the edits
                edits = annotator.annotate(orig, cor)
                # Write the editas as m2
                for e in edits:
                    out.write(e.to_m2(i)+"\n")
            # Newline after each block
            out.write("\n")

# Parse command line arguments
def parse_args():
    # Define and parse program input
    parser = argparse.ArgumentParser()
    parser.add_argument("json_file", help="Processed json file")
    parser.add_argument("-out", help="Output m2 file", required=True)
    args = parser.parse_args()
    return args

if __name__ == "__main__":
    main()