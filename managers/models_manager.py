from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch
import string
import os
# os.environ['TRANSFORMERS_CACHE'] = os.getcwd()+'/dags/.cache/'
import sys
sys.path.insert(0, os.getcwd())

class SentimentAnalyser:
    def __init__(self, model_name):
        self.modelname = model_name
        self.tokenizer = AutoTokenizer.from_pretrained(
            model_name, 
            cache_dir=os.getcwd()+'/dags/scheduled_dags/.cache/',
            # force_download=True,
            # resume_download=False
        )
        self.model = AutoModelForSequenceClassification.from_pretrained(
            model_name,
            cache_dir=os.getcwd()+'/dags/scheduled_dags/.cache/',
            # force_download=True,
            # resume_download=False
        )

    def sentiment_score(self, chat):

        def exclude_ascii_art(chat):
            printable = set(string.printable)
            parsed_string = ''.join(filter(lambda x: x in printable, chat))
            return parsed_string

        try: 
            chat = exclude_ascii_art(chat)
        except Exception as e:
            print(f"{chat}: ", e)


        if len(chat) > 400:
            print('token exceed the limit of 512: ', chat)
            return 1
        else:
            pass

        try:
            tokens = self.tokenizer.encode(chat, return_tensors='pt')
        except Exception as e:
            print(f"{chat}: ", e)
            return 1

        try:             
            result = self.model(tokens)
        except Exception as e:
            print(f"{chat}: ", e)
            return 1


        if self.modelname == 'cardiffnlp/twitter-roberta-base-sentiment':
            return int(torch.argmax(result.logits))
        elif self.modelname == "nlptown/bert-base-multilingual-uncased-sentiment":
            return int(torch.argmax(result.logits)) + 1