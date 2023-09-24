from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch
import os
# os.environ['TRANSFORMERS_CACHE'] = os.getcwd()+'/dags/.cache/'
import sys
sys.path.insert(0, os.getcwd())

class SentimentAnalyser:
    def __init__(self, model_name):
        self.modelname = model_name
        self.tokenizer = AutoTokenizer.from_pretrained(model_name, 
                                                       cache_dir=os.getcwd()+'/dags/scheduled_dags/.cache/'
                                                       )
        self.model = AutoModelForSequenceClassification.from_pretrained(model_name,
                                                                        cache_dir=os.getcwd()+'/dags/scheduled_dags/.cache/'
                                                                        )

    def sentiment_score(self, chat):
        tokens = self.tokenizer.encode(chat, return_tensors='pt')
        result = self.model(tokens)
        if self.modelname == 'cardiffnlp/twitter-roberta-base-sentiment':
            return int(torch.argmax(result.logits))
        elif self.modelname == "nlptown/bert-base-multilingual-uncased-sentiment":
            return int(torch.argmax(result.logits)) + 1