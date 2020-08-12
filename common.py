import smartpy as sp

#####################################################################
# This file defines global types which are used across the Oracle
# and Normalizer contracts.
#####################################################################

# The type of the Oracle's data.
OracleDataType = sp.TPair(
    sp.TTimestamp,                      # Start
    sp.TPair(
        sp.TTimestamp,                  # End
        sp.TPair(
            sp.TNat,                    # Open
            sp.TPair(
                sp.TNat,                # High
                sp.TPair(
                    sp.TNat,            # Low
                    sp.TPair(
                        sp.TNat,        # Close
                        sp.TNat         # Volume
                    )
                )
            )
        )
    )
)

# Compute a VWAP with the given inputs
def computeVWAP(high, low, close, volume):
    return ((high + low + close) // 3) * volume
