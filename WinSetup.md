# How to install
## Necessary software
- [Git](https://gitforwindows.org/)
- [Make](http://ftp.gnu.org/gnu/make/make-4.2.tar.gz)
- [CMake](https://github.com/Kitware/CMake/releases/download/v3.15.3/cmake-3.15.3-win64-x64.msi)
- [Python3 x64](https://www.python.org/ftp/python/3.7.4/python-3.7.4-amd64.exe)
- [Visual Studio Community 2019](https://visualstudio.microsoft.com/thank-you-downloading-visual-studio/?sku=Community&rel=16)
- [Unreal Engine 4.22+](https://www.unrealengine.com/en-US/)
- [Virtual Box](https://www.virtualbox.org/wiki/Downloads)

#### Python Libraries :
		python -m pip install --user [libname]
- setuptools
- pygame
- numpy
- pyaudio (you will need to install from a [wheel](https://www.lfd.uci.edu/~gohlke/pythonlibs/#pyaudio) )

Follow [Carla tutorial for building on Windows](https://carla.readthedocs.io/en/latest/how_to_build_on_windows/) :
- Instead of cloning from carla/simulator repo clone from 
	
		git clone --single-branch --branch eSoft-sim https://github.com/Garazbolg/carla.git

- After downloading **CARLA Contents** checkout the **eSoft-Sim branch** again. There are some files in this branch that modify CARLA Contents and they may be replaced when downloading the content
- To make sure that CMake uses the right compiler :
  
		ProgramFiles/Microsoft Visual Studio/2019/Community/VC/Tools/MSVC/{Build version}/Hostx64/x64/cl.exe

	I moved all the other compilers to another folder. If you have a better way to achieve this go ahead.
- I my case the scripts couldn't find ***vcvarsall.bat*** so I copied it inside the **Hostx64** Folder from :

		C:\Program Files (x86)\Microsoft Visual Studio\2019\Community\VC\Auxiliary\Build\vcvarsall.bat
- You might need to look for hard coded paths to change in some .bat files (notably the ones in carla/Run)
  
### Install the virtual machine
	***Missing***
	
### Install the wheel drivers
	[ Dowload Drivers](https://support.thrustmaster.com/fr/product/txracingwheel-fr/) and follow the procedure to install the drivers and update the firmware
	

# How to start the simulation

## .bat scripts
There are 4 scripts in carla/Run used to launch the simulation. You just need to execute them in order and wait for each of them to be ready before starting the next one.
To start it : 

		cd C:\Program Files\Oracle\VirtualBox
		VBoxManage startvm Lubuntu_18.04_esoft
Here are the different steps explained in more details.

## Starting the Linux Virtual Machine
For now because the board can't launch from its own SSD we need to flash the file system from a linux host. Since we are now running on Windows the file system is on a Linux VM

## Launching the simulator (server)
### From Unreal
- Open the unreal project in

		C:\Users\Megaport\eSoftThings\carla\Unreal\CarlaUE4\CarlaUE4.uproject
- Launch (play button) in either Viewport or Standalone
- Wait for the game to render something
- You can now launch the client

### From Latest Build
	cd C:\Users\Megaport\eSoftThings\carla\Dist\Latest\WindowsNoEditor
	CarlaUE4 ResX=10 ResY=10 NoVSync USEALLAVAILABLECORES NOSOUND
### From your Build
	cd <Path to your build directory>\WindowsNoEditor
	CarlaUE4 ResX=3840 ResY=720 NoVSync USEALLAVAILABLECORES NOSOUND

	
## Spawning the cars and walkers
	cd C:\Users\Megaport\eSoftThings\carla\PythonAPI\examples
	python spawn_npc.py -n 20 -w 100

## Launching the simulator (client)
### Without fullscreen
	cd C:\Users\Megaport\eSoftThings\carla\PythonAPI\examples
	python -O manual_control.py --mirror_size=1280x800 --wheel