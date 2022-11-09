from fastapi import FastAPI, HTTPException,Body, status, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
import hmac
from hashlib import sha512
import json
from deta import Deta

app = FastAPI(title="RAAS Demo Consumer")
CONSUMER_SECRET="CGTpgFwSvAXvbLlemYVXLw"

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
	return RedirectResponse("https://raasdemo.deta.dev/docs")

#receive webhook
@app.post("/fulfilment", tags=["RandomFulfilment"])
async def fulfilment(data : dict = Body(), x_raas_signature: str= Header(default=None)):
    #verify signature
	computed_sig = hmac.new(CONSUMER_SECRET.encode("utf-8"), msg=json.dumps(data).encode("utf-8"), digestmod=sha512).hexdigest()
	if x_raas_signature == computed_sig:
		#write to detabase
		deta = Deta()
		db = deta.Base('raasdemoDB')
		db.put(data)
	else:
		raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Signature",
        )
	return {"accepted":True}

#display received random fulfilments
@app.get('/randomwords',tags=['Random Words Received'])
async def random():
	deta = Deta()
	db = deta.Base('raasdemoDB')	
	return {"data":db.fetch().items}


