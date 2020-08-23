import smartpy as sp

class Contract(sp.Contract):
  def __init__(self):
    self.init(oracleData = {'BTC-USD' : (sp.timestamp(0), (sp.timestamp(0), (0, (0, (0, (0, 0)))))), 'XTZ-USD' : (sp.timestamp(0), (sp.timestamp(0), (0, (0, (0, (0, 0))))))}, publicKey = sp.some(sp.key('edpkumfjciYdSYPzFt5dzWt9k974Wnp2qPwHqqjfsJvEwJWpYJnFdW')))

  @sp.entry_point
  def push(self, params):
    sp.transfer(self.data.oracleData, sp.tez(0), params)

  @sp.entry_point
  def revoke(self, params):
    sp.verify(sp.check_signature(self.data.publicKey.open_some(), params, sp.pack(sp.set_type_expr(sp.none, sp.TOption(sp.TKey)))))
    self.data.publicKey = sp.none

  @sp.entry_point
  def update(self, params):
    sp.for assetData in params.items():
      compute_79 = sp.local("compute_79", sp.fst(assetData.value))
      compute_80 = sp.local("compute_80", sp.snd(assetData.value))
      sp.if self.data.oracleData.contains(assetData.key):
        compute_85 = sp.local("compute_85", self.data.oracleData[assetData.key])
        compute_86 = sp.local("compute_86", sp.fst(compute_85.value))
        compute_87 = sp.local("compute_87", sp.fst(compute_80.value))
        sp.if compute_87.value > compute_86.value:
          sp.verify(sp.check_signature(self.data.publicKey.open_some(), compute_79.value, sp.pack((assetData.key, compute_80.value))))
          self.data.oracleData[assetData.key] = compute_80.value