from datetime import datetime
from web3 import Web3


# user exception classes for later use
#
class ProviderError(Exception):
    def __init__(self, hook):
        self.blockchain = hook


class BlockError(Exception):
    def __init__(self, blockchain, block):
        self.blockchain = blockchain
        self.block = block


class ReceiptError(Exception):
    def __init__(self, blockchain, transaction):
        self.blockchain = blockchain
        self.transaction = transaction


# connect to existing chain
#
def connect_chain(http_hook=None, ipc_hook=None, ws_hook=None):
    if http_hook:
        method = 'HTTP'
        provider = Web3.HTTPProvider
        hook = http_hook
    elif ipc_hook:
        method = 'IPC'
        provider = Web3.IPCProvider
        hook = ipc_hook
    elif ws_hook:
        method = 'Websocket'
        provider = Web3.WebsocketProvider
        hook = ws_hook
    else:
        method = 'IPC'
        provider = Web3.IPCProvider
        hook = "\\\\.\\pipe\\geth.ipc"

    try:
        w3 = Web3(provider(hook))
        if w3.isConnected():
            print("Connected to %s: %s with latest block %d." % (method, hook, w3.eth.blockNumber))
            print()
            return w3
        else:
            print('%s connection to %s failed.' % (method, hook))
            return None

    except ProviderError(hook):
        pass


# read block from the blockchain
#
def read_block(block_number, blockchain):

    try:
        raw_block = blockchain.getBlock(block_number, full_transactions=True)

    except BlockError(blockchain, block_number):
        print('Reading block %d failed.' % block_number)
        return None

    block = dict()
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

    transaction = dict()
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
                log = dict()
                log['address'] = raw_log.address
                log['topics'] = raw_log.topics
                log['data'] = raw_log.data
                logs.append(log)
        transaction['logs'] = logs

    except ReceiptError(blockchain, tx.hash):
        print("Error reading receipt for tx: %s" % hash)
        transaction['gas_used'] = 0
        transaction['cost'] = 0
        transaction['contractAddress'] = None
        transaction['logs'] = None

    return transaction
