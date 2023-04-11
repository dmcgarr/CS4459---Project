import grpc
import chat_pb2_grpc
import chat_pb2

import threading
import sys

from tkinter import *
from tkinter import simpledialog
from tkinter import messagebox
from tkinter import ttk

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
    return serverName in runningServers

# this method returns a port number for a given server name
def getServerNumber (serverName):
    runningServers = getActiveServerSessions()

    if check(serverName):
        return runningServers[serverName]
    else:
        return -1   # note that this method is always called after we perform the previous check method 
                    # so theoretically, this return statement never be reached as we will always verify whether the server name exists
                    # but for proper error handling and testing, it is good to include this

class Client:
    def __init__(self, name, frame):
        
        self.connection = None
        self.firstName = name
        self.frame = frame
        root.protocol("WM_DELETE_WINDOW", self.exit)
        self.exit_button = Button(self.frame, text= "EXIT CHATROOM", command=self.exit)
        self.exit_button.pack()

        self.options=list(getActiveServerSessions().keys())
        
        self.dropdown = ttk.Combobox(value=self.options)
        self.dropdown.bind("<<ComboboxSelected>>", self.switch)
        self.dropdown.configure(postcommand=self.get_updated_server_list)
        self.dropdown.pack()
        self.chat_screen = Text(self.frame)
        self.chat_screen.tag_configure("left", justify=LEFT)
        self.chat_screen.tag_configure("right", justify=RIGHT)
        self.chat_screen.pack(side="top")
        self.username_label = Label(self.frame, text=self.firstName)
        self.username_label.pack(side="left")
        self.input_field = Entry(self.frame, bd=5, width=10)
        self.input_field.bind('<Return>', self.send_message)
        self.input_field.focus()
        self.input_field.pack(side="left")
        # move this into client setup

        self.chat_screen.insert(END, f"Welcome {self.firstName}!\n")

        self.chat_screen.insert(END, "Chat application has started. Please select a server from the dropdown menu.\n")
        main_frame.mainloop()
    
    def get_updated_server_list(self):
        self.servernames = list(getActiveServerSessions().keys())
        self.dropdown.configure(values= self.servernames)

    def join(self, selection):
        portNum = getServerNumber(selection)
        self.channel = grpc.insecure_channel(f'localhost:{portNum}')

    def switch(self, event):
        selection = self.dropdown.get()
        self.join(selection)
        answer = messagebox.askyesno(title="Change Server Confirmation", message= f"Are you sure you want to join the server {selection}\"?")
        if answer:

            self.connection = chat_pb2_grpc.ChatServiceStub(self.channel) 
        
            # generating a unique 4 digit client ID (just in case two or more people have the same name)
            self.clientID = self.connection.GetClientIdentifier(chat_pb2.ClientName(first_name = self.firstName)).client_identifier
            self.chat_screen.delete(1.0, END)
            self.chat_screen.insert(END,f"The server {selection} has given you a client identifier of {self.clientID}\n")
            self.chat_screen.insert(END, "Chat session has started. Enter your message in the text box below, then press enter.\n")

            self.newThread = threading.Thread(target=self.waitingForIncomingMessages)
            self.newThread.daemon = True
            self.newThread.start()

    def send_message(self, event):
        # sending the message to the server
        message= self.input_field.get()
        self.input_field.delete(0,END)
        self.connection.SendMessage(chat_pb2.MessageFormat(first_name = self.firstName, client_identifier = self.clientID, message_text = message))
        self.chat_screen.insert(END, f"{self.firstName}:\n{message}\n", "left")


    
    def waitingForIncomingMessages(self):

        for message in self.connection.GetMessage(chat_pb2.Empty()):  
            name = message.first_name
            msg = message.message_text

            if message.client_identifier != self.clientID: # this is to avoid printing a message that a client just sent on their own session
                self.chat_screen.insert(END, f"{name}:\n{msg}\n", "right")
    # make this function send a message to the server saying the user left the room
    # and display on screen that the person left, then exit application or for switching rooms
    def exit(self): 
        answer = messagebox.askyesno(title="Exit Confirmation", message= "Are you sure you want to exit the chat room?")
        if answer:
            if self.connection == None:
                root.destroy()
                sys.exit(0)
            else:
                self.chat_screen.insert(END, "Exiting Room\n")
                self.connection.SendMessage(chat_pb2.MessageFormat(first_name = self.firstName, client_identifier = self.clientID, message_text = "~LEFT THE CHATROOM~"))
                root.destroy()
                sys.exit(0)


if __name__ == "__main__":
    root = Tk()
    main_frame = Frame(root, width = 300, height = 300)
    main_frame.pack()
    root.withdraw() #hide main frame while taking input
    name = simpledialog.askstring("Registration", "Please enter your name:", parent=root)
    root.deiconify() # make main frame visible after taking input
    main_frame.title = ("GRPC Chat")
    
    c = Client(name, main_frame)
