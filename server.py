import os
import uuid
from flask import Flask, session, render_template, request, redirect, url_for
from flask.ext.socketio import SocketIO, emit, join_room, leave_room, send, rooms
import psycopg2
import psycopg2.extras

app = Flask(__name__, static_url_path='')
app.config['SECRET_KEY'] = 'secret!'

socketio = SocketIO(app)

messages = []
            
usersOnline = {}
#---------------------
# Getters and such
#---------------------
def connectToDB():
    connectionString = 'dbname=chat user=chatter password=stEtYhL8Gh2mtsnQ host=localhost'
    try:
        return psycopg2.connect(connectionString)
    except:
        print("Can't connect to database.")

def getMessages(room):
    tempMessages = []
    if room == 'default':
        tempMessages = [{'text': 'Booting system', 'name': 'Bot'},
            {'text': 'ISS Chat now live!', 'name': 'Bot'}]
    
    text = 'Welcome to the room ' + room + '!'
    tempMessages.append({'text': text, 'name': 'Welcome'})
            
    query = {'room': room}
            
    conn = connectToDB()
    cur = conn.cursor()    
    
    try:
        cur.execute("SELECT messages.Body, users.Username FROM messages JOIN users ON (messages.UserID = users.UserID) WHERE messages.RoomID IN (SELECT RoomID FROM rooms WHERE Name = %(room)s) ORDER BY messages.MessageID DESC LIMIT 5;", query)
    except:
        print("ERROR executing SELECT")
        print(cur.mogrify("SELECT messages.Body, users.Username FROM messages JOIN users ON (messages.UserID = users.UserID) WHERE messages.RoomID IN (SELECT RoomID FROM rooms WHERE Name = %(room)s) ORDER BY messages.MessageID DESC LIMIT 5;", query))
    
    if cur.rowcount > 0:
        dbMessages = cur.fetchall()
        print('database messages:')
        print(reversed(dbMessages))
        for dbMessage in reversed(dbMessages):
            tempMessages.append({'text': dbMessage[0], 'name':dbMessage[1]})
    
    return tempMessages
  
def getRooms():
    conn = connectToDB()
    cur = conn.cursor()
    
    try:
        cur.execute("SELECT Name FROM rooms;")
    except:
        print("ERROR executing SELECT")
        print(cur.mogrify("SELECT Name FROM rooms;"))
    
    rooms = cur.fetchall()
    return rooms
    
def getSubs():
    conn = connectToDB()
    cur = conn.cursor()
    
    query = {'username': session['username']}
    
    try:
        cur.execute("SELECT Name FROM rooms JOIN userrooms ON (rooms.RoomID = userrooms.RoomID) WHERE UserID IN (SELECT UserID FROM users WHERE Username = %(username)s);", query)
    except:
        print("ERROR executing SELECT")
        print(cur.mogrify("SELECT RoomID FROM rooms WHERE UserID IN (SELECT UserID FROM users WHERE Username = %(username)s);", query))
    
    subs = cur.fetchall()
    return subs
    
#---------------------
# Socket IO
#---------------------
@socketio.on('connect', namespace='/iss')
def makeConnection():
    session['uuid'] = uuid.uuid1()
    print('connected')
    if 'username' in session:
        usersOnline[session['uuid']] = {'username': session['username']}
    join_room('default');
    session['room'] = 'default'
    joinMessage = {'text': session['username'] + ' has joined the room', 'name': 'Bot'}
    emit('message', joinMessage, broadcast=True, room='default')
    rooms = getRooms()
    subs = getSubs()
    emit('joinRoom', 'default')
    for room in rooms:
        print(room)
        emit('room', room, broadcast=False)
    for sub in subs:
        print(sub)
        emit('subscription', sub, broadcast=False)
    for message in messages:
        print(message)
        emit('message', message, broadcast=False)


@socketio.on('message', namespace='/iss')
def newMessage(data):
    conn = connectToDB()
    cur = conn.cursor()
    
    temp = {'text': data['msg'], 'name':session['username'], 'room':data['room']}
    messages.append(temp)
    emit('message', temp, room=session['room'])
    print("the message is", temp)
    print("the room is", session['room'])
    
    try:
        cur.execute("""INSERT INTO messages (Body, UserID, RoomID) VALUES (%(text)s, (SELECT userid FROM users WHERE username=%(name)s), (SELECT RoomID FROM rooms WHERE Name = %(room)s));""", temp)
    except:
        print("ERROR executing INSERT")
        print(cur.mogrify("""INSERT INTO messages (Body, UserID) VALUES (%(text)s, (SELECT userid FROM users WHERE username=%(name)s));""", temp))
        conn.rollback()
    conn.commit()

@socketio.on('search', namespace='/iss')
def search(term):
    conn = connectToDB()
    cur = conn.cursor()
    
    query = {'searchTerm': '%' + term + '%', 'username': session['username']}
    
    print("searching:")
    try:
        cur.execute("SELECT messages.Body, users.Username FROM messages JOIN users ON (messages.UserID = users.UserID) JOIN rooms ON (messages.RoomID = rooms.RoomID) WHERE messages.Body LIKE %(searchTerm)s AND messages.RoomID IN (SELECT userrooms.RoomID FROM userrooms JOIN users ON (users.UserID = userrooms.UserID) WHERE users.username = %(username)s);", query)
        print(cur.mogrify("SELECT messages.Body, users.Username FROM messages JOIN users ON (messages.UserID = users.UserID) JOIN rooms ON (messages.RoomID = rooms.RoomID) WHERE messages.Body LIKE %(searchTerm)s AND messages.RoomID IN (SELECT rooms.RoomID FROM userrooms JOIN users ON (users.UserID = userrooms.UserID) WHERE users.username = %(username)s);", query))
    except:
        print("ERROR executing SELECT")
        print(cur.mogrify("SELECT messages.Body, users.Username FROM messages JOIN users ON (messages.UserID = users.UserID) JOIN rooms ON (messages.RoomID = rooms.RoomID) WHERE messages.Body LIKE %(searchTerm)s AND messages.RoomID IN (SELECT userrooms.RoomID FROM userrooms JOIN users ON (users.UserID = userrooms.UserID) WHERE users.username = %(username)s);", query))

    results = cur.fetchall()
    
    for result in results:
        resultDict = {'text': result[0], 'name':result[1]}
        print(resultDict)
        emit('search', resultDict)

@socketio.on('newRoom', namespace='/iss')
def newRoom(roomName):
    conn = connectToDB()
    cur = conn.cursor()
    
    query = {'name': roomName}
    if len(roomName) > 0:
        print("creating new room")
        try:
            cur.execute("SELECT RoomID FROM rooms WHERE Name = %(name)s;", query)
            
            if cur.rowcount < 1:
                try:
                    cur.execute("""INSERT INTO rooms (Name) VALUES (%(name)s);""", query)
                except:
                    print("ERROR executing INSERT")
                    print(cur.mogrify("""INSERT INTO rooms (Name) VALUES (%(name)s);""", query))
                    conn.rollback()
                conn.commit()
                
                emit('newRoom', roomName, broadcast=True)
            else:
                pass #exists
        except:
            print("ERROR executing SELECT")
            print(cur.mogrify("SELECT RoomID FROM rooms WHERE Name = %(name)s;", query))
    
    

@socketio.on('joinRoom', namespace='/iss')
def joinRoom(roomName):
    print("joining room", roomName)
    #print(rooms())
    tempMessages = getMessages(roomName)
    leave_room(session['room'])
    join_room(roomName)
    session['room'] = roomName
    print(tempMessages)
    emit('joinRoom', roomName)
    joinMessage = {'text': session['username'] + ' has joined the room', 'name': 'Bot'}
    emit('message', joinMessage, broadcast=True, room=roomName)
    for message in tempMessages:
        print(message)
        emit('message', message)
        
@socketio.on('subscribe', namespace='/iss')
def subscribeToRoom(roomName):
    conn = connectToDB()
    cur = conn.cursor()
    
    print("subscribing to room", roomName)
    
    query = {'username': session['username'], 'room': roomName}
    try:
        cur.execute("""INSERT INTO userrooms (UserID, RoomID) VALUES ((SELECT UserID FROM users WHERE Username = %(username)s), (SELECT RoomID FROM rooms WHERE Name = %(room)s));""", query)
    except:
        print("ERROR executing INSERT")
        print(cur.mogrify("""INSERT INTO userrooms (UserID, RoomID) VALUES ((SELECT UserID FROM users WHERE Username = %(username)s), (SELECT RoomID FROM rooms WHERE Name = %(room)s));""", query))
        conn.rollback()
    conn.commit()
    
    
    emit('subscription', roomName, broadcast=False)
    
    

#------------------------
# HOME ROUTE
#------------------------
@app.route('/')
def mainIndex():
    global messages
    print 'in hello world'
    if 'username' in session:
        user = session['username']
    else:
        user = ''
        
    tempMessages = getMessages('default')
    print(tempMessages)
    messages = tempMessages
    return render_template('index.html', user=user)

#------------------------
# SIGNUP ROUTE
#------------------------
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    print('in signup')
    conn = connectToDB()
    cur = conn.cursor()
    
    
    #get username
    if 'username' in session:
        user = session['username']
    else:
        user = ''
    
    #which menu to display
    menu = 'signup' 
    
    #if the user is signing up
    if request.method == 'POST':
        userInfo = {'username': request.form['username'],
                    'password': request.form['password'],
                    'confirm': request.form['confirm']}
                    
        if userInfo['password'] == userInfo['confirm']:
            try:
                #usernames have to be unique
                cur.execute("SELECT userid FROM users WHERE username = %(username)s;", userInfo)
                #if the username is unique
                if cur.rowcount == 0:
                    try: 
                        cur.execute("""INSERT INTO users (username, password) VALUES (%(username)s, crypt(%(password)s, gen_salt('bf')));""", userInfo)
                        #print(cur.mogrify("""INSERT INTO users (username, password) VALUES (%(username)s, crypt(%(password)s, gen_salt('bf')));""", userInfo))
                        menu = 'success'
                        try:
                            cur.execute("""INSERT INTO userrooms (UserID, RoomID) VALUES ((SELECT UserID FROM users WHERE Username = %(username)s), (SELECT RoomID FROM rooms WHERE Name = 'default'));""", userInfo)
                        except:
                            print("ERROR executing INSERT")
                            print(cur.mogrify("""INSERT INTO userrooms (UserID, RoomID) VALUES (%(username)s, (SELECT RoomID FROM rooms WHERE Name = 'default'));""", userInfo))
                    except:
                        print("ERROR executing INSERT")
                        print(cur.mogrify("""INSERT INTO users (username, password) VALUES (%(username)s, crypt(%(password)s, gen_salt('bf')));""", userInfo))
                        conn.rollback()
                        menu = 'failure'
                    conn.commit()
                #else tell the user that the username is already in use
                else:
                    menu='exists'
            except:
                print("ERROR executing SELECT")
                print(cur.mogrify("SELECT userid FROM users WHERE username = %(username)s;", userInfo))
            
        else:
            return render_template('signup.html', user=user, menu='mismatch')
        
    
    return render_template('signup.html', user=user, menu=menu)
#------------------------
# END SIGNUP ROUTE
#------------------------

#------------------------
# LOGIN ROUTE
#------------------------
@app.route('/login', methods=['POST'])
def login():
    print('in login')
    conn = connectToDB()
    cur = conn.cursor()
    
    if 'username' in session:
        user = session['username']
    else:
        user = ''
        
    if request.method == 'POST':
        userInfo = {'username': request.form['username'], 'password': request.form['password']}
        
        try:
            cur.execute("SELECT username FROM users WHERE username = %(username)s AND password = crypt(%(password)s, password);", userInfo)
        except:
            print("ERROR executing SELECT")
            print(cur.mogrify("SELECT username FROM users WHERE username = %(username)s AND password = crypt(%(password)s, gen_salt('bf'));", userInfo))
        
        if cur.rowcount == 1:
            session['username'] = userInfo['username']
    
    return redirect(url_for("mainIndex"))
#------------------------
# END LOGIN ROUTE
#------------------------    

#------------------------
# LOGOUT ROUTE
#------------------------    
@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for("mainIndex"))


# start the server
if __name__ == '__main__':
        socketio.run(app, host=os.getenv('IP', '0.0.0.0'), port =int(os.getenv('PORT', 8080)), debug=True)
