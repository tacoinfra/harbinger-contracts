import smartpy as sp

Harbinger = sp.import_script_from_url("file:common.py")
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
        self,
        assetCodes=["XTZ-USD"],
        oracleContractAddress=sp.address(
            "KT1QLPABNCD4z1cSYVv3ntYDYgtWTed7LkYr"),
        numDataPoints=sp.int(3)
    ):
        self.exception_optimization_level = "Unit"
        self.add_flag("no_comment")

        # Set last update timestamp to unix epoch.
        lastUpdateTime = sp.timestamp(0)

        initialValues = {}
        for assetCode in assetCodes:
            # Populate the queues with an initial zero elements
            pricesQueue = fifoDT()
            volumesQueue = fifoDT()

            assetRecord = sp.record(
                prices= pricesQueue,
                volumes= volumesQueue,
                lastUpdateTime= lastUpdateTime,
                computedPrice= 0
            )
            initialValues[assetCode] = assetRecord

        assetMap = sp.big_map(
            l=initialValues,
        )

        self.init(
                assetMap=assetMap,
                assetCodes=assetCodes,
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
        sp.set_type(updateMap, sp.TBigMap(sp.TString, Harbinger.OracleDataType))

        # Verify the sender is the whitelisted oracle contract.
        sp.verify(
            sp.sender == self.data.oracleContract,
            message="bad sender"
        )

        # Iterate over assets this normalizer is tracking
        sp.for assetCode in self.data.assetCodes:
            # Only process updates if this normalizer is tracking the asset code.
            sp.if updateMap.contains(assetCode):
                assetData = updateMap.get(assetCode)

                # Require updates be monotonically increasing in start times.
                updateStartTime = sp.compute(sp.fst(assetData))
                sp.verify(updateStartTime > self.data.assetMap[assetCode].lastUpdateTime)

                # Update the last updated time.
                self.data.assetMap[assetCode].lastUpdateTime = updateStartTime

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
                fifoDT.push(self.data.assetMap[assetCode].prices, volumePrice)
                fifoDT.push(self.data.assetMap[assetCode].volumes, volume)

                # Trim the queue if it exceeds the number of data points.
                sp.if fifoDT.len(self.data.assetMap[assetCode].prices) > self.data.numDataPoints:
                    fifoDT.pop(self.data.assetMap[assetCode].prices)
                    fifoDT.pop(self.data.assetMap[assetCode].volumes)

                # Calculate the volume
                self.data.assetMap[assetCode].computedPrice = self.data.assetMap[assetCode].prices.sum / self.data.assetMap[assetCode].volumes.sum

    # Returns the value in the Normalizer for the given asset.
    #
    # The normalized value is represented as a natural number with six
    # digits of precision. For instance $123.45 USD would be represented
    # as 123_450_000.
    #
    # Parameters a pair of the asset code (ex. XTZ-USD) and a Contract 
    # reference which will be called with the normalized value.
    @sp.entry_point
    def get(self, requestPair):
        # Destructure the arguments.
        requestedAsset = sp.compute(sp.fst(requestPair))
        callback = sp.compute(sp.snd(requestPair))

        # Verify this normalizer has data for the requested asset.
        sp.verify(
            self.data.assetMap.contains(requestedAsset),
            message="bad request"
        )

        # Callback with the requested data.
        requestedData = self.data.assetMap[requestedAsset].computedPrice
        sp.transfer(requestedData, sp.mutez(0), callback)

#####################################################################
# Normalizer Tests
#####################################################################

@sp.add_test(name="Fails with bad contract data")
def test():
    scenario=sp.test_scenario()
    scenario.h1("Fails when data is pushed from bad address")

    scenario.h2("GIVEN a Normalizer contract whitelisted to an address")
    contract=NormalizerContract(
        oracleContractAddress=defaultOracleContractAddress
    )
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

@sp.add_test(name="Fails with updates from the same time")
def test():
    scenario=sp.test_scenario()
    scenario.h1("Fails with updates from the past")

    scenario.h2("GIVEN a Normalizer contract with an update at a given time = 1")
    updateTime=sp.timestamp(1)
    contract=NormalizerContract()
    scenario += contract
    scenario += contract.update(
        makeMap(
            assetCode="XTZ-USD",
            start=updateTime,
            end=sp.timestamp(1595104531),
            open=3059701,
            high=1,
            low=2,
            close=3,
            volume=4
        )
    ).run(sender=defaultOracleContractAddress)

    scenario.h2("WHEN an update is provided at the same time.")
    scenario.h2("THEN the update fails.")
    scenario += contract.update(
        makeMap(
            assetCode="XTZ-USD",
            start=updateTime,
            end=sp.timestamp(1595104531),
            open=3059701,
            high=1,
            low=2,
            close=3,
            volume=4
        )
    ).run(sender=defaultOracleContractAddress, valid=False)

@sp.add_test(name="Fails with updates from the past time")
def test():
    scenario=sp.test_scenario()
    scenario.h1("Fails with updates from the past")

    scenario.h2(
        "GIVEN a Normalizer contract with an update at a current time and a time in the past")
    currentTime=sp.timestamp(2)
    pastTime=sp.timestamp(1)
    contract=NormalizerContract()
    scenario += contract
    scenario += contract.update(
        makeMap(
            assetCode="XTZ-USD",
            start=currentTime,
            end=sp.timestamp(1595104531),
            open=3059701,
            high=1,
            low=2,
            close=3,
            volume=4
        )
    ).run(sender=defaultOracleContractAddress)

    scenario.h2("WHEN an update is provided from the past.")
    scenario.h2("THEN the update fails.")
    scenario += contract.update(
        makeMap(
            assetCode="XTZ-USD",
            start=pastTime,
            end=sp.timestamp(1595104531),
            open=3059701,
            high=1,
            low=2,
            close=3,
            volume=4
        )
    ).run(sender=defaultOracleContractAddress, valid=False)

@sp.add_test(name="Normalizes One Data Point")
def test():
    scenario=sp.test_scenario()
    scenario.h1("Normalizes One Data Point")

    scenario.h2("GIVEN a Normalizer contract.")
    contract=NormalizerContract()
    scenario += contract

    high=1
    low=2
    close=3
    volume=4

    assetCode = "XTZ-USD"

    scenario.h2("WHEN an update is provided")
    scenario += contract.update(
        makeMap(
            assetCode=assetCode,
            start=sp.timestamp(1595104530),
            end=sp.timestamp(1595104531),
            open=3059701,
            high=high,
            low=low,
            close=close,
            volume=volume
        )
    ).run(sender=defaultOracleContractAddress)

    scenario.h2("THEN the ComputedPrice is the VWAP.")
    expected = Harbinger.computeVWAP(
        high=high,
        low=low,
        close=close,
        volume=volume
    ) // volume
    scenario.verify(contract.data.assetMap[assetCode].computedPrice == expected)

@sp.add_test(name="Normalizes Three Data Points")
def test():
    scenario=sp.test_scenario()
    scenario.h1("Normalizes Three Data Points")

    scenario.h2("GIVEN a Normalizer contract")
    contract=NormalizerContract()
    scenario += contract

    scenario.h2("WHEN three updates are provided")
    high1=1
    low1=2
    close1=3
    volume1=4
    assetCode = "XTZ-USD"

    scenario += contract.update(
        makeMap(
            assetCode=assetCode,
            start=sp.timestamp(1595104530),
            end=sp.timestamp(1595104531),
            open=3059701,
            high=high1,
            low=low1,
            close=close1,
            volume=volume1
        )
    ).run(sender=defaultOracleContractAddress)

    high2=5
    low2=6
    close2=7
    volume2=8
    scenario += contract.update(
        makeMap(
            assetCode=assetCode,
            start=sp.timestamp(1595104532),
            end=sp.timestamp(1595104533),
            open=3059701,
            high=high2,
            low=low2,
            close=close2,
            volume=volume2
        )
    ).run(sender=defaultOracleContractAddress)

    high3=9
    low3=10
    close3=11
    volume3=12
    scenario += contract.update(
        makeMap(
            assetCode=assetCode,
            start=sp.timestamp(1595104534),
            end=sp.timestamp(1595104535),
            open=3059701,
            high=high3,
            low=low3,
            close=close3,
            volume=volume3
        )
    ).run(sender=defaultOracleContractAddress)

    scenario.h2("WHEN the ComputedPrice is the VWAP of the updates")
    partialVWAP1 = Harbinger.computeVWAP(
        high=high1,
        low=low1,
        close=close1,
        volume=volume1
    )
    partialVWAP2 = Harbinger.computeVWAP(
        high=high2,
        low=low2,
        close=close2,
        volume=volume2
    )
    partialVWAP3 = Harbinger.computeVWAP(
        high=high3,
        low=low3,
        close=close3,
        volume=volume3
    )
    expected=(partialVWAP1 + partialVWAP2 +
                partialVWAP3) // (volume1 + volume2 + volume3)

    scenario.verify(contract.data.assetMap[assetCode].computedPrice == expected)


@sp.add_test(name="Bounds computation to the number of data points")
def test():
    scenario=sp.test_scenario()
    scenario.h1("Bounds computation to the number of data points")

    scenario.h2("GIVEN a Normalizer contract set to only hold two data points")
    numDataPoints=2
    contract=NormalizerContract(numDataPoints=numDataPoints)
    scenario += contract

    scenario.h2("WHEN three updates are provided")
    high1=1
    low1=2
    close1=3
    volume1=4
    assetCode = "XTZ-USD"

    scenario += contract.update(
        makeMap(
            assetCode=assetCode,
            start=sp.timestamp(1595104530),
            end=sp.timestamp(1595104531),
            open=3059701,
            high=high1,
            low=low1,
            close=close1,
            volume=volume1
        )
    ).run(sender=defaultOracleContractAddress)

    high2=5
    low2=6
    close2=7
    volume2=8
    scenario += contract.update(
        makeMap(
            assetCode=assetCode,
            start=sp.timestamp(1595104532),
            end=sp.timestamp(1595104533),
            open=3059701,
            high=high2,
            low=low2,
            close=close2,
            volume=volume2
        )
    ).run(sender=defaultOracleContractAddress)

    high3=9
    low3=10
    close3=11
    volume3=12
    scenario += contract.update(
        makeMap(
            assetCode=assetCode,
            start=sp.timestamp(1595104534),
            end=sp.timestamp(1595104535),
            open=3059701,
            high=high3,
            low=low3,
            close=close3,
            volume=volume3
        )
    ).run(sender=defaultOracleContractAddress)

    scenario.h2("THEN the contract is only tracking two updates")
    scenario.verify(fifoDT.len(contract.data.assetMap[assetCode].prices) == 2)
    scenario.verify(fifoDT.len(contract.data.assetMap[assetCode].volumes) == 2)

    scenario.h2("AND the computed price is the VWAP of the latter two updates")
    partialVWAP2 = Harbinger.computeVWAP(
        high=high2,
        low=low2,
        close=close2,
        volume=volume2
    )
    partialVWAP3 = Harbinger.computeVWAP(
        high=high3,
        low=low3,
        close=close3,
        volume=volume3
    )
    expected=(partialVWAP2 + partialVWAP3) // (volume2 + volume3)
    scenario.verify(contract.data.assetMap[assetCode].computedPrice == expected)

@sp.add_test(name="Calls back correctly when a valid asset is provided")
def test():
    scenario=sp.test_scenario()
    scenario.h1("Calls back correctly when a valid asset is provided")

    scenario.h2("GIVEN a Normalizer contract")
    assetCode = "XTZ-USD"
    contract=NormalizerContract(assetCodes=[assetCode])
    scenario += contract

    scenario.h2("AND a contract to call back to")
    dummyContract = DummyContract()
    scenario += dummyContract

    scenario.h2("WHEN a request is made")
    contractHandle = sp.contract(
        sp.TNat,
        dummyContract.address,
        entry_point = "callback"
    ).open_some()
    param = (assetCode, contractHandle)

    scenario.h2("THEN it succeeds.")
    scenario += contract.get(param)

@sp.add_test(name="Fails a get request when an invalid asset is provided")
def test():
    scenario=sp.test_scenario()
    scenario.h1("Fails a get request when an invalid asset is provided")

    scenario.h2("GIVEN a Normalizer contract")
    assetCode = "XTZ-USD"
    contract=NormalizerContract(assetCodes=[assetCode])
    scenario += contract

    scenario.h2("AND a contract to call back to")
    dummyContract = DummyContract()
    scenario += dummyContract

    scenario.h2("WHEN a request is made")
    contractHandle = sp.contract(
        sp.TNat,
        dummyContract.address,
        entry_point = "callback"
    ).open_some()
    badAssetCode = "BTC-USD" # Not XTZ-USD
    param = (badAssetCode, contractHandle)

    scenario.h2("THEN it fails.")
    scenario += contract.get(param).run(valid=False)

@sp.add_test(name="Unrelated Assets do not affect normalizer")
def test():
    scenario=sp.test_scenario()
    scenario.h1("Unrelated Assets do not affect normalizer")

    scenario.h2("GIVEN a Normalizer contract")
    contract=NormalizerContract()
    scenario += contract

    scenario.h2("WHEN two updates are provided for the asset")
    high1=1
    low1=2
    close1=3
    volume1=4
    assetCode = "XTZ-USD"

    scenario += contract.update(
        makeMap(
            assetCode=assetCode,
            start=sp.timestamp(1595104530),
            end=sp.timestamp(1595104531),
            open=3059701,
            high=high1,
            low=low1,
            close=close1,
            volume=volume1
        )
    ).run(sender=defaultOracleContractAddress)

    high2=5
    low2=6
    close2=7
    volume2=8
    scenario += contract.update(
        makeMap(
            assetCode=assetCode,
            start=sp.timestamp(1595104532),
            end=sp.timestamp(1595104533),
            open=3059701,
            high=high2,
            low=low2,
            close=close2,
            volume=volume2
        )
    ).run(sender=defaultOracleContractAddress)

    # AND a third update is provided for an unrelated asset
    high3=9
    low3=10
    close3=11
    volume3=12
    scenario += contract.update(
        makeMap(
            assetCode="BTC-USD",                    # Not XTZ-USD
            start=sp.timestamp(1595104534),
            end=sp.timestamp(1595104535),
            open=3059701,
            high=high3,
            low=low3,
            close=close3,
            volume=volume3
        )
    ).run(sender=defaultOracleContractAddress)

    scenario.h2("THEN the contract is only tracking two updates for the tracked asset")
    scenario.verify(fifoDT.len(contract.data.assetMap[assetCode].prices) == 2)
    scenario.verify(fifoDT.len(contract.data.assetMap[assetCode].volumes) == 2)

    scenario.h2("AND the computed price is the VWAP of the two updates")
    partialVWAP1 = Harbinger.computeVWAP(
        high=high1,
        low=low1,
        close=close1,
        volume=volume1
    )
    partialVWAP2 = Harbinger.computeVWAP(
        high=high2,
        low=low2,
        close=close2,
        volume=volume2
    )
    expected=(partialVWAP1 + partialVWAP2) // (volume1 + volume2)
    scenario.verify(contract.data.assetMap[assetCode].computedPrice == expected)

@sp.add_test(name="Computes correctly for multiple assets in parallel")
def test():
    scenario=sp.test_scenario()
    scenario.h1("Computes correctly for multiple assets in parallel")

    scenario.h2("GIVEN a Normalizer contract for two assets")
    assetCode1 = "BTC-USD"
    assetCode2 = "XTZ-USD"
    contract=NormalizerContract(assetCodes = [assetCode1, assetCode2])
    scenario += contract

    scenario.h2("WHEN two updates are provided which touch both assets")
    high1=1
    open1=1
    low1=2
    close1=3
    volume1=4

    high2=5
    open2=5
    low2=6
    close2=7
    volume2=8

    update1 = sp.big_map(
        l={
            assetCode1: makeOracleDataPairs(
                sp.timestamp(1),
                sp.timestamp(2),
                open1,
                high1,
                low1,
                close1,
                volume1
            ),
            assetCode2: makeOracleDataPairs(
                sp.timestamp(1),
                sp.timestamp(2),
                open2,
                high2,
                low2,
                close2,
                volume2
            )
        },
        tkey=sp.TString,
        tvalue=Harbinger.OracleDataType
    )
    scenario += contract.update(
        update1
    ).run(sender=defaultOracleContractAddress)

    high3=9
    open3=9
    low3=10
    close3=11
    volume3=12

    high4=13
    open4=13
    low4=14
    close4=15
    volume4=6

    update2 = sp.big_map(
        l={
            assetCode1: makeOracleDataPairs(
                sp.timestamp(3),
                sp.timestamp(4),
                open3,
                high3,
                low3,
                close3,
                volume3
            ),
            assetCode2: makeOracleDataPairs(
                sp.timestamp(3),
                sp.timestamp(4),
                open4,
                high4,
                low4,
                close4,
                volume4
            )
        },
        tkey=sp.TString,
        tvalue=Harbinger.OracleDataType
    )
    scenario += contract.update(
        update2
    ).run(sender=defaultOracleContractAddress)

    scenario.h2("THEN the contract is only tracking two updates for each asset")
    scenario.verify(fifoDT.len(contract.data.assetMap[assetCode1].prices) == 2)
    scenario.verify(fifoDT.len(contract.data.assetMap[assetCode1].volumes) == 2)
    scenario.verify(fifoDT.len(contract.data.assetMap[assetCode2].prices) == 2)
    scenario.verify(fifoDT.len(contract.data.assetMap[assetCode2].volumes) == 2)

    scenario.h2("AND the computed price is the VWAP of the two updates")
    partialVWAP1 = Harbinger.computeVWAP(
        high=high1,
        low=low1,
        close=close1,
        volume=volume1
    )
    partialVWAP2 = Harbinger.computeVWAP(
        high=high2,
        low=low2,
        close=close2,
        volume=volume2
    )
    partialVWAP3 = Harbinger.computeVWAP(
        high=high3,
        low=low3,
        close=close3,
        volume=volume3
    )
    partialVWAP4 = Harbinger.computeVWAP(
        high=high4,
        low=low4,
        close=close4,
        volume=volume4
    )
    expectedAssetCode1=(partialVWAP1 + partialVWAP3) // (volume1 + volume3)
    expectedAssetCode2=(partialVWAP2 + partialVWAP4) // (volume2 + volume4)

    scenario.verify(contract.data.assetMap[assetCode1].computedPrice == expectedAssetCode1)
    scenario.verify(contract.data.assetMap[assetCode2].computedPrice == expectedAssetCode2)

# TODO: Trim only affects one asset


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
        tvalue=Harbinger.OracleDataType
    )

# A dummy contract which can receive data from a normalizer.
class DummyContract(sp.Contract):
    def __init__(self, **kargs):
        self.init(**kargs)

    @sp.entry_point
    def callback(self, params):
        pass
