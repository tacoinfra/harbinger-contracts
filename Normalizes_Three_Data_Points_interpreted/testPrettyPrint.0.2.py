import smartpy as sp

class Contract(sp.Contract):
  def __init__(self):
    self.init(assetCode = 'XTZ-USD', computedPrice = 0, lastUpdateTime = sp.timestamp(0), numDataPoints = 3, oracleContract = sp.address('KT1QLPABNCD4z1cSYVv3ntYDYgtWTed7LkYr'), prices = sp.record(first = 0, last = -1, saved = {0 : 0}, sum = 0), volumes = sp.record(first = 0, last = -1, saved = {0 : 0}, sum = 0))

  @sp.entry_point
  def get(self, params):
    sp.transfer(self.data.computedPrice, sp.tez(0), params)

  @sp.entry_point
  def update(self, params):
    sp.set_type(params, sp.TBigMap(sp.TString, sp.TPair(sp.TTimestamp, sp.TPair(sp.TTimestamp, sp.TPair(sp.TNat, sp.TPair(sp.TNat, sp.TPair(sp.TNat, sp.TPair(sp.TNat, sp.TNat))))))))
    sp.verify(sp.sender == self.data.oracleContract, message = 'bad sender')
    compute_75 = sp.local("compute_75", params[self.data.assetCode])
    compute_78 = sp.local("compute_78", sp.fst(compute_75.value))
    sp.verify(compute_78.value > self.data.lastUpdateTime)
    self.data.lastUpdateTime = compute_78.value
    compute_85 = sp.local("compute_85", sp.snd(compute_75.value))
    compute_86 = sp.local("compute_86", sp.snd(compute_85.value))
    compute_87 = sp.local("compute_87", sp.snd(compute_86.value))
    compute_88 = sp.local("compute_88", sp.snd(compute_87.value))
    compute_89 = sp.local("compute_89", sp.snd(compute_88.value))
    compute_93 = sp.local("compute_93", sp.fst(compute_87.value))
    compute_94 = sp.local("compute_94", sp.fst(compute_88.value))
    compute_95 = sp.local("compute_95", sp.fst(compute_89.value))
    compute_96 = sp.local("compute_96", sp.snd(compute_89.value))
    self.data.prices.last += 1
    self.data.prices.sum += (((compute_93.value + compute_94.value) + compute_95.value) // 3) * compute_96.value
    self.data.prices.saved[self.data.prices.last] = (((compute_93.value + compute_94.value) + compute_95.value) // 3) * compute_96.value
    self.data.volumes.last += 1
    self.data.volumes.sum += compute_96.value
    self.data.volumes.saved[self.data.volumes.last] = compute_96.value
    sp.if ((self.data.prices.last - self.data.prices.first) + 1) > self.data.numDataPoints:
      sp.verify(self.data.prices.first < self.data.prices.last)
      self.data.prices.sum = sp.as_nat(self.data.prices.sum - self.data.prices.saved[self.data.prices.first])
      del self.data.prices.saved[self.data.prices.first]
      self.data.prices.first += 1
      sp.verify(self.data.volumes.first < self.data.volumes.last)
      self.data.volumes.sum = sp.as_nat(self.data.volumes.sum - self.data.volumes.saved[self.data.volumes.first])
      del self.data.volumes.saved[self.data.volumes.first]
      self.data.volumes.first += 1
    self.data.computedPrice = self.data.prices.sum // self.data.volumes.sum