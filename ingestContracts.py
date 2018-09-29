from datetime import datetime
from database import connect_database
from contract import get_abi


# main loop
#
start_timestamp = datetime.now()

ethdb = connect_database()
db_contracts = ethdb.contracts
db_transactions = ethdb.transactions

contract_txs = db_transactions.find({'contractAddress': {'$ne': None}})

i = 0
for tx in contract_txs:
    if not i//100:
        print('.', end='', flush=True)

    contract_address = tx['contractAddress']
    decoded, functions, events = get_abi(contract_address)

    contract = dict(address=contract_address,
                    creator=tx['from'],
                    creation_time=tx['timestamp'],
                    creation_tx=tx['hash'],
                    decoded=decoded,
                    functions=functions,
                    events=events)

    db_contracts.insert_one(contract)

    i += 1

print()

print('Creating index...')
db_contracts.create_index('address')

end_timestamp = datetime.now()
print('Total calculation time: %d s' % (end_timestamp - start_timestamp).total_seconds())
