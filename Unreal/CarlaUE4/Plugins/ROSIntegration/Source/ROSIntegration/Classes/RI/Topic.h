#pragma once

#include <functional>
#include <memory>
#include <CoreMinimal.h>
#include <UObject/ObjectMacros.h>
#include <UObject/Object.h>
#include <Runtime/Engine/Classes/Engine/Texture2D.h>
#include "ROSBaseMsg.h"
#include "ROSIntegrationCore.h"

#include "sensor_msgs/Image.h"

#include "Topic.generated.h"

/**
* @ingroup ROS Message Types
* Which Message type to work with.
*/
UENUM(BlueprintType, Category = "ROS")
enum class EMessageType : uint8
{
	String = 0,
	Float32 = 1,
	Image = 2
};

UCLASS(Blueprintable)
class ROSINTEGRATION_API UTopic: public UObject
{
	GENERATED_UCLASS_BODY()

public:

	bool Subscribe(std::function<void(TSharedPtr<FROSBaseMsg>)> func);

	bool Unsubscribe();

	bool Advertise();

	bool Unadvertise();

	bool Publish(TSharedPtr<FROSBaseMsg> msg);

	void BeginDestroy() override;

	void Init(UROSIntegrationCore *Ric, FString Topic, FString MessageType, int32 QueueSize = 10);

	virtual void PostInitProperties() override;

	void MarkAsDisconnected();
	bool Reconnect(UROSIntegrationCore* ROSIntegrationCore);

protected:

	virtual FString GetDetailedInfoInternal() const override;

	UTexture2D* InitDynamicTexture(uint32 Width, uint32 Height);

	void UpdateTextureRegions(UTexture2D* Texture, uint32 width, uint32 height, uint32 colorSize, const uint8* SrcData);

	UFUNCTION(BlueprintImplementableEvent, Category = ROS)
	void OnConstruct();

	UFUNCTION(BlueprintImplementableEvent, Category = ROS)
	void OnStringMessage(const FString& Data);

	UFUNCTION(BlueprintImplementableEvent, Category = ROS)
	void OnFloat32Message(const float& Data);

	UFUNCTION(BlueprintImplementableEvent, Category = ROS)
	void OnImageInit(const UTexture2D* Image);

	UPROPERTY()
	UROSIntegrationCore* _ROSIntegrationCore;

private:

	struct State
	{
		bool Connected;
		bool Advertised;
		bool Subscribed;
		bool Blueprint;
		EMessageType BlueprintMessageType;
	} _State;


	UFUNCTION(BlueprintCallable, Category = "ROS|Topic")
	void Init(const FString& TopicName, EMessageType MessageType, int32 QueueSize = 1);

	/**
	 * Subscribe to the given topic
	 */
	UFUNCTION(BlueprintCallable, Category = "ROS|Topic")
	bool Subscribe();

	UFUNCTION(BlueprintCallable, Category = "ROS|Topic")
	bool PublishStringMessage(const FString& Message);

	UFUNCTION(BlueprintCallable, Category = "ROS|Topic")
	void SetImageSize(int32 width, int32 height);

	// Helper to keep track of self-destruction for async functions
	TSharedPtr<UTopic, ESPMode::ThreadSafe> _SelfPtr;

	// PIMPL
	class Impl;
	Impl *_Implementation;

	UPROPERTY()
	UTexture2D *m_pDynamicTexture = nullptr;
	uint8 *m_pDataBuffer = nullptr;
	uint32 m_pImageWidth = 640;
	uint32 m_pImageHeight = 400;
	TSharedPtr<ROSMessages::sensor_msgs::Image,ESPMode::NotThreadSafe> ConcreteImageMessage;
};
