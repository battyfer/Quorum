import grpc
from concurrent import futures
import random
import quorum_pb2
import quorum_pb2_grpc

class Registry(quorum_pb2_grpc.RegistryServicer):
    def __init__(self, N_r, N_w, N):
        self.N_r = N_r
        self.N_w = N_w
        self.N = N
        self.replicas = []
        
    def RegisterReplica(self, request, context):
        replica = (request.ip, request.port)
        if replica not in self.replicas:
            self.replicas.append(replica)
            print("Replica Registered: ", replica)
            # print("length -> ", len(self.replicas))
            return quorum_pb2.RegisterResponse(status="SUCCESS", count = len(self.replicas))
        else:
            print("Replica already registered: ", replica)
        return quorum_pb2.RegisterResponse(status="FAILURE", count = len(self.replicas))
    
    def GetReadReplicas(self, request, context):
        read_replicas = random.sample(self.replicas, self.N_r)
        return quorum_pb2.ReplicaList(replicas=[quorum_pb2.Replica(ip=ip, port=port) for ip,port in read_replicas])
    
    def GetWriteReplicas(self, request, context):
        write_replicas = random.sample(self.replicas, self.N_w)
        return quorum_pb2.ReplicaList(replicas=[quorum_pb2.Replica(ip=ip, port=port) for ip,port in write_replicas])
    
    def GetAllReplicas(self, request, context):
        return quorum_pb2.ReplicaList(replicas=[quorum_pb2.Replica(ip=ip, port=port) for ip,port in self.replicas])


def serve(N_r: int, N_w: int, N: int):
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    quorum_pb2_grpc.add_RegistryServicer_to_server(Registry(N_r,N_w,N), server)
    print("Registry Server Started!")
    server.add_insecure_port('localhost:8888')
    server.start()
    server.wait_for_termination()

if __name__ == '__main__':
    while True:
        try:
            N_r = int(input("Enter Value of N_r: "))
            N_w = int(input("Enter Value of N_w: "))
            N = int(input("Enter Value of N: "))
            if not (N_r + N_w > N and N_w > N/2):
                print("Invalid values. Please enter valid values for N_r, N_w and N")
                print("\n")
            else:
                serve(N_r, N_w, N)
                break
        except ValueError:
            print("Please enter valid integer values for N_r, N_w and N")