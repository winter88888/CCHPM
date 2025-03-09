#initial train
del ..\classifier.joblib
python train.py --input .\data\nomralized_Logtaker_baseline.csv --model ..\classifier.joblib
