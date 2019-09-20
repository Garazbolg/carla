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
	