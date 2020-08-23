import smartpy as sp

class Contract(sp.Contract):
  def __init__(self):
    self.init(assetCodes = sp.list(['XTZ-USD']), assetMap = {'XTZ-USD' : sp.record(computedPrice = 0, lastUpdateTime = sp.timestamp(0), prices = sp.record(first = 0, last = -1, saved = {0 : 0}, sum = 0), volumes = sp.record(first = 0, last = -1, saved = {0 : 0}, sum = 0))}, numDataPoints = 3, oracleContract = sp.address('KT1QLPABNCD4z1cSYVv3ntYDYgtWTed7LkYr'))

  @sp.entry_point
  def get(self, params):
    compute_140 = sp.local("compute_140", sp.fst(params))
    compute_141 = sp.local("compute_141", sp.snd(params))
    sp.verify(self.data.assetMap.contains(compute_140.value), message = 'bad request')
    sp.transfer(self.data.assetMap[compute_140.value].computedPrice, sp.tez(0), compute_141.value)

  @sp.entry_point
  def update(self, params):
    sp.set_type(params, sp.TBigMap(sp.TString, sp.TPair(sp.TTimestamp, sp.TPair(sp.TTimestamp, sp.TPair(sp.TNat, sp.TPair(sp.TNat, sp.TPair(sp.TNat, sp.TPair(sp.TNat, sp.TNat))))))))
    sp.verify(sp.sender == self.data.oracleContract, message = 'bad sender')
    sp.for assetCode in self.data.assetCodes:
      sp.if params.contains(assetCode):
        compute_96 = sp.local("compute_96", sp.fst(params[assetCode]))
        sp.verify(compute_96.value > self.data.assetMap[assetCode].lastUpdateTime)
        self.data.assetMap[assetCode].lastUpdateTime = compute_96.value
        compute_103 = sp.local("compute_103", sp.snd(params[assetCode]))
        compute_104 = sp.local("compute_104", sp.snd(compute_103.value))
        compute_105 = sp.local("compute_105", sp.snd(compute_104.value))
        compute_106 = sp.local("compute_106", sp.snd(compute_105.value))
        compute_107 = sp.local("compute_107", sp.snd(compute_106.value))
        compute_111 = sp.local("compute_111", sp.fst(compute_105.value))
        compute_112 = sp.local("compute_112", sp.fst(compute_106.value))
        compute_113 = sp.local("compute_113", sp.fst(compute_107.value))
        compute_114 = sp.local("compute_114", sp.snd(compute_107.value))
        self.data.assetMap[assetCode].prices.last += 1
        self.data.assetMap[assetCode].prices.sum += (((compute_111.value + compute_112.value) + compute_113.value) // 3) * compute_114.value
        self.data.assetMap[assetCode].prices.saved[self.data.assetMap[assetCode].prices.last] = (((compute_111.value + compute_112.value) + compute_113.value) // 3) * compute_114.value
        self.data.assetMap[assetCode].volumes.last += 1
        self.data.assetMap[assetCode].volumes.sum += compute_114.value
        self.data.assetMap[assetCode].volumes.saved[self.data.assetMap[assetCode].volumes.last] = compute_114.value
        sp.if ((self.data.assetMap[assetCode].prices.last - self.data.assetMap[assetCode].prices.first) + 1) > self.data.numDataPoints:
          sp.verify(self.data.assetMap[assetCode].prices.first < self.data.assetMap[assetCode].prices.last)
          self.data.assetMap[assetCode].prices.sum = sp.as_nat(self.data.assetMap[assetCode].prices.sum - self.data.assetMap[assetCode].prices.saved[self.data.assetMap[assetCode].prices.first])
          del self.data.assetMap[assetCode].prices.saved[self.data.assetMap[assetCode].prices.first]
          self.data.assetMap[assetCode].prices.first += 1
          sp.verify(self.data.assetMap[assetCode].volumes.first < self.data.assetMap[assetCode].volumes.last)
          self.data.assetMap[assetCode].volumes.sum = sp.as_nat(self.data.assetMap[assetCode].volumes.sum - self.data.assetMap[assetCode].volumes.saved[self.data.assetMap[assetCode].volumes.first])
          del self.data.assetMap[assetCode].volumes.saved[self.data.assetMap[assetCode].volumes.first]
          self.data.assetMap[assetCode].volumes.first += 1
        self.data.assetMap[assetCode].computedPrice = self.data.assetMap[assetCode].prices.sum // self.data.assetMap[assetCode].volumes.sum