# File: text_ai/train.py
import argparse
import pandas as pd
from sklearn.feature_extraction.text import HashingVectorizer
from sklearn.linear_model import SGDClassifier
from sklearn.pipeline import Pipeline
import joblib
import os


def load_data(file_path):
    df = pd.read_csv(file_path)
    return df['text'].tolist(), df['label'].tolist()


def train_model(args):
    # 初始化或加载已有模型
    if os.path.exists(args.model):
        model = joblib.load(args.model)
        print(f"Loaded existing model from {args.model}")
    else:
        model = Pipeline([
            ('vectorizer', HashingVectorizer(
                n_features=2 ** 16,  # 固定特征维度
                ngram_range=(1, 2))),
             ('clf', SGDClassifier(
             loss='log_loss',
             warm_start=True,
             random_state=42))
        ])
        print("Initialized new model")

    # 加载数据
    X, y = load_data(args.input)

    # 训练模式判断
    if hasattr(model.named_steps['clf'], 'coef_'):
        # 使用Pipeline的vectorizer转换数据
        X_transformed = model.named_steps['vectorizer'].transform(X)
        model.named_steps['clf'].partial_fit(X_transformed, y)
        print("Incremental training completed")
    else:
        model.fit(X, y)
        print("Initial training completed")

    # 保存模型
    joblib.dump(model, args.model)
    print(f"Model saved to {args.model}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--input', type=str, required=True, help='Training data file path')
    parser.add_argument('--model', type=str, required=True, help='Model output path')
    args = parser.parse_args()

    train_model(args)