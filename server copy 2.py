from concurrent import futures
import random

import grpc
import chat_pb2_grpc
import chat_pb2

clients = {}
messages = [] # all the messages will be stored in here

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
    server.add_insecure_port('localhost:8435')
    print("gRPC starting")
    server.start()
    server.wait_for_termination()

server()
