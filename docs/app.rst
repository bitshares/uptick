************************
Full uptick Command List
************************

Swiss army knife for interacting with the BitShares blockchain.

::

    $ uptick --help
    Usage: uptick [OPTIONS] COMMAND [ARGS]...

    Options:
      --debug / --no-debug            Enable/Disable Debugging (no-broadcasting
                                      mode)
      --node TEXT                     Websocket URL for public BitShares API
                                      (default: "wss://this.uptick.rocks/")
      --rpcuser TEXT                  Websocket user if authentication is required
      --rpcpassword TEXT              Websocket password if authentication is
                                      required
      -d, --nobroadcast / --broadcast
                                      Do not broadcast anything
      -x, --unsigned / --signed       Do not try to sign the transaction
      -e, --expires INTEGER           Expiration time in seconds (defaults to 30)
      -v, --verbose INTEGER           Verbosity (0-15)
      --version                       Show version
      --help                          Show this message and exit.

    Commands:
      addkey                  Add a private key to the wallet
      allow                   Add a key/account to an account's permission
      api                     Open an local API for trading bots
      approvecommittee        Approve committee member(s)
      approveproposal         Approve a proposal
      approvewitness          Approve witness(es)
      balance                 Show Account balances
      broadcast               Broadcast a json-formatted transaction
      buy                     Buy a specific asset at a certain rate...
      cancel                  Cancel one or multiple orders
      changewalletpassphrase  Change the wallet passphrase
      configuration           Show configuration variables
      delkey                  Delete a private key from the wallet
      disallow                Remove a key/account from an account's...
      disapprovecommittee     Disapprove committee member(s)
      disapproveproposal      Disapprove a proposal
      disapprovewitness       Disapprove witness(es)
      feeds                   Price Feed Overview
      getkey                  Obtain private key in WIF format
      history                 Show history of an account
      info                    Obtain all kinds of information
      listaccounts            List accounts (for the connected network)
      listkeys                List all keys (for all networks)
      newaccount              Create a new account
      newfeed                 Publish a price feed! Examples:  uptick...
      openorders              List open orders of an account
      orderbook               Show the orderbook of a particular market
      permissions             Show permissions of an account
      proposals               List proposals
      randomwif               Obtain a random private/public key pair
      sell                    Sell a specific asset at a certain rate...
      set                     Set configuration parameters
      sign                    Sign a json-formatted transaction
      ticker                  Show ticker of a market
      trades                  List trades in a market
      transfer                Transfer assets
      upgrade                 Upgrade Account
