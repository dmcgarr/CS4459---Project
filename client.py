import grpc
import chat_pb2_grpc
import chat_pb2
import threading
import argparse

parser = argparse.ArgumentParser(description="client arguments") 
parser.add_argument('firstName', help = "firstName of client")
args = parser.parse_args()

# this method returns a dictionary of all the servers that are currently running (key = server name, value = port number)
def getActiveServerSessions():
    servers = {}

    logFile = open("log.txt", "r")
    runningServers = logFile.readlines()
    logFile.close()

    for i in range(len(runningServers)): #f or each line in the log file
        lineSplitted = runningServers[i].split("_")
        runningServers[i] = lineSplitted

        # due to whitespace issues, we check if runningServers[0] is a number
        # if it is, then it's a valid line with a server port number and name
        if runningServers[i][0].isnumeric():
            serverName = runningServers[i][1].strip('\n')
            serverPortNumber = runningServers[i][0]

            servers[serverName] = serverPortNumber

    return servers


# this method returns True if the server name provided exists
def check (serverName):
    runningServers = getActiveServerSessions()

    for key in runningServers:
        if serverName == key:
            return True
   
    return False

# this method returns a port number for a given server name
def getServerNumber (serverName):
    runningServers = getActiveServerSessions()

    if serverName in runningServers:
        return runningServers[serverName]
    else:
        return -1   # note that this method is always called after we perform the previous check method 
                    # so theoretically, this return statement never be reached as we will always verify whether the server name exists
                    # but for proper error handling and testing, it is good to include this

# this method joins a server
# it's called when we start a client session OR if the client decides to switch chat sessions
def join():

    joined = False 

    while joined == False:
        runningServers = getActiveServerSessions()

        print("The following chatrooms are open:")

        for key in runningServers:
            print(f"    - {key}")
           
        serverName = input("\nPlease type the name of the chatroom you wish to enter: ")

        if check(serverName): # if the user provided input corresponds to a running server
            joined = True
            serverPortNumber = getServerNumber(serverName)
        else: 
            print("\nThe chatroom name you have entered does not exist.\n") # we go back to the beginning of the while loop and start over

    # establishing a connection to the GRPC server
    channel = grpc.insecure_channel(f'localhost:{serverPortNumber}')

    return channel



class Client:
    def __init__(self):

        self.firstName = args.firstName

        print(f"\nWelcome {self.firstName}!\n")

        channel = join()

        self.connection = chat_pb2_grpc.ChatServiceStub(channel) 
        
        # generating a unique 4 digit client ID (just in case two or more people have the same name)
        self.clientID = self.connection.GetClientIdentifier(chat_pb2.ClientName(first_name = self.firstName)).client_identifier

        print("The server has given you a client identifier of", self.clientID)

        newThread = threading.Thread(target=self.waitingForIncomingMessages)
        newThread.daemon = True
        newThread.start()

        print("Chat session has started. Enter your message, then press enter.")

        while True:
            messageText = input("") 

            if messageText == "switch":
                channel = join()

                self.connection = chat_pb2_grpc.ChatServiceStub(channel) 
        
                # generating a unique 4 digit client ID (just in case two or more people have the same name)
                self.clientID = self.connection.GetClientIdentifier(chat_pb2.ClientName(first_name = self.firstName)).client_identifier

                print("The server has given you a client identifier of", self.clientID)

                newThread = threading.Thread(target=self.waitingForIncomingMessages)
                newThread.daemon = True
                newThread.start()

            else:
                # sending the message to the server
                self.connection.SendMessage(chat_pb2.MessageFormat(first_name = self.firstName, client_identifier = self.clientID, message_text = messageText))  
            
    
    def waitingForIncomingMessages(self):

        for message in self.connection.GetMessage(chat_pb2.Empty()):  
            name = message.first_name
            msg = message.message_text

            if message.client_identifier != self.clientID: # this is to avoid printing a message that a client just sent on their own session
                print(f"{name}: {msg}")

c = Client()
