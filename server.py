from concurrent import futures
import random

import grpc
import chat_pb2_grpc
import chat_pb2

import sys
import threading
import os

from tkinter import *
from tkinter import simpledialog
from tkinter import messagebox

serverPortNum = ""
serverName = ""
server_started = False
server_tk = Tk()
server = None

# Function that is called when X/close button is pressed or the end server
# button is pressed. it will remove itself from the list of servers.
# If the server has not been started it will exit normally
def exit():
    answer = messagebox.askyesno(title="Exit Confirmation", message= "Are you sure you want to shut down the server?")
    if answer:
        if server_started == False:
            server_tk.destroy()
            sys.exit()
        else:
            server_chat_list.insert(END, "The server is shutting down.")
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
            server_tk.destroy()
            server.stop(1)
            newThread.join()
            os._exit(0)
    
clients = {}
messages = [] # all the messages will be stored in here



# This function appends the server's port and name to a file for storage.
# If the server name or port number was not inputted it will print an error
# message and exit the program
def setup():
    if serverName == None or serverPortNum == None:
        print("Error: Either server name or port number was left empty")
        server_tk.destroy()
        sys.exit(0)
    global server_started
    server_started = True
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
                        server_tk.destroy()
                        sys.exit(0)

                    elif serverPortNum == serverPortNumberFromFile:
                        print("Error: The server port number you have provided in the command argument already exists")
                        print("Please restart the server using a unique server port number.")   
                        server_tk.destroy()
                        sys.exit(0)
    with open("log.txt", "a") as logFile:
        logFile.write(f"{serverPortNum}_{serverName}\n")


# Main server class that will send and receive messages send from clients that
# are currently in the server.
class ChatService(chat_pb2_grpc.ChatServiceServicer):
    
    # this function will receive the join message from the client and assign
    # it a unique identifier and return it to the client
    def GetClientIdentifier(self, request, context):
        firstName = request.first_name
        clientNumber = random.randint(1000,9999) # generate a random 4 digit number for the client id

        while clientNumber in clients: # if the client number is already picked
            clientNumber = random.randint(1000,9999) # generate another one

        clients[clientNumber] = firstName
        server_chat_list.insert(END, "Generating a new client identifier of {} for {}\n".format(clientNumber, firstName))

        return chat_pb2.ClientIdentifier(client_identifier = clientNumber)
    
    # This function will receive a chat message from a client and append it to
    # the messages array. The Get messages function will send it in a separate
    # thread. It will send the client a response to indicate it received the 
    # message but will distribute it later.
    def SendMessage(self, request, context): 
        name = request.first_name
        id = request.client_identifier
        msg = request.message_text
        server_chat_list.insert(END, f"{name}: {msg}\n")
        if (msg == "~LEFT THE CHATROOM~"):
            clients.pop(id)
        messages.append(request)
        
        return chat_pb2.MessageReceived(response = "ok")
    
    # Handles the request from the client to get the servers port number.
    # This function returns its port number to the client
    def GetPortNumber(self, request, context): 
        return chat_pb2.PortNumber(port_number = serverPortNum)
    
    def GetMessage(self, request, context): # this method will broadcast incoming messages to all the clients
        numMessagesClientReceived = 0 # when the client starts up, they will have not received any messages so far
        
        while True: # infinite loop
            numMessagesSent = len(messages) # the length of messages will be the number of messages sent so far in the chat
      
            if numMessagesSent > numMessagesClientReceived: # if more messages have been sent then what the client receivied
                # if this is true, then we need to send these new messages to all the clients currently in the server

                messageToSend = messages[numMessagesClientReceived] # the first (or only) message that the client has not received
                numMessagesClientReceived = numMessagesClientReceived + 1 # incrememting
                yield messageToSend # send this message
                # the reason why this is a "yield" and not "return", because if a client joins a chat when messages have already been sent, the server needs to be able to
                # send ALL messages that have not been sent yet, and "yield" allows multiple things to be returned

# function that will start the gRPC server.
def server():
    global server
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=5))
    chat_pb2_grpc.add_ChatServiceServicer_to_server(ChatService(), server)
    server.add_insecure_port(f'localhost:{serverPortNum}')
    server_chat_list.insert(END, f"gRPC starting through port {serverPortNum}\n")
    server.start()
    server.wait_for_termination()

# since the GUI is threaded the start server function will need to be threaded
# as well to run concurrently.
newThread= threading.Thread(target=server, daemon=True)

# This function is called when the start server button is pressed. It will call
# the function setup and start the server thread. It will also disable the 
# start server button from being pressed and enable the stop server button
def start_server():
    start_button.configure(state=DISABLED)
    end_button.configure(state=NORMAL)
    setup()
    newThread.start()

# main loop to setup the servers GUI.
# it will ask the user for the port number and server's name to begin running the server
if __name__ == "__main__":
    # set size of server GUI
    server_tk.geometry("410x360")
    # hide the GUI when the user inputs port number and 
    server_tk.withdraw()
    # ask for user inputs
    serverPortNum = simpledialog.askinteger("Port Number", "Input a port number for this server:", parent=server_tk)
    serverName = simpledialog.askstring("Port Name", "Input the server's name:", parent= server_tk)
    server_tk.title(f'Chatroom Server {serverName}')
    # the GUI appears after the inputs have been made
    server_tk.deiconify()
    # sets functionality of the X/close button to run the function exit when pressed
    server_tk.protocol("WM_DELETE_WINDOW", exit)
    # Main frame to add to
    frame = Frame (server_tk, width=300, height=300)
    frame.pack()
    # add start button
    start_button = Button(frame, text="START SERVER", command=start_server)
    start_button.pack(side= "left")
    # add end button
    end_button = Button(frame, text="STOP SERVER", command=exit, state=DISABLED)
    end_button.pack(side="right")
    # create text field to display incoming messages
    server_chat_list = Text()
    server_chat_list.pack(side="bottom")
    # start GUI thread
    server_tk.mainloop()
