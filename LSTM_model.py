import tensorflow as tf
from tensorflow.python.ops import rnn_cell
from tensorflow.python.ops import seq2seq
import utils

import numpy as np

class LSTM_model(object):
  def __init__(self, config=None, mode=None):
    self.config = config
    self.mode = mode

    self.reader = utils.DataReader()

    self.cell = rnn_cell.BasicLSTMCell(config.rnn_size, state_is_tuple=True)

    self.input_data = tf.placeholder(tf.int32, [config.batch_size, config.input_length])
    self.targets = tf.placeholder(tf.int32, [config.batch_size, 1])
    self.initial_state = self.cell.zero_state(config.batch_size, tf.float32)

    with tf.variable_scope("input_embedding"):
      embedding = tf.get_variable("embedding", [config.vocab_size, config.rnn_size])
      inputs = tf.split(1, config.input_length, tf.nn.embedding_lookup(embedding, self.input_data))
      inputs = [tf.squeeze(input, [1]) for input in inputs]

    with tf.variable_scope("send_to_rnn", reuse=True):
      state = self.initial_state
      output = None

      for i, input in enumerate(inputs):
        ouput, state = self.cell(input, state)

    with tf.variable_scope("softmax"):
      softmax_w = tf.get_variable("softmax_w", [config.rnn_size, config.vocab_size])
      softmax_b = tf.get_variable("softmax_b", [config.vocab_size])
      self.logits = tf.matmul(output, softmax_w) + softmax_b
      self.probs = tf.nn.softmax(self.logits)

    loss = seq2seq.sequence_loss_by_example([self.logits],
                                            [tf.reshape(self.targets, [-1])],
                                            tf.ones([config.batch_size]),
                                            config.vocab_size)

    self.cost = tf.reduce_mean(loss)
    self.final_state = state

    # self.lr = tf.Variable(0.0, trainable=False)
    tvars = tf.trainable_variables()
    grads, _ = tf.clip_by_global_norm(tf.gradients(self.cost, tvars),
                                      config.grad_clip)
    optimizer = tf.train.AdadeltaOptimizer()
    self.train_op = optimizer.apply_gradients(zip(grads, tvars))