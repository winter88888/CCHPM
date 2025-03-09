# File: text_ai/predict.py
import joblib
from sklearn.feature_extraction.text import HashingVectorizer
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer


class TextClassifier:
    def __init__(self, model_path):
        self.model = joblib.load(model_path)

    def predict(self, text):
        try:
            result=self.model.predict([text])
            return result[0]
        except Exception as e:
            print(f"Prediction error: {str(e)}")
            return "error"


def test_prediction():
    clf = TextClassifier("..\classifier.joblib")
    text_transformer = TfidfVectorizer(
        ngram_range=(1, 2),
        stop_words='english',
        max_features=5000
    )


    samples = [
        "larc still doing cr",
        "got a stack of dots at all?",
        "zoned wiz - LOGS"
    ]
    for text in samples:
        print(f"'{text}' => {clf.predict(text)}")
    # 查看特征提取效果



if __name__ == "__main__":
    test_prediction()
