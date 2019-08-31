from preprocess import preproces
import json

orgin_path = "./dataset/hot_app_pp.csv"

# data = preproces.CalDataLabel(orgin_path).cal_label("./data_status/")
data = preproces.CalDataLabel(orgin_path).summary()
#
#
# preproces.CalDataLabel(orgin_path).extract_train_data("./dataset/")
