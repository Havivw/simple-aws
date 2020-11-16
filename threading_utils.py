import threading, queue


def run_thread_classes(thread_cls, num_of_threads, list_of_init_args=None):
    thread_classes = []
    for i in range(num_of_threads):
        if list_of_init_args and i < len(list_of_init_args):
            thread_classes.append(thread_cls(*list_of_init_args[i]).start())
        else:
            thread_classes.append(thread_cls().start())
    return thread_classes


def run_func_in_threads(thread_func, num_of_threads, list_of_args=None, callback=None):
    queue_res = queue.Queue()
    list_of_args.append(queue_res)
    t = threading.Thread(target=thread_func, args=tuple(list_of_args))
    t.start()
    t.join()
    result = queue_res.get()
    return result
