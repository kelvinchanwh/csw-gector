import os
import sys
import pandas as pd
import numpy as np
import copy
import subprocess
from dect_lang import *

if __name__ == "__main__":
	if len(sys.argv) != 4:
		print("[USAGE] %s input_test_src_file input_test_tgt_file splits" % sys.argv[0])
		sys.exit()

	input_test_src_file = sys.argv[1]
	input_test_tgt_file = sys.argv[2]
	splits = int(sys.argv[3])

	with open(input_test_src_file, "r") as input_src_f, open(input_test_tgt_file, "r") as input_tgt_f:
		sentences_src = input_src_f.read().split("\n")
		sentences_tgt = input_tgt_f.read().split("\n")
		assert len(sentences_src) == len(sentences_tgt), "Source and Target file have different lengths"

		sentences = [tokenize(sent, "EN").replace("\u3000", " ") for sent in copy.deepcopy(sentences_tgt)]
		cs_list = [create_cslang_list(sentence.split(" ")) for sentence in sentences]
		ratio = [sum(sent)/len(sent) for sent in cs_list]
	
	buckets = [0.50 + i/(2*splits) for i in range(splits + 1)]
	labels = ["%.2f"%i for i in buckets[:-1]]

	df = pd.DataFrame()
	df["src"] = sentences_src
	df["tgt"] = sentences_tgt
	df["ratio"] = ratio
	df["bucket"] = pd.cut(df.ratio, bins=buckets, precision=2, labels=labels,)
	
	df.to_csv(os.path.join("/".join(input_test_src_file.split("/")[:-1]), "stats_"+ ".".join(input_test_src_file.split("/")[-1].split(".")[:-2]) + ".tsv"), sep="\t")
	for label in labels:
		if len(df[df["bucket"]==label]["src"].values.tolist()) > 0:
			orig = os.path.join("/".join(input_test_src_file.split("/")[:-1]), str(label)+"_"+input_test_src_file.split("/")[-1])
			cor = os.path.join("/".join(input_test_tgt_file.split("/")[:-1]), str(label)+"_"+input_test_tgt_file.split("/")[-1])
			out = os.path.join("/".join(input_test_tgt_file.split("/")[:-1]), str(label)+"_"+ ".".join(input_test_tgt_file.split("/")[-1].split(".")[:-2]) + ".m2")
		
			with open(orig, "w+") as output_src_f, open(cor, "w+") as output_tgt_f:
				src_list = df[df["bucket"]==label]["src"].values.tolist()
				tgt_list = df[df["bucket"]==label]["tgt"].values.tolist()

				for src_line, tgt_line in zip(src_list, tgt_list):
					output_src_f.write(f"{src_line}\n")
					output_tgt_f.write(f"{tgt_line}\n")
			print (f"Processing {out}")
			os.system(f"source errant_env/bin/activate && errant_parallel -orig {orig} -cor {cor} -out {out}")
			
			
					

