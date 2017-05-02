var ISSChatApp = angular.module('ISSChatApp', ['ngSanitize']);

ISSChatApp.controller('ChatController', function($scope, $sce) {
    var socket = io.connect('https://' + document.domain + ':' +
        location.port + '/iss');
        
    $scope.rooms = [];
    
    $scope.messages = [];
    $scope.searchResults = [];
    $scope.subscriptions = [];
    $scope.name = '';
    $scope.text = '';
    $scope.term = '';
    $scope.roomName = '';
    $scope.theRoom = [];
    $scope.currentRoom = '';
    
    
    socket.on('message', function(msg) {
        console.log(msg);
        $scope.messages.push(msg);
        $scope.$apply();
        
        var elem = document.getElementById('msgpane');
        elem.scrollTop = elem.scrollHeight;
        
    });
    
    socket.on('room', function(rm) {
        console.log("the room is", rm);
    /*    var tempRoom = '<div><input type="hidden" ng-model="theRoom[&#39;' 
            + rm + '&#39;]" value="' 
            + rm + '"><button type="button" ng-click="$parent.joinRoom()">' + rm + '</button></div>'; */
        var tempRoom = rm;
        console.log(tempRoom);
        
        //$scope.rooms.push($sce.trustAsHtml(tempRoom));
        $scope.rooms.push(tempRoom);
        $scope.$apply();
        
    });
    
    socket.on('subscription', function(sub) {
        console.log("the sub is", sub);
        $scope.subscriptions.push(sub);
        $scope.$apply();
    });
    
    socket.on('search', function(result) {
        console.log(result);
        $scope.searchResults.push(result);
        $scope.$apply();
        
        var elem = document.getElementById('searchpane');
        elem.scrollTop = elem.scrollHeight;
        
    });
    
    socket.on('newRoom', function(newRoomName) {
        /*var tempName = '<div><form ng-submit="$parent.joinRoom()"><input type="hidden" ng-model="theRoom[&quot;' 
            + newRoomName + '&quot;]" value="' 
            + newRoomName + '"><input type="submit" value="' 
            + newRoomName + '"></form></div>';*/
        console.log(tempName);
        var tempName = newRoomName;
        //$scope.rooms.push($sce.trustAsHtml(tempName));
        $scope.rooms.push(tempName);
        $scope.$apply();
        
    });
    
    socket.on('joinRoom', function(roomToJoin) {
        $scope.currentRoom = roomToJoin;
        $scope.$apply();
    });
    
    $scope.send = function send() {
        var data = {"msg":$scope.text, "room":$scope.currentRoom};
        console.log("Sending message", data);
        socket.emit('message', data);
        $scope.text = '';
    };
    
    $scope.search = function search() {
        $scope.searchResults = [];
        console.log("Searching term", $scope.term);
        socket.emit('search', $scope.term);
        $scope.term = '';
    };
    
    $scope.newRoom = function newRoom() {
        console.log("Creating new room", $scope.roomName);
        socket.emit('newRoom', $scope.roomName);
        $scope.roomName = '';
    };
    
/*    $scope.joinRoom = function joinRoom() {
      console.log("joining room", $scope.theRoom);
      socket.emit('joinRoom', $scope.theRoom);
      $scope.messages = [];
    };*/
    
    $scope.joinRoom = function joinRoom(roomToJoin) {
      console.log("joining room", roomToJoin);
      socket.emit('joinRoom', roomToJoin);
      $scope.messages = [];
    };
    
    $scope.subscribe = function subscribe(roomToSubscribe) {
        console.log("subscribing to room", roomToSubscribe);
        socket.emit('subscribe', roomToSubscribe);
    };
    
    socket.on('connect', function() {
        console.log('connected');
    });
});

