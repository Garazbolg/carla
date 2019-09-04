// Copyright (c) 2017 Computer Vision Center (CVC) at the Universitat Autonoma de Barcelona (UAB). This work is licensed under the terms of the MIT license. For a copy, see <https://opensource.org/licenses/MIT>.

#include "CarlaUE4.h"
#include "UDPListener.h"
#include <functional>

#include <WinSock2.h>


class FUDPListenerWorker : FRunnable
{
public:
	FUDPListenerWorker(UUDPListener* p, int sock, uint8* buffer, unsigned short bufferSize, unsigned short port)
		:m_parent(p), m_sock(sock), m_port(port), m_buffer(buffer), m_size(bufferSize), StopTaskCounter(0)
	{
	}

	~FUDPListenerWorker()
	{
		if (Thread != nullptr)
		{
			Thread->WaitForCompletion();
			delete Thread;
			Thread = nullptr;
		}
		delete m_sbuffer;
	}

	void Start()
	{
		FString name = "FUDPListenerWorker_" + FString::FromInt(m_port);
		Thread = FRunnableThread::Create(this, *name, 0, EThreadPriority::TPri_AboveNormal);
		m_sbuffer = new uint8[m_size];
	}

	// Hérité via FRunnable
	virtual uint32 Run() override
	{
		//Initial wait before starting
		FPlatformProcess::Sleep(0.03);

		int n = 0;
		while (StopTaskCounter.GetValue() == 0 && m_buffer != nullptr && m_parent != nullptr)
		{
			n = recvfrom(m_sock, (char*)m_sbuffer, m_size, 0, nullptr, nullptr);
			if (n < 0)
			{
				UE_LOG(LogTemp, Error, TEXT("recvfrom"));
			}
			else
			{
				if (m_parent != nullptr && m_buffer != nullptr) {
					if (!m_parent->mutex)
					{
						m_parent->mutex = true;
						m_parent->bytes = n;
						memcpy(m_buffer, m_sbuffer, n);
						m_parent->messageFlag = true;
						m_parent->mutex = false;
					}
				}
			}

		}

		return 0;
	}

	void Stop()
	{
		StopTaskCounter.Increment();
	}

	UUDPListener* m_parent;

private:
	int m_sock;
	unsigned short m_port;
	uint8* m_buffer;
	uint8* m_sbuffer;
	unsigned short m_size;

	FRunnableThread* Thread;
	FThreadSafeCounter StopTaskCounter;
};

void UUDPListener::Init(EMessageType type, int32 port, int32 bufferSize)
{
	UUDPListener::InitWinSock();
	m_messageType = type;

	int length;
	struct sockaddr_in server;
	m_sock = socket(AF_INET, SOCK_DGRAM, 0);
	if (m_sock < 0)
	{
		UE_LOG(LogTemp, Error, TEXT("Opening socket failed"));
	}
	else
	{
		length = sizeof(server);
		memset(&server, 0, length);
		server.sin_family = AF_INET;
		server.sin_addr.s_addr = INADDR_ANY;
		server.sin_port = htons(port);
		if (bind(m_sock, (struct sockaddr*) & server, length) < 0)
		{
			UE_LOG(LogTemp, Error, TEXT("Binding socket %d failed"), port);
		}
		else
		{
			UE_LOG(LogTemp, Warning, TEXT("Init Successfull, Spawning Thread : (UDP,%d)"),port);
			m_buffer = new uint8[bufferSize];
			m_thread = new FUDPListenerWorker(this, m_sock, m_buffer, bufferSize, port);
			m_thread->Start();
		}
	}
}

void UUDPListener::Stop()
{
	if (m_thread != nullptr)
	{
		m_thread->Stop();
		delete m_thread;
	}
	if (m_sock >= 0)
		closesocket(m_sock);
	
	if (m_buffer != nullptr)
	{
		delete m_buffer;
		m_buffer = nullptr;
	}
	UUDPListener::ClearWinSock();
}

void UUDPListener::Tick()
{
	if (!mutex) {
		mutex = true;
		if(messageFlag)
			Callback(bytes);
		messageFlag = false;
		mutex = false;
	}
}
UUDPListener::~UUDPListener()
{
	if (m_thread != nullptr)
	{
		m_thread->m_parent = nullptr;
	}
}

void UUDPListener::Callback(unsigned short bytesRead)
{
	switch (m_messageType) {
	case EMessageType::String:
		if (bytesRead > 0)
		{
			FString outF = ANSI_TO_TCHAR((char*)m_buffer);
			OnStringMessage(outF);
		}
		break;
	case EMessageType::Int:
		if (bytesRead >= sizeof(int32))
		{
			int32 out;
			FMemory::Memcpy((uint8*)& out, m_buffer, sizeof(int32));
			OnIntMessage(out);
		}
		break;
	}
}

int UUDPListener::nbOpenSockets = 0;

void UUDPListener::InitWinSock()
{
	if (UUDPListener::nbOpenSockets++ == 0)
	{
		WSADATA data;
		WSAStartup(MAKEWORD(2, 2), &data);
	}
}

void UUDPListener::ClearWinSock()
{
	/*if (UUDPListener::nbOpenSockets-- == 1)
	{
		WSACleanup();
	}*/
}
