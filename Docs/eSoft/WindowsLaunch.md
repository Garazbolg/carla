# How to start the simulation

## .bat scripts
There are 4 scripts in carla/Run used to launch the simulation. You just need to execute them in order and wait for each of them to be ready before starting the next one.

Here are the different steps explained in more details.

## Starting the Linux Virtual Machine
For now because the board can't launch from its own SSD we need to flash the file system from a linux host. Since we are now running on Windows the file system is on a Linux VM.
To start it : 

		cd C:\Program Files\Oracle\VirtualBox
		VBoxManage startvm Lubuntu_18.04_esoft

## Launching the simulator (server)

### From Unreal
- Open the unreal project in

		C:\Users\Megaport\eSoftThings\carla\Unreal\CarlaUE4\CarlaUE4.uproject
		
- Launch (play button) in either Viewport or Standalone (Check that Edit/Editor Preferences/Level Editor/Play/Game Viewport Settings have a window size of 5760x1080)
- Wait for the game to render something
- You can now launch the client

### From Latest Build
	cd C:\Users\Megaport\eSoftThings\carla\Dist\Latest\WindowsNoEditor
	CarlaUE4 ResX=5760 ResY=1080 NoVSync USEALLAVAILABLECORES NOSOUND
### From your Build
	cd <Path to your build directory>\WindowsNoEditor
	CarlaUE4 ResX=5760 ResY=1080 NoVSync USEALLAVAILABLECORES NOSOUND

	
## Spawning the cars and walkers
	cd C:\Users\Megaport\eSoftThings\carla\PythonAPI\examples
	python spawn_npc.py -n 20 -w 100

## Launching the simulator (client)
### Without fullscreen
	cd C:\Users\Megaport\eSoftThings\carla\PythonAPI\examples
	python -O manual_control.py --mirror_size=1280x800 --wheel