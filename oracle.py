import smartpy as sp

TezosOracle = sp.import_script_from_url("file:common.py")

# Data type that represents a signed update to the Oracle.
SignedOracleDataType = sp.TPair(sp.TSignature, TezosOracle.OracleDataType)

#####################################################################
# An Oracle contract accepts signed updates for a list of assets.
#
# Oracles are configured with a list of assets whose updates they
# track and a public key which will verify signatures on the asset
# data.
#
# Anyone may update the Oracle with properly signed data. Signatures
# for the oracle are provided by signing the packed bytes of the
# following Michelson data:
# 'pair <asset code | string> (pair <start | timestamp> (pair <end | timestamp> (pair <nat | open> (pair <nat | high> (pair <nat low> (pair <close | nat> <volume | nat>))))))'
#
# Anyone can request the Oracle push its data to another contract. Pushed
# data should generally be pushed to a Normalizer contract rather than
# consumed directly.
#
# Oracles can be revoked by calling the revoke entry point with the
# signature for bytes representing an Option(Key) Michelson type with
# value none. After revocation, the Oracle will refuse to process
# further updates.
#
# Updates to the Oracle must be monotonically increasing in start time.
#
# Values in the Oracle are represented as a natural numbers with six
# digits of precision. For instance $123.45 USD would be represented
# as 123_450_000.
#####################################################################


class OracleContract(sp.Contract):
    # Initialze a new oracle.
    #
    # Parameters:
    # publicKey(sp.TKey): The public key used to verify Oracle updates.
    # initialData(sp.TBigMap(sp.TString, TezosOracle.OracleDataType)): A map of initial values for the Oracle.
    def __init__(
        self,
        publicKey=sp.some(
            sp.key("sppk7bkCcE4TZwnqqR7JAKJBybJ2XTCbKZu11ESTvvZQYtv3HGiiffN")),
        initialData=sp.big_map(
            l={
                "XTZ-USD": (sp.timestamp(0), (sp.timestamp(0), (0, (0, (0, (0, 0))))))
            },
            tkey=sp.TString,
            tvalue=TezosOracle.OracleDataType
        )
    ):
        self.exception_optimization_level = "Unit"
        self.add_flag("no_comment")

        self.init(
            publicKey=publicKey,
            oracleData=initialData
        )

    # Update the Oracle.
    #
    # The parameter is a map of asset codes to a pair of signatures and oracle data.
    # The signature specification is described in the header of this file.
    #
    # Updates must be monotonically increasing in start time.
    #
    # An example parameter looks like:
    # { elt <asset code | string> (pair <signature | signature> (pair <start | timestamp> (pair <end | timestamp> (pair <nat | open> (pair <nat | high> (pair <nat low> (pair <close | nat> <volume | nat>)))))))'
    @sp.entry_point
    def update(self, params):
        # Iterate over assets in the input map.
        keyValueList = params.items()
        sp.for assetData in keyValueList:
            # Extract asset names, signatures, and the new data.
            assetName = assetData.key
            signature = sp.compute(sp.fst(assetData.value))
            newData = sp.compute(sp.snd(assetData.value))

            # Verify Oracle is tracking this asset.
            sp.verify(
                self.data.oracleData.contains(assetName),
                "bad asset"
            )

            # Verify signature.
            bytes = sp.pack((assetName, newData))
            sp.verify(
                sp.check_signature(
                    self.data.publicKey.open_some(), signature, bytes),
                "bad sig"
            )

            # Verify start timestamp is newer than the last update.
            oldData = sp.compute(self.data.oracleData[assetName])
            oldStartTime = sp.compute(sp.fst(oldData))
            newStartTime = sp.compute(sp.fst(newData))
            sp.verify(newStartTime > oldStartTime, "bad time")

            # Replace the data.
            self.data.oracleData[assetName] = newData

    # Revoke the Oracle.
    #
    # This entrypoint is destructive and non-reversible.
    #
    # The parameter format is a signature of the Michelson type Option(Key) with
    # value None signed by the secret key of this Oracle's public key.
    #
    # A successful call to this entrypoint will effectively freeze the Oracles value
    # by removing the Oracle's public key, preventing future updates from arriving.
    @sp.entry_point
    def revoke(self, param):
        # Recreate the message which should have been signed.
        message = sp.set_type_expr(sp.none, sp.TOption(sp.TKey))
        bytes = sp.pack(message)

        # Verify that the message is signed correctly.
        publicKey = self.data.publicKey.open_some()
        sp.verify(sp.check_signature(publicKey, param, bytes))

        # Revoke the Oracle's public Key.
        self.data.publicKey = sp.none

    # Push the data for the Oracle to another contract.
    #
    # The parameter is a contract to push the data to.
    @sp.entry_point
    def push(self, contract):
        sp.transfer(self.data.oracleData, sp.mutez(0), contract)

#####################################################################
# Oracle Tests
#####################################################################

# Import Normalizer for E2E testing.
Normalizer = sp.import_script_from_url("file:normalizer.py")


@sp.add_test(name="Update Once With Valid Data")
def test():
    scenario = sp.test_scenario()
    scenario.h1("Update Once With Valid Data")

    scenario.h2("GIVEN an Oracle contract")
    contract = OracleContract(
        publicKey=testAccountPublicKey,
    )
    scenario += contract

    scenario.h2("AND an update")
    assetCode = "XTZ-USD"
    start = sp.timestamp(1)
    end = sp.timestamp(2)
    open = 3
    high = 4
    low = 5
    close = 6
    volume = 7
    updateData = (
        start,
        (end,
         (open,
          (high,
           (low,
            (close, volume))))))
    message = sp.pack((assetCode, updateData))
    signature = sp.make_signature(
        testAccountSecretKey,
        message,
        message_format='Raw'
    )

    scenario.h2("WHEN the oracle is updated")
    update = sp.pair(signature, updateData)
    parameter = sp.map(
        l={
            assetCode: update
        },
        tkey=sp.TString,
        tvalue=SignedOracleDataType
    )
    scenario += contract.update(parameter)

    scenario.h2("THEN the oracle contains the data points")
    assetData = contract.data.oracleData["XTZ-USD"]
    endPair = sp.snd(assetData)
    openPair = sp.snd(endPair)
    highPair = sp.snd(openPair)
    lowPair = sp.snd(highPair)
    closeAndVolumePair = sp.snd(lowPair)

    expectedStart = sp.fst(assetData)
    expectedEnd = sp.fst(endPair)
    expectedOpen = sp.fst(openPair)
    expectedHigh = sp.fst(highPair)
    expecteLow = sp.fst(lowPair)
    expectedClose = sp.fst(closeAndVolumePair)
    expectedVolume = sp.snd(closeAndVolumePair)

    scenario.verify(start == expectedStart)
    scenario.verify(end == expectedEnd)
    scenario.verify(open == expectedOpen)
    scenario.verify(high == expectedHigh)
    scenario.verify(low == expecteLow)
    scenario.verify(close == expectedClose)
    scenario.verify(volume == expectedVolume)

# TODO(keefertaylor): Enable this test
# @sp.add_test(name = "Update Once With Coinbase Data")
# def test():
#     scenario = sp.test_scenario()
#     scenario.h1("Update Once With Valid Data")

#     scenario.h2("GIVEN an Oracle contract and data extracted from the Coinbase Oracle")
#     contract = OracleContract(
#         publicKey = sp.some(sp.key("sppk7bkCcE4TZwnqqR7JAKJBybJ2XTCbKZu11ESTvvZQYtv3HGiiffN"))
#     )
#     scenario += contract

#     scenario.h2("AND an update")
#     start = sp.timestamp(1595707200)
#     end = sp.timestamp(1595707260)
#     open = 3076200
#     high = 3080400
#     low = 3076200
#     close = 3079200
#     volume = 1923470000
#     updateData = (
#         start,
#         (end,
#         (open,
#         (high,
#         (low,
#         (close, volume))))))
#     signature = sp.signature("spsig1f8mcfVYrjqzaFfa6hT63dbzomCAPac61utM5iv7bE6fpVXKLpaeLkZXNWqPvtRV8z2GW8gBPzsU9jV2CJiEA8sXkD4qht")

#     scenario.h2("WHEN the oracle is updated")
#     update = sp.pair(signature, updateData)
#     parameter = sp.map(
#         l = {
#             "XTZ-USD": update
#         },
#         tkey = sp.TString,
#         tvalue = SignedOracleDataType
#     )
#     scenario += contract.update(parameter)

#     scenario.h2("THEN the oracle contains the data points")
#     assetData = contract.data.oracleData["XTZ-USD"]
#     endPair = sp.snd(assetData)
#     openPair = sp.snd(endPair)
#     highPair = sp.snd(openPair)
#     lowPair = sp.snd(highPair)
#     closeAndVolumePair = sp.snd(lowPair)

#     expectedStart = sp.fst(assetData)
#     expectedEnd = sp.fst(endPair)
#     expectedOpen = sp.fst(openPair)
#     expectedHigh = sp.fst(highPair)
#     expecteLow = sp.fst(lowPair)
#     expectedClose = sp.fst(closeAndVolumePair)
#     expectedVolume = sp.snd(closeAndVolumePair)

#     scenario.verify(start == expectedStart)
#     scenario.verify(end == expectedEnd)
#     scenario.verify(open == expectedOpen)
#     scenario.verify(high == expectedHigh)
#     scenario.verify(low == expecteLow)
#     scenario.verify(close == expectedClose)
#     scenario.verify(volume == expectedVolume)


@sp.add_test(name="Second Update Overwrites First Update")
def test():
    scenario = sp.test_scenario()
    scenario.h1("Second Update Overwrites First Update")

    scenario.h2("GIVEN an Oracle contract")
    assetCode = "XTZ-USD"
    contract = OracleContract(
        publicKey=testAccountPublicKey,
        initialData=sp.big_map(
            l={
                assetCode: initialOracleData
            },
            tkey=sp.TString,
            tvalue=TezosOracle.OracleDataType
        )
    )
    scenario += contract

    scenario.h2("AND two updates")
    start1 = sp.timestamp(1)
    end1 = sp.timestamp(2)
    open1 = 3
    high1 = 4
    low1 = 5
    close1 = 6
    volume1 = 7
    updateData1 = (
        start1,
        (end1,
         (open1,
          (high1,
           (low1,
            (close1, volume1))))))
    message1 = sp.pack((assetCode, updateData1))
    signature1 = sp.make_signature(
        testAccountSecretKey,
        message1,
        message_format='Raw'
    )

    start2 = sp.timestamp(8)
    end2 = sp.timestamp(9)
    open2 = 10
    high2 = 11
    low2 = 12
    close2 = 13
    volume2 = 14
    updateData2 = (
        start2,
        (end2,
         (open2,
          (high2,
           (low2,
            (close2, volume2))))))
    message2 = sp.pack((assetCode, updateData2))
    signature2 = sp.make_signature(
        testAccountSecretKey,
        message2,
        message_format='Raw'
    )

    scenario.h2("WHEN the oracle is updated")
    update1 = sp.pair(signature1, updateData1)
    update2 = sp.pair(signature2, updateData2)
    parameter1 = sp.map(
        l={
            assetCode: update1
        },
        tkey=sp.TString,
        tvalue=SignedOracleDataType
    )
    parameter2 = sp.map(
        l={
            assetCode: update2
        },
        tkey=sp.TString,
        tvalue=SignedOracleDataType
    )
    scenario += contract.update(parameter1)
    scenario += contract.update(parameter2)

    scenario.h2("THEN the oracle contains the data points of the latter update")
    assetData = contract.data.oracleData[assetCode]
    endPair = sp.snd(assetData)
    openPair = sp.snd(endPair)
    highPair = sp.snd(openPair)
    lowPair = sp.snd(highPair)
    closeAndVolumePair = sp.snd(lowPair)

    oracleStart = sp.fst(assetData)
    oracleEnd = sp.fst(endPair)
    oracleOpen = sp.fst(openPair)
    oracleHigh = sp.fst(highPair)
    oracleLow = sp.fst(lowPair)
    oracleClose = sp.fst(closeAndVolumePair)
    oracleVolume = sp.snd(closeAndVolumePair)

    scenario.verify(oracleStart == start2)
    scenario.verify(oracleEnd == end2)
    scenario.verify(oracleOpen == open2)
    scenario.verify(oracleHigh == high2)
    scenario.verify(oracleLow == low2)
    scenario.verify(oracleClose == close2)
    scenario.verify(oracleVolume == volume2)


@sp.add_test(name="Update Fails With Data From The Same Timestamp")
def test():
    scenario = sp.test_scenario()
    scenario.h1("Update Fails With Data From The Same Timestamp")

    scenario.h2("GIVEN an Oracle contract")
    assetCode = "XTZ-USD"
    contract = OracleContract(
        publicKey=testAccountPublicKey,
        initialData=sp.big_map(
            l={
                assetCode: initialOracleData
            },
            tkey=sp.TString,
            tvalue=TezosOracle.OracleDataType
        )
    )
    scenario += contract

    scenario.h2("AND an update")
    start = sp.timestamp(1)
    end = sp.timestamp(2)
    open = 3
    high = 4
    low = 5
    close = 6
    volume = 7
    updateData = (
        start,
        (end,
         (open,
          (high,
           (low,
            (close, volume))))))
    message = sp.pack((assetCode, updateData))
    signature = sp.make_signature(
        testAccountSecretKey,
        message,
        message_format='Raw'
    )

    scenario.h2("WHEN the oracle is updated twice")
    update = sp.pair(signature, updateData)
    parameter = sp.map(
        l={
            assetCode: update
        },
        tkey=sp.TString,
        tvalue=SignedOracleDataType
    )
    scenario += contract.update(parameter)

    scenario.h2("THEN the second update fails")
    scenario += contract.update(parameter).run(valid=False)


@sp.add_test(name="Update Fails With Data From The Past")
def test():
    scenario = sp.test_scenario()
    scenario.h1("Update Fails With Data From The Past")

    scenario.h2("GIVEN an Oracle contract with some initial data.")
    assetCode = "XTZ-USD"

    contract = OracleContract(
        publicKey=testAccountPublicKey,
        initialData=sp.big_map(
            l={
                assetCode: initialOracleData
            },
            tkey=sp.TString,
            tvalue=TezosOracle.OracleDataType
        )
    )
    scenario += contract

    start = sp.timestamp(2)
    end = sp.timestamp(3)
    open = 3
    high = 4
    low = 5
    close = 6
    volume = 7
    updateData = (
        start,
        (end,
         (open,
          (high,
           (low,
            (close, volume))))))
    message = sp.pack((assetCode, updateData))
    signature = sp.make_signature(
        testAccountSecretKey,
        message,
        message_format='Raw'
    )

    update = sp.pair(signature, updateData)
    parameter = sp.map(
        l={
            assetCode: update
        },
        tkey=sp.TString,
        tvalue=SignedOracleDataType
    )
    scenario += contract.update(parameter)

    scenario.h2("WHEN the oracle is updated with a time in the past")
    updateData = (
        sp.timestamp(1),
        (sp.timestamp(2),
         (open,
          (high,
           (low,
            (close, volume))))))
    message = sp.pack(updateData)
    signature = sp.make_signature(
        testAccountSecretKey,
        message,
        message_format='Raw'
    )

    update = sp.pair(signature, updateData)
    parameter = sp.map(
        l={
            assetCode: update
        },
        tkey=sp.TString,
        tvalue=SignedOracleDataType
    )

    scenario.h2("THEN the update in the past fails")
    scenario += contract.update(parameter).run(valid=False)


@sp.add_test(name="Update Fails With Untracked Asset")
def test():
    scenario = sp.test_scenario()
    scenario.h1("Update Fails With Untracked Asset")

    scenario.h2("GIVEN an Oracle contract")
    assetCode = "XTZ-USD"

    contract = OracleContract(
        publicKey=testAccountPublicKey,
        initialData=sp.big_map(
            l={
                assetCode: initialOracleData
            },
            tkey=sp.TString,
            tvalue=TezosOracle.OracleDataType
        )
    )
    scenario += contract

    start = sp.timestamp(2)
    end = sp.timestamp(3)
    open = 3
    high = 4
    low = 5
    close = 6
    volume = 7
    updateData = (
        start,
        (end,
         (open,
          (high,
           (low,
            (close, volume))))))
    message = sp.pack((assetCode, updateData))
    signature = sp.make_signature(
        testAccountSecretKey,
        message,
        message_format='Raw'
    )

    scenario.h2("WHEN the oracle is updated with an untracked asset")
    update = sp.pair(signature, updateData)
    parameter = sp.map(
        l={
            "BTC-USD": update           # Not XTZ-USD
        },
        tkey=sp.TString,
        tvalue=SignedOracleDataType
    )

    scenario.h2("THEN the update fails.")
    scenario += contract.update(parameter).run(valid=False)


@sp.add_test(name="Update Fails With Bad Signature")
def test():
    scenario = sp.test_scenario()
    scenario.h1("Update Fails With Bad Signature")

    scenario.h2("GIVEN an Oracle contract")
    assetCode = "XTZ-USD"

    contract = OracleContract(
        publicKey=testAccountPublicKey,
        initialData=sp.big_map(
            l={
                assetCode: initialOracleData
            },
            tkey=sp.TString,
            tvalue=TezosOracle.OracleDataType
        )
    )
    scenario += contract

    scenario.h2("AND an update signed by an alternative key")
    alternativeAccount = sp.test_account("AlternativeAccount")
    alternativeSecretKey = alternativeAccount.secret_key
    start = sp.timestamp(1)
    end = sp.timestamp(2)
    open = 3
    high = 4
    low = 5
    close = 6
    volume = 7
    updateData = (
        start,
        (end,
         (open,
          (high,
           (low,
            (close, volume))))))
    message = sp.pack(updateData)
    signature = sp.make_signature(
        alternativeSecretKey,
        message,
        message_format='Raw'
    )

    scenario.h2("WHEN the oracle is updated")
    update = sp.pair(signature, updateData)
    parameter = sp.map(
        l={
            assetCode: update
        },
        tkey=sp.TString,
        tvalue=SignedOracleDataType
    )

    scenario.h2("THEN the update fails")
    scenario += contract.update(parameter).run(valid=False)


@sp.add_test(name="Revokes An Oracle")
def test():
    scenario = sp.test_scenario()
    scenario.h1("Revokes An Oracle")

    scenario.h2(
        "GIVEN an oracle contract and a correctly signed revoke message.")
    message = sp.pack(sp.none)
    signature = sp.make_signature(
        testAccountSecretKey,
        message,
        message_format='Raw'
    )

    assetCode = "XTZ-USD"
    contract = OracleContract(
        publicKey=testAccountPublicKey,
        initialData=sp.big_map(
            l={
                assetCode: initialOracleData
            },
            tkey=sp.TString,
            tvalue=TezosOracle.OracleDataType
        )
    )
    scenario += contract

    scenario.h2("WHEN revoke is called.")
    scenario += contract.revoke(signature)

    scenario.h2("THEN the oracle is revoked")
    scenario.verify(~contract.data.publicKey.is_some())

    scenario.h2("AND future updates fail.")
    start = sp.timestamp(1)
    end = sp.timestamp(2)
    open = 3
    high = 4
    low = 5
    close = 6
    volume = 7
    updateData = (
        start,
        (end,
         (open,
          (high,
           (low,
            (close, volume))))))
    message = sp.pack((assetCode, updateData))
    signature = sp.make_signature(
        testAccountSecretKey,
        message,
        message_format='Raw'
    )

    update = sp.pair(signature, updateData)
    parameter = sp.map(
        l={
            assetCode: update
        },
        tkey=sp.TString,
        tvalue=SignedOracleDataType
    )
    scenario += contract.update(parameter).run(valid=False)


@sp.add_test(name="Incorrect Revoke Fails to Revoke An Oracle")
def test():
    scenario = sp.test_scenario()
    scenario.h1("Incorrect Revoke Fails to Revoke An Oracle")

    scenario.h2(
        "GIVEN an oracle contract and a revoke message signed by another account.")
    testAccount = sp.test_account("Incorrect_Account")
    message = sp.pack(sp.none)
    signature = sp.make_signature(
        testAccount.secret_key,
        message,
        message_format='Raw'
    )

    assetCode = "XTZ-USD"
    contract = OracleContract(
        publicKey=testAccountPublicKey,
        initialData=sp.big_map(
            l={
                assetCode: initialOracleData
            },
            tkey=sp.TString,
            tvalue=TezosOracle.OracleDataType
        )
    )
    scenario += contract

    scenario.h2("WHEN revoke is called")
    scenario.h2("THEN the call fails")
    scenario += contract.revoke(signature).run(valid=False)

    scenario.h2("AND future updates succeed")
    start = sp.timestamp(1)
    end = sp.timestamp(2)
    open = 3
    high = 4
    low = 5
    close = 6
    volume = 7
    updateData = (
        start,
        (end,
         (open,
          (high,
           (low,
            (close, volume))))))
    message = sp.pack((assetCode, updateData))
    signature = sp.make_signature(
        testAccountSecretKey,
        message,
        message_format='Raw'
    )

    update = sp.pair(signature, updateData)
    parameter = sp.map(
        l={
            assetCode: update
        },
        tkey=sp.TString,
        tvalue=SignedOracleDataType
    )
    scenario += contract.update(parameter)

# TODO(keefertaylor): Re-enable.
# @sp.add_test(name = "E2E Push Test")
# def test():
#     scenario = sp.test_scenario()
#     scenario.h1("E2E Push Test")

#     scenario.h2("GIVEN an Oracle contract")
#    assetCode = "XTZ-USD"
#     start = 1
#     end = 2
#     open = 3
#     high = 4
#     low = 5
#     close = 6
#     volume = 7
#     initialData = (
#         sp.timestamp(start),
#         (
#             sp.timestamp(end),
#             (
#                 open,
#                 (
#                     high,
#                     (
#                         low,
#                         (
#                             close,
#                             volume
#                         )
#                     )
#                 )
#             )
#         )
#     )
#     oracle = OracleContract(
#         publicKey = testAccountPublicKey,
#         initialData = sp.big_map(
#             l = {
#                 assetCode: initialData
#             },
#             tkey = sp.TString,
#             tvalue = TezosOracle.OracleDataType
#         )
#     )
#     scenario += oracle

#     scenario.h2("AND a normalizer contract.")
#     normalizer = Normalizer.NormalizerContract(
#         oracleContractAddress = oracle.address
#     )
#     scenario += normalizer

#     scenario.h2("WHEN an update is pushed from the oracle to the normalizer")
#     contractHandle = sp.contract(
#         sp.TBigMap(sp.TString, TezosOracle.OracleDataType),
#         sp.to_address(sp.self),
#         entry_point = "update"
#     ).open_some()
#     scenario += oracle.push(contractHandle)

#     scenario.h2("THEN the normalizer contains the VWAP.")
#     expectedVWAP = TezosOracle.computeVWAP(high, low, close, volume)  // volume
#     scenario.verify(normalizer.data.computedPrice == expectedVWAP)

#####################################################################
# Test Helpers
#####################################################################


# Default Oracle Contract Keys
testAccount = sp.test_account("Test1")
testAccountPublicKey = sp.some(testAccount.public_key)
testAccountSecretKey = testAccount.secret_key

# Initial data for the oracle
initialOracleData = (
    sp.timestamp(0),
    (
        sp.timestamp(0),
        (
            0,
            (
                0,
                (
                    0,
                    (
                        0,
                        0
                    )
                )
            )
        )
    )
)
