class Blockchain(object):
    def __init__(self):
        self.chain = []
        self.current_transaction = []

    def new_block(self):
        # 创建一个想的数据块,并加入的链上
        pass

    def new_transaction(self):
        # 添加一个想的交易到交易列表中
        pass

    @staticmethod
    def hash(block):
        # 对一个block进行hash
        pass

    @property
    def last_block(self):
        # 返回链上最新的数据块
        pass
