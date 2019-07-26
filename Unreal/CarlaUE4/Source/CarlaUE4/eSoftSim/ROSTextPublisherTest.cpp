// Copyright (c) 2017 Computer Vision Center (CVC) at the Universitat Autonoma de Barcelona (UAB). This work is licensed under the terms of the MIT license. For a copy, see <https://opensource.org/licenses/MIT>.

#include "CarlaUE4.h"
#include "ROSTextPublisherTest.h"

#include "ROSIntegration/Classes/RI/Topic.h"
#include "ROSIntegration/Classes/ROSIntegrationGameInstance.h"
#include "ROSIntegration/Public/std_msgs/String.h"

// Sets default values
AROSTextPublisherTest::AROSTextPublisherTest()
{
 	// Set this actor to call Tick() every frame.  You can turn this off to improve performance if you don't need it.
	PrimaryActorTick.bCanEverTick = true;

}

// Called when the game starts or when spawned
void AROSTextPublisherTest::BeginPlay()
{
	Super::BeginPlay();

	UE_LOG(LogTemp,Log,TEXT("Publishing !!!!!!!!!!!!!!!!!!!!!!"))

	// Initialize a topic
	UTopic *ExampleTopic = NewObject<UTopic>(UTopic::StaticClass());
	UROSIntegrationGameInstance* rosinst = Cast<UROSIntegrationGameInstance>(GetGameInstance());
	ExampleTopic->Init(rosinst->ROSIntegrationCore, TEXT("/example_topic"), TEXT("std_msgs/String"));

	// (Optional) Advertise the topic
	ExampleTopic->Advertise();

	// Publish a string to the topic
	TSharedPtr<ROSMessages::std_msgs::String> StringMessage(new ROSMessages::std_msgs::String("This is an example"));
	ExampleTopic->Publish(StringMessage);
}

// Called every frame
void AROSTextPublisherTest::Tick(float DeltaTime)
{
	Super::Tick(DeltaTime);

}

