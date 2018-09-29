from datetime import datetime
import json, requests, pickle
from web3 import Web3, HTTPProvider


def decodeContractABI(address):

    url = 'https://api.etherscan.io/api'
    params = dict(
        module='contract',
        action='getabi',
        address=address,
        apikey='RDI8SMM3K9DWAF18WHT556ARRI4FVJT76W'
    )
    resp = requests.get(url=url, params=params).json()

    if resp['status'] == '1' and resp['message'] == 'OK':
        abi_dict = json.loads(resp['result'])
        contract_abi = {'functions': {}, 'events': {}}

        for item in abi_dict:
            if 'type' in item:
                if item['type'] in ('function', 'event'):
                    canonical = "%s(" % item['name']
                    parameters = []
                    for i, input in enumerate(item['inputs']):
                        canonical += ("%s" % input['type'])
                        if i < len(item['inputs']) - 1:
                            canonical += ","
                        parameters.append({"name": input['name'], "type": input['type']})
                    canonical += ")"
                    hash = Web3.sha3(text=canonical).hex()
                    if item['type'] == 'function':
                        signature = hash[0:10]
                        contract_abi['functions'][signature] = {'name': item['name'], 'parameters': parameters}
                    else:
                        signature = hash
                        contract_abi['events'][signature] = {'name': item['name'], 'parameters': parameters}
    else:
        contract_abi = {}

    return contract_abi


class contract:

    class function:
        def __init__(self, signature, name, inputs, outputs):
            self.signature = signature
            self.name = name
            self.inputs = inputs
            self.outputs = outputs

        def printf(self, args):
            text = self.name
            return text

    class event:
        def __init__(self, signature, name, parameters):
            self.signature = signature
            self.name = name
            self.paramters = parameters

        def printf(self, params):
            text = self.name
            return text

    class storage:
        def __init__(self):
            self.box = None

    def __init__(self, address):
        self.address = address
        self.name = ''
        self.code = ''
        self.creator = None
        self.genesis = None
        self.storage = None
        self.functions = {}
        self.events = {}

        url = 'https://api.etherscan.io/api'
        params = dict(
            module='contract',
            action='getabi',
            address=address,
            apikey='RDI8SMM3K9DWAF18WHT556ARRI4FVJT76W'
        )
        resp = requests.get(url=url, params=params).json()

        if resp['status'] == '1' and resp['message'] == 'OK':

            self.abi = json.loads(resp['result'])

            for item in self.abi:
                if 'type' in item:
                    if item['type'] == 'function':
                        canonical = "%s(" % item['name']
                        inputs = []
                        for i, input in enumerate(item['inputs']):
                            canonical += ("%s" % input['type'])
                            if i < len(item['inputs']) - 1:
                                canonical += ","
                            inputs.append({"name": input['name'], "type": input['type']})
                        canonical += ")"
                        hash = Web3.sha3(text=canonical).hex()
                        signature = hash[0:10]
                        outputs = []
                        for i, output in enumerate(item['outputs']):
                            outputs.append({"name": output['name'], "type": output['type']})
                        self.functions[signature] = self.function(signature, item['name'], inputs, outputs)

                    elif item['type'] == 'event':
                        canonical = "%s(" % item['name']
                        parameters = []
                        for i, input in enumerate(item['inputs']):
                            canonical += ("%s" % input['type'])
                            if i < len(item['inputs']) - 1:
                                canonical += ","
                            parameters.append({"name": input['name'], "type": input['type']})
                        canonical += ")"
                        hash = Web3.sha3(text=canonical).hex()
                        signature = hash
                        self.events[signature] = self.event(signature, item['name'], parameters)
        else:
            self.abi = None


class transaction:

    class input:
        def __init__(self, message, contract):
            self.raw = message
            self.function_signature = ''
            self.function_arguments = []

            if contract:
                self.function_signature = message[:10]
                message = message[10:]
                for i in range(len(message) // 64):
                    argument = message[i * 64: (i + 1) * 64]
                    self.function_arguments.append(argument)

    class output:
        def __init__(self, receipt):
            self.events = None
            # for log in receipt['logs']:
            #         print('Event address: %s' % log['address'])
            #         for i, topic in enumerate(log['topics']):
            #             print('Event topic %d: %s' % (i, topic.hex()))
            #         data = log['data'][2:]
            #         for i in range(len(data) // 64):
            #             print("Event arg %d: %s" % (i, data[i * 64: (i + 1) * 64]))
            #         if len(data) > (i+1)*64:
            #             print("Event arg %d: %s" % (i+1, data[(i + 1) * 64:]))

    def __init__(self, hash, timestamp):
        global contracts

        self.hash = hash.hex()
        self.block = None
        self.nonce = 0
        self.time = datetime.fromtimestamp(timestamp)
        self.sender = None
        self.receiver = None
        self.value = 0.
        self.status = None
        self.gas_used = 0.
        self.cost = 0.
        self.message = None
        self.receipt = None

        tx = w3.eth.getTransaction(hash)
        if tx is not None:
            self.block = tx.blockNumber
            self.nonce = tx.nonce
            self.sender = tx['from']
            self.receiver = tx.to
            self.value = w3.fromWei(tx.value, 'ether')

            # if self.receiver not in contracts:
            #     contracts[self.receiver] = contract(self.receiver)

            if self.receiver in contracts:
                self.message = self.input(tx.input, contracts[self.receiver])
            else:
                self.message = self.input(tx.input, None)

            rcpt = w3.eth.getTransactionReceipt(tx.hash)
            if rcpt is not None:
                self.status = rcpt.status
                self.gas_used = rcpt.gasUsed
                self.cost = float(w3.fromWei(rcpt.gasUsed * tx.gasPrice, 'ether'))
                if self.receiver in contracts:
                    self.receipt = self.output(rcpt)
            else:
                print("Error reading receipt for tx: %s" % hash)
        else:
            print("Error reading tx: %s" % hash)

    def printf(self):
        print("TX: %s" % self.hash)
        print("    From: %s" % self.sender)
        print("    To: %s" % self.receiver)
        print("    Value: %s" % self.value)
        print("    Input: %s" % self.message.function_signature)
        for i, argument in enumerate(self.message.function_arguments):
            print("    Arg %d: %s" % (i, argument))


class block:

    def __init__(self, block_number):

        mining_reward = 5.

        self.number = block_number
        self.hash = None
        self.time = None
        self.miner = None
        self.reward = 0.

        block = w3.eth.getBlock(block_number)
        if block is not None:
            self.hash = block.hash.hex()
            if block.timestamp != 0:
                self.time = datetime.fromtimestamp(block.timestamp)
            self.miner = block.miner
            self.reward = mining_reward * (1 + len(block.uncles)/32)
        else:
            print("Error reading block: %d" % block_number)

        self.printf()

        for tx_hash in block.transactions:
            tx = transaction(tx_hash, block.timestamp)
            self.reward += tx.cost
            if tx.receiver == '0x06012c8cf97BEaD5deAe237070F9587f8E7A266d':
                tx.printf()

    def printf(self):
        print("Block: %d %s" % (self.number, self.time))


def connectChain(ip):
    w3 = Web3(HTTPProvider('https://mainnet.infura.io/ubiNQxis8bBSZFdQbnSs'))
    # w3 = Web3(HTTPProvider('http://%s:8545' % ip))
    print("Connected with latest block: ", w3.eth.blockNumber)
    print()
    return w3


def readChain(w3, fromBlock=1, toBlock=None):
    blockNum = fromBlock
    if toBlock is None:
        toBlock = w3.eth.blockNumber

    # iterate blocks
    while blockNum <= toBlock:
        bl = block(blockNum)
        blockNum += 1

    return


w3 = connectChain('34.244.1.28')
start_timestamp = datetime.now()

# read and unpickle saved contracts
print('Reading contracts ABI.')
try:
    with open('contracts.abi', 'rb') as f:
        contracts = pickle.load(f)
except:
    contracts = {}

readChain(w3, 4605167, 4606000)

# pickle and save contracts
print('Storing contracts ABI.')
with open('contracts.abi', 'wb') as f:
    pickle.dump(contracts, f)

end_timestamp = datetime.now()
print('Total calculation time: %d s, %d tx' % ((end_timestamp - start_timestamp).total_seconds(), transactions))

# ToDO: Genesis block