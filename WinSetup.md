# How to install
##Necessary software
- Git
- Make
- CMake
- Python3 x64
- Visual Studio Community 2019
- Unreal Engine 4.22+

Follow [Carla tutorial for building on Windows](https://carla.readthedocs.io/en/latest/how_to_build_on_windows/) :
- Instead of cloning from carla/simulator repo clone from 
	git clone --single-branch --branch eSoft-sim https://github.com/Garazbolg/carla.git
- After downloading **CARLA Contents** checkout the **eSoft-Sim branch** again. There are some files in this branch that modify CARLA Contents and they may be replaced when downloading the content
- To make sure that CMake uses the right compiler (VSC2019 vc.exe Hostx64/x64) I moved all the other compilers to another folder. If you have a better way to achieve this go ahead.
- You might need to look for hard coded paths to change in some .bat files (specially the ones in carla/Run)

# How to start the simulation

## Launching the simulator (server)
### From Unreal
- Open the unreal project in
"C:\Users\Megaport\eSoftThings\carla\Unreal\CarlaUE4\CarlaUE4.uproject"
- Launch (play button) in either Viewport or Standalone
- Wait for the small window to display something (Alt+Tab to get back control of the mouse)

### From Latest Build
	cd C:\Users\Megaport\eSoftThings\carla\Dist\Latest\WindowsNoEditor
	CarlaUE4 ResX=10 ResY=10 NoVSync USEALLAVAILABLECORES NOSOUND
### From your Build
	cd <Path to your build directory>\WindowsNoEditor
	CarlaUE4 ResX=10 ResY=10 NoVSync USEALLAVAILABLECORES NOSOUND

	
## Spawning the cars and walkers
	cd C:\Users\Megaport\eSoftThings\carla\PythonAPI\examples
	python spawn_npc.py -n 100

## Launching the simulator (client)
### Without fullscreen
cd C:\Users\Megaport\eSoftThings\carla\PythonAPI\examples
	python -O manual_control.py --mirror_size=640x360 --wheel
### With fullscreen
	cd C:\Users\Megaport\eSoftThings\carla\PythonAPI\examples
	python -O manual_control.py --res=3840x720 --fullscreen --mirror_size=1280x720 --wheel