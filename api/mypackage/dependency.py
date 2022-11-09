from mypackage import schemas
from jose import JWTError, jwt
from fastapi import HTTPException, status, Depends
from mypackage import auth, schemas, crud
from fastapi.security import OAuth2PasswordBearer
from deta import Deta
from web3 import Web3
from decouple import config
import json

#for security
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


#for connecting to the blockchain and retrieving contract
def connectWeb3():
    w3 = Web3(Web3.HTTPProvider(config("ALCHEMY_URL")))
    contract_details = {}
    with open('mypackage/contract.json') as file:
        contract_details = json.load(file)
    raas_contract = w3.eth.contract(address=contract_details.get('address'), abi=contract_details.get('abi'))
    return raas_contract
    
#Dependency - to avail DB
#A lot of inconsistency here
def get_db():
    try:
        deta = Deta ()
        db = deta.Base('raasDB')
        return db
    except:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail = "Opps, something went wrong, kindly try again later")
  
async def get_current_user(token: str = Depends(oauth2_scheme), db = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, auth.SECRET_KEY, algorithms=[auth.ALGORITHM])
        username: str = payload.get("sub")
        if not username:
            raise credentials_exception
        token_data = schemas.TokenData(username=username)
    except JWTError:
        raise credentials_exception
    user = crud.get_user_by_username(db, username=token_data.username)
    if not user:
        raise credentials_exception
    return user

#Users are active by default, will be used if need for email activation
def get_current_active_user(current_user = Depends(get_current_user)):
    if not current_user[0].get("is_active"):
        raise HTTPException(status_code=400, detail="Inactive user - Activate Your Account Via Link Sent To Your Email")
    return current_user