#include "defines.h"
#include "TCPServer.h"

void *TCP_Server_Run(void* arg)
{
    struct TCP_Server_Data * data = arg;
    while((data->active) && (data->clientsockfd_in = accept(data->sockfd_in,0,0))>0)
    {
        if (data->clientsockfd_in < 0)
            perror("accept");
        data->connected = 1;
        sleep(1);

        while (data->connected && data->active)
        {
            data->read_size = recv(data->clientsockfd_in, (data->recv_buffer) + (data->received_bytes), data->buffer_size-data->received_bytes, 0);
            if(data->read_size > 0)
            {
                data->received_bytes += data->read_size;
                if (data->received_bytes >= data->buffer_size)
                {
                    data->received_bytes = 0;
                    
                    pthread_mutex_lock(&(data->mutex));
                    memcpy(data->input_buffer,data->recv_buffer,data->buffer_size);
                    pthread_mutex_unlock(&(data->mutex));
                }
            }
            else if(data->read_size == 0) // disconnect
            {
                data->connected = 0;
                data->received_bytes = 0;
            }
            else
            {
                data->received_bytes = 0;
                data->connected = 0;
                perror("recv");
            }
        }
        data->received_bytes = 0;
    }

    free(data->recv_buffer);
    data->recv_buffer = NULL;

    free(data->input_buffer);
    data->input_buffer = NULL;
}

struct TCP_Server_Data * TCP_Server_Start(int port_in, long buffer_size)
{
    struct TCP_Server_Data * data = malloc(sizeof(struct TCP_Server_Data));

    data->active = 1;
    data->connected = 0;
    data->read_size = 0;
    data->received_bytes = 0;
    data->buffer_size = buffer_size;

    pthread_mutex_init(&(data->mutex),NULL);

    data->recv_buffer = malloc(data->buffer_size);
    memset(data->recv_buffer,200,data->buffer_size);
    data->input_buffer = malloc(data->buffer_size);
    memset(data->input_buffer,255,data->buffer_size);

    data->sockfd_in = socket(AF_INET, SOCK_STREAM, 0);
    
    memset(&data->address_in, 0, sizeof(data->address_in));
    data->address_in.sin_family      = AF_INET;
    data->address_in.sin_addr.s_addr = INADDR_ANY;
    data->address_in.sin_port        = htons(port_in);

    if (bind(data->sockfd_in,(struct sockaddr *)&data->address_in, sizeof(struct sockaddr_in))<0)
        perror ("binding_in");
    if(listen(data->sockfd_in,5)<0)
        perror("listen");
    if(!pthread_create(&(data->tid), NULL, TCP_Server_Run, (void*) data))
    {
        perror("thread create");
    }

    return data;
}

char * TCP_Server_Read(struct TCP_Server_Data * data, char * buffer)
{
    pthread_mutex_lock(&(data->mutex));
    memcpy(buffer,data->input_buffer,data->buffer_size);
    pthread_mutex_unlock(&(data->mutex));
    return buffer;
}

struct TCP_Server_Data * TCP_Server_Stop(struct TCP_Server_Data * data)
{
    data->active = 0;

    if(data->sockfd_in > 0)
    {
        close(data->sockfd_in);
        data->sockfd_in = 0;
    }

    if(data->clientsockfd_in > 0)
    {
        close(data->clientsockfd_in);
        data->clientsockfd_in = 0;
    }

    pthread_join(data->tid,NULL);

    return NULL;
}