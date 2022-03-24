import socket, pickle, struct, math

DEFAULT_BYTES = 1024  # max bytes to be sent in one message


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

            # send some metadata about the bot
            self.send({"updated": {"bot": True, "username": "SlUgGyFrOgS"}})

            return data
        except Exception as e:
            print("Could not connect to server!")
            print("error while trying to connect:", e)
            return False

    # send some data to the server
    def send(self, data, pickle_data=True):
        try:
            if pickle_data:
                data = pickle.dumps(data)

            if len(data) >= DEFAULT_BYTES:
                return self.send_huge(data)

            self.client.sendall(struct.pack("h", len(data)))
            self.client.sendall(data)
            return True

        except Exception as e:
            print("error while trying to send data:", e)
            return False

    # recieve some data from the server
    def recv(self, load=True):
        data = None
        try:
            lenData = self.client.recv(2)
            if not lenData:
                return ""  # server down
            lenData = struct.unpack("h", lenData)[
                0
            ]  # length of data will be padded to 2  bytes
            data = self.client.recv(lenData)

            try:
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
                            return ""  # server down

                        binData += batchData

                    return binData

            except Exception as e:
                print("error while trying to get huge data: ", e)

            return pickle.loads(data) if load else data

        except Exception as e:
            print("error while recieving:", e)
            print(data)
            return False

    def send_huge(self, data_bytes):

        size = len(data_bytes)
        n_batches = math.ceil(size / DEFAULT_BYTES)
        batch_lengths = [DEFAULT_BYTES] * (n_batches - 1) + [
            size - (n_batches - 1) * DEFAULT_BYTES
        ]
        fmt = "h" * n_batches

        # send the data in batches
        self.send({"message_type": "huge", "n_batches": n_batches})

        self.client.sendall(struct.pack(fmt, *batch_lengths))
        for i in range(n_batches):
            self.client.sendall(data_bytes[i * DEFAULT_BYTES : (i + 1) * DEFAULT_BYTES])

        return True

