# margin-foundation

The trust layer of The Margin (margin.report): the hash-chain code that
makes the public forecast ledger tamper-evident. Deliberately tiny —
one file, no dependencies — so anyone can read all of it and re-verify
the published chain themselves.

    ledger/chain.py   append / head / verify · GENESIS_HASH anchor

Verify the live ledger:

    curl -s https://margin.report/api/ledger/chain.json > chain.json
    python3 -c "import json,sys; sys.path.insert(0,'ledger'); import chain; \
      doc=json.load(open('chain.json')); \
      es=[{k:v for k,v in e.items() if k!='resolved'} for e in doc['entries']]; \
      print(chain.verify(es))"

History note: recreated 2026-07-05 after the original (authored in an
ephemeral environment) was lost before ever publishing an entry. The
genesis anchor is unchanged; no published chain ever existed under the
old copy, so there is nothing to migrate and nothing that could have
been rewritten.
