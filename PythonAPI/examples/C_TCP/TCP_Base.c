#include "defines.h"
#include "TCPServer.h"
#include "TCPClient.h"

#define IMAGE_WIDTH 1280
#define IMAGE_HEIGHT 720
#define COLOR_SIZE 4

#define BUFFER_SIZE IMAGE_WIDTH*IMAGE_HEIGHT*COLOR_SIZE

int main(int argc, char **argv)
{
    /*  Init   */
    struct TCP_Server_Data * server = TCP_Server_Start(5581,BUFFER_SIZE);
    struct TCP_Client_Data * client = TCP_Client_Start("192.168.56.1",5581,BUFFER_SIZE);
    
    char * buffer = malloc(BUFFER_SIZE);
    memset(buffer,0,BUFFER_SIZE);

    while(1)
    {
        /*  Frame Start  */
        buffer = TCP_Server_Read(server,buffer);
        // Gets you the current frame
        // may run multiple times on the same frame
        // or even skip some frames

        /*  Do stuff with image  */


        /*  Send the image  */
        TCP_Client_Send(client,buffer);
        // Only does a memcpy,
        // after that it runs on another thread

    }
    
    /*  End of execution  */
    server = TCP_Server_Stop(server);
    client = TCP_Client_Stop(client);

    return 0;
}