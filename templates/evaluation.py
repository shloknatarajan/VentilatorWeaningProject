import glob
import keras
import matplotlib.pyplot as plt
import numpy as np
import time
from keras.layers.core import Dense, Activation, Dropout
from keras.layers.recurrent import LSTM, GRU
from keras.models import Sequential
import keras.backend as K
import wfdb
from sklearn.utils import class_weight
from sklearn.model_selection import train_test_split
from keras.layers import Merge
from keras.layers.convolutional import Conv1D, MaxPooling1D

for model_dir in glob.glob('models/*/'):
	print('model_dir')
	loaded_model = None
	model_json = glob.glob('model_dir'+'*.json')[0]
	with open(model_json, 'r') as json_file:
		loaded_model = model_from_json(json_file.read())
	# load weights into new model
	model_weights = glob.glob('model_dir'+'*.hdf5')[0]
	loaded_model.load_weights(model_weights)
	print("Loaded model from disk")
