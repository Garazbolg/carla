# How to Install
    #First install VisualStudioCode by downloading the package from 
    #https://code.visualstudio.com/download#
    #and install it

# Create the directory
    mkdir eSoftThings_simulation
    cd eSoftThings_simulation

# Tools
    sudo add-apt-repository ppa:ubuntu-toolchain-r/test
    wget -O - https://apt.llvm.org/llvm-snapshot.gpg.key|sudo apt-key add -
    sudo apt-add-repository "deb http://apt.llvm.org/xenial/ llvm-toolchain-xenial-7 main"
    sudo apt-get update
    sudo apt-get install build-essential clang-7 lld-7 g++-7 cmake ninja-build python python-pip python-dev python3-dev python3-pip libpng16-16 libtiff5-dev libjpeg-dev tzdata sed curl wget unzip autoconf libtool
    pip2 install setuptools
    pip3 install setuptools
    sudo update-alternatives --install /usr/bin/clang++ clang++ /usr/lib/llvm-7/bin/clang++ 170
    sudo update-alternatives --install /usr/bin/clang clang /usr/lib/llvm-7/bin/clang 170
    python -m pip install -U pygame --user
    pip install --user numpy
    sudo apt-get install joystick jstest-gtk
    sudo apt-get install ros-melodic-catkin
    sudo apt-get install portaudio19-dev python-all-dev
    pip install pyaudio
    sudo apt-get update

# Unreal

    mkdir UnrealEngine
    git clone https://github.com/EpicGames/UnrealEngine.git UnrealEngine
        #Vulkan
        wget -qO - http://packages.lunarg.com/lunarg-signing-key-pub.asc | sudo apt-key add -
        sudo wget -qO /etc/apt/sources.list.d/lunarg-vulkan-1.1.108-bionic.list http://packages.lunarg.com/vulkan/1.1.108/lunarg-vulkan-1.1.108-bionic.list
        sudo apt update
        sudo apt install vulkan-sdk
    cd UnrealEngine
    export UE4_ROOT= $PWD
    ./Setup.sh && ./GenerateProjectFiles.sh && make
    alias ue="$PWD/Engine/Binaries/Linux/UE4Editor"
    cd ..

# ros
    sudo sh -c 'echo "deb http://packages.ros.org/ros/ubuntu $(lsb_release -sc) main" > /etc/apt/sources.list.d/ros-latest.list'
    sudo apt-key adv --keyserver 'hkp://keyserver.ubuntu.com:80' --recv-key C1CF6E31E6BADE8868B172B4F42ED6FBAB17C654
    sudo apt update
    sudo apt install ros-melodic-ros-base ros-melodic-rosbridge-suite
    sudo apt install python-rosinstall python-rosinstall-generator python-wstool build-essential

    sudo rosdep init
    rosdep update
    echo "source /opt/ros/melodic/setup.bash" >> ~/.bashrc
    source ~/.bashrc
    mkdir -p ros/catkin_ws/src
    cd ros
    git clone http://github.com/carla-simulator/ros-bridge.git
    cd  catkin_ws/src
    ln -s ../../ros-bridge
    source /opt/ros/melodic/setup.bash
    cd ..
    rosdep update
    rosdep install --from-paths src --ignore-src -r
    catkin_make
    echo "source $PWD/devel/setup.bash" >> ~/.bashrc
    source ~/.bashrc
    cd ../..


# Carla
    mkdir carla
    git clone https://github.com/Garazbolg/carla.git carla
    cd carla
    ./Update.sh
    git checkout --track origin/eSoft-simulator

    #Here you need to open the unreal project (cf below) and in the content browser open the blueprint : Content/Carla/Blueprints/Vehicles/VahicleFactory
        # Click on the local variable Vehicles (bottom left)
        # In the default value array add an element and edit it
        # Make :eSoft
        # Model :Realistic
        # Class :BP_eSoft
        # and leave the rest as default

    make launch     # Compiles the simulator and launches Unreal Engine's Editor.
    make PythonAPI  # Compiles the PythonAPI module necessary for running the Python examples.
    make package    # Compiles everything and creates a packaged version able to run without UE4 editor.
    make help       # Print all available commands.make launch

    cd PythonAPI/carla/dist
        export PYTHONPATH=$PYTHONPATH:$PWD/$(ls | grep 2.7)
        echo "export PYTHONPATH=$PYTHONPATH" >> ~/.bashrc
        source ~/.bashrc
    cd ../../..
    cd ..

# Generate Unreal Project
    cd UnrealEngine
    ./GenerateProjectFiles.sh -project="$PWD/../Carla/carla/Unreal/CarlaUE4/CarlaUE4.uproject" -game -engin -vscode

# Make sure the computer can communicate with the board using :
    #ping hostname
    #netcat -l 1234
    #or editing the /etc/hosts if needed

# To open the unreal project :
    cd ~/eSoftThings_simulation/carla/Unreal/CarlaUE4 && ue $PWD/CarlaUE4.uproject

# To launch the game :
## Terminal 1
    roslaunch rosbridge_server rosbridge_tcp.launch bson_only_mode:=True

## Terminal 2
    cd ~/eSoftThings_simulation/carla/Dist/$(ls)/LinuxNoEditor && ./CarlaUE4.sh -ResX=10 -ResY=10 -benchmark

## Terminal 3
### For 1080p
    cd ~/eSoftThings_simulation/ros/ros-bridge/catkin_ws && source devel/setup.bash && cd ~/eSoftThings_simulation/carla/PythonAPI/examples && python -O manual_control.py --res=5760x1080 --fullscreen --mirror_size=640x400 --wheel
### For 720p
    cd ~/eSoftThings_simulation/ros/ros-bridge/catkin_ws && source devel/setup.bash && cd ~/eSoftThings_simulation/carla/PythonAPI/examples && python -O manual_control.py --res=3840x720 --fullscreen --mirror_size=640x400 --wheel

## Terminal 4
    cd ~/eSoftThings_simulation/carla/PythonAPI/examples && ./spawn_npc.py -n 100 -w 50

# If pcm audio bugs : 
    code /usr/share/alsa/alsa.conf

## For "Unknown PCM cards.pcm.*" error
    # Change the problematic
    # pcm.* cards.pcm.* 
    # to 
    # pcm.* cards.pcm.default

## For "Found no matching channel map" error
    # Comment the lines
    # pcm.surround??