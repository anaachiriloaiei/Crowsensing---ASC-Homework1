"""
This module represents a device.
Achiriloaiei Ana
334 CC
Computer Systems Architecture Course
Assignment 1
March 2019
"""

from threading import Event, Thread, Lock, Semaphore
import Queue

class ReusableBarrier(object):
    """
    Barrier implementation using Semaphores
    """
    def __init__(self, num_threads):
        self.num_threads = num_threads
        self.count_threads1 = [self.num_threads]
        self.count_threads2 = [self.num_threads]
        self.count_lock = Lock()
        self.threads_sem1 = Semaphore(0)
        self.threads_sem2 = Semaphore(0)

    def wait(self):
        """
        wait method
        """
        self.phase(self.count_threads1, self.threads_sem1)
        self.phase(self.count_threads2, self.threads_sem2)

    def phase(self, count_threads, threads_sem):
        """
        phase method
        """
        with self.count_lock:
            count_threads[0] -= 1
            if count_threads[0] == 0:
                for _ in range(self.num_threads):
                    threads_sem.release()
                count_threads[0] = self.num_threads
        threads_sem.acquire()



class Device(object):
    """
    Class that represents a device.
    """

    def __init__(self, device_id, sensor_data, supervisor):
        """
        Constructor.

        @type device_id: Integer
        @param device_id: the unique id of this node; between 0 and N-1

        @type sensor_data: List of (Integer, Float)
        @param sensor_data: a list containing (location, data) as measured by this device

        @type supervisor: Supervisor
        @param supervisor: the testing infrastructure's control and validation component
        """
        self.device_barrier = None
        self.devices = []
        self.locations_locks = {}
        self.script_queue = Queue.Queue()
        self.device_id = device_id
        self.sensor_data = sensor_data
        self.supervisor = supervisor
        self.script_received = Event()
        self.scripts = []
        self.timepoint_done = Event()
        self.thread = DeviceThread(self)
        self.thread.start()

    def __str__(self):
        """
        Pretty prints this device.

        @rtype: String
        @return: a string containing the id of this device
        """
        return "Device %d" % self.device_id

    def setup_devices(self, devices):
        """
        Setup the devices before simulation begins.

        @type devices: List of Device
        @param devices: list containing all devices
        """
        # se creaza bariera rentranta si lock-urile comune fiecarui device
        self.devices = devices
        if self.device_id == 0:
            if self.device_barrier is None:
                self.device_barrier = ReusableBarrier(len(devices))
            for i in range(0, len(devices)):
                devices[i].device_barrier = self.device_barrier
                for location in devices[i].sensor_data:
                    if location not in self.locations_locks:
                        lock = Lock()
                        self.locations_locks[location] = lock
                devices[i].locations_locks = self.locations_locks

    def assign_script(self, script, location):
        """
        Provide a script for the device to execute.

        @type script: Script
        @param script: the script to execute from now on at each timepoint; None if the
            current timepoint has ended

        @type location: Integer
        @param location: the location for which the script is interested in
        """
        if script is not None:
            self.scripts.append((script, location))
        else:
            self.timepoint_done.set()

    def get_data(self, location):
        """
        Returns the pollution value this device has for the given location.

        @type location: Integer
        @param location: a location for which obtain the data

        @rtype: Float
        @return: the pollution value
        """
        return self.sensor_data[location] if location in self.sensor_data else None

    def set_data(self, location, data):
        """
        Sets the pollution value stored by this device for the given location.

        @type location: Integer
        @param location: a location for which to set the data

        @type data: Float
        @param data: the pollution value
        """
        if location in self.sensor_data:
            self.sensor_data[location] = data

    def shutdown(self):
        """
        Instructs the device to shutdown (terminate all threads). This method
        is invoked by the tester. This method must block until all the threads
        started by this device terminate.
        """
        self.thread.join()


class DeviceThread(Thread):
    """
    Class that implements the device's worker thread.
    """

    def __init__(self, device):
        """
        Constructor.

        @type device: Device
        @param device: the device which owns this thread
        """
        Thread.__init__(self, name="Device Thread %d" % device.device_id)
        self.device = device

    def run(self):
        threads_list = []

		#se creaza workerii
        for i in range(8):
            subthreads = MyThread(self.device, self.device.script_queue, i)
            threads_list.append(subthreads)

        for subthreads in threads_list:
            subthreads.start()

        while True:
            # afla vecinii
            neighbours = self.device.supervisor.get_neighbours()
            if neighbours is None:
                break

			#se asteapta ca toate scripturile timepont-ului curent sa fie primite
            self.device.timepoint_done.wait()

			#se adauga in coada tuplurile
            for (script, location) in self.device.scripts:
                self.device.script_queue.put((script, location, neighbours))

			#se asteapta prelucrarea tuturor scripturilor
            self.device.script_queue.join()

			#se asteapta ca toate threadurile master sa ajunga aici
            self.device.device_barrier.wait()

			#se  poate trece la urmatorul timepoint
            self.device.timepoint_done.clear()

		#se opresc workerii daca nu mai au ce sa prelucreze
        for i in range(8):
            self.device.script_queue.put((None, None, None))

        for subthreads in threads_list:
            subthreads.join()

class MyThread(Thread):
    """
    Class that implements a worker thread.
    """

    def __init__(self, device, script_queue, subthread_id):
        Thread.__init__(self, name="Device Thread %d" % device.device_id)
        self.device = device
        self.script_queue = script_queue
        self.subthread_id = subthread_id

    def run(self):

        while True:
			#extrag scriptul, locatia si vecinii din tuplu
            tuples = self.script_queue.get()
            script = tuples[0]
            location = tuples[1]
            neighbours = tuples[2]

            if neighbours is None or script is None:
                break

			#acaparez locatia
            self.device.locations_locks[location].acquire()

			#colecteza date de la vecini despre locatie
            script_data = []
            for device in neighbours:
                data = device.get_data(location)
                if data is not None:
                    script_data.append(data)
            # adauga si datele proprii daca le detine
            data = self.device.get_data(location)
            if data is not None:
                script_data.append(data)
            # ruleaza script-ul pe datele colectate
            if script_data != []:
                result = script.run(script_data)
                # actualizeaza datele vecinilor
                for device in neighbours:
                    device.set_data(location, result)
                    # actualizeaza datele proprii
                    self.device.set_data(location, result)
            # elibereaza lock-ul pentru locatie
            self.device.locations_locks[location].release()
			#procesarea operariilor este completa
            self.device.script_queue.task_done()
