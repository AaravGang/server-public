import socket, pickle


class Network:
    def __init__(self, ip=None, port=None):
        # initialise the client
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server = (
            ip if ip is not None else input("Enter the IP address of the server: ")
        )  # the ip address of the server
        self.port = (
            port if port is not None else int(input("Enter port to connect to: "))
        )  # port of the server
        self.addr = (
            self.server,
            self.port,
        )  # complete address, to which we can now connect to
        self.id = None

    # function to connect to the server
    def connect(self):
        try:
            self.client.connect(self.addr)
            print("Connected!")
            # the server sends some initialisation data, so recieve it
            data = self.recv()
            self.id = data  # the first element in the data will be the id
            return data
        except Exception as e:
            print("Could not connect to server!")
            print("error while trying to connect:",e)
            return False

    # send some data to the server
    def send(self, data, pickle_data=True):
        try:
            if pickle_data:
                data = pickle.dumps(data)

            self.client.sendall(data)
            return True

        except Exception as e:
            print("error while trying to send data:",e)
            return False

    # recieve some data from the server
    def recv(self, buffer_size=2048, load=True):
        data = None
        try:
            data = self.client.recv(buffer_size)
            if not data:
                return False
            return pickle.loads(data) if load else data
        except Exception as e:
            print("error while recieving:",e)
            print(data)
            return False
