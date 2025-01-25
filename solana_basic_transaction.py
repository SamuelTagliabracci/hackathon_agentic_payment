import os
from langchain.agents import AgentType, initialize_agent, Tool
from langchain_community.llms import Ollama
from langchain.tools import BaseTool
from typing import Optional, Type
from pydantic import BaseModel, Field
from solana.rpc.async_api import AsyncClient
from solana.transaction import Transaction
from solana.publickey import PublicKey

class SolanaWalletTool(BaseTool):
    name = "solana_wallet"
    description = "Utility for making SOL token transfers between wallets"
    rpc_url = "https://api.devnet.solana.com"
    #rpc_url = "https://api.mainnet-beta.solana.com"

    class SolanaTransferInput(BaseModel):
        recipient_address: str = Field(..., description="Destination wallet address")
        amount_in_sol: float = Field(..., description="Amount of SOL to transfer")

    args_schema: Type[BaseModel] = SolanaTransferInput

    def __init__(self, sender_private_key: str, rpc_url: str = rpc_url):
        super().__init__()
        self.sender_private_key = sender_private_key
        self.solana_client = AsyncClient(rpc_url)

    async def _make_transfer(self, recipient_address: str, amount_in_sol: float):
        try:
            lamports = int(amount_in_sol * 10**9)
            
            sender_pubkey = PublicKey(self.sender_private_key.public_key())
            recipient_pubkey = PublicKey(recipient_address)
            
            transaction = Transaction().add(
                Transaction.transfer(
                    Transaction.get_transfer_instruction(
                        from_pubkey=sender_pubkey, 
                        to_pubkey=recipient_pubkey, 
                        lamports=lamports
                    )
                )
            )
            
            signed_txn = transaction.sign(self.sender_private_key)
            tx_hash = await self.solana_client.send_transaction(signed_txn)
            
            return f"Transfer successful. Transaction hash: {tx_hash}"
        
        except Exception as e:
            return f"Transfer failed: {str(e)}"

    def _run(self, **kwargs):
        import asyncio
        return asyncio.run(self._make_transfer(
            kwargs['recipient_address'], 
            kwargs['amount_in_sol']
        ))

class AIWalletAgent:
    def __init__(self, solana_private_key: str, model: str = "llama2"):
        # Initialize Ollama language model
        self.llm = Ollama(
            model=model, 
            temperature=0
        )
        
        # Create Solana wallet tool
        solana_tool = SolanaWalletTool(solana_private_key)
        
        # Initialize agent with tools
        self.agent = initialize_agent(
            tools=[solana_tool],
            llm=self.llm,
            agent=AgentType.STRUCTURED_CHAT_ZERO_SHOT_REACT_DESCRIPTION
        )

    def make_purchase(self, recipient_address: str, amount_in_sol: float):
        """Execute a purchase via AI agent"""
        purchase_prompt = (
            f"Make a SOL transfer to {recipient_address} "
            f"for {amount_in_sol} SOL. Use the solana_wallet tool."
        )
        
        return self.agent.run(purchase_prompt)

def main():
    # Ensure Ollama is running and llama3.2 is installed
    solana_private_key = os.getenv("SOLANA_PRIVATE_KEY")
    
    # Create AI wallet agent with Ollama and Llama3.2
    ai_agent = AIWalletAgent(solana_private_key)
    
    # Simulate a purchase

    recipient = "3TXeXnSamcqA8TfXunna8f3LqFuaUzTnRm5VXep7ykQo" #Jeff
    #recipient = "7nBegYE2dmLpdwYR3LAnSprC2X1e3YqrTdLtyY2Nzhgs" #Fabio
    #recipient = "8Pez7F3NspKQLsL5C57jVzfD6vv2ghWuoMHk2x8hmwU5" #Hani

    amount = 0.1  # 0.1 SOL

    result = ai_agent.make_purchase(recipient, amount)
    print(result)

if __name__ == "__main__":
    main()
