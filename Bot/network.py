import socket
import pickle
import struct
import math

DEFAULT_BYTES = 1024  # Maximum bytes to be sent in one message


class Network:
    def __init__(self, ip=None, port=None):
        # Initialize the client socket
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        # Set server IP and port, or prompt user if not provided
        self.server = (
            ip if ip is not None else input(
                "Enter the IP address of the server: ")
        )  # The IP address of the server
        self.port = (
            port if port is not None else int(
                input("Enter port to connect to: "))
        )  # Port of the server

        # Complete address to connect to
        self.addr = (
            self.server,
            self.port,
        )

        self.id = None  # Initialize the client ID as None

    # Function to connect to the server
    def connect(self):
        try:
            self.client.connect(self.addr)  # Connect to the server
            print("Connected!")

            # Receive initial data from the server
            data = self.recv()
            self.id = data  # The first element in the data is the client ID

            # Send metadata about the bot
            self.send({"updated": {"bot": True, "username": "SlUgGyFrOgS"}})

            return data
        except Exception as e:
            print("Could not connect to server!")
            print("Error while trying to connect:", e)
            return False

    # Send data to the server
    def send(self, data, pickle_data=True):
        try:
            # Pickle the data if specified
            if pickle_data:
                data = pickle.dumps(data)

            # Send large data in batches
            if len(data) >= DEFAULT_BYTES:
                return self.send_huge(data)

            # Send the length of the data and then the data itself
            self.client.sendall(struct.pack("h", len(data)))
            self.client.sendall(data)
            return True

        except Exception as e:
            print("Error while trying to send data:", e)
            return False

    # Receive data from the server
    def recv(self, load=True):
        data = None
        try:
            # Receive the length of the data
            lenData = self.client.recv(2)
            if not lenData:
                return ""  # Server might be down

            # Unpack the length of the data
            lenData = struct.unpack("h", lenData)[0]
            data = self.client.recv(lenData)

            try:
                # Unpickle data and handle large data in batches
                pickled = pickle.loads(data)
                if isinstance(pickled, dict) and pickled.get("message_type") == "huge":
                    n_batches = pickled["n_batches"]
                    binData = b""
                    batch_sizes = struct.unpack(
                        "h" * n_batches, self.client.recv(2 * n_batches)
                    )
                    for size in batch_sizes:
                        batchData = self.client.recv(size)

                        if not batchData:
                            return ""  # Server might be down

                        binData += batchData

                    return binData

            except Exception as e:
                print("Error while trying to get huge data:", e)

            return pickle.loads(data) if load else data

        except Exception as e:
            print("Error while receiving:", e)
            print(data)
            return False

    def send_huge(self, data_bytes):
        # Send large data in multiple batches
        size = len(data_bytes)
        n_batches = math.ceil(size / DEFAULT_BYTES)
        batch_lengths = [DEFAULT_BYTES] * (n_batches - 1) + [
            size - (n_batches - 1) * DEFAULT_BYTES
        ]
        fmt = "h" * n_batches

        # Send the metadata about the large message
        self.send({"message_type": "huge", "n_batches": n_batches})

        # Send batch lengths and data in batches
        self.client.sendall(struct.pack(fmt, *batch_lengths))
        for i in range(n_batches):
            self.client.sendall(
                data_bytes[i * DEFAULT_BYTES: (i + 1) * DEFAULT_BYTES])

        return True
