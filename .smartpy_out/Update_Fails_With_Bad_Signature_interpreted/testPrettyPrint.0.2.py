import smartpy as sp

class Contract(sp.Contract):
  def __init__(self):
    self.init(oracleData = {'XTZ-USD' : (sp.timestamp(0), (sp.timestamp(0), (0, (0, (0, (0, 0))))))}, publicKey = sp.some(sp.key('edpkumfjciYdSYPzFt5dzWt9k974Wnp2qPwHqqjfsJvEwJWpYJnFdW')))

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
      sp.verify(self.data.oracleData.contains(assetData.key))
      sp.verify(sp.check_signature(self.data.publicKey.open_some(), compute_79.value, sp.pack((assetData.key, compute_80.value))))
      compute_97 = sp.local("compute_97", self.data.oracleData[assetData.key])
      compute_98 = sp.local("compute_98", sp.fst(compute_97.value))
      compute_99 = sp.local("compute_99", sp.fst(compute_80.value))
      sp.verify(compute_99.value > compute_98.value)
      self.data.oracleData[assetData.key] = compute_80.value