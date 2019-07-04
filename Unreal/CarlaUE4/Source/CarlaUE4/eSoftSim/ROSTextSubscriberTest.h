// Copyright (c) 2017 Computer Vision Center (CVC) at the Universitat Autonoma de Barcelona (UAB). This work is licensed under the terms of the MIT license. For a copy, see <https://opensource.org/licenses/MIT>.

#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "ROSIntegration/Classes/RI/Topic.h"
#include "ROSTextSubscriberTest.generated.h"

UCLASS()
class CARLAUE4_API AROSTextSubscriberTest : public AActor
{
	GENERATED_BODY()
	
public:	
	// Sets default values for this actor's properties
	AROSTextSubscriberTest();

protected:
	// Called when the game starts or when spawned
	virtual void BeginPlay() override;

	UFUNCTION(BlueprintImplementableEvent, Category = ROS)
	void OnMessageReceived(const FString& Data);

	UTopic *ExampleTopic;

public:	
	// Called every frame
	virtual void Tick(float DeltaTime) override;

	
	
};
