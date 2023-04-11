# CS4459 - Final Project
## A Distributed Application: Multi-Server Chat System 
### Created by: Daniel McGarr and Alex Mihas 

Multi-server and multi-client chat application created with gRPC. Created as a final prject for CS4459 - Selected Topics on Scalable and Robust 
Distributed Systems at the University of Western Ontario.

Please install tkinter package before running. Install by typing ```pip3 install tk``` into the terminal.

To run the GRPC protofile type the following command into the terminal ```python -m grpc_tools.protoc -I . --python_out=. --grpc_python_out=. chat.proto```. This will create the ```chat_pb2_grpc.py``` and ```chat_pb2.py``` files. These are generated by running the protofile and will handle the communication services of our chat system. 
 
To start a server, run ```python3 server.py``` in the terminal. It will prompt for a integer port number and a name for the server.
   
To start a client, run ```python client.py``` in the terminal. I will prompt the user for their name. To start exchanging messsages select a server from the drop down list. If the user wishes to switch to a different active server it will be selected by the same method.
