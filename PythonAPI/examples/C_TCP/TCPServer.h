#ifndef TCP_SERVER_DEFINES
#define TCP_SERVER_DEFINES

#include "defines.h"

struct TCP_Server_Data
{
    int sockfd_in, clientsockfd_in;
    
    char* recv_buffer;
    char* input_buffer;

    long read_size;
    long received_bytes;
    long buffer_size;
    
    struct sockaddr_in address_in;

    char active;
    char connected;

    pthread_mutex_t mutex;
    pthread_t tid;
};

struct TCP_Server_Data * TCP_Server_Start(int port_in, long buffer_size);

char * TCP_Server_Read(struct TCP_Server_Data * data, char * buffer);

struct TCP_Server_Data * TCP_Server_Stop(struct TCP_Server_Data * data);

#endif