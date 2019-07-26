// Copyright (c) 2017 Computer Vision Center (CVC) at the Universitat Autonoma de Barcelona (UAB). This work is licensed under the terms of the MIT license. For a copy, see <https://opensource.org/licenses/MIT>.

#include "CarlaUE4.h"
#include "ROSTextSubscriberTest.h"
#include "ROSIntegration/Classes/RI/Topic.h"
#include "ROSIntegration/Classes/ROSIntegrationGameInstance.h"
#include "ROSIntegration/Public/std_msgs/String.h"


// Sets default values
AROSTextSubscriberTest::AROSTextSubscriberTest()
{
 	// Set this actor to call Tick() every frame.  You can turn this off to improve performance if you don't need it.
	PrimaryActorTick.bCanEverTick = true;

}

// Called when the game starts or when spawned
void AROSTextSubscriberTest::BeginPlay()
{
	Super::BeginPlay();

	// Initialize a topic
	ExampleTopic = NewObject<UTopic>(UTopic::StaticClass());
	UROSIntegrationGameInstance* rosinst = Cast<UROSIntegrationGameInstance>(GetGameInstance());
	ExampleTopic->Init(rosinst->ROSIntegrationCore, TEXT("/example_topic"), TEXT("std_msgs/String"));

	// Create a std::function callback object
	std::function<void(TSharedPtr<FROSBaseMsg>)> SubscribeCallback = [](TSharedPtr<FROSBaseMsg> msg) -> void
	{
		UE_LOG(LogTemp,Log,TEXT("ROS String Message Received !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!"));
		auto Concrete = StaticCastSharedPtr<ROSMessages::std_msgs::String>(msg);
		if (Concrete.IsValid())
		{
			UE_LOG(LogTemp, Log, TEXT("Incoming string was: %s"), (*(Concrete->_Data)));
		}
		return;
	};

	// Subscribe to the topic
	ExampleTopic->Subscribe(SubscribeCallback);
	
	UE_LOG(LogTemp,Log,TEXT("Subscribing !!!!!!!!!!!!!!!!!!!!!!"))
}

// Called every frame
void AROSTextSubscriberTest::Tick(float DeltaTime)
{
	Super::Tick(DeltaTime);

}

