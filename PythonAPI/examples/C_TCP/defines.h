#ifndef TCP_DEFINES
#define TCP_DEFINES

#include <stdio.h>
#include <stdlib.h>
#include <string.h> // memset, memcpy
#include <sys/types.h>
#include <signal.h>

#ifdef _Win32
#include <winsock2.h>
#pragma comment(lib, "Ws2_32.lib")
#elif __unix__
#include <sys/socket.h>
#include <netinet/in.h>
#include <arpa/inet.h> //sockaddr_in
#include <unistd.h> //close
#include <pthread.h>
#include <unistd.h>
#endif
/*
void error(char* s)
{
    printf("Error : %s\n",s);
    exit(1);
}*/

#endif