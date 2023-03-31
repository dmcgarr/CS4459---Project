import grpc
import chat_pb2_grpc
import chat_pb2
import threading

class Client:
    def __init__(self):

        self.firstName = input("Welcome! Please enter your first name: ")

        # establishing a connection to the GRPC server
        channel = grpc.insecure_channel('localhost:8435')
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
            # sending the message to the server
            self.connection.SendMessage(chat_pb2.MessageFormat(first_name = self.firstName, client_identifier = self.clientID, message_text = messageText))  


    def waitingForIncomingMessages(self):

        for message in self.connection.GetMessage(chat_pb2.Empty()):  
            name = message.first_name
            msg = message.message_text

            if message.client_identifier != self.clientID: # no point in printing a message that a user just send on the user's screen
                print(f"{name}: {msg}")

c = Client()
