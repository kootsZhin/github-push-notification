from connectors.GithubConnector import GithubConnector

solidity = GithubConnector("Solidity", 1, 30)

# print on terminal
solidity.print()

# ping in telegram
solidity.pingTelegram()

# ping on twitter
solidity.pingTwitter()
