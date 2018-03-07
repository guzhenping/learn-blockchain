from flask import Flask, jsonify, request
import hashlib
import json
import requests
import time
from uuid import uuid4
from urllib.parse import urlparse


class Blockchain(object):
    def __init__(self):
        self.chain = []
        self.current_transaction = []
        self.nodes = set()

        # 创建创始块(genesis block)
        self.new_block(previous_hash=1, proof=100)

    def register_node(self, address):
        """
        添加一个新的节点到节点集合中.

        :param address: <str> 节点地址, Eg: 'http://192.168.0.5:5000'
        :return: None
        """

        parsed_url = urlparse(address)
        self.nodes.add(parsed_url)

    def valid_chain(self, chain):
        """
        决定一条链是否合法.

        :param chain: <list> 一条链
        :return: <bool> true代表合法, false代表不合法
        """

        last_block = chain[0]
        current_index = 1

        while current_index < len(chain):
            block = chain[current_index]
            print('%s' % last_block)
            print('%s' % block)
            print('\n-------------------\n')

            # 检测这个数据块的hash是否合法
            if block['previous_hash'] != self.hash(last_block):
                return False

            # 检测工作量证明是否合法
            if not self.valid_proof(last_block['proof'], block['proof']):
                return False

            last_block = block
            current_index += 1
        return True

    def resolve_conflicts(self):
        """
        共识算法解决冲突.
        使用网络中最长的链.

        :return: <bool> true 链被取代, false
        """

        neighbours = self.nodes
        new_chain = None

        # 用来寻找最长的链
        max_length = len(self.chain)

        # 遍历所有的节点
        for node in neighbours:
            response = requests.get('http://%s/chain' % node)
            if response.status_code == 200:
                length = response.json()['length']
                chain = response.json()['chain']

                # 检测这条的链的长度,以及是否合法
                if length > max_length and self.valid_chain(chain):
                    max_length = length
                    new_chain = chain

        # 如果找到了最长的链,就替换自己的
        if new_chain:
            self.chain = new_chain
            return True

        return False

    def new_block(self, proof, previous_hash=None):
        """
        创建一个想的数据块,并加入的链上.
        desigh of block: 索引,Unix时间戳,交易列表,工作量证明,前一个区块的hash值. Eg:
        block = {
            'index': 1,
            'timestamp': 1520328303.51874,
            'transactions': [{
                'sender': '0xsdfasdfasdfadsf',
                'recipient': '0xdfkkdskdfjkkkkk',
                'amount': 5
            }],
            'proof': 1,
            'previous_hash': 'sdfasdfakkdkdkklladeste',
        }

        :param proof: <int> 由工作量证明算法(PoW)提供
        :param previous_hash: (Optional) <str> 前一个区块的hash值
        :return: <dict> 一个新的区块
        """

        block = {
            'index': len(self.chain) + 1,
            'timestamp': time.time(),
            'transactions': self.current_transaction,
            'proof': proof,
            'previous_hash': previous_hash or self.hash(self.chain[-1])
        }

        # 把这笔交易信息写入block后,重置变量
        self.current_transaction = []

        self.chain.append(block)
        return block

    def new_transaction(self, sender, recipient, amount):
        """
        添加一个想的交易到交易列表中
        生成一个新的交易信息,信息将加入的像一个带外的区块中.

        :param sender: <str> Sender的地址
        :param recipient: <str> Recipient的地址
        :param amount: <int> 金额
        :return: <int> 将存放这笔交易的区块索引
        """

        self.current_transaction.append({
            'sender': sender,
            'recipient': recipient,
            'amount': amount
        })

        return self.last_block['index'] + 1

    @staticmethod
    def hash(block):
        """
        对一个block进行hash.
        生成block的SHA-256 hash值.

        :param block: <dict> Block
        :return: <str>
        """

        # 必须要确保block是有序的,按时间序列的...否则容易发送hash冲突
        block_string = json.dumps(block, sort_keys=True).encode()
        return hashlib.sha256(block_string).hexdigest()

    @property
    def last_block(self):
        """
        返回链上最新的数据块.

        :return: <dict>
        """

        return self.chain[-1]

    def proof_of_work(self, last_proof):
        """
        一个简单的工作量证明:
        - 查找一个 p' 使得 hash(pp') 以4个0开头
        - p是上一个block的证明, p'是当前block的证明

        :param last_proof: <int> 上一个block的工作量证明
        :return: <int>
        """

        proof = 0
        while self.valid_proof(last_proof, proof) is False:
            proof += 1
        return proof

    @staticmethod
    def valid_proof(last_proof, proof):
        """
        验证: 是否hash(last_proof, proof)以4个0开头?

        :param last_proof: <int> 上一个证明
        :param proof: <int> 当前的证明
        :return: <bool> true代表正确, false代表不行
        """

        guess = ('%s%s' % (last_proof, proof)).encode()
        guess_hash = hashlib.sha256(guess).hexdigest()
        return guess_hash[:4] == "0000"


app = Flask(__name__)

node_identifier = str(uuid4()).replace('-', '')

blockchain = Blockchain()


@app.route('/mine', methods=['GET'])
def mine():
    last_block = blockchain.last_block
    last_proof = last_block['proof']
    proof = blockchain.proof_of_work(last_proof)    # 挖矿, 难度较高时比较耗时间

    # 给工作量证明的节点提供奖励
    # 发送者为 '0'表名是新挖出的的币
    blockchain.new_transaction(
        sender="0",
        recipient='node_identifier',
        amount=1
    )

    # 给链上添加一个新的Block
    block = blockchain.new_block(proof)
    response = {
        'message': "New Block Forged",
        'index': block['index'],
        'transactions': block['transactions'],
        'proof': block['proof'],
        'previous_hash': block['previous_hash']
    }
    return jsonify(response), 200


@app.route('/transactions/new', methods=['POST'])
def new_transaction():
    values = request.get_json()
    required = ['sender', 'recipient', 'amount']
    if not all(k in values for k in required):
        return 'Missing values', 400

    # 创建一个新的交易
    index = blockchain.new_transaction(values['sender'], values['recipient'], values['amount'])
    response = {'message': 'Transaction will be added to Blcok %s' % index}

    return jsonify(response), 201


@app.route('/chain', methods=['GET'])
def full_chain():
    response = {
        'chain': blockchain.chain,
        'length': len(blockchain.chain)
    }
    return jsonify(response), 200


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
