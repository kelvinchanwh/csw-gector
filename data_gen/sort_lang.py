import argparse
import json

# This code uses the Compact Language Detection Module:
# https://github.com/bsolomon1124/pycld3
def main():
    # Parse command line args
    args = parse_args()
    # Load map between English language and 2 letter language code
    lang_dict = json.load(open("lang639-1.json"))
    lang_dict = {info["alpha2"]: info["English"] for info in lang_dict}
    # Create a l1 dict
    l1_dict = {}
    # Count noisy sentences we ignore
    noisy = 0
    total = 0

    # Open the file
    with open(args.json_file) as jfile:
        jfile = json.load(jfile)
        # Loop through sent_dicts
        for sent_dict in jfile:
            # Get the L1
            author_l1 = sent_dict["author_l1"]
            # Loop through sents
            for sent in sent_dict["sents"]:
                total += 1
                # Get the languages of the text
                l1 = sent["orig_langs"]["Lang1"]
                l2 = sent["orig_langs"]["Lang2"]
                # Get the non-english
                not_en = [l1, l2]
                not_en.remove("en")
                not_en = not_en[0]
                # Check whether not_en agrees with L1
                if not_en not in lang_dict or lang_dict[not_en] not in author_l1: 
                    noisy += 1
                    continue
                # Create a formatted copy for output
                out_dict = sent_dict.copy()
                for k, v in sent.items(): out_dict[k] = v
                out_dict.pop("sents")
                # Put the language in the l1_dict if it's not there
                if not_en in l1_dict: l1_dict[not_en].append(out_dict)
                else: l1_dict[not_en] = [out_dict]
    # Loop through l1s
    for l1 in l1_dict:
        # Open a new file for this l1
        with open("l1s_cor/"+l1+".json", "w") as out:
            json.dump(l1_dict[l1], out, ensure_ascii=False, indent=4)
    print("Ignored: "+str(noisy)+"/"+str(total)+" ("+str(round(noisy/total*100, 2))+"%)")

# Parse command line arguments
def parse_args():
    # Define and parse program input
    parser = argparse.ArgumentParser()
    parser.add_argument("json_file", help="Processed json file")
    args = parser.parse_args()
    return args

if __name__ == "__main__":
    main()