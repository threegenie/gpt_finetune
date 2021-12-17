import os
import torch
from gluonnlp.data import SentencepieceTokenizer
from kogpt2.model.sample import sample_sequence
from kogpt2.utils import get_tokenizer
from kogpt2.utils import download, tokenizer
from kogpt2.model.torch_gpt2 import GPT2Config, GPT2LMHeadModel
import gluonnlp

def main(temperature = 0.7, top_p = 0.8, top_k = 40, tmp_sent = "", text_size = 100, loops = -1,
	load_path = './checkpoint/KoGPT2_checkpoint_long.tar', ctx= 'cuda',cachedir='~/kogpt2/', samples="gdrive/drive/My Drive/KoGPT2-FineTuning/samples"):

	pytorch_kogpt2 = {
		'url': 'https://kobert.blob.core.windows.net/models/kogpt2/pytorch/pytorch_kogpt2_676e9bcfa7.params',
		'fname': 'pytorch_kogpt2_676e9bcfa7.params',
		'chksum': '676e9bcfa7'
	}

	kogpt2_config = {
		"initializer_range": 0.02,
		"layer_norm_epsilon": 1e-05,
		"n_ctx": 1024,
		"n_embd": 768,
		"n_head": 12,
		"n_layer": 12,
		"n_positions": 1024,
		"vocab_size": 50000
	}

	model_info = pytorch_kogpt2
	model_path = download(model_info['url'],
						  model_info['fname'],
						  model_info['chksum'],
						  cachedir=cachedir)

	vocab_info = tokenizer
	vocab_path = download(vocab_info['url'],
						  vocab_info['fname'],
						  vocab_info['chksum'],
						  cachedir=cachedir)

	device = torch.device(ctx)

	# 저장한 Checkpoint 불러오기
	checkpoint = torch.load(load_path, map_location=device)

	# KoGPT-2 언어 모델 학습을 위한 GPT2LMHeadModel 선언
	kogpt2model = GPT2LMHeadModel(config=GPT2Config.from_dict(kogpt2_config))
	kogpt2model.load_state_dict(checkpoint['model_state_dict'])

	kogpt2model.eval()
	vocab_b_obj = gluonnlp.vocab.BERTVocab.from_sentencepiece(vocab_path,
															  mask_token=None,
															  sep_token=None,
															  cls_token=None,
															  unknown_token='<unk>',
															  padding_token='<pad>',
															  bos_token='<s>',
															  eos_token='</s>')

	tok_path = get_tokenizer()
	model, vocab = kogpt2model, vocab_b_obj
	tok = SentencepieceTokenizer(tok_path)
	num = 0

	if loops != -1:
		num = 1

	while 1:
		sent =''
		if tmp_sent == "":
			tmp_sent = input('input : ')
		sent = sent+tmp_sent

		toked = tok(sent)

		if len(toked) > 1022:
			break

		sent = sample_sequence(model, tok, vocab, sent, text_size, temperature, top_p, top_k)
		sent = sent.replace("<unused0>", "\n")
		print(sent)

		now = [int(n) for n in os.listdir(samples)]
		now = max(now)
		f = open(samples + str(now + 1), 'w', encoding="utf-8")
		f.write(sent)
		f.close()

		if num:
			num += 1
			if num >= loops:
				print("good")
				return