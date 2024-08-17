import threading
import queue

class Scene:
    def __init__(self):
        self.objects = []
        self.lock = threading.Lock()
        self.update_queue = queue.Queue()

    def add_object(self, obj):
        self.update_queue.put(('add', obj))

    def remove_object(self, obj):
        self.update_queue.put(('remove', obj))

    def process_updates(self):
        updated = False
        while True:
            try:
                action, obj = self.update_queue.get_nowait()
                with self.lock:
                    if action == 'add':
                        self.objects.append(obj)
                    elif action == 'remove':
                        self.objects.remove(obj)
                updated = True
            except queue.Empty:
                break
        return updated
