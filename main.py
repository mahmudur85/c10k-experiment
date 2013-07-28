import multiprocessing
import os
import select
import socket


def handle_conn(conn, addr):
    msg = 'Process: %(pid)s; Peer: %(addr)s' % {
        'pid': os.getpid(),
        'addr': addr,
    }
    print msg

    print 'Wait for data from peer'
    data = conn.recv(32)

    print 'Data received from peer'
    conn.sendall(data)
    conn.close()


def basic_server(socket_):
    child = []
    try:
        while True:
            print 'Waiting for peer'

            conn, addr = socket_.accept()
            print 'Peer connected:', addr

            p = multiprocessing.Process(target=handle_conn, args=(conn, addr))
            p.start()
            child.append(p)
    finally:
        [p.terminate() for p in child if p.is_alive()]


def select_server_v0(socket_):
    '''Single process select(). Use non-blocking accept() but blocking recv().

    Since this is using single process and recv() blocks the next accept(),
    concurrency is not achieved.
    '''
    while True:
        print 'Waiting for peer'
        readable, w, e = select.select([socket_], [], [], 1)

        if socket_ not in readable:
            continue

        conn, addr = socket_.accept()
        print 'Peer connected:', addr

        handle_conn(conn, addr)


def select_server_v1(socket_):
    '''Single process select() with sub-processes to recv(). Use non-blocking
       accept() but blocking recv().

    Non-blocking accept() is not affected by the blocking recv() since the
    blocks happens in the sub-processes. Concurrency is achieved but it's only
    a slight improvement from *basic_server* because CPU time is still consumed
    for context-switching when waiting for the blocking recv().
    '''
    child = []
    try:
        while True:
            print 'Waiting for peer'
            readable, w, e = select.select([socket_], [], [], 1)

            if socket_ not in readable:
                continue

            conn, addr = socket_.accept()
            print 'Peer connected:', addr

            p = multiprocessing.Process(target=handle_conn, args=(conn, addr))
            p.start()
            child.append(p)
    finally:
        [p.terminate() for p in child if p.is_alive()]


def main():
    # Ref: http://is.gd/S1dtCH
    HOST, PORT = '127.0.0.1', 8000

    socket_ = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    socket_.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    socket_.bind((HOST, PORT))

    try:
        #socket_.listen(0)
        #basic_server(socket_)

        #socket_.setblocking(0)
        #socket_.listen(0)
        #select_server_v0(socket_)

        socket_.setblocking(0)
        socket_.listen(0)
        select_server_v1(socket_)
    finally:
        socket_.close()


if __name__ == '__main__':
    main()
