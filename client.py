import grpc
import chat_pb2_grpc
import chat_pb2

import threading
import sys

from tkinter import *
from tkinter import simpledialog
from tkinter import messagebox
from tkinter import ttk



# this method returns a dictionary of all the servers that are currently running
# (key = server name, value = port number)
def getActiveServerSessions():
    servers = {}
    # Open text file and read the lines from it
    logFile = open("log.txt", "r")
    runningServers = logFile.readlines()
    logFile.close()

    # pasrse through the lines and split on the delimeter
    for i in range(len(runningServers)): #f or each line in the log file
        lineSplitted = runningServers[i].split("_")
        runningServers[i] = lineSplitted

        # due to whitespace issues, we check if runningServers[0] is a number
        # if it is, then it's a valid line with a server port number and name
        if runningServers[i][0].isnumeric():
            serverName = runningServers[i][1].strip('\n')
            serverPortNumber = runningServers[i][0]

            servers[serverName] = serverPortNumber
    # return the dictionary
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

# client class for setting up Client GUI and handling messages
class Client:
    # set up GUI and start client
    def __init__(self, name, frame):
        
        # Variables used in client
        self.connection = None
        self.firstName = name
        self.frame = frame
        self.serverPortNumber = None
        
        # Override the X button to perform the self.exit button when clicked
        root.protocol("WM_DELETE_WINDOW", self.exit)
        # Frame for selection of server
        self.selections_frame = Frame(self.frame)
        # Frame for the displaying of messages and sending messages
        self.chatbox_frame = Frame(self.frame)
        # Frame for the exit button to keep it away from other functions of the GUI
        self.exit_frame = Frame(self.frame)
        # Label for Server Dropdown list
        self.space = Label(self.selections_frame, text="").pack()
        self.server_label = Label(self.selections_frame, text="Server List").pack(side="left")
        # Get Dropdown list
        self.options=list(getActiveServerSessions().keys())
        # Create dropdown and add to frame. When the dropdown is selected the 
        # values are updated by the postcommand function
        self.dropdown = ttk.Combobox(self.selections_frame, value=self.options)
        self.dropdown.bind("<<ComboboxSelected>>", self.switch)
        self.dropdown.configure(postcommand=self.get_updated_server_list)
        self.dropdown.pack(side="left")
        self.space = Label(self.selections_frame, text="").pack()
        # Set up of chat box where messages are displayed
        self.chat_screen = Text(self.frame)
        self.chat_screen.tag_configure("left", justify=LEFT)
        self.chat_screen.tag_configure("right", justify=RIGHT)
        self.chat_screen.pack(side="top")

        # setup text input to send a message when the enter button is pressed
        # or when the send button is pressed.
        self.input_field = Entry(self.chatbox_frame, bd=5, width=50, state=DISABLED)
        self.input_field.bind('<Return>', self.send_message)
        self.input_field.focus()
        self.input_field.pack(side="left")
        self.send_button = Button(self.chatbox_frame, text="SEND", command=lambda:None, state=DISABLED)
        self.send_button.bind("<ButtonRelease-1>", self.send_message)
        self.send_button.pack(side="left")
        # Add exit button
        self.space = Label(self.exit_frame, text="").pack()
        self.exit_button = Button(self.exit_frame, text= "EXIT CHATROOM", command=self.exit, bg="red")
        self.exit_button.pack()
        self.space = Label(self.exit_frame, text="").pack()
        self.chat_screen.insert(END, f"Welcome {self.firstName}!\n")

        self.chat_screen.insert(END, "Chat application has started. Please select a server from the dropdown menu.\n")
        # add elements to GUI and start GUI loop
        self.selections_frame.pack(side="top")
        self.chatbox_frame.pack(side="top")
        self.exit_frame.pack()
        self.frame.mainloop()
    
    # function returns nothing and it will give the class a list of active 
    # server names and update the dropdown
    def get_updated_server_list(self):
        self.servernames = list(getActiveServerSessions().keys())
        self.dropdown.configure(values= self.servernames)

    # Function takes in a servers name and gets its port number from the 
    # helper function getServerNumber and sets the gRPC insecure channel
    def join(self, selection):
        self.serverPortNumber = getServerNumber(selection)
        self.channel = grpc.insecure_channel(f'localhost:{self.serverPortNumber}')

    # This function is called once a server has been selected from the dropdown 
    # menu. It will confirm whether the user would like to switch servers to 
    # prevent accidental switching
    def switch(self, event):
        # get input from dropdown
        selection = self.dropdown.get()
        # ask user if they would like to switch to indicated server
        answer = messagebox.askyesno(title="Change Server Confirmation", message= f"Are you sure you want to join the server {selection}?")
        if answer:
            # if this is not the first time joining a server inform the current server you are leaving
            if self.connection != None:
                self.connection.SendMessage(chat_pb2.MessageFormat(first_name = self.firstName, client_identifier = self.clientID, message_text = "~LEFT THE CHATROOM~", server_port_number = self.serverPortNumber))         
            # set up new gRPC channel
            self.join(selection)
            self.connection = chat_pb2_grpc.ChatServiceStub(self.channel) 
            # error prevetion to enable text input only when server is connected.
            self.input_field.configure(state=NORMAL)
            self.send_button.configure(state=NORMAL)
            # generating a unique 4 digit client ID (just in case two or more people have the same name)
            self.clientID = self.connection.GetClientIdentifier(chat_pb2.ClientName(first_name = self.firstName)).client_identifier
            # get the servers port number and save it as a member variable
            self.serverPortNumber = self.connection.GetPortNumber(chat_pb2.Empty()).port_number
            # clear the screen and display the information of the server
            self.chat_screen.delete(1.0, END)
            self.chat_screen.insert(END,f"The server {selection} has given you a client identifier of {self.clientID}\n")
            self.chat_screen.insert(END, "Chat session has started. Enter your message in the text box below, then press enter.\n")

            # send message to others that you have joined the server and start 
            # listening for messages
            self.connection.SendMessage(chat_pb2.MessageFormat(first_name = self.firstName, client_identifier = self.clientID, message_text = "~ENTERED THE CHATROOM~", server_port_number = self.serverPortNumber))
            self.newThread = threading.Thread(target=self.waitingForIncomingMessages)
            self.newThread.daemon = True
            self.newThread.start()

    def send_message(self, event):
        # sending the message to the server
        message= self.input_field.get()
        self.input_field.delete(0,END)
        self.connection.SendMessage(chat_pb2.MessageFormat(first_name = self.firstName, client_identifier = self.clientID, message_text = message, server_port_number = self.serverPortNumber))
        self.chat_screen.insert(END, f"{self.firstName}: {message}\n", "right")


    # wait for incoming messages from the server sent by other users
    def waitingForIncomingMessages(self):

        for message in self.connection.GetMessage(chat_pb2.Empty()):  
            name = message.first_name
            msg = message.message_text
            if message.client_identifier != self.clientID and message.server_port_number == self.serverPortNumber: # this is to avoid printing a message that a client just sent on their own session
                self.chat_screen.insert(END, f"{name}: {msg}\n", "left")
    
    # called when either the exit chatroom button is selected or the X button 
    # is pressed. It will send a message to other clients that the user has
    # left the room
    def exit(self): 
        # confirm that the user would like to exit the program
        answer = messagebox.askyesno(title="Exit Confirmation", message= "Are you sure you want to exit the chat room?")
        if answer:
            if self.connection == None or self.serverPortNumber == None:
                root.destroy()
                sys.exit(0)
            else:
                self.chat_screen.insert(END, "Exiting Room\n")
                self.connection.SendMessage(chat_pb2.MessageFormat(first_name = self.firstName, client_identifier = self.clientID, message_text = "~LEFT THE CHATROOM~", server_port_number = self.serverPortNumber))
                root.destroy()
                sys.exit(0)


if __name__ == "__main__":
    # root tkinter window
    root = Tk()
    # Set
    root.title("gRPC Chat")
    root.maxsize(720,1080)
    main_frame = Frame(root, width = 300, height = 300, padx=5, pady=5)
    main_frame.pack()
    root.withdraw() #hide main frame while taking input
    name = simpledialog.askstring("Registration", "Please enter your name:", parent=root)
    root.deiconify() # make main frame visible after taking input
    # launch the client and GUI
    c = Client(name, main_frame)
