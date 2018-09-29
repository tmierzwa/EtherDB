from datetime import datetime
from database import connect_database
from contract import decode_contract_tx

ADDRESS = '0x06012c8cf97BEaD5deAe237070F9587f8E7A266d'


# main loop
#
start_timestamp = datetime.now()

ethdb = connect_database()
db_contracts = ethdb.contracts
db_transactions = ethdb.transactions
db_facts = ethdb.facts

contract_abi = db_contracts.find({'address': ADDRESS})[0]
contract_txs = db_transactions.find({'to': ADDRESS})

for i, tx in enumerate(contract_txs):

    if not i % 100:
        print('.', end='', flush=True)
    if not i % 1000:
        print(i)

    contract_facts = decode_contract_tx(tx, contract_abi, db_contracts)
    for fact in contract_facts:
        db_facts.insert_one(fact)

print()

end_timestamp = datetime.now()
print('Total calculation time: %d s' % (end_timestamp - start_timestamp).total_seconds())
