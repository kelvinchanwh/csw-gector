import numpy as np
import os
import sys
import dect_lang

BASE_DIR = os.getcwd().split('utils')[0]
DATA_DIR = os.path.join(BASE_DIR, 'data')

def count_cs(tag3d, langtags, langind=1):
	'''
	Fraction of CS terms in an utterance.
	'''
	counter = 0
	for i in tag3d:
		if i[langind] != langtags[1] and i[langind] in langtags:
			counter += 1
	return counter/len(tag3d)


def stats_cs(tags3d, langtags, langind=1):
	'''
	Average of count_cs over all the utterances present.
	'''
	sp_avg, sp_std = 0, 0
	sp_list = []
	for tag in tags3d:
		sp_list.append(count_cs(tag, langtags, langind))

	sp_avg = np.mean(sp_list)
	sp_std = np.std(sp_list)

	return sp_avg, sp_std

def main(rcm_corpus, langtags, verbose=False):
	rcm_corpus = os.path.join(DATA_DIR, rcm_corpus)

	with open(rcm_corpus, "r") as f:
		data = f.readlines()

	processed_data = []
	for d in data:
		t = d.split()
		tmp = []

		for x in t:
			tmp.append(x.split('/'))
		
		processed_data.append(tmp)

	sp_avg, sp_std = stats_cs(processed_data, langtags)
	if verbose:
		print("Mean and Standard Deviation of RCM Corpus:", (sp_avg, sp_std))

	return sp_avg, sp_std

if __name__ == "__main__":
	if len(sys.argv) != 4:
		print("[USAGE] %s input_rcm_file lang1_tag lang2_tag" % sys.argv[0])
		sys.exit()

	input_rcm_file = sys.argv[1]
	lang1_tag = sys.argv[2].upper() 
	lang2_tag = sys.argv[3].upper()

	with open(input_rcm_file, "r") as input_f:
		sentences = input_f.read().split("\n")
		sentences = [dect_lang.tokenize(sent, lang2_tag).replace("\u3000", " ") for sent in sentences]
		cs_list = [dect_lang.create_cslang_list(sentence.split(" ")) for sentence in sentences]
		count_list = [sum(sentence)/len(sentence) for sentence in cs_list]
		sp_avg = np.mean(count_list)
		sp_std = np.std(count_list)
		print("Mean and Standard Deviation of RCM Corpus:", (sp_avg, sp_std))