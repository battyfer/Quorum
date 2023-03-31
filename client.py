import grpc
import uuid
import quorum_pb2
import quorum_pb2_grpc
import time

file_names = {}

class Client:
    def __init__(self, registry_address):
        self.registry_channel = grpc.insecure_channel(registry_address)
        self.registry_stub = quorum_pb2_grpc.RegistryStub(self.registry_channel)

    def write(self, filename: str, content: str):
        write_replicas = self.registry_stub.GetWriteReplicas(quorum_pb2.Empty())

        # if client is updating an existing file, then it reuses the same UUID which was generated previously.                   
        if filename in file_names:
            file_uuid = file_names[filename]
        else:
            file_uuid = str(uuid.uuid4())
            file_names[filename] = file_uuid

        timestamp = None
        for replica in write_replicas.replicas:
            replica_address = f"localhost:{replica.port}"
            with grpc.insecure_channel(replica_address) as channel:
                stub = quorum_pb2_grpc.Replica_ServiceStub(channel)
                response = stub.Write(quorum_pb2.WriteRequest(uuid=file_uuid, filename=filename, content=content))
                if timestamp is None or response.timestamp > timestamp:
                    timestamp = response.timestamp
                    status = response.status
            ts = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(timestamp))
            print('\n')
            print(f"Status: {status}")
            print(f"UUID: {file_uuid}")
            print(f"Version: {ts}")
            print('\n')
        return file_uuid, timestamp, response.status
    
    def read(self, file_uuid: str):
        read_replicas = self.registry_stub.GetReadReplicas(quorum_pb2.Empty())
        latest_status = None
        latest_filename = None
        latest_timestamp = None
        latest_content = None
        for replica in read_replicas.replicas:
            replica_address = f"localhost:{replica.port}"
            with grpc.insecure_channel(replica_address) as channel:
                stub = quorum_pb2_grpc.Replica_ServiceStub(channel)
                response = stub.Read(quorum_pb2.ReadRequest(uuid=file_uuid))
                if latest_timestamp is None or response.timestamp > latest_timestamp:
                    latest_status = response.status
                    latest_filename = response.filename
                    latest_timestamp = response.timestamp
                    latest_content = response.content
        ts2 = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(latest_timestamp))
        print('\n')
        print(f"Status: {latest_status}")
        print(f"Name: {latest_filename}")
        print(f"Content: {latest_content}")
        print(f"Version: {ts2}")
        return latest_status
    
    def delete(self, file_uuid: str):
        write_replicas = self.registry_stub.GetWriteReplicas(quorum_pb2.Empty())
        for replica in write_replicas.replicas:
            replica_address = f"localhost:{replica.port}"
            with grpc.insecure_channel(replica_address) as channel:
                stub = quorum_pb2_grpc.Replica_ServiceStub(channel)
                response = stub.Delete(quorum_pb2.DeleteRequest(uuid=file_uuid))
                print(f"Status: {response.status}")


def serve():
    registry_address = "localhost:8888"
    client = Client(registry_address)
    while True:
        print('\n')
        print("Menu:")
        print("1. Get all replicas")
        print("2. Write")
        print("3. Read")
        print("4. Delete")
        print("5. Exit")
        choice = int(input("Enter your choice: "))

        if choice == 1:
            # print("All replicas:")
            replicas = client.registry_stub.GetAllReplicas(quorum_pb2.Empty())
            if(replicas.replicas == []):
                print("No replicas found")
            else:
                for replica in replicas.replicas:
                    print(f"Replica: {replica.ip}:{replica.port}")
            # print("Write replicas:")

        elif choice == 2:
            filename = input("Enter filename: ")
            content = input("Enter content: ")
            file_uuid, timestamp, status = client.write(filename, content)
            

        elif choice == 3:
            file_uuid = input("Enter file UUID: ")
            status = client.read(file_uuid)

        elif choice == 4:
            file_uuid = input("Enter file UUID: ")
            client.delete(file_uuid)
            # print("File deleted")

        elif choice == 5:
            break
        else:
            print("Invalid choice")


if __name__ == '__main__':
    serve()