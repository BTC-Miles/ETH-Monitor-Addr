import threading
import logging
from web3 import Web3
import time
import tkinter as tk
from tkinter import scrolledtext

# 使用Infura连接以太坊节点，替换为你自己的Infura项目ID
infura_url = "https://mainnet.infura.io/v3/860b13c04ecb4dcb9080a8887ba1b446"
web3 = Web3(Web3.HTTPProvider(infura_url))

# 检查是否成功连接到以太坊节点
if not web3.is_connected():
    raise Exception("无法连接到以太坊节点")

# 初始化日志记录
logging.basicConfig(filename="transaction_history.log", level=logging.INFO,
                    format="%(asctime)s - %(message)s")

# 存储已经监控的地址，避免重复监控
monitored_addresses = set()

class ETHMonitorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("ETH Address Monitor")

        # 创建输入框，用于输入要监控的ETH地址
        tk.Label(root, text="Enter Ethereum Address to Monitor:").grid(row=0, column=0, padx=10, pady=10)
        self.address_entry = tk.Entry(root, width=50)
        self.address_entry.grid(row=0, column=1, padx=10, pady=10)

        # 创建按钮，启动监控
        self.start_button = tk.Button(root, text="Start Monitoring", command=self.start_monitoring)
        self.start_button.grid(row=0, column=2, padx=10, pady=10)

        # 创建输出框，用于显示监控结果
        tk.Label(root, text="Transaction Log:").grid(row=1, column=0, padx=10, pady=10)
        self.log_output = scrolledtext.ScrolledText(root, width=100, height=20)
        self.log_output.grid(row=2, column=0, columnspan=3, padx=10, pady=10)

    def start_monitoring(self):
        address_to_watch = self.address_entry.get().strip()
        if Web3.is_address(address_to_watch):
            address_to_watch = Web3.to_checksum_address(address_to_watch)
            threading.Thread(target=self.monitor_balance_and_transactions, args=(address_to_watch,)).start()
            self.log_output.insert(tk.END, f"Started monitoring: {address_to_watch}\n")
        else:
            self.log_output.insert(tk.END, "Invalid Ethereum address. Please enter a valid address.\n")

    def log_transaction(self, tx, address_to_watch):
        """记录交易信息到日志文件和GUI输出框"""
        log_message = (
            f"检测到交易: {tx['hash'].hex()}\n"
            f"监控地址: {address_to_watch}\n"
            f"来自: {tx['from']}\n"
            f"去向: {tx['to']}\n"
            f"金额: {Web3.from_wei(tx['value'], 'ether')} ETH\n"
        )
        if tx['from'] == address_to_watch:
            log_message += "交易类型: 转出\n"
        if tx['to'] == address_to_watch:
            log_message += "交易类型: 转入\n"

        # 记录到日志文件
        logging.info(log_message.strip().replace("\n", " | "))
        # 输出到GUI
        self.log_output.insert(tk.END, log_message + "\n")

    def monitor_balance_and_transactions(self, address_to_watch):
        """监控余额和交易，并在检测到输出时自动跟进"""
        global monitored_addresses
        initial_balance = web3.eth.get_balance(address_to_watch)
        monitored_addresses.add(address_to_watch)

        while True:
            try:
                latest_block = web3.eth.block_number
                block = web3.eth.get_block(latest_block, full_transactions=True)
                for tx in block.transactions:
                    if tx['from'] == address_to_watch or tx['to'] == address_to_watch:
                        self.log_transaction(tx, address_to_watch)

                        if tx['from'].lower() == address_to_watch.lower() and tx['to'].lower() not in monitored_addresses:
                            new_address = tx['to']
                            self.log_output.insert(tk.END, f"\n检测到新地址: {new_address}，启动监控...\n")
                            threading.Thread(target=self.monitor_balance_and_transactions, args=(new_address,)).start()

                current_balance = web3.eth.get_balance(address_to_watch)
                if current_balance != initial_balance:
                    balance_change = current_balance - initial_balance
                    balance_message = (
                        f"\n余额变化: {Web3.from_wei(balance_change, 'ether')} ETH\n"
                        f"当前余额: {Web3.from_wei(current_balance, 'ether')} ETH\n"
                    )
                    self.log_output.insert(tk.END, balance_message)
                    initial_balance = current_balance  # 更新初始余额

                time.sleep(10)  # 每10秒检查一次

            except Exception as e:
                logging.error(f"发生错误: {str(e)}")
                self.log_output.insert(tk.END, f"发生错误: {str(e)}\n")
                break

if __name__ == "__main__":
    root = tk.Tk()
    app = ETHMonitorApp(root)
    root.mainloop()
