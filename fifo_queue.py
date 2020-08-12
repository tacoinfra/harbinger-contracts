import smartpy as sp

#####################################################################
# This file defines a simple FIFO queue which keeps track of a sum
# of items in the queue.
#####################################################################


class FifoDataType:
    def __call__(self):
        return sp.record(first=0, last=-1, sum=sp.nat(0), saved={0: sp.nat(0)})

    # Pop the next element off the queue.
    def pop(self, data):
        sp.verify(data.first < data.last)
        data.sum = sp.as_nat(data.sum - data.saved[data.first])
        del data.saved[data.first]
        data.first += 1

    # Push an element onteh the queue.
    def push(self, data, element):
        data.last += 1
        data.sum += element
        data.saved[data.last] = element

    # Peek at the head of the queue.
    def head(self, data):
        return data.saved[data.first]

    # Return the length of the queue.
    def len(self, data):
        return data.last - data.first + 1
