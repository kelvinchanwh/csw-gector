import numpy as np
import os
import sys
import dect_lang

BASE_DIR = os.getcwd().split('utils')[0]
DATA_DIR = os.path.join(BASE_DIR, 'data')

def switchpoint_u(tag3d, langtags, langind=1):
    '''
    Number of times the tag is switched in an utterance.
    '''
    context = None
    counter = -1
    for i in tag3d:
        if i[langind] != context and i[langind] in langtags:
            counter += 1
            context = i[langind]
    return counter


def switchpoint_c(tags3d, langtags, langind=1):
    '''
    Average of switchpoint_u over all the utterances present.
    '''
    sp_avg, sp_std = 0, 0
    sp_list = []
    for tag in tags3d:
        sp_list.append(switchpoint_u(tag, langtags, langind))

    sp_avg = np.mean(sp_list)
    sp_std = np.std(sp_list)

    return sp_avg, sp_std

def main(rcm_corpus, langtags):
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

    sp_avg, sp_std = switchpoint_c(processed_data, langtags)
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
		count_list = [[[token, int(cs_token)] for token, cs_token in zip(sentence.split(), cs)] for sentence, cs in zip(sentences, cs_list) ]
		sp_avg, sp_std = switchpoint_c(count_list, [0, 1])
		print("Mean and Standard Deviation of RCM Corpus:", (sp_avg, sp_std))

# >>> spf_std_mean.main("rcm_lang_tagged_zh.txt", ["EN", "ZH"])
# Mean and Standard Deviation of RCM Corpus: (2.6386138613861387, 1.7891571275700173)
# (2.6386138613861387, 1.7891571275700173)
# >>> spf_std_mean.main("rcm_lang_tagged_ja.txt", ["EN", "JA"])
# Mean and Standard Deviation of RCM Corpus: (2.9234768143065084, 2.227535177936978)
# (2.9234768143065084, 2.227535177936978)
# >>> spf_std_mean.main("rcm_lang_tagged_ko.txt", ["EN", "KO"])
# Mean and Standard Deviation of RCM Corpus: (2.3856209150326797, 1.5319012195604083)
# (2.3856209150326797, 1.5319012195604083)