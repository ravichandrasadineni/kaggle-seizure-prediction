import json, shutil, cPickle, os, csv
from pandas import read_csv
from sklearn.preprocessing import MinMaxScaler
from theano import config
from pandas import DataFrame
from cnn.conv_net import ConvNet
from utils.loader import load_test_data
from utils.config_name_creator import *
from utils.data_scaler import scale_across_time, scale_across_features

config.floatX = 'float32'


def rescale(probability):
    scaler = MinMaxScaler(feature_range=(0.000000001, 0.999999999))
    return scaler.fit_transform(probability)


def merge_csv_data(submission_path, subjects, submission_name, scale=True):
    submission_name += '_scaled' if scale else ''

    with open(submission_path + '/' + submission_name + '.csv', 'wb') as f:
        writer = csv.writer(f)
        writer.writerow(['clip', 'preictal'])

    for subject in subjects:
        df = read_csv(submission_path + '/' + subject + '.csv')
        df['preictal'] = rescale(df.drop('clip', axis=1).values)
        with open(submission_path + '/' + submission_name + '.csv', 'a') as f:
            df.to_csv(f, header=False, index=False)


def predict(subject, data_path, model_path, submission_path):
    patient_filenames = [filename for filename in os.listdir(model_path) if
                         subject in filename and filename.endswith('.pickle')]
    for filename in patient_filenames:
        print filename

        d = load_test_data(data_path, subject)
        x, id = d['x'], d['id']

        with open(model_path + '/' + filename, 'rb') as f:
            state_dict = cPickle.load(f)

        scalers = state_dict['scalers']
        x, _ = scale_across_time(x, x_test=None, scalers=scalers) if state_dict['params']['scale_time'] \
            else scale_across_features(x, x_test=None, scalers=scalers)

        cnn = ConvNet(state_dict['params'])
        cnn.set_weights(state_dict['weights'])
        test_proba = cnn.get_test_proba(x)

        ans = zip(id, test_proba)

        df = DataFrame(data=ans, columns=['clip', 'preictal'])
        csv_name = '.'.join(filename.split('.')[:-1]) if '.' in filename else filename
        df.to_csv(submission_path + '/' + csv_name + '.csv', index=False, header=True)


def run_predictor():
    with open('SETTINGS.json') as f:
        settings_dict = json.load(f)

    model_path = settings_dict['path']['model_path'] + '/' + create_cnn_model_name(settings_dict)
    data_path = settings_dict['path']['processed_data_path'] + '/' + create_fft_data_name(settings_dict)
    submission_path = settings_dict['path']['submission_path'] + '/' + create_cnn_model_name(settings_dict)

    if not os.path.exists(submission_path):
        os.makedirs(submission_path)
    shutil.copy2('SETTINGS.json', submission_path + '/SETTINGS.json')

    subjects = ['Dog_1', 'Dog_2', 'Dog_3', 'Dog_4', 'Dog_5', 'Patient_1', 'Patient_2']
    for subject in subjects:
        print '***********************', subject, '***************************'
        predict(subject, data_path, model_path, submission_path)

    merge_csv_data(submission_path, subjects, submission_name='submission', scale=True)


if __name__ == '__main__':
    run_predictor()
