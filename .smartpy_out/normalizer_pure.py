import smartpy as sp

TezosOracle = sp.import_script_from_url("file:common.py")
FifoQueue = sp.import_script_from_url("file:fifo_queue.py")

# We need only one instance of FifoDataType
fifoDT = FifoQueue.FifoDataType()

#####################################################################
# A Normalizer contract normalizes incoming data by computing a
# volume weighted average price (VWAP) across a set number of data
# points.
#
# Normalizers are configured to for one asset whose data is provided
# from one oracle.
#
# Updates sent to the normalizer must be pushed with monotonically
# increasing start times.
#
# The normalized value is represented as a natural number with six
# digits of precision. For instance $123.45 USD would be represented
# as 123_450_000.
#####################################################################

class NormalizerContract(sp.Contract):
    # Create a new Normalizer contract.
    #
    # Parameters:
    #   assetCode(sp.TString): The asset code the Normalizer will normalize
    #   oracleContractAddress(sp.TAddress): The address of the Oracle contract which provides data points.
    #   numDataPoints(sp.TInt): The number of data points to normalize. Larger values provide a better VWAP but result in larger contract storage.
    def __init__(
        self
        # self,
        # assetCode="XTZ-USD",
        # oracleContractAddress=sp.address(
        #     "KT1QLPABNCD4z1cSYVv3ntYDYgtWTed7LkYr"),
        # numDataPoints=sp.int(3)
    ):
        assetCode = "XTZ-USD"
        oracleContractAddress=sp.address("KT1QLPABNCD4z1cSYVv3ntYDYgtWTed7LkYr"),
        numDataPoints=sp.int(3)

        self.exception_optimization_level = "Unit"
        self.add_flag("no_comment")

        assetRecord = sp.record(
            pricesQueue= fifoDT(),
            volumesQueue= fifoDT(),
            lastUpdateTime= sp.timestamp(0),
            computedPrice= 0
        )

        # A map of all assets to their data.
        assetMap = sp.big_map(
            l={
                assetCode: assetRecord
            },
        )

        self.init(assetCode=assetCode,
                  assetMap=assetMap,

                  oracleContract=oracleContractAddress,
                  numDataPoints=numDataPoints
                  )

    # Update the Normalizer contract with a new set of data points.
    #
    # Updates must be:
    # (1) Monotonically increasing in start time.
    # (2) Sent from the whitelisted oracle contract
    # (3) Be for the asset tracked in this Normalizer.
    #
    # Params is a map in the format of:
    # { <asset code | string>: Pair <start time | timestamp > (Pair <end time | timestamp> (Pair <open | nat> Pair( <high | nat> Pair( <low | nat> Pair( <close> <volume>))))) }
    @sp.entry_point
    def update(self, updateMap):
        sp.set_type(updateMap, sp.TBigMap(sp.TString, TezosOracle.OracleDataType))

        # Verify the sender is the whitelisted oracle contract.
        sp.verify(
            sp.sender == self.data.oracleContract,
            message="bad sender"
        )

        # Retrieve the asset data from the map.
        assetData = sp.compute(updateMap[self.data.assetCode])

        # Require updates be monotonically increasing in start times.
        updateStartTime = sp.compute(sp.fst(assetData))
        sp.verify(updateStartTime > self.data.assetMap[self.data.assetCode].lastUpdateTime)

        # Update the last updated time.
        self.data.assetMap[self.data.assetCode].lastUpdateTime = updateStartTime

        # Extract required information
        endPair = sp.compute(sp.snd(assetData))
        openPair = sp.compute(sp.snd(endPair))
        highPair = sp.compute(sp.snd(openPair))
        lowPair = sp.compute(sp.snd(highPair))
        closeAndVolumePair = sp.compute(sp.snd(lowPair))

        # Calculate the the price for this data point.
        # average price * volume
        high = sp.compute(sp.fst(highPair))
        low = sp.compute(sp.fst(lowPair))
        close = sp.compute(sp.fst(closeAndVolumePair))
        volume = sp.compute(sp.snd(closeAndVolumePair))
        volumePrice = ((high + low + close) / 3) * volume

        # Push the latest items to the FIFO queue
        fifoDT.push(self.data.assetMap[self.data.assetCode].prices, volumePrice)
        fifoDT.push(self.data.assetMap[self.data.assetCode].volumes, volume)

        # Trim the queue if it exceeds the number of data points.
        with sp.if_(fifoDT.len(self.data.assetMap[self.data.assetCode].prices) > self.data.numDataPoints):
            fifoDT.pop(self.data.assetMap[self.data.assetCode].prices)
            fifoDT.pop(self.data.assetMap[self.data.assetCode].volumes)

        # Calculate the volume
        self.data.assetMap[self.data.assetCode].computedPrice = self.data.assetMap[self.data.assetCode].prices.sum / self.data.assetMap[self.data.assetCode].volumes.sum

    # Returns the value in the Normalizer.
    #
    # The normalized value is represented as a natural number with six
    # digits of precision. For instance $123.45 USD would be represented
    # as 123_450_000.
    #
    # callback is a Contract reference which will be called with the normalized
    # value.
    @sp.entry_point
    def get(self, callback):
        sp.transfer(self.data.assetMap[self.data.assetCode].computedPrice, sp.mutez(0), callback)

#####################################################################
# Normalizer Tests
#####################################################################

@sp.add_test(name="Fails with bad contract data")
def test():
    scenario=sp.test_scenario()
    scenario.h1("Fails when data is pushed from bad address")

    scenario.h2("GIVEN a Normalizer contract whitelisted to an address")
    contract = NormalizerContract()
    scenario += contract

    scenario.h2("WHEN an update is pushed from the wrong address")
    scenario.h2("THEN the update fails.")
    badAddress=sp.address("KT1FrRkunqmB7futF3EyRwTt8f7fPEVJW39P")
    scenario += contract.update(
        makeMap(
            assetCode="XTZ-USD",
            start=sp.timestamp(1595104501),
            end=sp.timestamp(1595104531),
            open=3059701,
            high=1,
            low=2,
            close=3,
            volume=4
        )
    ).run(sender=badAddress, valid=False)

# @sp.add_test(name="Fails with updates from the same time")
# def test():
#     scenario=sp.test_scenario()
#     scenario.h1("Fails with updates from the past")

#     scenario.h2("GIVEN a Normalizer contract with an update at a given time = 1")
#     updateTime=sp.timestamp(1)
#     contract=NormalizerContract()
#     scenario += contract
#     scenario += contract.update(
#         makeMap(
#             assetCode="XTZ-USD",
#             start=updateTime,
#             end=sp.timestamp(1595104531),
#             open=3059701,
#             high=1,
#             low=2,
#             close=3,
#             volume=4
#         )
#     ).run(sender=defaultOracleContractAddress)

#     scenario.h2("WHEN an update is provided at the same time.")
#     scenario.h2("THEN the update fails.")
#     scenario += contract.update(
#         makeMap(
#             assetCode="XTZ-USD",
#             start=updateTime,
#             end=sp.timestamp(1595104531),
#             open=3059701,
#             high=1,
#             low=2,
#             close=3,
#             volume=4
#         )
#     ).run(sender=defaultOracleContractAddress, valid=False)

# @sp.add_test(name="Fails with updates from the past time")
# def test():
#     scenario=sp.test_scenario()
#     scenario.h1("Fails with updates from the past")

#     scenario.h2(
#         "GIVEN a Normalizer contract with an update at a current time and a time in the past")
#     currentTime=sp.timestamp(2)
#     pastTime=sp.timestamp(1)
#     contract=NormalizerContract()
#     scenario += contract
#     scenario += contract.update(
#         makeMap(
#             assetCode="XTZ-USD",
#             start=currentTime,
#             end=sp.timestamp(1595104531),
#             open=3059701,
#             high=1,
#             low=2,
#             close=3,
#             volume=4
#         )
#     ).run(sender=defaultOracleContractAddress)

#     scenario.h2("WHEN an update is provided from the past.")
#     scenario.h2("THEN the update fails.")
#     scenario += contract.update(
#         makeMap(
#             assetCode="XTZ-USD",
#             start=pastTime,
#             end=sp.timestamp(1595104531),
#             open=3059701,
#             high=1,
#             low=2,
#             close=3,
#             volume=4
#         )
#     ).run(sender=defaultOracleContractAddress, valid=False)


# @sp.add_test(name="Fails with updates for the wrong asset")
# def test():
#     scenario=sp.test_scenario()
#     scenario.h1("Fails with updates from the wrong asset")

#     scenario.h2("GIVEN a Normalizer contract for the bitcoin price")
#     contract=NormalizerContract(assetCode="BTC-USD")
#     scenario += contract

#     scenario.h2("WHEN an update is provided for XTZ-USD")
#     scenario.h2("THEN the update fails.")
#     scenario += contract.update(
#         makeMap(
#             assetCode="XTZ-USD",
#             start=sp.timestamp(1595104530),
#             end=sp.timestamp(1595104531),
#             open=3059701,
#             high=1,
#             low=2,
#             close=3,
#             volume=4
#         )
#     ).run(sender=defaultOracleContractAddress, valid=False)

# @sp.add_test(name="Normalizes One Data Point")
# def test():
#     scenario=sp.test_scenario()
#     scenario.h1("Normalizes One Data Point")

#     scenario.h2("GIVEN a Normalizer contract.")
#     contract=NormalizerContract()
#     scenario += contract

#     high=1
#     low=2
#     close=3
#     volume=4

#     scenario.h2("WHEN an update is provided")
#     scenario += contract.update(
#         makeMap(
#             assetCode="XTZ-USD",
#             start=sp.timestamp(1595104530),
#             end=sp.timestamp(1595104531),
#             open=3059701,
#             high=high,
#             low=low,
#             close=close,
#             volume=volume
#         )
#     ).run(sender=defaultOracleContractAddress)

#     scenario.h2("THEN the ComputedPrice is the VWAP.")
#     expected = TezosOracle.computeVWAP(
#         high=high,
#         low=low,
#         close=close,
#         volume=volume
#     ) // volume
#     scenario.verify(contract.data.computedPrice == expected)

# @sp.add_test(name="Normalizes Three Data Points")
# def test():
#     scenario=sp.test_scenario()
#     scenario.h1("Normalizes Three Data Points")

#     scenario.h2("GIVEN a Normalizer contract")
#     contract=NormalizerContract()
#     scenario += contract

#     scenario.h2("WHEN three updates are provided")
#     high1=1
#     low1=2
#     close1=3
#     volume1=4
#     scenario += contract.update(
#         makeMap(
#             assetCode="XTZ-USD",
#             start=sp.timestamp(1595104530),
#             end=sp.timestamp(1595104531),
#             open=3059701,
#             high=high1,
#             low=low1,
#             close=close1,
#             volume=volume1
#         )
#     ).run(sender=defaultOracleContractAddress)

#     high2=5
#     low2=6
#     close2=7
#     volume2=8
#     scenario += contract.update(
#         makeMap(
#             assetCode="XTZ-USD",
#             start=sp.timestamp(1595104532),
#             end=sp.timestamp(1595104533),
#             open=3059701,
#             high=high2,
#             low=low2,
#             close=close2,
#             volume=volume2
#         )
#     ).run(sender=defaultOracleContractAddress)

#     high3=9
#     low3=10
#     close3=11
#     volume3=12
#     scenario += contract.update(
#         makeMap(
#             assetCode="XTZ-USD",
#             start=sp.timestamp(1595104534),
#             end=sp.timestamp(1595104535),
#             open=3059701,
#             high=high3,
#             low=low3,
#             close=close3,
#             volume=volume3
#         )
#     ).run(sender=defaultOracleContractAddress)

#     scenario.h2("WHEN the ComputedPrice is the VWAP of the updates")
#     partialVWAP1 = TezosOracle.computeVWAP(
#         high=high1,
#         low=low1,
#         close=close1,
#         volume=volume1
#     )
#     partialVWAP2 = TezosOracle.computeVWAP(
#         high=high2,
#         low=low2,
#         close=close2,
#         volume=volume2
#     )
#     partialVWAP3 = TezosOracle.computeVWAP(
#         high=high3,
#         low=low3,
#         close=close3,
#         volume=volume3
#     )
#     expected=(partialVWAP1 + partialVWAP2 +
#                 partialVWAP3) // (volume1 + volume2 + volume3)

#     scenario.verify(contract.data.computedPrice == expected)


# @sp.add_test(name="Bounds computation to the number of data points")
# def test():
#     scenario=sp.test_scenario()
#     scenario.h1("Bounds computation to the number of data points")

#     scenario.h2("GIVEN a Normalizer contract set to only hold two data points")
#     numDataPoints=2
#     contract=NormalizerContract(numDataPoints=numDataPoints)
#     scenario += contract

#     scenario.h2("WHEN three updates are provided")
#     high1=1
#     low1=2
#     close1=3
#     volume1=4
#     scenario += contract.update(
#         makeMap(
#             assetCode="XTZ-USD",
#             start=sp.timestamp(1595104530),
#             end=sp.timestamp(1595104531),
#             open=3059701,
#             high=high1,
#             low=low1,
#             close=close1,
#             volume=volume1
#         )
#     ).run(sender=defaultOracleContractAddress)

#     high2=5
#     low2=6
#     close2=7
#     volume2=8
#     scenario += contract.update(
#         makeMap(
#             assetCode="XTZ-USD",
#             start=sp.timestamp(1595104532),
#             end=sp.timestamp(1595104533),
#             open=3059701,
#             high=high2,
#             low=low2,
#             close=close2,
#             volume=volume2
#         )
#     ).run(sender=defaultOracleContractAddress)

#     high3=9
#     low3=10
#     close3=11
#     volume3=12
#     scenario += contract.update(
#         makeMap(
#             assetCode="XTZ-USD",
#             start=sp.timestamp(1595104534),
#             end=sp.timestamp(1595104535),
#             open=3059701,
#             high=high3,
#             low=low3,
#             close=close3,
#             volume=volume3
#         )
#     ).run(sender=defaultOracleContractAddress)

#     scenario.h2("THEN the contract is only tracking two updates")
#     scenario.verify(fifoDT.len(contract.data.prices) == 2)
#     scenario.verify(fifoDT.len(contract.data.volumes) == 2)

#     scenario.h2("AND the computed price is the VWAP of the latter two updates")
#     partialVWAP2 = TezosOracle.computeVWAP(
#         high=high2,
#         low=low2,
#         close=close2,
#         volume=volume2
#     )
#     partialVWAP3 = TezosOracle.computeVWAP(
#         high=high3,
#         low=low3,
#         close=close3,
#         volume=volume3
#     )
#     expected=(partialVWAP2 + partialVWAP3) // (volume2 + volume3)
#     scenario.verify(contract.data.computedPrice == expected)

#####################################################################
# Test Helpers
#####################################################################

# Default address of the Oracle Contract.
# Exported for convenience
defaultOracleContractAddress=sp.address(
    "KT1QLPABNCD4z1cSYVv3ntYDYgtWTed7LkYr")

# Convenience function to make the data for an Oracle.
def makeOracleDataPairs(start, end, open, high, low, close, volume):
    return (start, (end, (open, (high, (low, (close, volume))))))

# Convenience function to make a map for a single asset code.
def makeMap(assetCode, start, end, open, high, low, close, volume):
    return sp.big_map(
        l={
            assetCode: makeOracleDataPairs(
                start,
                end,
                open,
                high,
                low,
                close,
                volume
            )
        },
        tkey=sp.TString,
        tvalue=TezosOracle.OracleDataType
    )

