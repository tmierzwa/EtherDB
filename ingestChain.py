from datetime import datetime
from chain import connect_chain, read_block, read_transaction
from database import connect_database


# main loop
#
start_timestamp = datetime.now()

blockchain = connect_chain().eth
ethdb = connect_database()
db_blocks = ethdb.blocks1m
db_transactions = ethdb.transactions1m

for blockNumber in range(1000000, 2000000):
    block = read_block(blockNumber, blockchain)
    if block:
        db_blocks.insert_one({key: block[key] for key in block if key != 'transactions'})
        for tx in block['transactions']:
            transaction = read_transaction(tx, block['timestamp'], blockchain)
            db_transactions.insert_one(transaction)
        print("Block: %d, %s tx: %d" % (block['number'], block['timestamp'], len(block['transactions'])))

end_timestamp = datetime.now()
print('Total calculation time: %d s' % (end_timestamp - start_timestamp).total_seconds())
