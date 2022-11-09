# RAAS
Random As A Service (RAAS) powered by chainlink. RAAS provides chainlink verifiable Random Function as a simple REST api. RAAS abstracts the complexity of integrating
chainlink services, blockchain technology and decentralized application frontend integration. To use RAAS, there is no need to have a crypto wallet or even crypto itself.
## Demo
This project comprises of three parts, the api, the demoapi to receive webhooks and the User Interface for verification. The User Interface is independent, only reads data
from the blockchain rather than the api.

## To get started, head to:
```
https://raas.deta.dev
```
* [https://raas.deta.dev](https://raas.deta.dev)\
You will find the api specification and documentation.\
You can create an account with a username, password and dummy email\
You can also use the demo user:\
username: demo\
password: demo

## Request RandomWords
To make the post request, you must first be authenticated.

The request takes two parameters:\
numWords: int (1-10)\
callBackUrl: string\
You can use the demo callBackUrl or provide your own.
```
"https://raasdemo.deta.dev/fulfilment"
```
The response is a json object on success and error 500 on error:\
Sample response: 
```
{"accepted":true,
"requestId":"15260532474928153757688577042866486546840004664658265696233553265432660055854"
}
```
## Webhooks
After the randomWords request has been fulfilled, the results are posted to the callBackUrl provided
during the initial request for randomWords.\
A signature is provided in the header for verification: x-raas-signature
```
CONSUMER_SECRET="CGTpgFwSvAXvbLlemYVXLw"
```
Expected Payload:
```
{
  "timestamp":"string", // "1667903417"
  "requestId":"string", // "62417537013408832516397952547060344155328317163732249833545943104538413825859"
  "numWords":int, // 1
  "randomWords":str(request[5]) // "[18530413331264412574886300412089947772531121429925866762427491851193136677172]"
}
```
How to verify: Python

```
import json
import hmac
computed_sig = hmac.new(CONSUMER_SECRET.encode("utf-8"), msg=json.dumps(data).encode("utf-8"), digestmod=sha512).hexdigest()
if x_raas_signature == computed_sig:
  .
  .
  .
```
## Verification
There are four ways to view the returned random words / number.
1. main api
```
https://raas.deta.dev/draws
```
```
https://raas.deta.dev/draw/{requestId}
```
```
https://raas.deta.dev/users/{username}
```

2. Demo API
```
https://raasdemo.deta.dev/randomwords
```
3. Smart Contract\
The smart contract is deployed on the Polygon Mumbai Network.
```
Address: 0x7E0730E81eEceA3c65fc440a1494de2fF1c8939A
```
4. raasdemo.info\
The web app provides a simple and clean user interface for verification of the random words generated.
```
https://raasdemo.info
```
* [https://raasdemo.info](https://raasdemo.info)

## Built With

* [chainlink services](https://chain.link/) - VRF v2, Automation and Connect Any API
* [Polygon Network](https://polygon.technology/) - Smart Contract Deployment
* [Solidity](https://docs.soliditylang.org/en/v0.8.7/) - The smart contract language
* [web3py](https://web3py.readthedocs.io/en/stable/) - For smart contract interaction
* [ethers js](https://docs.ethers.io/v5/) - For smart contract interaction
* [Quasar Framework](https://quasar.dev/) - For template styling and responsiveness
* [FastAPI Framework](https://fastapi.tiangolo.com/) - For the api
* [Deta](https://deta.sh/) - For the cloud hosting

## Authors

* **Robert Mutua** - *Buidling on web3* - [freelancer254](https://github.com/freelancer254)



## Acknowledgments

* Chainlink




