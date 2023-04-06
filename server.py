from concurrent import futures
import random
import argparse

import grpc
import chat_pb2_grpc
import chat_pb2

import signal
import sys

parser = argparse.ArgumentParser(description="server arguments") 
parser.add_argument('portNum', help = "port number to bind server to")
parser.add_argument('serverName', help = "name for clients to recognize the server as")
args = parser.parse_args()

serverPortNum = args.portNum
serverName = args.serverName

def sigint_handler(signal, frame):
    print("\nThe server is shutting down.")

    logFile = open("log.txt", "r")
    arr = logFile.readlines()
    logFile.close()
    for i in range(len(arr)):
        arraySplitted = arr[i].split("_")
        arr[i] = arraySplitted
        if (arr[i][0] == str(serverPortNum)):
            removeItem = i

    arr.pop(removeItem)

    for i in range(len(arr)):
        arraySplitted = "_".join(arr[i])
        arr[i] = arraySplitted
        if (arr[i][0] == str(serverPortNum)):
            removeItem = i

    with open('log.txt', 'w') as logFile:
        for line in arr:
            logFile.write(f"{line}")

    sys.exit(0)




clients = {}
messages = [] # all the messages will be stored in here





with open("log.txt", "r") as logFile:
    runningServers = logFile.readlines()

    for i in range(len(runningServers)):
        arraySplitted = runningServers[i].split("_")
        
        runningServers[i] = arraySplitted

        if runningServers[i][0].isnumeric():
                serverNameFromFile = runningServers[i][1].strip('\n')
                serverPortNumberFromFile = runningServers[i][0]

                if serverName == serverNameFromFile:
                    print("Error: The server name you have provided in the command argument already exists")
                    print("Please restart the server using a unique server name.")   
                    sys.exit(0)

                elif serverPortNum == serverPortNumberFromFile:
                    print("Error: The server port number you have provided in the command argument already exists")
                    print("Please restart the server using a unique server port number.")   
                    sys.exit(0)

    with open("log.txt", "a") as logFile:
        logFile.write(f"{serverPortNum}_{serverName}\n")



class ChatService(chat_pb2_grpc.ChatServiceServicer):
    def GetClientIdentifier(self, request, context):
        firstName = request.first_name
        clientNumber = random.randint(1000,9999) # generate a random 4 digit number for the client id

        while clientNumber in clients: # if the client number is already picked
            clientNumber = random.randint(1000,9999) # generate another one

        clients[clientNumber] = firstName
        print("Generating a new client identifier of {} for {}".format(clientNumber, firstName))

        return chat_pb2.ClientIdentifier(client_identifier = clientNumber)
    
    def SendMessage(self, request, context): 
        name = request.first_name
        msg = request.message_text

        print(f"{name}: {msg}")
        messages.append(request)
        
        return chat_pb2.MessageReceived(response = "ok")
    
    def GetMessage(self, request, context): # this method was taken directly from the source code, so it needs to be changed
        lastindex = 0
        # For every client a infinite loop starts (in gRPC's own managed thread)
        while True:
            # Check if there are any new messages
            while len(messages) > lastindex:
                n = messages[lastindex]
                lastindex += 1
                yield n

def server():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=5))
    chat_pb2_grpc.add_ChatServiceServicer_to_server(ChatService(), server)
    server.add_insecure_port(f'localhost:{serverPortNum}')
    print(f"gRPC starting through port {serverPortNum}")
    server.start()
    signal.signal(signal.SIGINT, sigint_handler)
    server.wait_for_termination()

server()
