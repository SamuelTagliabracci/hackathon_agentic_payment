import os
from solathon.core.instructions import transfer
from solathon import Client, Transaction, PublicKey, Keypair

class SolanaTransactionNode:
    def __init__(self, rpc_url="https://api.devnet.solana.com"):
        self.client = Client(rpc_url)

    def send_transaction(self, sender_private_key, receiver_address, amount_in_sol):
        # Convert SOL to lamports
        lamports = int(amount_in_sol * 10**9)

        # Create keypair from private key
        sender = Keypair.from_private_key(sender_private_key)

        # Create transfer instruction
        instruction = transfer(
            from_public_key=sender.public_key,
            to_public_key=PublicKey(receiver_address),
            lamports=lamports
        )

        # Create and send transaction
        transaction = Transaction(instructions=[instruction], signers=[sender])
        result = self.client.send_transaction(transaction)

        return result

def main():
    # Get environment variables
    sender_private_key = os.getenv('SOLANA_SENDER_PRIVATE_KEY')
    receiver_address = os.getenv('SOLANA_RECIPIENT_ADDRESS')
    sol_amount = 0.01

    if not sender_private_key or not receiver_address:
        raise ValueError("Set SOLANA_SENDER_PRIVATE_KEY and SOLANA_RECEIVER_ADDRESS")

    # Create transaction node
    node = SolanaTransactionNode()

    # Send transaction
    result = node.send_transaction(sender_private_key, receiver_address, sol_amount)
    print("Transaction response:", result)

if __name__ == "__main__":
    main()
