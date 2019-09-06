#include "CarlaUE4.h"
#include "TCPImageListener.h"
#include "UDPListener.h"

class FTCPListenerWorker : FRunnable
{
public:
	FTCPListenerWorker(UTCPImageListener* p, int sock, uint8* buffer, int32 bufferSize, unsigned short port)
		:m_parent(p), m_sock(sock), m_port(port), m_buffer(buffer), m_size(bufferSize), StopTaskCounter(0)
	{
	}

	~FTCPListenerWorker()
	{
	}

	void Start()
	{
		FString name = "FTCPListenerWorker_" + FString::FromInt(m_port);
		Thread = FRunnableThread::Create(this, *name, 0, EThreadPriority::TPri_AboveNormal);
		m_sbuffer = new uint8[m_size];
	}

	// Hérité via FRunnable
	virtual uint32 Run() override
	{
		listen(m_sock, 100);
		int n = 0;
		int32 received_bytes = 0;
		
		int client_sock, c, read_size;
		struct sockaddr_in client;
		c = sizeof(struct sockaddr_in);
		while ((StopTaskCounter.GetValue() == 0) && (m_buffer != nullptr) && (m_parent != nullptr) && ((client_sock = accept(m_sock, (struct sockaddr*) & client, (int*)& c)) > 0))
		{
			received_bytes = 0;
			if (client_sock < 0)
			{
				UE_LOG(LogTemp, Error, TEXT("accept failed"));
				return 1;
			}
			UE_LOG(LogTemp, Warning, TEXT("Connection accepted : Buffer size = %d"),m_size);

			//Receive a message from client
			while ((StopTaskCounter.GetValue() == 0) && (read_size = recv(client_sock, (char*)m_sbuffer+ received_bytes, m_size/4, 0)) > 0)
			{
				if (m_sbuffer == nullptr || m_buffer == nullptr) break;

				received_bytes += read_size;
				//UE_LOG(LogTemp, Log, TEXT("Data received : %d/%d (%d)"),received_bytes,m_size,read_size);
				if (received_bytes >= m_size)
				{
					received_bytes = 0;
					if (m_parent != nullptr && m_buffer != nullptr) {
						if (!m_parent->mutex)
						{
							m_parent->mutex = true;
							m_parent->bytes = m_size;
							memcpy(m_buffer, m_sbuffer, m_size);
							m_parent->messageFlag = true;
							m_parent->mutex = false;
						}
					}
				}
			}

			if (read_size == 0)
			{
				UE_LOG(LogTemp, Error, TEXT("Client disconnected"));
			}
			else if (read_size == -1)
			{
				UE_LOG(LogTemp, Error, TEXT("recv failed"));
			}

			UE_LOG(LogTemp, Warning, TEXT("Connection closed"));
			closesocket(client_sock);
		}

		if (m_sbuffer != nullptr)
		{
			delete m_sbuffer;
			m_sbuffer = nullptr;
		}

		return 0;
	}

	void Stop()
	{
		StopTaskCounter.Increment();
		/*if (Thread != nullptr)
		{
			Thread->Kill(false);
			//delete Thread;
			Thread = nullptr;
		}
		if (m_sbuffer != nullptr)
		{
			delete m_sbuffer;
			m_sbuffer = nullptr;
		}*/
	}

	UTCPImageListener* m_parent;

private:
	int m_sock;
	unsigned short m_port;
	uint8* m_buffer;
	uint8* m_sbuffer;
	int32 m_size;

	FRunnableThread* Thread;
	FThreadSafeCounter StopTaskCounter;
};

UTCPImageListener::UTCPImageListener()
{
}

UTCPImageListener::~UTCPImageListener()
{
	if (m_thread != nullptr)
	{
		m_thread->m_parent = nullptr;
	}
}

void UTCPImageListener::Init(int32 port,int32 bufferSize)
{
	UTCPImageListener::InitWinSock();

	m_port = port;
	UE_LOG(LogTemp, Log, TEXT("InitSocket(port: %d, buffer size: %d)"),port,bufferSize);
	int length;
	struct sockaddr_in server;
	m_sock = socket(AF_INET, SOCK_STREAM, 0);
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
			UE_LOG(LogTemp, Warning, TEXT("Init Successfull, Spawning Thread : (TCP, % d)"),port);
			m_buffer = new uint8[m_bufferSize];
			m_thread = new FTCPListenerWorker(this, m_sock, m_buffer, m_bufferSize, port);
			m_thread->Start();
		}
	}
}

int32 UTCPImageListener::SetImageSize(int32 width, int32 height, EPixelFormat pixelFormat, int32 colorSize)
{
	if (width > 0 && height > 0 && colorSize > 0)
	{
		m_width = width;
		m_height = height;
		m_colorSize = colorSize;

		m_dynamicTexture = UTexture2D::CreateTransient(m_width, m_height, pixelFormat);

		#define UpdateResource UpdateResource
		m_dynamicTexture->UpdateResource();
		OnImageInit(m_dynamicTexture);
		m_bufferSize = m_width * m_height * m_colorSize;
		//UE_LOG(LogTemp, Warning, TEXT("Image buffer size = %d/%d"), m_width * m_height * m_colorSize, m_bufferSize);
		return m_bufferSize;
	}

	return 0;
}

void UTCPImageListener::Stop()
{
	if (m_thread != nullptr)
	{
		//m_thread->Stop();
		//delete m_thread;
	}

	if (m_sock >= 0)
		closesocket(m_sock);

	if (m_buffer != nullptr)
	{
		delete m_buffer;
		m_buffer = nullptr;
	}
	UTCPImageListener::ClearWinSock();
}

void UTCPImageListener::Tick()
{
	if (!mutex) {
		mutex = true;
		if (messageFlag)
			Callback(bytes);
		messageFlag = false;
		mutex = false;
	}
}

void UTCPImageListener::Callback(unsigned short bytesRead)
{
	if (m_dynamicTexture != nullptr)
	{
		if (m_dynamicTexture->Resource)
		{
			struct FUpdateTextureRegionsData
			{
				FTexture2DResource* Texture2DResource;
				FUpdateTextureRegion2D Region;
				uint32 SrcPitch;
				const uint8* SrcData;
			};

			FUpdateTextureRegionsData* RegionData = new FUpdateTextureRegionsData;

			RegionData->Texture2DResource = (FTexture2DResource*)m_dynamicTexture->Resource;
			RegionData->Region.Width = m_width;
			RegionData->Region.Height = m_height;
			RegionData->Region.SrcX = 0;
			RegionData->Region.SrcY = 0;
			RegionData->Region.DestX = 0;
			RegionData->Region.DestY = 0;
			RegionData->SrcPitch = m_width * m_colorSize;
			RegionData->SrcData = m_buffer;

			ENQUEUE_RENDER_COMMAND(UpdateTextureRegionsData)(
				[RegionData](FRHICommandListImmediate& RHICmdList)
				{
					RHIUpdateTexture2D(
						RegionData->Texture2DResource->GetTexture2DRHI(),
						0,
						RegionData->Region,
						RegionData->SrcPitch,
						RegionData->SrcData
					);
					delete RegionData;
				});
		}
	}
}

void UTCPImageListener::InitWinSock()
{
	UUDPListener::InitWinSock();
}

void UTCPImageListener::ClearWinSock()
{
	UUDPListener::ClearWinSock();
}
