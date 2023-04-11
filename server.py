from concurrent import futures
import random

import grpc
import chat_pb2_grpc
import chat_pb2

import sys
import threading

from tkinter import *
from tkinter import simpledialog
from tkinter import messagebox

serverPortNum = ""
serverName = ""
server_started = False
server_tk = Tk()
server = None

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
            server.stop(None)
            sys.exit(0)
    
clients = {}
messages = [] # all the messages will be stored in here




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




class ChatService(chat_pb2_grpc.ChatServiceServicer):
    def GetClientIdentifier(self, request, context):
        firstName = request.first_name
        clientNumber = random.randint(1000,9999) # generate a random 4 digit number for the client id

        while clientNumber in clients: # if the client number is already picked
            clientNumber = random.randint(1000,9999) # generate another one

        clients[clientNumber] = firstName
        server_chat_list.insert(END, "Generating a new client identifier of {} for {}\n".format(clientNumber, firstName))

        return chat_pb2.ClientIdentifier(client_identifier = clientNumber)
    
    def SendMessage(self, request, context): 
        name = request.first_name
        id = request.client_identifier
        msg = request.message_text
        server_chat_list.insert(END, f"{name}: {msg}\n")
        print(clients)
        if (msg == "~LEFT THE CHATROOM~"):
            clients.pop(id)
            print(clients)
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
    global server
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=5))
    chat_pb2_grpc.add_ChatServiceServicer_to_server(ChatService(), server)
    server.add_insecure_port(f'localhost:{serverPortNum}')
    server_chat_list.insert(END, f"gRPC starting through port {serverPortNum}\n")
    server.start()
    server.wait_for_termination()

newThread= threading.Thread(target=server, daemon=True)

def start_server():
    start_button.configure(state=DISABLED)
    end_button.configure(state=NORMAL)
    setup()
    newThread.start()


if __name__ == "__main__":
    server_tk.geometry("410x360")
    server_tk.withdraw()
    serverPortNum = simpledialog.askinteger("Port Number", "Input Port Number For this server:", parent=server_tk)
    serverName = simpledialog.askstring("Port Name", "Input Servers Name:", parent= server_tk)
    server_tk.title(f'Chatroom Server {serverName}')
    server_tk.deiconify()
    server_tk.protocol("WM_DELETE_WINDOW", exit)
    frame = Frame (server_tk, width=300, height=300)
    frame.pack()
    start_button = Button(frame, text="START", command=start_server)
    start_button.pack(side= "left")

    end_button = Button(frame, text="END", command=exit, state=DISABLED)
    end_button.pack(side="right")

    server_chat_list = Text()
    server_chat_list.pack(side="bottom")
    server_tk.mainloop()
