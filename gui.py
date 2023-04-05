from tkinter import *


if __name__ == '__main__':
    root = Tk()
    chat_frame = Frame(root, width=500, height= 500)
    root.title("Chat Room")
    message_label = Label(root, text="Message:")
    message_label.pack()
    
    message_entry = Entry(root, width=50)
    message_entry.pack()
    
    send_button = Button(root, text="Send", command=lambda: None)
    send_button.pack()
    
    message_listbox = Listbox(root, height=20, width=50)
    message_listbox.pack()
    
    # Create thread to handle receiving messages
    # receive_thread = threading.Thread(target=receive_messages)
    # receive_thread.start()
    # Start GUI
    root.mainloop()
