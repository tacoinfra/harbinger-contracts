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
      sp.verify(self.data.oracleData.contains(assetData.key))
      sp.verify(sp.check_signature(self.data.publicKey.open_some(), sp.fst(assetData.value), sp.pack((assetData.key, sp.snd(assetData.value)))))
      sp.verify(sp.fst(sp.snd(assetData.value)) > sp.fst(self.data.oracleData[assetData.key]))
      self.data.oracleData[assetData.key] = sp.snd(assetData.value)