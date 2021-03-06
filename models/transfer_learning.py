import collections
import tensorflow as tf
import tensorflow.keras.applications as ka
from tensorflow.keras.layers import Dense, Dropout, Flatten, Conv2D, MaxPooling2D, Input, Lambda
from tensorflow.keras.models import Model, Sequential
from miso.layers.cyclic import *


TransferLearningParams = collections.namedtuple(
    'TransferLearningParams',
    ['model_func','prepro_func','default_input_shape']
)


def head(cnn_type, input_shape):
    subtypes = cnn_type.split('_')
    model_type = subtypes[0]
    if 'cyclic' in subtypes:
        use_cyclic = True
    else:
        use_cyclic = False
    if 'gain' in subtypes:
        use_gain = True
    else:
        use_gain = False

    params = TRANSFER_LEARNING_PARAMS[model_type]
    inputs, x = params.prepro_func(input_shape)
    if use_cyclic:
        if use_gain:
            x = CyclicGainSlice12()(x)
        else:
            x = CyclicSlice4()(x)
    x = params.model_func(include_top=False, weights='imagenet', pooling='avg', input_shape=input_shape)(x)
    if use_cyclic:
        if use_gain:
            x = CyclicDensePoolN(pool_op=tf.reduce_mean)(x)
        else:
            x = CyclicDensePool4(pool_op=tf.reduce_mean)(x)
    model = Model(inputs=inputs, outputs=x)
    for layer in model.layers:
        layer.trainable = False
    return model


# Input range is [0,1], not [0,255] as expected by keras
# So all prepro are adjusted to this.
def tf_prepro(input_shape):
    # (x / 127.5) - 1
    inputs = Input(shape=input_shape)
    x = Lambda(lambda y: tf.subtract(tf.multiply(y, 2), 1))
    # x = Lambda(lambda y: y * 2 - 1)(inputs)
    return inputs, x


def torch_prepro(input_shape):
    # (x / 255 - mean) / std_dev
    inputs = Input(shape=input_shape)
    x = Lambda(lambda y: tf.subtract(y, tf.reshape(tf.constant([0.485, 0.456, 0.406]), [1, 1, 1, 3])))(inputs)
    x = Lambda(lambda y: tf.divide(y, tf.reshape(tf.constant([0.229, 0.224, 0.225]), [1, 1, 1, 3])))(x)
    # x = Lambda(lambda y: y - tf.reshape(tf.constant([0.485, 0.456, 0.406]), [1, 1, 1, 3]))(inputs)
    # x = Lambda(lambda y: y / tf.reshape(tf.constant([0.229, 0.224, 0.225]), [1, 1, 1, 3]))(x)
    return inputs, x


def default_prepro(input_shape):
    # Convert to BGR then x - mean
    inputs = Input(shape=input_shape)
    x = Lambda(lambda y: tf.reverse(y, axis=[-1]))(inputs)
    x = Lambda(lambda y: tf.subtract(tf.multiply(y, 255.0), tf.reshape(tf.constant([103.939, 116.779, 128.68]), [1, 1, 1, 3])))(x)
    # x = Lambda(lambda y: tf.reverse(y, axis=[-1]))(inputs)
    # x = Lambda(lambda y: y * tf.constant(255.0) - tf.reshape(tf.constant([103.939, 116.779, 128.68]), [1, 1, 1, 3]))(x)
    return inputs, x
#
#
# def densenet121_head(input_shape):
#     return densenet_head(input_shape, 'densenet121')
#
#
# def densenet_head(input_shape, type):
#
#     x = densenet121.DenseNet121(include_top=False, weights='imagenet', pooling='avg')(x)
#     model = Model(inputs=inputs, outputs=x)
#     model.summary()
#     model.get_layer(type).trainable = False
#     return model
#
#
# def resnet50_head(input_shape):
#     inputs = Input(shape=input_shape)
#     x = Lambda(lambda y: tf.reverse(y, axis=[-1]))(inputs)
#     x = Lambda(lambda y: y * tf.constant(255.0)
#                          - tf.reshape(tf.constant([103.939, 116.779, 128.68]),
#                                       [1, 1, 1, 3]))(x)
#     x = resnet50.ResNet50(include_top=False,
#                           weights='imagenet',
#                           pooling='avg')(x)
#     model = Model(inputs=inputs, outputs=x)
#     model.get_layer('resnet50').trainable = False
#     return model
#
# def resnet50_cyclic_head(input_shape):
#     inputs = Input(shape=input_shape)
#     x = Lambda(lambda y: tf.reverse(y, axis=[-1]))(inputs)
#     x = Lambda(lambda y: y * tf.constant(255.0)
#                          - tf.reshape(tf.constant([103.939, 116.779, 128.68]),
#                                       [1, 1, 1, 3]))(x)
#     x = CyclicSlice4()(x)
#     x = resnet50.ResNet50(include_top=False,
#                           weights='imagenet',
#                           pooling='avg')(x)
#     x = CyclicDensePool4(pool_op=tf.reduce_mean)(x)
#     model = Model(inputs=inputs, outputs=x)
#     model.get_layer('resnet50').trainable = False
#     return model
#
# def resnet50_cyclic_gain_head(input_shape):
#     inputs = Input(shape=input_shape)
#     x = Lambda(lambda y: tf.reverse(y, axis=[-1]))(inputs)
#     x = Lambda(lambda y: y * tf.constant(255.0)
#                          - tf.reshape(tf.constant([103.939, 116.779, 128.68]),
#                                       [1, 1, 1, 3]))(x)
#     x = CyclicGainSlice12()(x)
#     x = resnet50.ResNet50(include_top=False,
#                           weights='imagenet',
#                           pooling='avg')(x)
#     x = CyclicDensePoolN(pool_op=tf.reduce_mean)(x)
#     model = Model(inputs=inputs, outputs=x)
#     model.get_layer('resnet50').trainable = False
#     return model
#
# def resnet50_head(input_shape):
#     inputs = Input(shape=input_shape)
#     x = Lambda(lambda y: tf.reverse(y, axis=[-1]))(inputs)
#     x = Lambda(lambda y: y * tf.constant(255.0)
#                          - tf.reshape(tf.constant([103.939, 116.779, 128.68]),
#                                       [1, 1, 1, 3]))(x)
#     x = resnet50.ResNet50(include_top=False,
#                           weights='imagenet',
#                           pooling='avg')(x)
#     model = Model(inputs=inputs, outputs=x)
#     model.get_layer('resnet50').trainable = False
#     return model


def tail(num_classes, input_shape):
    return marchitto_tail(num_classes, input_shape)


def tail_regression(input_shape):
    return marchitto_tail_regression(input_shape)


def tail_vector(num_classes, input_shape):
    inp = Input(shape=input_shape)
    outp = Dropout(0.05)(inp)
    outp = Dense(512, activation='relu')(outp)
    outp = Dropout(0.15)(outp)
    outp = Dense(512, activation='relu')(outp)
    # model = Sequential()
    # model.add(Dropout(0.05))
    # model.add(Dense(512, activation='relu'))
    # model.add(Dropout(0.15))
    # model.add(Dense(512, activation='relu'))
    return Model(inp, outp)


def marchitto_tail(nb_classes, input_shape):
    inp = Input(shape=input_shape)
    outp = Dropout(0.05)(inp)
    outp = Dense(512, activation='relu')(outp)
    outp = Dropout(0.15)(outp)
    outp = Dense(512, activation='relu')(outp)
    outp = Dense(nb_classes, activation='softmax')(outp)
    return Model(inp, outp)
    # model = Sequential()
    # model.add(Dropout(0.05))
    # model.add(Dense(512, activation='relu'))
    # model.add(Dropout(0.15))
    # model.add(Dense(512, activation='relu'))
    # model.add(Dense(nb_classes, activation='softmax'))
    # return model

def marchitto_tail_regression(input_shape):
    inp = Input(shape=input_shape)
    outp = Dropout(0.05)(inp)
    outp = Dense(512, activation='relu')(outp)
    outp = Dropout(0.15)(outp)
    outp = Dense(512, activation='relu')(outp)
    outp = Dense(1)(outp)
    return Model(inp, outp)


TRANSFER_LEARNING_PARAMS = {
        'xception': TransferLearningParams(ka.xception.Xception, tf_prepro, [299,299,3]),
        'vgg16': TransferLearningParams(ka.vgg16.VGG16, default_prepro, [224,224,3]),
        'vgg19': TransferLearningParams(ka.vgg19.VGG19, default_prepro, [224,224,3]),
        'resnet50': TransferLearningParams(ka.resnet50.ResNet50, default_prepro, [224,224,3]),
        #'resnet101': TransferLearningParams(ka.xception.Xception, default_prepro, [224,224,3]),
        #'resnet152': TransferLearningParams(ka.xception.Xception, default_prepro, [224,224,3]),
        #'resnet50V2': TransferLearningParams(ka.xception.Xception, default_prepro, [224,224,3]),
        #'resnet101V2': TransferLearningParams(ka.xception.Xception, default_prepro, [224,224,3]),
        #'resnet152V2': TransferLearningParams(ka.xception.Xception, default_prepro, [224,224,3]),
        'inceptionV3': TransferLearningParams(ka.inception_v3.InceptionV3, tf_prepro, [299,299,3]),
        'inceptionresnetV2': TransferLearningParams(ka.inception_resnet_v2.InceptionResNetV2, tf_prepro, [299,299,3]),
        'mobilenet': TransferLearningParams(ka.mobilenet.MobileNet, tf_prepro, [224,224,3]),
        'mobilenetV2': TransferLearningParams(ka.mobilenet_v2.MobileNetV2, tf_prepro, [224,224,3]),
        'densenet121': TransferLearningParams(ka.densenet.DenseNet121, torch_prepro, [224,224,3]),
        'densenet169': TransferLearningParams(ka.densenet.DenseNet169, torch_prepro, [224,224,3]),
        'densenet201': TransferLearningParams(ka.densenet.DenseNet201, torch_prepro, [224,224,3]),
        'nasnetmobile': TransferLearningParams(ka.nasnet.NASNetMobile, tf_prepro, [224,224,3]),
        'nasnetlarge': TransferLearningParams(ka.nasnet.NASNetLarge, tf_prepro, [331,331,3])
    }
