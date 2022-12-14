import pandas as pd
import numpy as np
import tensorflow
from sklearn.model_selection import train_test_split
from keras.models import Sequential
from keras.optimizers import Adam
from matplotlib import pyplot as plt
from keras.callbacks import ModelCheckpoint
from keras.layers import Lambda, Conv2D, MaxPooling2D, Dropout, Dense, Flatten, Cropping2D
from utils import INPUT_SHAPE, balanceData, batch_generator
import argparse
import os

np.random.seed(0)

print("Num GPUs Available: ", len(tensorflow.config.list_physical_devices('GPU')))

def load_data(args):
    """
    Load training data and split it into training and validation set
    """
    columns = ['center', 'left', 'right', 'steering', 'throttle', 'brake', 'speed']
    data_df = pd.read_csv(os.path.join(args.data_dir, 'driving_log.csv'), names=columns)

    # Before starting anything, we need to redundant data
    data_df = balanceData(data_df, display=False)

    # With the data that we have, we get center, left and right
    X = data_df[['center', 'left', 'right']].values
    y = data_df['steering'].values
    
    # in here we make 20% for testing and 80% for training
    X_train, X_valid, y_train, y_valid = train_test_split(X, y, test_size=args.test_size, random_state=0)

    return X_train, X_valid, y_train, y_valid


def build_model(args):
    """
    Modified NVIDIA model
    """

    model = Sequential()
    # We need Cropping to reduce the size of input but keep the focus point
    #  used for cropping
    #  75px from top to bottom
    # 25px from bottom to top
    model.add(Cropping2D(cropping=((75, 25), (10, 10)), input_shape=INPUT_SHAPE))

    model.add(Lambda(lambda x: x/127.5-1.0, input_shape=INPUT_SHAPE))
    model.add(Conv2D(24, (3, 3), (2, 2), activation='elu'))
    
    # We need max pool after each hidden layer
    model.add(MaxPooling2D(pool_size=(2, 2)))

    model.add(Conv2D(36, (3, 3), (2, 2), activation='elu'))
    model.add(MaxPooling2D(pool_size=(2, 2)))
    
    model.add(Flatten())
    model.add(Dense(1024, activation='elu'))

    model.add(Dropout(args.keep_prob))

    model.add(Dense(128, activation='elu'))
    model.add(Dense(50, activation='elu'))
    model.add(Dense(1))
    model.summary()

    return model


def train_model(model, args, X_train, X_valid, y_train, y_valid):
    """
    Train the model
    """
    # Depend on the needed, here we use MSE and learning rage = 0.0001
    model.compile(loss='mean_squared_error', optimizer=Adam(learning_rate=args.learning_rate))

    checkpoint = ModelCheckpoint('model.h5',
                                    monitor='val_loss',
                                    verbose=0,
                                    save_best_only=args.save_best_only,
                                    mode='auto')
    
    # We using history to capture the loss data of training and testing mode
    history = model.fit(batch_generator(args.data_dir, X_train, y_train, args.batch_size, True), steps_per_epoch=args.samples_per_epoch, epochs=args.nb_epoch, 
                validation_data=batch_generator(args.data_dir, X_valid, y_valid, args.batch_size, True),callbacks=[checkpoint], validation_steps=args.samples_per_epoch, verbose=1)
    
    # We gonna save the model
    model.save('model.h5')

def s2b(s):
    """
    Converts a string to boolean value
    """
    s = s.lower()
    return s == 'true' or s == 'yes' or s == 'y' or s == '1'


def main():
    """
    Load train/validation data set and train the model
    """
    parser = argparse.ArgumentParser(description='Behavioral Cloning Training Program')
    parser.add_argument('-d', help='data directory',        dest='data_dir',          type=str,   default='data')
    parser.add_argument('-t', help='test size fraction',    dest='test_size',         type=float, default=0.2)
    parser.add_argument('-k', help='drop out probability',  dest='keep_prob',         type=float, default=0.25)
    parser.add_argument('-n', help='number of epochs',      dest='nb_epoch',          type=int,   default=1)
    parser.add_argument('-s', help='samples per epoch',     dest='samples_per_epoch', type=int,   default=10)
    parser.add_argument('-b', help='batch size',            dest='batch_size',        type=int,   default=40)
    parser.add_argument('-o', help='save best models only', dest='save_best_only',    type=s2b,   default='true')
    parser.add_argument('-l', help='learning rate',         dest='learning_rate',     type=float, default=1.0e-4)
    args = parser.parse_args()

    print('-' * 30)
    print('Parameters')
    print('-' * 30)
    for key, value in vars(args).items():
        print('{:<20} := {}'.format(key, value))
    print('-' * 30)

    data = load_data(args)
    model = build_model(args)
    train_model(model, args, *data)


if __name__ == '__main__':
    main()

