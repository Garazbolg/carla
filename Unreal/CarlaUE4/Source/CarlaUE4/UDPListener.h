#pragma once

#include "CoreMinimal.h"
#include "UObject/NoExportTypes.h"

#include <WinSock2.h>

#include "UDPListener.generated.h"

class FUDPListenerWorker;

UENUM(BlueprintType, Category = "UDPTransport")
enum class EMessageType : uint8
{
	String = 0,
	Int = 3
};

UCLASS(Blueprintable)
class CARLAUE4_API UUDPListener : public UObject
{
	GENERATED_BODY()

public:

	~UUDPListener();

	UFUNCTION(BlueprintCallable, Category = "UDPTransport")
	void Init(EMessageType type, int32 port, int32 bufferSize);

	UFUNCTION(BlueprintCallable, Category = "UDPTransport")
	void Stop();

	UFUNCTION(BlueprintCallable, Category = "UDPTransport")
	void Tick();

	UFUNCTION(BlueprintImplementableEvent, Category = "UDPTransport")
	void OnStringMessage(const FString& Data);

	UFUNCTION(BlueprintImplementableEvent, Category = "UDPTransport")
	void OnIntMessage(const int32& Data);

	void Callback(unsigned short bytesRead);

	UPROPERTY()
	EMessageType m_messageType;

	bool mutex = false;
	int bytes = 0;
	bool messageFlag = false;

	static void InitWinSock();
	static void ClearWinSock();
private:
	int m_sock;
	unsigned short m_bufferSize;

	uint8* m_buffer = nullptr;

	FUDPListenerWorker* m_thread = nullptr;

	static int nbOpenSockets;
};