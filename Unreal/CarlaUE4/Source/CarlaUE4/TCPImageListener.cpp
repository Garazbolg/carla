// Copyright (c) 2017 Computer Vision Center (CVC) at the Universitat Autonoma de Barcelona (UAB). This work is licensed under the terms of the MIT license. For a copy, see <https://opensource.org/licenses/MIT>.

#include "CarlaUE4.h"
#include "TCPImageListener.h"
#include "UDPListener.h"
/*
class ImageReconstructor {
public :
	struct Header {
		int32 data_size;
		unsigned long frame_id;
		unsigned long long chunk_pos;
	};

	struct Image {
		unsigned long frame_id;
		int32 currentlyReceived;
		uint8* data;
	};


	ImageReconstructor(unsigned short backlogSize,int32 bufferSize) {
		UE_LOG(LogTemp, Error, TEXT("Create IR backlog size = %d ; buffer size = %d"),backlogSize,bufferSize);
		backlog_size = backlogSize;
		buffer_size = bufferSize;
		logs = new Image[backlog_size];
		for (int i = 0; i < backlog_size; i++)
		{
			logs[i].data = new uint8[buffer_size];
			clear_id(i);
		}
	}

	~ImageReconstructor() {
		for (int i = 0; i < backlog_size; i++) {
			delete logs[i].data;
		}
		delete logs;
	}

	void clear_id(int i) {
		logs[i].frame_id = 0;
		logs[i].currentlyReceived = 0;
	}

	bool Add(uint8* buffer, int read_bytes)
	{
		countdown2Reset -= 1;
		if (countdown2Reset < 0) {
			countdown2Reset = 30;
			last_frame_id = 0;
		}
		Header* head = (Header*)buffer;
		uint8* data = buffer + sizeof(Header);
		UE_LOG(LogTemp, Log, TEXT("IR::Add : ( size: %d , frame id: %d/%d , position: %d )"),head->data_size,head->frame_id,last_frame_id, head->chunk_pos);
		if (head->frame_id < last_frame_id) return false;// Current frame is older then the last frame displayed (Freeze > roll back)
		unsigned long lowest_id = head->frame_id;
		short index = -1;
		bool set = false;
		for (int i = 0; i < backlog_size; i++)
		{
			// Already tracking frame
			if (logs[i].frame_id == head->frame_id) {
				index = i;
				set = true;
				break;
			}// there is an older frame
			if (logs[i].frame_id <= lowest_id) {
				lowest_id = logs[i].frame_id;
				index = i;
			}
		}

		if (index == -1) return false; // Frame is older then any other in the backlog, don't track

		UE_LOG(LogTemp, Log, TEXT("Frame Registering"));
		// We need to replace the old frame by the new one
		if(!set) {
			UE_LOG(LogTemp, Log, TEXT("Frame Setting"));
			clear_id(index);
			logs[index].frame_id = head->frame_id;
		}

		memcpy(logs[index].data + head->chunk_pos, data, head->data_size);
		logs[index].currentlyReceived += head->data_size;
		float completion = float(logs[index].currentlyReceived) * 100;
		completion = completion / buffer_size;
		UE_LOG(LogTemp, Log, TEXT("Frame Registered (%d) : %f/100 (%d)"),logs[index].frame_id,completion,logs[index].currentlyReceived);
		if (logs[index].currentlyReceived >= (buffer_size))
		{
			lastImageBuffer = logs[index].data;
			last_frame_id = logs[index].frame_id;
			UE_LOG(LogTemp, Log, TEXT("Frame Fully received"));
			return true;
		}
		return false;
	}

	Image* logs;
	unsigned short backlog_size;
	unsigned long last_frame_id = -1;
	int countdown2Reset = 0;
	int32 buffer_size;
	uint8* lastImageBuffer = nullptr;
};*/

class FTCPListenerWorker : FRunnable
{
public:
	FTCPListenerWorker(UTCPImageListener* p, int sock, uint8* buffer, int32 bufferSize, unsigned short port)
		:m_parent(p), m_sock(sock), m_port(port), m_buffer(buffer), m_size(bufferSize), StopTaskCounter(0)
	{
		//ir = new ImageReconstructor(3, bufferSize);
	}

	~FTCPListenerWorker()
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
		FString name = "FTCPListenerWorker_" + FString::FromInt(m_port);
		Thread = FRunnableThread::Create(this, *name, 0, EThreadPriority::TPri_AboveNormal);
		m_sbuffer = new uint8[m_size];
	}

	// Hérité via FRunnable
	virtual uint32 Run() override
	{
		/*
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
				if (ir->Add(m_sbuffer, n))
				{
					if (m_parent != nullptr && m_buffer != nullptr) {
						if (!m_parent->mutex)
						{
							m_parent->mutex = true;
							m_parent->bytes = ir->buffer_size;
							memcpy(m_buffer, ir->lastImageBuffer, ir->buffer_size);
							m_parent->messageFlag = true;
							m_parent->mutex = false;
						}
					}
				}
			}

		}

		return 0;*/
		
		//Initial wait before starting
		FPlatformProcess::Sleep(0.03);


		listen(m_sock, 100);
		UE_LOG(LogTemp, Warning, TEXT("Connection Listen"));
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
			while ((read_size = recv(client_sock, (char*)m_sbuffer+ received_bytes, m_size/4, 0)) > 0)
			{
				received_bytes += read_size;
				UE_LOG(LogTemp, Log, TEXT("Data received : %d/%d (%d)"),received_bytes,m_size,read_size);
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

		return 0;
	}

	void Stop()
	{
		StopTaskCounter.Increment();
	}

	UTCPImageListener* m_parent;

private:
	int m_sock;
	unsigned short m_port;
	uint8* m_buffer;
	uint8* m_sbuffer;
	int32 m_size;
	//ImageReconstructor* ir;

	FRunnableThread* Thread;
	FThreadSafeCounter StopTaskCounter;
};

UTCPImageListener::UTCPImageListener()
{
}

UTCPImageListener::~UTCPImageListener()
{
}

void UTCPImageListener::Init(int32 port,int32 bufferSize)
{
	UTCPImageListener::InitWinSock();

	m_port = port;
	//m_bufferSize = bufferSize;
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
			UE_LOG(LogTemp, Warning, TEXT("Init Successfull, Spawning Thread"));
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
		UE_LOG(LogTemp, Warning, TEXT("Image buffer size = %d/%d"), m_width * m_height * m_colorSize, m_bufferSize);
		return m_bufferSize;
	}

	return 0;
}

void UTCPImageListener::Stop()
{
	//if (m_thread != nullptr)
	//{
	//	m_thread->Stop();
		//delete m_thread;
	//}

	//if (m_sock >= 0)
		//closesocket(m_sock);
	/*
	if (m_dynamicTexture != nullptr)
		delete m_dynamicTexture;

	if (m_buffer != nullptr)
	{
		delete m_buffer;
		m_buffer = nullptr;
	}*/
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
	UE_LOG(LogTemp, Warning, TEXT("Callback !"));
	if (m_dynamicTexture != nullptr)
	{
		UE_LOG(LogTemp, Warning, TEXT("Callback !!"));
		if (/*bytesRead >= m_width * m_height * m_colorSize &&*/ m_dynamicTexture->Resource)
		{
			UE_LOG(LogTemp, Warning, TEXT("Callback !!!"));
			//TWeakPtr<UUDPListener, ESPMode::ThreadSafe> SelfPtr(_SelfPtr);

			//AsyncTask(ENamedThreads::GameThread, [this, SelfPtr]()
				//{
					//if (!SelfPtr.IsValid()) return;
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
			//});
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
