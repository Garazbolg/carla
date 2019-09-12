#ifndef TCP_CLIENT_DEFINES
#define TCP_CLIENT_DEFINES

#include "defines.h"

struct TCP_Client_Data
{
    int sockfd_out;
    
    char* output_buffer;

    long buffer_size;
    
    struct sockaddr_in address_out;

    char active;
    char connected;

    pthread_mutex_t mutex;
    pthread_t tid;
    pthread_cond_t cond;

};

struct TCP_Client_Data * TCP_Client_Start(char* addr_out, int port_out, long buffer_size);

struct TCP_Client_Data * TCP_Client_Stop(struct TCP_Client_Data * data);

void TCP_Client_Send(struct TCP_Client_Data * data, char * buffer);

#endif