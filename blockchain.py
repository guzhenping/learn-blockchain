from flask import Flask
import hashlib
import json
import time
from uuid import uuid4


class Blockchain(object):
    def __init__(self):
        self.chain = []
        self.current_transaction = []

        # 创建创始块(genesis block)
        self.new_block(previous_hash=1, proof=100)

    def new_block(self, proof, previous_hash=None):
        """
        创建一个想的数据块,并加入的链上.
        desigh of block: 索引,Unix时间戳,交易列表,工作量证明,前一个区块的hash值. eg:
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
        return hashlib.sha256(block_string).hexdiest()

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

        guess = '{last_proof}{proof}'.format(last_proof, proof)
        guess_hash = hashlib.sha256(guess).hexdigest()
        return guess_hash[:4] == "0000"


app = Flask(__name__)

node_identifier = str(uuid4()).replace('-', '')

blockchain = Blockchain()


@app.route('/mine', methods=['GET'])
def mine():
    return 'Will add a new block'


@app.route('/transactions/new', methods=['GET'])
def new_transaction():
    return 'Will add a new transaction'


@app.route('/chain', methods=['GET'])
def full_chain():
    response = {
        'chain': blockchain.chain,
        'length': len(blockchain.chain)
    }
    return json.jsonify(response), 200


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)