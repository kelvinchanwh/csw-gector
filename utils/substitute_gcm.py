import sys
import benepar
import random
from googletrans import Translator
from tqdm import tqdm
import time
import httpcore
import multiprocessing
import platform
import spf_std_mean, spf_sampling
import frac_std_mean, frac_sampling

def divide_chunks(l, n):
	# looping till length l
	for i in range(0, len(l), n):
		yield l[i:i + n]
	

def retry(func, ex_type=Exception, limit=0, wait_ms=100, wait_increase_ratio=2, logger=None):
	"""
	Retry a function invocation until no exception occurs
	:param func: function to invoke
	:param ex_type: retry only if exception is subclass of this type
	:param limit: maximum number of invocation attempts
	:param wait_ms: initial wait time after each attempt in milliseconds.
	:param wait_increase_ratio: increase wait period by multiplying this value after each attempt.
	:param logger: if not None, retry attempts will be logged to this logging.logger
	:return: result of first successful invocation
	:raises: last invocation exception if attempts exhausted or exception is not an instance of ex_type
	"""
	attempt = 1
	while True:
		try:
			return func
		except Exception as ex:
			if not isinstance(ex, ex_type):
				raise ex
			if 0 < limit <= attempt:
				if logger:
					logger.warning("no more attempts")
				raise ex

			if logger:
				logger.error("failed execution attempt #%d", attempt, exc_info=ex)

			attempt += 1
			if logger:
				logger.info("waiting %d ms before attempt #%d", wait_ms, attempt)
			time.sleep(wait_ms / 1000)
			wait_ms *= wait_increase_ratio


def apply_edit_to_cs(cs_words, cs_list, m2_edits):
	"""
	
	"""
	sid = eid = 0
	prev_sid = prev_eid = -1
	pos = 0
	corrected = list()
	corrected = ['<S>'] + cs_words[:]
	for i in range(len(m2_edits)):
		edit = m2_edits[i]
		sid = int(edit[0][0]) + 1
		eid = int(edit[0][1]) + 1
		error_type = edit[1]
		if error_type == "Um":
			continue
		if sum(cs_list[sid-1:eid]) > 0:
			continue
		for idx in range(sid, eid):
			corrected[idx] = ""
		if sid == eid:
			if sid == 0: continue	# Originally index was -1, indicating no op
			if sid != prev_sid or eid != prev_eid:
				pos = len(corrected[sid-1].split())
			cur_words = corrected[sid-1].split()
			cur_words.insert(pos, edit[2])
			pos += len(edit[2].split())
			corrected[sid-1] = " ".join(cur_words)
		else:
			corrected[sid] = edit[2]
			pos = 0
		prev_sid = sid
		prev_eid = eid
	else:
		target_sentence = [word for word in corrected if word != ""]
		if target_sentence[0].strip() != "<S>":
			if target_sentence[0].startswith("<S> "):
				target_sentence[0] = target_sentence[0][4:]
				return target_sentence
			else:
				print ('Sentence does not start with <S> (' + str(target_sentence) + ')')

		target_sentence = target_sentence[1:]
		return target_sentence

def parse_m2(input_m2_path):
	m2_dict = dict()
	with open(input_m2_path) as input_m2:
		# English Sentence
		for line in input_m2:
			line = line.strip()
			if line.startswith('S'):
				line = line[2:]
				S = "".join(line.split(" "))
				m2_dict[S] = {"corr": line.split(" ")  , "edits":[]}
			elif line.startswith('A'):
				line = line[2:]
				info = line.split("|||")
				info[0] = [int(i) for i in info[0].split(" ")]
				m2_dict[S]["edits"].append(info)
	return m2_dict

def select_least_intersect(phrases, edit_intervals, sent_len):
	def interval_intersection(a, b):
		return max(0, min(a[1], b[1]) - max(a[0], b[0]))
	
	def total_intersection(cs_interval, edit_interval):
		return sum(interval_intersection(cs_interval, other) for other in edit_interval)
	if len(edit_intervals) > 0:
		intersections = [total_intersection((interval[1], interval[2]), edit_intervals) for interval in phrases]
		min_intersection = min(intersections)
		least_intersecting_phrases = [phrases[i] for i in range(len(intersections)) if intersections[i]==min_intersection]
		
		return max(least_intersecting_phrases, key=lambda phrase: phrase[2] - phrase[1])
	else:
		# 15% code-switching ratio based on reference CS
		# >>> frac_std_mean.main("rcm_lang_tagged_zh.txt", ["EN", "ZH"])
		# (0.8458093800319865, 0.13028245915220268)
		# >>> frac_std_mean.main("rcm_lang_tagged_ko.txt", ["EN", "KO"])
		# (0.7961622654916878, 0.16734657894380928)
		# >>> frac_std_mean.main("rcm_lang_tagged_ja.txt", ["EN", "JA"])
		# (0.734999068414355, 0.16464834557312077)
		cs_ratio = sent_len * 0.15
		# Return phrase closest to cs_ratio
		return min(phrases, key = lambda phrase: abs(phrase[2]-phrase[1]-cs_ratio))
	
def sub_cs(sentence, parser, translator, edits=None, reference = None, src_lang="en", tgt_lang="zh-tw", select = 'random-token', verbose = False):
	if "token" in select:
		if select == 'random-token':
			i = list(range(len(sentence)))
			start = random.sample(i, k=random.randint(0, len(sentence)))
			end = [i + 1 for i in start]
			tokens_to_translate = [sentence[i] for i in start]
		elif select == "frac-token" and reference is not None:
			i = list(range(len(sentence)))
			start = random.sample(i, int(reference * len(sentence)))
			end = [i + 1 for i in start]
			tokens_to_translate = [sentence[i] for i in start]
		elif select == "contfrac-token" and reference is not None:
			try:
				frac_len = int(reference * len(sentence))
				frac_len = 1 if frac_len == 0 else frac_len
				i = list(range(len(sentence)-frac_len))
				start = random.sample(i, 1)
				end = [start[0] + frac_len]
				tokens_to_translate = [" ".join(sentence[start[0]:end[0]])]
			except Exception:
				return (sentence, [False]*len(sentence)) 
		else:
			print ("M2 edits much be provided for intersect selection method. Reference corpus must be provided for spf and frac method")
			i = list(range(len(sentence)))
			start = random.sample(i, k=random.randint(0, len(sentence)))
			end = [i + 1 for i in start]
			tokens_to_translate = [sentence[i] for i in start]

		# translate the selected words
		try:
			translation = retry(translator.translate(tokens_to_translate, src=src_lang, dest=tgt_lang), ex_type=httpcore._exceptions.ReadTimeout, limit=10, wait_ms=100, wait_increase_ratio=10, logger=None)
		except httpcore._exceptions.ReadTimeout:
			print ("Timeout Error - Sentence: {}".format(" ".join(sentence)))
			# Return original sentence
			return (sentence, [False]*len(sentence))
		new_sentence = sentence
		
	elif "phrase" in select:
		# parse the sentence using Benepar
		tree = parser.parse(sentence)

		for idx, _ in enumerate(tree.leaves()):
			tree_location = tree.leaf_treeposition(idx)
			non_terminal = tree[tree_location[:-1]]
			non_terminal[0] = non_terminal[0] + "|:::|" + str(idx)

		# create a list of all phrases in the sentence
		phrases = []
		for subtree in tree.subtrees():
			if subtree.label() in ['NP', 'VP', 'PP', 'ADJP', 'ADVP']:
				leaves = subtree.leaves()
				leaf_positions = [int(leaf.split("|:::|")[1]) for leaf in leaves]
				phrase = [leaf.split("|:::|")[0] for leaf in leaves]
				leaf_start, leaf_end = min(leaf_positions), max(leaf_positions)+1
				if leaf_start <= 0 and leaf_end >= len(sentence):
					# Ignore translation of entire sentence
					pass
				else:
					phrases.append((' '.join(phrase), leaf_start, leaf_end))

		if len(phrases)>0:
			if select == 'random-phrase':
				# randomly select a phrase to translate
				phrase_to_translate, start, end = random.choice(phrases)
			elif select == 'intersect-phrase' and (edits is not None):
				edit_spans = [(edit[0][0], edit[0][1]) for edit in edits if edit[0][0]!=-1]
				phrase_to_translate, start, end = select_least_intersect(phrases, edit_spans, len(sentence))
			elif select == 'frac-phrase' and (reference is not None):
				cs_ratio = len(sentence) * reference
				phrase_to_translate, start, end = min(phrases, key = lambda phrase: abs(phrase[2]-phrase[1]-cs_ratio))

			else:
				print ("M2 edits much be provided for intersect selection method. Reference corpus must be provided for spf and frac method")
				phrase_to_translate, start, end = random.choice(phrases)


			sentence = [leaf.split("|:::|")[0] for leaf in tree.leaves()]

			# translate the selected phrase
			try:
				translation = retry(translator.translate(phrase_to_translate, src=src_lang, dest=tgt_lang), ex_type=httpcore._exceptions.ReadTimeout, limit=10, wait_ms=100, wait_increase_ratio=10, logger=None)
			except httpcore._exceptions.ReadTimeout:
				print ("Timeout Error - Sentence: {}".format(" ".join(sentence)))
				# Return original sentence
				return (sentence, [False]*len(sentence))
			translation = [translation]
			start = [start]
			end = [end]
			
		else:
			return (sentence, [False]*len(sentence))
	
	# replace the selected phrase with its translation
	new_sentence = sentence
	cs_list = [False] * len(sentence)
	for translation_i, start_i, end_i in zip(translation, start, end):
		new_sentence = new_sentence[:start_i] + [translation_i.text] + ["<CS_FILL>"]*(end_i-start_i-1) + sentence[end_i:]
		for i in range(start_i, end_i):
			cs_list[i] = True

	if verbose:
		# print the original and translated sentences, and the span
		print(f"Original sentence: {sentence}")
		print(f"Translated sentence: {new_sentence}")
		print(f"Translated span: ({start}, {end})")

	return (new_sentence, cs_list)
	
def main(args):
	try:
		pid = args[0]
		in_m2 = args[1]
		input_path = args[2]
		src_lang = args[3]
		tgt_lang = args[4]
		selection = args[5]
		reference = args[6]
		with open(input_path + ".p" + str(pid) + ".src", "w+") as src_cache, open(input_path + ".p" + str(pid) + ".tgt", "w+") as tgt_cache:
			# download and load the Benepar model
			# benepar.download('benepar_en3')
			parser = benepar.Parser('benepar_en3')

			# create a translator object
			translator = Translator()
			output = list()
			tqdm_text = "Batch #" + "{}".format(pid).zfill(3)
			for sentence in in_m2: # tqdm(in_m2, desc=tqdm_text, position=pid+1):
				try:
					if len(sentence["corr"]) > 100:
						# Sentence too long, may cause issues with parser
						# Split sentences
						# TODO: Implement intersection for split sentences
						cs_words = []
						cs_list = []
						current_words = []
						current_list = []
						select = "random-phrase" if "phrase" in selection else "random-token"
						for token in sentence["corr"]:
							current_words.append(token)
							if token == ".":
								# Selection method will default to random-phrase to avoid needing to pass in m2
								current_words, current_list = sub_cs(current_words, parser, translator, src_lang=src_lang, tgt_lang=tgt_lang, select = select)
								cs_words += current_words
								cs_list += current_list
								current_words = []
								current_list = []
						if current_words:
							current_words, current_list = sub_cs(current_words, parser, translator, src_lang=src_lang, tgt_lang=tgt_lang, select = select)
							cs_words += current_words
							cs_list += current_list
					else:
						cs_words, cs_list = sub_cs(sentence["corr"], parser, translator, edits=sentence["edits"], reference=reference, src_lang=src_lang, tgt_lang=tgt_lang, select=selection)
					
					if max([m2_edit[0][1] for m2_edit in sentence["edits"]]) <= len(cs_list):
						incorr = apply_edit_to_cs(cs_words, cs_list, sentence["edits"])

						corr = [i for i in cs_words if i != "<CS_FILL>"]
						incorr = [i for i in incorr if i != "<CS_FILL>"]

						corr = " ".join(corr)
						incorr = " ".join(incorr)

						output.append((incorr, corr))
						src_cache.write(incorr + '\n')
						tgt_cache.write(corr + '\n')
					else:
						print ("Sentence is shorter than m2 edit")
				except Exception as e:
					print (e)
					print (len(sentence["corr"]))
					print ("ERROR processing sentence: {}".format(sentence))
		return output
	except Exception as e:
		print (e)

if __name__ == "__main__":
	if len(sys.argv) < 7:
		print("[USAGE] %s input_inv_m2_file output_cs_incorr output_cs_corr src_lang tgt_lang select" % sys.argv[0])
		sys.exit()

	# define a sentence to parse and translate
	input_path = sys.argv[1]
	output_cs_incorr_path = sys.argv[2]
	output_cs_corr_path = sys.argv[3]
	src_lang = sys.argv[4]
	tgt_lang = sys.argv[5]
	selection = sys.argv[6]
	reference = None
	if "spf" in selection or "frac" in selection:
		if len(sys.argv) != 8:
			print("[USAGE] %s input_inv_m2_file output_cs_incorr output_cs_corr src_lang tgt_lang select reference_file" % sys.argv[0])
			sys.exit()
		reference = sys.argv[7]
		if "frac" in selection:
			langtags = [tgt_lang.upper()[:2], src_lang.upper()[:2]]
			reference = float(frac_std_mean.main(reference, langtags, verbose=True)[0])
		elif "spf" in selection:
			langtags = [tgt_lang.upper()[:2], src_lang.upper()[:2]]
			reference = float(spf_std_mean.main(reference, langtags, verbose=True)[0])

	if platform.system() == "Darwin":
		multiprocessing.set_start_method('spawn')

	with open(output_cs_incorr_path, "w+") as output_cs_incorr, open(output_cs_corr_path, "w+") as output_cs_corr:
		in_m2  = parse_m2(input_path)
		cpu_count = multiprocessing.cpu_count()
		chunks = list(divide_chunks(list(in_m2.values()), int((len(in_m2)/cpu_count)+1)))
		print ("Total {} Chunks".format(len(chunks)))
		with multiprocessing.Pool(processes=cpu_count, initargs=(multiprocessing.RLock(),), initializer=tqdm.set_lock) as pool:
			# Pool(processes=num_processes, initargs=(RLock(),), initializer=tqdm.set_lock)
			results = pool.map(main, [(i, n, input_path, src_lang, tgt_lang, selection, reference) for i, n in enumerate(chunks)])
		for result in results:
			for ret in result:
				output_cs_incorr.write(ret[0] + '\n')
				output_cs_corr.write(ret[1] + '\n')
