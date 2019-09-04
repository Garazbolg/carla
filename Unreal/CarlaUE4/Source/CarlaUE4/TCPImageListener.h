// Copyright (c) 2017 Computer Vision Center (CVC) at the Universitat Autonoma de Barcelona (UAB). This work is licensed under the terms of the MIT license. For a copy, see <https://opensource.org/licenses/MIT>.

#pragma once

#include "CoreMinimal.h"
#include "UObject/NoExportTypes.h"

#include <WinSock2.h>


#include "TCPImageListener.generated.h"


class FTCPListenerWorker;


/**
 * 
 */
UCLASS(Blueprintable)
class CARLAUE4_API UTCPImageListener : public UObject
{
	GENERATED_BODY()

public:
	UTCPImageListener();
	~UTCPImageListener();

	UFUNCTION(BlueprintCallable, Category = "TCPTransport")
		void Init(int32 port, int32 bufferSize);

	UFUNCTION(BlueprintCallable, Category = "TCPTransport")
		int32 SetImageSize(int32 width, int32 height, EPixelFormat pixelFormat, int32 colorSize);

	UFUNCTION(BlueprintCallable, Category = "TCPTransport")
		void Stop();

	UFUNCTION(BlueprintCallable, Category = "TCPTransport")
		void Tick();

	UFUNCTION(BlueprintImplementableEvent, Category = "TCPTransport")
		void OnImageInit(const UTexture2D* Image);

	void Callback(unsigned short bytesRead);

	UPROPERTY()
		UTexture2D* m_dynamicTexture = nullptr;

	bool mutex = false;
	int bytes = 0;
	bool messageFlag = false;

	static void InitWinSock();
	static void ClearWinSock();

private:

	int m_sock;
	int32 m_bufferSize;
	unsigned short m_port;

	uint8* m_buffer = nullptr;
	uint8* m_buffer2 = nullptr;

	FTCPListenerWorker* m_thread = nullptr;

	uint32 m_width;
	uint32 m_height;
	uint32 m_colorSize;

};
