# Oracle Contract

## Deploy

```shell
./alpha-client     -P 443     -S     -A tezos-dev.cryptonomic-infra.tech     --wait none     originate     contract ArthurContract4     transferring 0 from tz1XVJ8bZUXs7r5NV8dHvuiBhzECvLRLR3jW     running ../coinbase-oracle/contract/oracle.tz     --init 'Pair
    (Some "sppk7bM2qnLJAci6YE9eCtKL1mHpzR7EsVcZ8Ub2ndQsUuewq8GeRwd")
    {
        Elt "btc-usd" (Pair 1590928740 (Pair 1590928800 (Pair 9559450000 (Pair 9561710000 (Pair 9561710000 (Pair 9559440000 7193127))))));
        Elt "xtz-btc" (Pair 1590928680 (Pair 1590928740 (Pair 305 (Pair 305 (Pair 305 (Pair 305 343000000))))));
        Elt "xtz-usd" (Pair 1590928740 (Pair 1590928800 (Pair 2927500 (Pair 2927500 (Pair 2927500 (Pair 2927500 116310000))))));
    }' --burn-cap 1.668
```

## Update BTC-USD

```shell
./alpha-client -P 443 -S -A tezos-dev.cryptonomic-infra.tech --wait none transfer 0 from tz1XVJ8bZUXs7r5NV8dHvuiBhzECvLRLR3jW  to ArthurContract4 --arg 'Left (Left {Elt "btc-usd" (Pair "spsig1e9rFfniuAoRMvz6nzS1KEHinVmPMh6uJMHnjmhoPhK6mAiJaptNxPenmSyRRM8BqgFgZmDt7VUMiTJjhvzKT4SeqmPiCf" (Pair 1590945420 (Pair 1590945480 (Pair 9511500000 (Pair 9519550000 (Pair 9511490000 (Pair 9516320000 5793139)))))))})'
```

## Update XTZ Pairs

```shell
./alpha-client -P 443 -S -A tezos-dev.cryptonomic-infra.tech --wait none transfer 0 from tz1XVJ8bZUXs7r5NV8dHvuiBhzECvLRLR3jW  to ArthurContract4 --arg 'Left (Left {Elt "xtz-btc" (Pair "spsig17XWiDk9SBJ3nXXctxbPr15i8uvfd8ccyphGXEWyr4ETfUSQR4wTvGoxRa6ULYnMDvzvosmqu8EAHTbtnx4VnGjCjZX1uZ" (Pair 1590945840 (Pair 1590945900 (Pair 299 (Pair 299 (Pair 298 (Pair 298 41920000))))))); Elt "xtz-usd" (Pair "spsig1QRxAi11jNz6EQuu551y1q6rCUp8V2L4br5zZJRbgH6gaHhbE5ejyrAkoJzbPxX98risjG3QSoCF2MoE2xQ8QfVzw71KBW" (Pair 1590945900 (Pair 1590945960 (Pair 2842100 (Pair 2843300 (Pair 2840000 (Pair 2843300 175070000)))))))})'
```

## Revoke Contract

```shell
./alpha-client -P 443 -S -A tezos-dev.cryptonomic-infra.tech --wait none transfer 0 from tz1XVJ8bZUXs7r5NV8dHvuiBhzECvLRLR3jW  to ArthurContract4 --arg 'Left (Right "spsig18Ek8ShSVEQn8WzZxAjQr1pSTSPZj6G9hQ6zvKbQXxd6PvbJY9LeVbEfqzge5JvzqjvauEAHLvmaYT8nfbj7oz2B2eB3hK")'
```

## Push update

Medianizer Contract Address: KT1QypTCmpC9CxR7RdKH958LKeF54PQ5MVEJ
Oracle Contract Address: KT1VWfQLQL2KDZ1J8htBjccSSkLrdC9tQ4xN

Manual:

```shell
tezos-client -P 443 -S -A tezos-dev.cryptonomic-infra.tech --wait none transfer 0.000001 from tz1XVJ8bZUXs7r5NV8dHvuiBhzECvLRLR3jW  to KT1QypTCmpC9CxR7RdKH958LKeF54PQ5MVEJ  --arg '{ Elt "btc-usd" (Pair 1590928740 (Pair 1590928800 (Pair 9559450000 (Pair 9561710000 (Pair 9561710000 (Pair 9559440000 7193127)))))); }'
```

Via Oracle:

```shell
tezos-client -P 443 -S -A tezos-dev.cryptonomic-infra.tech --wait none transfer 0.000001 from tz1XVJ8bZUXs7r5NV8dHvuiBhzECvLRLR3jW  to KT1VWfQLQL2KDZ1J8htBjccSSkLrdC9tQ4xN --arg 'Right "KT1QypTCmpC9CxR7RdKH958LKeF54PQ5MVEJ"'
```
