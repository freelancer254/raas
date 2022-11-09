from datetime import timedelta
from fastapi import FastAPI, HTTPException,Body, Depends, status
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.responses import RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from mypackage import crud, schemas, dependency, auth
from web3 import Web3
from decouple import config
import json
import time
import requests
import hmac
from hashlib import sha512

app = FastAPI(title="Random As A Service")

origins = [
	"*"
]

app.add_middleware(
	CORSMiddleware,
	allow_origins=origins,
	allow_credentials=True,
	allow_methods=["*"],
	allow_headers=["*"],
)


#redirect to the docs
@app.get("/", tags=["Docs"])
async def redirect_docs():
	return RedirectResponse("https://raas.deta.dev/docs")

#login and get access token
@app.post("/token", response_model=schemas.Token, tags=["Login"])
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db = Depends(dependency.get_db)):
    user = auth.authenticate_user(form_data.username, form_data.password, db)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=auth.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = auth.create_access_token(
        data={"sub": user[0]["username"]}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}
	

#create new user 
#User provides username, email and password
@app.post("/users/", tags=["Users"])
async def create_user(user: schemas.UserCreate, db = Depends(dependency.get_db)):
    #check if user exists
    if crud.get_user_by_username(db, username=user.username) or crud.get_user_by_email(db, email=user.email):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User already exists")
    return await crud.create_user(db=db, user=user)
   
#get user
@app.get("/users/{username}", tags=["Users"])
def get_user(username: str, db = Depends(dependency.get_db)):
    db_user = crud.get_user_by_username(db, username=username)
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    user_draws = crud.get_user_draws(db, db_user[0]["username"] )
    return {"data":{"username":db_user[0].get("username"), "draws":user_draws}}

#get draws
@app.get("/draws/", tags=["Latest Draws"])
def get_latest_draws( db = Depends(dependency.get_db)):
    latest_draws = crud.get_latest_draws(db) 
    return latest_draws

#get draw using requestId
@app.get("/draw/{requestId}", tags=["Draws"])
def get_draw( requestId: str, db = Depends(dependency.get_db)):
    draw = crud.get_draw(db, requestId)
    if not draw:
        raise HTTPException(status_code=404, detail="Draw not found") 
    return draw

#Request randomWords
@app.post('/random/',  tags = ["Random Words"])
def get_random_words(numWords: int = Body(gt=0, lt=11), callBackUrl: str = Body(), db = Depends(dependency.get_db),
	token: str = Depends(dependency.oauth2_scheme), user: schemas.User = Depends(dependency.get_current_user)):

    #request randomWords
    w3 = Web3(Web3.HTTPProvider(config("ALCHEMY_URL")))
    contract_details = {}
    with open('mypackage/contract.json') as file:
        contract_details = json.load(file)
    raas_contract = w3.eth.contract(address=contract_details.get('address'), abi=contract_details.get('abi'))
    nonce = w3.eth.get_transaction_count(config('ADMIN'))

    #Build tx for requestRandomWords
    tx = raas_contract.functions.requestRandomWords(user[0].get("username"), numWords).buildTransaction({
        'chainId':80001,
        'gas':2500000,
        'maxFeePerGas':w3.toWei('2','gwei'),
        'maxPriorityFeePerGas':w3.toWei('2','gwei'),
        'nonce':nonce
    })
    #sign with private key
    signed_tx = w3.eth.account.sign_transaction(tx, config('PRIVATE_KEY'))
    
    #send signed_tx
    tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)

    #wait for tx to be mined
    tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash)

    #check if tx is successful
    if(tx_receipt.get('status')):
        #process receipt - might fail due to micro timeout of 10s
        requestId = str(raas_contract.events.RandomRequestSent().processReceipt(tx_receipt)[0]['args']['requestId'])
        #create draw object
        draw: dict = {
        "timestamp" : str(int(time.time())),
        "requestId" : requestId,
        "callBackUrl":callBackUrl,
        "numWords" : 0,
        "randomWords" : "",
        "username" : user[0].get("username")
        }
        crud.create_user_draw(db, draw)
        return {'data':{'accepted':True, 'requestId':requestId}}
    
    else:
        #error
        raise HTTPException(status_code=500, detail="Request Not Processed, Kindly try again later") 

@app.get('/fulfilment', tags=['Fulfilment'])
def fulfilment(db = Depends(dependency.get_db)):
    #get the latestRequestId
    w3 = Web3(Web3.HTTPProvider(config("ALCHEMY_URL")))
    contract_details = {}
    with open('mypackage/contract.json') as file:
        contract_details = json.load(file)
    raas_contract = w3.eth.contract(address=contract_details.get('address'), abi=contract_details.get('abi'))
    latest_request_id = raas_contract.functions.latestRequestId().call()
    #retrieve from db
    draw = crud.get_draw_unfulfilled(db, str(latest_request_id))
    #if draw exists
    if draw:
        #retrieve the randomWords from blockchain events based on requestId and username
        request = raas_contract.functions.getRandomRequest(latest_request_id).call()
        if(request[1]):
            #update draw
            crud.update_draw(db, request, draw)
            #send webhook to user
            data = {
                "timestamp":draw[0].get('timestamp'),
                "requestId":draw[0].get('requestId'),
                "numWords":len(request[5]),
                "randomWords":str(request[5])
            }
            #hmac signature
            sig = hmac.new(config('CONSUMER_SECRET').encode("utf-8"), msg=json.dumps(data).encode("utf-8"), digestmod=sha512).hexdigest()
            headers = {'x-raas-signature':sig}
            url = draw[0].get('callBackUrl')
            try:
                requests.post(url, data = json.dumps(data), headers=headers)
            except:
                pass

    return {'accepted':True}