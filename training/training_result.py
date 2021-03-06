import numpy as np
from sklearn.metrics import precision_recall_fscore_support, accuracy_score
from sklearn.metrics import mean_squared_error


class TrainingResult:

    def __init__(self, model_params, history, y_true, y_pred, y_prob, cls_labels, training_time, inference_time):

        # Model configuration
        self.model_params = model_params
        self.cls_labels = cls_labels

        # Training statistics
        self.training_time = training_time
        self.inference_time = inference_time

        # Overall accuracy
        self.accuracy = accuracy_score(y_true, y_pred)

        # Training history
        self.epochs = history.epoch
        self.loss = history.history['loss']
        # self.acc = history.history['acc']
        self.acc = 0
        # if 'val_loss' in history.history.keys():
        #     self.val_loss = history.history['val_loss']
        #     self.val_acc = history.history['val_acc']
        #     self.val_acc = history.history['val_mse']
        # else:
        #     self.val_loss = []
        #     self.val_acc = []

        # Class history
        # p, r, f1, s = precision_recall_fscore_support(y_true, y_pred, labels=range(len(self.cls_labels)))
        self.recall = 0
        self.precision = 0
        self.f1_score = 0
        self.support = 0

        # Test predictions (for later analysis)
        self.y_true = y_true
        self.y_pred = y_pred
        self.y_prob = y_prob

    def mean_precision(self):
        return np.mean(self.precision)

    def mean_recall(self):
        return np.mean(self.recall)

    def mean_f1_score(self):
        return np.mean(self.f1_score)

    def mse(self):
        return mean_squared_error(self.y_true, self.y_pred)
