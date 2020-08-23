import smartpy as sp

class Contract(sp.Contract):
  def __init__(self):
    self.init()

  @sp.entry_point
  def callback(self, params):
    pass