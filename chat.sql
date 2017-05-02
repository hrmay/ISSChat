DROP DATABASE IF EXISTS chat;
CREATE DATABASE chat;

\c chat;

DROP TABLE IF EXISTS users;
DROP TABLE IF EXISTS messages;
DROP TABLE IF EXISTS rooms;
DROP TABLE IF EXISTS userrooms;

--Holds information for registered users
CREATE TABLE users
(
    UserID SERIAL NOT NULL,
    Username VARCHAR(20) NOT NULL,
    Password TEXT NOT NULL,
    PRIMARY KEY (UserID)
);

--Holds info about the rooms
CREATE TABLE rooms
(
    RoomID SERIAL NOT NULL,
    Name VARCHAR(25) NOT NULL,
    PRIMARY KEY (RoomID)
);

--Holds all messages in the database
CREATE TABLE messages
(
    MessageID SERIAL NOT NULL,
    Body TEXT,
    UserID SERIAL NOT NULL,
    RoomID SERIAL NOT NULL,
    PRIMARY KEY (MessageID),
    FOREIGN KEY (UserID) REFERENCES users(UserID),
    FOREIGN KEY (RoomID) REFERENCES rooms(RoomID)
);

--User-rooms junction table
CREATE TABLE userrooms
(
    UserID SERIAL NOT NULL,
    RoomID SERIAL NOT NULL,
    PRIMARY KEY (UserID, RoomID),
    FOREIGN KEY (UserID) REFERENCES users(UserID),
    FOREIGN KEY (RoomID) REFERENCES rooms(RoomID)
);

DROP USER IF EXISTS chatter;
CREATE USER chatter WITH PASSWORD 'stEtYhL8Gh2mtsnQ';
GRANT SELECT, INSERT, UPDATE ON TABLE users, messages, rooms, userrooms TO chatter;
GRANT SELECT, USAGE, UPDATE ON SEQUENCE users_userid_seq, messages_messageid_seq, rooms_roomid_seq, userrooms_userid_seq, userrooms_roomid_seq TO chatter;

CREATE EXTENSION pgcrypto;

INSERT INTO rooms (Name) VALUES ('default');
INSERT INTO rooms (Name) VALUES ('test');
INSERT INTO rooms (Name) VALUES ('fun');
INSERT INTO users (Username, Password) VALUES ('test', crypt('test', gen_salt('bf')));
INSERT INTO users (Username, Password) VALUES ('abc', crypt('abc', gen_salt('bf')));
INSERT INTO userrooms (UserID, RoomID) VALUES ((SELECT UserID FROM users WHERE Username = 'test'), (SELECT RoomID FROM rooms WHERE Name = 'default'));
INSERT INTO userrooms (UserID, RoomID) VALUES ((SELECT UserID FROM users WHERE Username = 'test'), (SELECT RoomID FROM rooms WHERE Name = 'test'));
INSERT INTO userrooms (UserID, RoomID) VALUES ((SELECT UserID FROM users WHERE Username = 'test'), (SELECT RoomID FROM rooms WHERE Name = 'fun'));
INSERT INTO userrooms (UserID, RoomID) VALUES ((SELECT UserID FROM users WHERE Username = 'abc'), (SELECT RoomID FROM rooms WHERE Name = 'fun'));
INSERT INTO messages (Body, UserID, RoomID) VALUES ('this is a test', (SELECT UserID FROM users WHERE Username = 'test'), (SELECT RoomID FROM rooms WHERE Name = 'test'));
INSERT INTO messages (Body, UserID, RoomID) VALUES ('this is also a test', (SELECT UserID FROM users WHERE Username = 'test'), (SELECT RoomID FROM rooms WHERE Name = 'test'));
INSERT INTO messages (Body, UserID, RoomID) VALUES ('this is a test', (SELECT UserID FROM users WHERE Username = 'test'), (SELECT RoomID FROM rooms WHERE Name = 'test'));
INSERT INTO messages (Body, UserID, RoomID) VALUES ('fun fun', (SELECT UserID FROM users WHERE Username = 'abc'), (SELECT RoomID FROM rooms WHERE Name = 'fun'));