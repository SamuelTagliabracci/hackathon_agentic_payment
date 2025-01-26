import os
from solathon.core.instructions import transfer
from solathon import Client, Transaction, PublicKey, Keypair

client = Client("https://api.devnet.solana.com")

sender = Keypair.from_private_key(os.getenv('SOLANA_SENDER_PRIVATE_KEY'))

receiver = PublicKey("8Pez7F3NspKQLsL5C57jVzfD6vv2ghWuoMHk2x8hmwU5") #Jeff
#receiver = PublicKey("7nBegYE2dmLpdwYR3LAnSprC2X1e3YqrTdLtyY2Nzhgs") #Fabio
#receiver = PublicKey("856BoJkeVqiByHzvWx3h8CT1XdRkfY8knUivsX8dAcAq") #Sam
#receiver = PublicKey("8Pez7F3NspKQLsL5C57jVzfD6vv2ghWuoMHk2x8hmwU5") #Hani
#receiver = PublicKey("") #Brent

sol = 0.01
lamports = int(sol * 10**9)

instruction = transfer(
        from_public_key=sender.public_key,
        to_public_key=receiver,
        lamports=lamports
    )

transaction = Transaction(instructions=[instruction], signers=[sender])

result = client.send_transaction(transaction)
print("Transaction response: ", result)
