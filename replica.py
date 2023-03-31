import grpc
from concurrent import futures
import time
import os
import quorum_pb2
import quorum_pb2_grpc

storage_path = ""

class Replica(quorum_pb2_grpc.Replica_ServiceServicer):
    def __init__(self):
        self.files = {}

    def Write(self, request, context):
        global storage_path
        file_uuid = request.uuid
        filename = request.filename
        content = request.content
        print("Name : ", filename)
        print("Content : ", content)
        print("UUID : ", file_uuid)
        timestamp = time.time()
        
        if file_uuid not in self.files:
            if not any(filename == file_info[0] for file_info in self.files.values()):
                self.files[file_uuid] = (filename, timestamp)
                # filename = filename + ".txt"
                path = storage_path + "\\" + filename + ".txt"
                with open(path, 'w') as f:
                    if(f.write(content)):
                        return quorum_pb2.WriteResponse(status="SUCCESS", timestamp=timestamp, uuid=file_uuid)
                    else:
                        return quorum_pb2.WriteResponse(status="FAILED", timestamp=timestamp, uuid=file_uuid)
            else:
                return quorum_pb2.WriteResponse(status="FILE WITH THE SAME NAME ALREADY EXISTS", timestamp=timestamp, uuid=file_uuid)
        else:
            if any(filename == file_info[0] for file_info in self.files.values()):
                # filename = filename + ".txt"
                path2 = storage_path + "\\" + filename + ".txt"
                with open(path2, 'w') as f:
                    if(f.write(content)):
                        return quorum_pb2.WriteResponse(status="SUCCESS", timestamp=timestamp, uuid=file_uuid)
                    else:
                        return quorum_pb2.WriteResponse(status="FAILED", timestamp=timestamp, uuid=file_uuid)
            else:
                # print(f"Filename : {filename} and File UUID : {file_uuid}")
                # print(self.files.values[0])
                return quorum_pb2.WriteResponse(status="DELETED FILE CANNOT BE UPDATED", timestamp=timestamp, uuid=file_uuid)
        
            
    
    def Read(self, request, context):
        global storage_path
        file_uuid = request.uuid
        if file_uuid not in self.files:
            return quorum_pb2.ReadResponse(status="FILE DOES NOT EXIST", timestamp=None, content=None, filename=None)
        else:
            filename, timestamp = self.files[file_uuid]
            if not filename == "":
                path3 = storage_path + "\\" + filename + ".txt"
                with open(path3, 'r') as f:
                    content = f.read()
                    return quorum_pb2.ReadResponse(status = "SUCCESS", filename=filename, content=content, timestamp=timestamp)
            else:
                timestamp = time.time()
                return quorum_pb2.ReadResponse(status="FILE ALREADY DELETED", filename=None, content=None, timestamp=timestamp)
            

    
    def Delete(self, request, context):
        global storage_path
        file_uuid = request.uuid
        filename, t = self.files[file_uuid]
        if file_uuid not in self.files:
            timestamp = time.time()
            self.files[file_uuid] = ("", timestamp)
            return quorum_pb2.DeleteResponse(status="SUCCESS")
        else:
            if filename == "":
                return quorum_pb2.DeleteResponse(status="FILE ALREADY DELETED", timestamp=timestamp)
            else:
                path5 = storage_path + "\\" + filename + ".txt"
                os.remove(path5)
                timestamp = time.time()
                self.files[file_uuid] = ("", timestamp)
                return quorum_pb2.DeleteResponse(status="SUCCESS")
    

def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    quorum_pb2_grpc.add_Replica_ServiceServicer_to_server(Replica(), server)
    ip = input("Enter IP Address: ")
    while True:
        port = int(input("Enter Port Number: "))
        if port == "8888":
            print("Port 8888 is reserved for the registry server. Please choose a different port.")
        else:
            break
    server.add_insecure_port(f'{ip}:{port}')
    server.start()
    ## register this replica with the registry server
    with grpc.insecure_channel('localhost:8888') as channel:
        stub = quorum_pb2_grpc.RegistryStub(channel)
        response = stub.RegisterReplica(quorum_pb2.Replica(ip=ip, port=port))
        print("Replica Registaration Status: ", response.status)

        ## create a directory for this replica
        global storage_path
        path = os.getcwd()
        storage_path = os.path.join(path, "Replica_")
        storage_path = storage_path + str(response.count)
        if not os.path.exists(storage_path):
            os.makedirs(storage_path)
            print("Directory ", storage_path, " Created")
        else:
            print("Directory ", storage_path, " already exists")

    server.wait_for_termination()

if __name__ == '__main__':
    serve()