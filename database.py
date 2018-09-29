from pymongo import MongoClient


# user exception classes for later use
#
class ClientError(Exception):
    def __init__(self, host, port):
        self.host = host
        self.port = port


# connect to database
#
def connect_database(host='localhost', port=27017):
    try:
        mongo = MongoClient(host=host, port=port)
        ethdb = mongo.ethdb
        return ethdb

    except ClientError(host, port):
        return None
