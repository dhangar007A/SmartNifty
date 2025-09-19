cmake_minimum_required(VERSION 3.11)
project(C++)

set(CMAKE_CXX_STANDARD 17)

include_directories(include)

file(GLOB SRC_FILES src/*.cpp)

add_executable(main ${SRC_FILES} Strategy-1/main.cpp)
