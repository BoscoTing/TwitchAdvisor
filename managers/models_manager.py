from transformers import AutoTokenizer, AutoModelForSequenceClassification
from datetime import datetime
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import torch
import sys
import os
sys.path.insert(0, os.getcwd())

class SentimentAnalyser:
    def __init__(self, model_name):
        self.modelname = model_name
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModelForSequenceClassification.from_pretrained(model_name)

    def analyse_sentiment(self, chat):
        tokens = self.tokenizer.encode(chat, return_tensors='pt')
        result = self.model(tokens)
        if self.modelname == 'cardiffnlp/twitter-roberta-base-sentiment':
            return int(torch.argmax(result.logits))
        elif self.modelname == "nlptown/bert-base-multilingual-uncased-sentiment":
            return int(torch.argmax(result.logits)) + 1