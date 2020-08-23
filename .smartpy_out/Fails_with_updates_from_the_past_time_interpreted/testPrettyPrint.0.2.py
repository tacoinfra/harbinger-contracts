import smartpy as sp

class Contract(sp.Contract):
  def __init__(self):
    self.init(assetCodes = sp.list(['XTZ-USD', 'BTC-USD']), assetMap = {'BTC-USD' : sp.record(computedPrice = 0, lastUpdateTime = sp.timestamp(0), prices = sp.record(first = 0, last = -1, saved = {0 : 0}, sum = 0), volumes = sp.record(first = 0, last = -1, saved = {0 : 0}, sum = 0)), 'XTZ-USD' : sp.record(computedPrice = 0, lastUpdateTime = sp.timestamp(0), prices = sp.record(first = 0, last = -1, saved = {0 : 0}, sum = 0), volumes = sp.record(first = 0, last = -1, saved = {0 : 0}, sum = 0))}, numDataPoints = 3, oracleContract = sp.address('KT1QLPABNCD4z1cSYVv3ntYDYgtWTed7LkYr'))

  @sp.entry_point
  def get(self, params):
    compute_139 = sp.local("compute_139", sp.fst(params))
    compute_140 = sp.local("compute_140", sp.snd(params))
    sp.verify(self.data.assetMap.contains(compute_139.value), message = 'bad request')
    sp.transfer(self.data.assetMap[compute_139.value].computedPrice, sp.tez(0), compute_140.value)

  @sp.entry_point
  def update(self, params):
    sp.set_type(params, sp.TBigMap(sp.TString, sp.TPair(sp.TTimestamp, sp.TPair(sp.TTimestamp, sp.TPair(sp.TNat, sp.TPair(sp.TNat, sp.TPair(sp.TNat, sp.TPair(sp.TNat, sp.TNat))))))))
    sp.verify(sp.sender == self.data.oracleContract, message = 'bad sender')
    sp.for assetCode in self.data.assetCodes:
      sp.if params.contains(assetCode):
        compute_96 = sp.local("compute_96", sp.fst(params[assetCode]))
        sp.if compute_96.value > self.data.assetMap[assetCode].lastUpdateTime:
          self.data.assetMap[assetCode].lastUpdateTime = compute_96.value
          compute_102 = sp.local("compute_102", sp.snd(params[assetCode]))
          compute_103 = sp.local("compute_103", sp.snd(compute_102.value))
          compute_104 = sp.local("compute_104", sp.snd(compute_103.value))
          compute_105 = sp.local("compute_105", sp.snd(compute_104.value))
          compute_106 = sp.local("compute_106", sp.snd(compute_105.value))
          compute_110 = sp.local("compute_110", sp.fst(compute_104.value))
          compute_111 = sp.local("compute_111", sp.fst(compute_105.value))
          compute_112 = sp.local("compute_112", sp.fst(compute_106.value))
          compute_113 = sp.local("compute_113", sp.snd(compute_106.value))
          self.data.assetMap[assetCode].prices.last += 1
          self.data.assetMap[assetCode].prices.sum += (((compute_110.value + compute_111.value) + compute_112.value) // 3) * compute_113.value
          self.data.assetMap[assetCode].prices.saved[self.data.assetMap[assetCode].prices.last] = (((compute_110.value + compute_111.value) + compute_112.value) // 3) * compute_113.value
          self.data.assetMap[assetCode].volumes.last += 1
          self.data.assetMap[assetCode].volumes.sum += compute_113.value
          self.data.assetMap[assetCode].volumes.saved[self.data.assetMap[assetCode].volumes.last] = compute_113.value
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