#include "defines.h"
#include "TCPClient.h"

void *TCP_Client_Run(void* arg)
{
    struct TCP_Client_Data * data = arg;
    pthread_mutex_lock(&(data->mutex));
    while(data->active)
    {
        while(connect(data->sockfd_out,(struct sockaddr *)&data->address_out, sizeof(struct sockaddr_in))<0)
        {
            data->connected=0;
            sleep(1);
        }
        
        data->connected=1;
        while(data->connected && data->active)
        {
            if(!pthread_cond_wait(&(data->cond),&(data->mutex)))
            {
                if(send(data->sockfd_out,data->output_buffer,data->buffer_size,0)<=0)
                {
                    data->connected = 0;
                }
            }
        }
    }
    
    pthread_mutex_unlock(&(data->mutex));
}

struct TCP_Client_Data * TCP_Client_Start(char* addr_out, int port_out, long buffer_size)
{
    struct TCP_Client_Data * data = malloc(sizeof(struct TCP_Client_Data));

    data->connected = 0;
    data->active = 1;
    data->buffer_size = buffer_size;

    pthread_cond_init(&(data->cond),NULL);
    pthread_mutex_init(&(data->mutex),NULL);

    data->output_buffer = malloc(data->buffer_size);
    memset(data->output_buffer,50,data->buffer_size);

    data->sockfd_out = socket(AF_INET, SOCK_STREAM, 0);
    
    memset(&data->address_out, 0, sizeof(data->address_out));
    data->address_out.sin_family      = AF_INET;
    data->address_out.sin_addr.s_addr = inet_addr(addr_out);
    data->address_out.sin_port        = htons(port_out);

    if(!pthread_create(&(data->tid), NULL, TCP_Client_Run, (void*) data))
    {
        perror("thread create");
    }

    return data;
}

struct TCP_Client_Data * TCP_Client_Stop(struct TCP_Client_Data * data)
{
    data->active = 0;

    if(data->sockfd_out > 0)
    {
        close(data->sockfd_out);
        data->sockfd_out = 0;
    }

    pthread_join(data->tid,NULL);

    return NULL;
}

void TCP_Client_Send(struct TCP_Client_Data * data, char * buffer)
{
    if(data->active && data->connected && data->output_buffer != NULL)
    {
        pthread_mutex_lock(&(data->mutex));
        memcpy(data->output_buffer,buffer,data->buffer_size);
        pthread_cond_signal(&(data->cond));
        pthread_mutex_unlock(&(data->mutex));
    }
}