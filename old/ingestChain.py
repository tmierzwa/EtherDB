from datetime import datetime
from pymongo import MongoClient
from web3 import Web3


# connect to database
#
def connectDatabase(host='localhost', port=27017):
    mongo = MongoClient(host=host, port=port)
    blocks = mongo.ethdb.blocks
    transactions = mongo.ethdb.transactions

    return blocks, transactions


# connect to existing chain
#
def connectChain(httpHook=None, ipcHook=None, wsHook=None):
    if httpHook:
        method = 'HTTP'
        provider = Web3.HTTPProvider
        hook = httpHook
    elif ipcHook:
        method = 'IPC'
        provider = Web3.IPCProvider
        hook = ipcHook
    elif wsHook:
        method = 'Websocket'
        provider = Web3.WebsocketProvider
        hook = wsHook
    else:
        method = 'IPC'
        provider = Web3.IPCProvider
        hook = "\\\\.\\pipe\\geth.ipc"

    try:
        w3 = Web3(provider(hook))
    except:
        pass

    if w3.isConnected():
        print("Connected to %s: %s with latest block %d." % (method, hook, w3.eth.blockNumber))
        print()
        return w3
    else:
        print('%s connetion to %s failed.' % (method, hook))
        return None


# read block from the blockchain
#
def read_block(block_number, blockchain):

    try:
        raw_block = blockchain.getBlock(block_number, full_transactions=True)
    except:
        print('Reading block %d failed.' % block_number)
        return None

    block = {}
    block['number'] = raw_block.number
    if raw_block.timestamp != 0:
        block['timestamp'] = datetime.fromtimestamp(raw_block.timestamp)
    else:
        block['timestamp'] = raw_block.timestamp
    block['hash'] = raw_block.hash.hex()
    block['parentHash'] = raw_block.parentHash.hex()
    block['gasUsed'] = raw_block.gasUsed
    block['miner'] = raw_block.miner
    block['transactions'] = raw_block.transactions

    return block


# create transaction and read its receipt from the blockchain
#
def read_transaction(tx, timestamp, blockchain):

    transaction = {}
    transaction['hash'] = tx.hash.hex()
    transaction['blockNumber'] = tx.blockNumber
    transaction['nonce'] = tx.nonce
    transaction['timestamp'] = timestamp
    transaction['from'] = tx['from']
    transaction['to'] = tx.to
    transaction['value'] = str(tx.value)
    transaction['input'] = tx.input

    try:
        raw_receipt = blockchain.getTransactionReceipt(tx.hash)
        transaction['gas_used'] = raw_receipt.gasUsed
        transaction['cost'] = str(raw_receipt.gasUsed * tx.gasPrice)
        transaction['contractAddress'] = raw_receipt.contractAddress
        logs = []
        for raw_log in raw_receipt.logs:
            if not raw_log.removed:
                log = {}
                log['address'] = raw_log.address
                log['topics'] = raw_log.topics
                log['data'] = raw_log.data
                logs.append(log)
        transaction['logs'] = logs
    except:
        print("Error reading receipt for tx: %s" % hash)
        transaction['gas_used'] = 0
        transaction['cost'] = 0
        transaction['contractAddress'] = None
        transaction['logs'] = None

    return transaction


# main loop
#
start_timestamp = datetime.now()

blockchain = connectChain().eth
db_blocks, db_transactions = connectDatabase()

for blockNumber in range(4600000, 5000000):
    block = read_block(blockNumber, blockchain)
    if block:
        db_blocks.insert_one({key: block[key] for key in block if key != 'transactions'})
        for tx in block['transactions']:
            transaction = read_transaction(tx, block['timestamp'], blockchain)
            db_transactions.insert_one(transaction)
        print("Block: %d, %s tx: %d" % (block['number'], block['timestamp'], len(block['transactions'])))


end_timestamp = datetime.now()
print('Total calculation time: %d s' % (end_timestamp - start_timestamp).total_seconds())