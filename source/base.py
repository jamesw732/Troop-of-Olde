import math

def sigmoid(x):
    return 1 / (1 + math.exp(-x))

def sqnorm(v):
    """Returns the squared norm of a vector.
    v: Any vector"""
    return sum(v ** 2)

def sqdist(v1, v2):
    """Returns the squared distance between two vectors
    v1: Any vector
    v2: Any vector, same shape as v1"""
    return sum((v1 - v2) ** 2)