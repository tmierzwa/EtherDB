# EtherDB
Ethereum analytics PoC 

This code is a Proof of Concept for ingesting the Ethereum data into MongoDB and automated processing into analytical cubes.
The whole proces is based on contract ABI and custome Contract Analytical Interface (CAI) JSON file.

Current status:
- ingesting blockchain data (blocks, transactions, and receipts) works fine
- ingesting and parsing contract ABI works fine
- processing transactions into analytical facts works fine
- processing facts into sample cubes works fine

Areas of improvement:
- porting Python to JS or GO
- parsing other types of arguments
- parsing contract code for events emiting method signature instead of event signature
- multi-fact cubes
- BFT architecture
