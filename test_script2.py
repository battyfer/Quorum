"""
For each protocol, write an automated test script which does the following tasks:
Create/Run a registry server.
Create/Run N replicas.
Create/run a client
Client then performs a write operation
Client then reads from all the replicas one by one
Print the result of read from each replica
Client then again performs a write operation
Client then reads from all the replicas one by one
Print the result of read from each replica
Client then deletes one of the files (which was written previously)
Client then tries to read the deleted file from all the replicas one by one
Print the result of read from each replica

"""
import unittest
import threading
import time
from registry import serve as registry_serve
from replica import serve as replica_serve
from client import serve as client_serve

class TestQuorumProtocol(unittest.TestCase):
    def setUp(self):
        self.N = 3
        self.N_r = 2
        self.N_w = 2
        self.registry_address = "localhost:8888"
        self.replica_addresses = [f"localhost:{50051+i}" for i in range(self.N)]
        self.registry_thread = threading.Thread(target=registry_serve, args=(self.N_r,self.N_w,self.N))
        self.replica_threads = [threading.Thread(target=replica_serve, args=(f"/tmp/replica_storage_{i}",)) for i in range(self.N)]
        self.registry_thread.start()
        for replica_thread in self.replica_threads:
            replica_thread.start()
        time.sleep(1)
        self.client = client_serve(self.registry_address)
        for replica_address in self.replica_addresses:
            self.client.register_replica(replica_address)

    def tearDown(self):
        self.registry_thread.do_run = False
        for replica_thread in self.replica_threads:
            replica_thread.do_run = False
        self.registry_thread.join()
        for replica_thread in self.replica_threads:
            replica_thread.join()

    def test_write_read_delete(self):
        file_uuid, timestamp = self.client.write("example.txt", "Hello World!")
        for replica_address in self.replica_addresses:
            content = self.client.read_from_replica(replica_address, file_uuid)
            self.assertEqual(content, "Hello World!")
        file_uuid, timestamp = self.client.write("example.txt", "Hello again!")
        for replica_address in self.replica_addresses:
            content = self.client.read_from_replica(replica_address, file_uuid)
            self.assertEqual(content, "Hello again!")
        self.client.delete(file_uuid)
        for replica_address in self.replica_addresses:
            content = self.client.read_from_replica(replica_address, file_uuid)
            self.assertIsNone(content)

if __name__ == '__main__':
    unittest.main()