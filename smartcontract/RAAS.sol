// SPDX-License-Identifier: MIT

pragma solidity ^0.8.0;

import "@chainlink/contracts/src/v0.8/ChainlinkClient.sol";
import "@chainlink/contracts/src/v0.8/interfaces/VRFCoordinatorV2Interface.sol";
import "@chainlink/contracts/src/v0.8/VRFConsumerBaseV2.sol";



contract RAAS is VRFConsumerBaseV2, ChainlinkClient {
    using Chainlink for Chainlink.Request;
    VRFCoordinatorV2Interface COORDINATOR;

    //events
    event RandomRequestSent(string indexed username, uint256 requestId, uint8 numWords);
    event RandomRequestFulfilled( uint256 requestId, uint256[] randomWords);
    event RandomRequestFulfilmentComplete( string indexed username, string refUsername, uint256 requestId, uint256[] randomWords, uint256 timestamp);

    // Set to Max
    uint32 callbackGasLimit = 2500000;

    // The default is 3, but you can set this higher.
    uint16 requestConfirmations = 3;

    // For this example, retrieve X as specified in the request random values in one request.
    // Cannot exceed VRFCoordinatorV2.MAX_NUM_WORDS. 500 for polygon mumbai

    // Addresses
    address vrfCoordinator;
    bytes32 keyHash;
    //required by connect any api
    bytes32 jobId;
    uint256 fee;

    // Storage parameters
    uint256 public  latestRequestId = 0;
    uint64 subscriptionId;
    uint256[] public requestIds; // to store fulfilled requestIds, will be used by frontend to fetch fulfilled random requests

    address owner;
    struct PendingRandomFulfilment{
        bool valid;
        uint256 requestId;
        uint256[] randomWords;
    }
    struct RandomRequest{
        bool valid;
        bool fulfilled;
        string username;
        uint8 numWords;
        uint256 timestamp;
        uint256[] randomWords;
    }
    mapping(uint256 => RandomRequest) public randomRequests;
    mapping(uint256 => PendingRandomFulfilment) public pendingRandomFulfilment; // to store random words that should be relayed to the backend

    constructor(
        address _vrfCoordinator,
        bytes32 _keyHash,
        uint64 _subscriptionId
    ) VRFConsumerBaseV2(_vrfCoordinator) {
        keyHash = _keyHash;
        vrfCoordinator = _vrfCoordinator;
        COORDINATOR = VRFCoordinatorV2Interface(vrfCoordinator);
        subscriptionId = _subscriptionId;
        owner = msg.sender;
        setChainlinkToken(0x326C977E6efc84E512bB9C30f76E30c160eD06FB);
        setChainlinkOracle(0x40193c8518BB267228Fc409a613bDbD8eC5a97b3);
        jobId = 'c1c5e92880894eb6b27d3cae19670aa3'; //get bool
        fee = (1 * LINK_DIVISIBILITY) / 10; // 0,1 * 10**18 (Varies by network and job)
    }


    // Assumes the subscription is funded sufficiently.
    function requestRandomWords(string memory _username, uint8 _numWords) public onlyOwner returns (uint256 requestId) {

        //cannot request if there is a pending request
        //avoid making multiple requests, it will make vrf not fulfill random words request
        if(latestRequestId != 0){
        require(randomRequests[latestRequestId].valid && randomRequests[latestRequestId].fulfilled,'Pending Request Not Fulfilled');
        }
        // Will revert if subscription is not set and funded.
        requestId = COORDINATOR.requestRandomWords(
            keyHash,
            subscriptionId,
            requestConfirmations,
            callbackGasLimit,
            _numWords
        );
        //create new Request object
        randomRequests[requestId] = RandomRequest({valid:true, fulfilled:false,username:_username,numWords:_numWords,timestamp:block.timestamp,randomWords: new uint256[](0)});
        latestRequestId = requestId;
        //emit event
        emit RandomRequestSent(_username, requestId, _numWords);
        return requestId;
    }

    function fulfillRandomWords(
        uint256 _requestId,
        uint256[] memory _randomWords
    ) internal  override {
        //to avoid this fxn reverting, just store the random words
        //logic will be executed in another fxn - manually or using chainlink automation
        pendingRandomFulfilment[0] = PendingRandomFulfilment({valid: true, requestId:_requestId, randomWords:_randomWords});
        //emit event
        emit RandomRequestFulfilled(_requestId, _randomWords);
    }

    //gets the status of a random request
    function getRandomRequest(uint256 _requestId) external view returns(RandomRequest memory request){
        require(randomRequests[_requestId].valid, 'Invalid Request Id');
        request = randomRequests[_requestId];
        return(request);
    }

    //gets all the requestIds
    function getRequestIds() external view returns(uint256[] memory){
        return requestIds;
    }

   //for chainlink automation
    function checkUpkeep(bytes calldata /* checkData */ ) external view  returns (bool upkeepNeeded, bytes memory performData) {
    //upkeepNeeded when the pendingRandomRequest is valid
    if(pendingRandomFulfilment[0].valid){
        upkeepNeeded = true;
    }
    return (upkeepNeeded, '');

}
    //will be executed by chainlink automation when the pendingRandomFulfilment contains
    function performUpkeep(bytes calldata /* performData */) external {
    //Revalidating that there is a pending fulfilment
        if (pendingRandomFulfilment[0].valid){
        PendingRandomFulfilment memory pending = pendingRandomFulfilment[0];

        //logic for the randomWords
        //make sure exists and not already fulfilled
        require(randomRequests[pending.requestId].valid && !randomRequests[pending.requestId].fulfilled,'Invalid Request' );
        randomRequests[pending.requestId].fulfilled = true;
        randomRequests[pending.requestId].randomWords = pending.randomWords;

        //reset
        pendingRandomFulfilment[0] = PendingRandomFulfilment({valid:false, requestId:0, randomWords: new uint256[](0)});

        //add requestId to requestIds array
        requestIds.push(pending.requestId);

        //emit event
        emit RandomRequestFulfilmentComplete(randomRequests[pending.requestId].username, randomRequests[pending.requestId].username, pending.requestId, pending.randomWords, randomRequests[pending.requestId].timestamp);

        //connect to chainlink any api
        Chainlink.Request memory req = buildChainlinkRequest(jobId, address(this), this.fulfill.selector);
        //url
        req.add('get','https://raas.deta.dev/fulfilment');
        req.add('path','accepted'); //path
        //send request
        sendChainlinkRequest(req, fee);
        }
    }

    //do nothing
    function fulfill(bytes32 _requestId, bool _approved) public recordChainlinkFulfillment(_requestId) {

    }
    //withdraw link from contract
    function withdrawLink() public onlyOwner{
        LinkTokenInterface link = LinkTokenInterface(chainlinkTokenAddress());
        require(link.transfer(msg.sender, link.balanceOf(address(this))), 'Unable to tranfer Link Balance');
    }

    modifier onlyOwner() {
        require(msg.sender == owner);
        _;
    }
}
