from datetime import datetime
import json, requests, pickle
from web3 import Web3

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


def connectChain(ip):
    # w3 = Web3(HTTPProvider('https://mainnet.infura.io/ubiNQxis8bBSZFdQbnSs'))
    # w3 = Web3(HTTPProvider('http://%s:8545' % ip))
    w3 = Web3(Web3.IPCProvider("\\\\.\\pipe\\geth.ipc"))
    print("Connected with latest block: ", w3.eth.blockNumber)
    print()
    return w3


def readContract(w3, contract_hash, fromBlock=1, toBlock=None):

    tx_file = open('tx.csv', 'w')
    event_file = open('event.csv', 'w')

    block_number = fromBlock
    if toBlock is None:
        toBlock = w3.eth.blockNumber

    # read contract ABI
    main_contract = contract(contract_hash)
    other_contracts = {}
    mining_reward = 5.

    # iterate blocks
    while block_number <= toBlock:

        block_time = 0
        block_reward = mining_reward

        block = w3.eth.getBlock(block_number, full_transactions=True)
        print(block_number, len(block.transactions))

        if block is not None:
            block_hash = block.hash.hex()
            block_time = block.timestamp
            block_miner = block.miner
            block_reward += mining_reward * len(block.uncles) / 32
        else:
            print("Error reading block: %d" % block_number)
            return

        for tx in block.transactions:

            # tx = w3.eth.getTransaction(tx_hash)
            tx_hash = tx.hash.hex()

            if tx is not None:

                tx_cost = 0.

                if tx.to == contract_hash:
                    tx_block = tx.blockNumber
                    tx_nonce = tx.nonce
                    tx_sender = tx['from']
                    tx_receiver = tx.to
                    tx_value = w3.fromWei(tx.value, 'ether')

                    tx_message_raw = tx.input
                    tx_message_function_signature = tx_message_raw[:10]

                    tx_message_function_arguments = []
                    arguments = tx_message_raw[10:]
                    for i in range(len(arguments) // 64):
                        argument_value = arguments[i * 64: (i + 1) * 64]
                        tx_message_function_arguments.append(argument_value)

                    rcpt = w3.eth.getTransactionReceipt(tx_hash)
                    if rcpt is not None:
                        tx_status = rcpt.status
                        tx_gas_used = rcpt.gasUsed
                        tx_cost = float(w3.fromWei(rcpt.gasUsed * tx.gasPrice, 'ether'))

                        tx_events = []
                        for log in rcpt['logs']:
                            tx_event_address = log['address']
                            if tx_event_address == main_contract.address:
                                this_contract = main_contract
                            else:
                                if tx_event_address not in other_contracts:
                                    other_contracts[tx_event_address] = contract(tx_event_address)
                                this_contract = other_contracts[tx_event_address]

                            tx_event_topics = []
                            for i, topic in enumerate(log['topics']):
                                tx_event_topics.append(topic.hex())
                            data = log['data'][2:]
                            tx_event_parameters = []
                            for i in range(len(data) // 64):
                                parameter_value = data[i * 64: (i + 1) * 64]
                                tx_event_parameters.append(parameter_value)

                            # if len(data) > (i+1)*64:
                            #     parameter_value = data[(i + 1) * 64:]

                            tx_events.append((tx_event_address, tx_event_topics, tx_event_parameters))

                    else:
                        print("Error reading receipt for tx: %s" % tx_hash)
                        return

                    print("Block: %d %s" % (block_number, datetime.fromtimestamp(block_time)))
                    print("   Tx: %s" % tx_hash)
                    print(" From: %s" % tx_sender)
                    print("   To: %s" % tx_receiver)
                    print("Value: %s ETH" % tx_value)

                    print("Input: %s(" % main_contract.functions[tx_message_function_signature].name, end='')
                    for i, argument in enumerate(tx_message_function_arguments):
                        argument_type = main_contract.functions[tx_message_function_signature].inputs[i]['type']
                        if argument_type == 'address':
                            argument_value = '0x' + argument[-40:]
                        elif argument_type in ('uint256'):
                            argument_value = int(argument, 16)
                        else:
                            argument_value = argument
                        print("%s=%s" % (main_contract.functions[tx_message_function_signature].inputs[i]['name'], argument_value), end='')
                        if i+1 < len(tx_message_function_arguments):
                            print(", ", end='')
                    print(')')

                    max_arguments = 4
                    tx_record = ''
                    for field in [tx_hash, block_time, tx_sender, tx_receiver, tx_value, tx_cost, tx_message_function_signature]:
                        tx_record += str(field)+';'
                    for i in range(max_arguments):
                        if i < len(tx_message_function_arguments):
                            argument = tx_message_function_arguments[i]
                        else:
                            argument = ''
                        tx_record += argument
                        if i < max_arguments - 1:
                            tx_record += ';'
                    tx_record += '\n'
                    tx_file.write(tx_record)

                    for event in tx_events:
                        if event[0] == main_contract.address:
                            this_contract = main_contract
                        else:
                            this_contract = other_contracts[event[0]]

                        print("Event: %s(" % this_contract.events[event[1][0]].name, end='')
                        for i, parameter in enumerate(event[2]):
                            parameter_type = this_contract.events[event[1][0]].paramters[i]['type']
                            if parameter_type == 'address':
                                parameter_value = '0x' + parameter[-40:]
                            elif parameter_type in ('uint256'):
                                parameter_value = int(parameter, 16)
                            else:
                                parameter_value = parameter

                            print("%s=%s" % (this_contract.events[event[1][0]].paramters[i]['name'], parameter_value),
                                  end='')
                            if i + 1 < len(event[2]):
                                print(", ", end='')
                        print(')')

                        max_parameters = 5
                        event_record = ''
                        for field in [tx_hash, block_time, event[0], event[1][0]]:
                            event_record += str(field) + ';'
                        for i in range(max_parameters):
                            if i < len(event[2]):
                                parameter = event[2][i]
                            else:
                                parameter = ''
                            event_record += parameter
                            if i < max_parameters - 1:
                                event_record += ';'
                        event_record += '\n'
                        event_file.write(event_record)

                    print()

                block_reward += tx_cost

            else:
                print("Error reading tx: %s" % tx_hash)
                return

        block_number += 1

    tx_file.close()
    event_file.close()

    return


start_timestamp = datetime.now()

contract_hash = '0x06012c8cf97BEaD5deAe237070F9587f8E7A266d'
# contract_hash = '0xba2184520A1cC49a6159c57e61E1844E085615B6'
start_block = 6272342

w3 = connectChain('localhost')
readContract(w3, contract_hash, start_block, start_block+100)

end_timestamp = datetime.now()
print('Total calculation time: %d s' % (end_timestamp - start_timestamp).total_seconds())