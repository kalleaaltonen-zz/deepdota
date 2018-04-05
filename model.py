import tensorflow as tf
import numpy as np
import json

class DotaNN:
    def __init__(self, savefile):
        self.savefile = savefile
        #self.dimensions = dimensions
        self.beta = 0.0005
        self.alpha = 0.01 
        self.minibatch_size = 1024

    def forwardprop(self, X):
        h1    = tf.nn.relu(tf.add(tf.matmul(X, self.w_1), self.b_1)) 
        h2    = tf.nn.relu(tf.add(tf.matmul(h1, self.w_2), self.b_2))  
        h3    = tf.nn.relu(tf.add(tf.matmul(h2, self.w_3), self.b_3))  
        yhat = tf.nn.sigmoid(tf.add(tf.matmul(h3, self.w_4), self.b_4))
        return yhat
        
        
    def build(self):
        # Layer's sizes
        x_size = 115
        y_size = 1

        h1_size = 100
        h2_size = 20
        h3_size = 10

        def init_weights(shape):
            weights = tf.random_normal(shape, stddev=0.1)
            return tf.Variable(weights)

        self.w_1 = init_weights((x_size, h1_size))
        self.b_1 = tf.Variable(tf.zeros([h1_size]))
        self.w_2 = init_weights((h1_size, h2_size))
        self.b_2 = tf.Variable(tf.zeros([h2_size]))
        self.w_3 = init_weights((h2_size, h3_size))
        self.b_3 = tf.Variable(tf.zeros([h3_size]))
        self.w_4 = init_weights((h3_size, y_size))
        self.b_4 = tf.Variable(tf.zeros([y_size]))



        # Symbols
        self.X = tf.placeholder('float', shape=[None, x_size])
        self.y = tf.placeholder('float', shape=[None, y_size])

        self.saver = tf.train.Saver({
            'w_1': self.w_1, 'b_1': self.b_1,
            'w_2': self.w_2, 'b_2': self.b_2,
            'w_3': self.w_3, 'b_3': self.b_3,
            'w_4': self.w_4, 'b_4': self.b_4
        })

        self.yhat = self.forwardprop(self.X)
        self.predict_op = tf.round(self.yhat)

        # Backward propagation
        left = tf.multiply(self.y, tf.log(self.yhat))
        right = tf.multiply(tf.subtract(tf.constant(1.0), self.y), 
                            tf.log(tf.subtract(tf.constant(1.0), self.yhat)))

        regularizers = tf.nn.l2_loss(self.w_1) + tf.nn.l2_loss(self.w_2) +  tf.nn.l2_loss(self.w_3) + tf.nn.l2_loss(self.w_4)

        cost = tf.negative(tf.reduce_mean(tf.add(left, right))) + self.beta * regularizers

        return cost


    def fit(self, train_X, train_y, test_X, test_y):
        cost = self.build()
        
        updates = tf.train.MomentumOptimizer(self.alpha, 0.9).minimize(cost)
        
        init = tf.global_variables_initializer()
        costs = []
        with tf.Session() as sess:
            sess.run(init)

            print("starting training")
            for epoch in range(141):
                for i in range(0, len(train_X), self.minibatch_size):
                    cc, _ = sess.run([cost, updates], feed_dict={self.X: train_X[i:i+self.minibatch_size], self.y: train_y[i:i+self.minibatch_size]})
                    costs.append(cc)

                if epoch % 10 == 0:
                    #train_accuracy = np.mean(train_y ==
                    #                         sess.run(self.predict_op, feed_dict={self.X: train_X, self.y: train_y}))
                    test_accuracy  = np.mean(test_y ==
                                             sess.run(self.predict_op, feed_dict={self.X: test_X, self.y: test_y}))

                    print("Epoch = %d, test accuracy = %.2f%%, win mean = %.2f" % (epoch + 1, 100. * test_accuracy, win_mean))
            # save the model
            self.saver.save(sess, self.savefile)
        return costs

    def predict(self, X):
        with tf.Session() as session:
            self.saver.restore(session, self.savefile)
            P = session.run(self.yhat, feed_dict={self.X: X})
        return P


#    def score(self, X, Y):
#        return 1 - error_rate(self.predict(X), Y)

    def save(self, filename):
        j = {'model': self.savefile}
        with open(filename, 'w') as f:
            json.dump(j, f)

    @staticmethod
    def load(filename):
        with open(filename) as f:
            j = json.load(f)
        m = DotaNN(j['model'])
        m.build()
        return m