// Copyright (c) 2017 Computer Vision Center (CVC) at the Universitat Autonoma de Barcelona (UAB). This work is licensed under the terms of the MIT license. For a copy, see <https://opensource.org/licenses/MIT>.

#pragma once

#include "CoreMinimal.h"
#include "UObject/NoExportTypes.h"

#include <WinSock2.h>
//#include <Runtime/Engine/Classes/Engine/Texture2D.h>

#include "UDPListener.generated.h"

class FUDPListenerWorker;

UENUM(BlueprintType, Category = "UDPTransport")
enum class EMessageType : uint8
{
	String = 0,
	//Bool = 1,
	Image = 2,
	Int = 3
};

UCLASS(Blueprintable)
class CARLAUE4_API UUDPListener : public UObject
{
	GENERATED_BODY()

public:

	UUDPListener();
	UUDPListener(EMessageType type, unsigned short port, unsigned short bufferSize);
	~UUDPListener();

	UFUNCTION(BlueprintCallable, Category = "UDPTransport")
	void Init(EMessageType type, int32 port, int32 bufferSize);

	UFUNCTION(BlueprintCallable, Category = "UDPTransport")
	void SetImageSize(int32 width, int32 height, EPixelFormat pixelFormat, int32 colorSize);

	UFUNCTION(BlueprintCallable, Category = "UDPTransport")
	void Stop();

	UFUNCTION(BlueprintCallable, Category = "UDPTransport")
	void Tick();

	UFUNCTION(BlueprintImplementableEvent, Category = "UDPTransport")
	void OnStringMessage(const FString& Data);

	/*UFUNCTION(BlueprintImplementableEvent, Category = "UDPTransport")
	void OnBoolMessage(const bool& Data);*/

	UFUNCTION(BlueprintImplementableEvent, Category = "UDPTransport")
	void OnIntMessage(const int32& Data);

	UFUNCTION(BlueprintImplementableEvent, Category = "UDPTransport")
	void OnImageInit(const UTexture2D* Image);

	void Callback(unsigned short bytesRead);

	UPROPERTY()
	EMessageType m_messageType;


	UPROPERTY()
	UTexture2D* m_dynamicTexture = nullptr;

	bool mutex = false;
	int bytes = 0;
	bool messageFlag = false;
private:
	int m_sock;
	unsigned short m_bufferSize;
	unsigned short m_port;

	uint8* m_buffer = nullptr;

	FUDPListenerWorker* m_thread = nullptr;

	uint32 m_width;
	uint32 m_height;
	uint32 m_colorSize;

	static int nbOpenSockets;
	static void InitWinSock();
	static void ClearWinSock();

};