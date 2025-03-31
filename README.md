# Device under Test

## Install

This code has been run inside a Ubuntu docker container using Python 3.12.
To replicate my setup one can perform the following instructions:
1. Create docker image: `docker build -t sevensense .`

## Method

The idea behind this device is to be able to perform a software update.
This update shall only be started once the state of the device is Idle.
I therefore decided to use a thread which allows the device to operate as
usual while waiting for the state to switch to the Idle state. Once this 
happens then we stop waiting and start updating. The first step is to check 
if the new version is the same as the old version. In that case we don't 
need to perform any update. In case they differ then we can start downloading
the new image. I used a subprocess for this particular step as I wanted to 
be able to have that run independently from the Device instance so that I 
could continuously check the internet connection and monitor the process
to make sure we also don't exceed the maximum allowed download time. Once the
download has been completed successfully the second phase of the update can 
start by installing the image. In a similar fashion to the download process
an installation subprocess performs the installation. This again allows for 
monitoring the power supply and the maximum allowed time for the installation.
Once the update has been successful then we can update the notification status.
In case any of the 2 steps fail then we will revert back to the idle state and
update the notification status to failure. 

In addition to the main code I also decided to implement a logger which can be
used to investigate any past updates later on.

## Testing

To run the tests including coverage one can run the following command:
`docker run -it sevensense`

The tests mostly reflect the requirements. The additionally challenge for the timeout
interruption tests was to mock/simulate a difference response from the device object.
This was necessary in order to simulate a power interruption or a connection interruption
but also to simulate the time passing faster than expected.

## Assumptions

* System is linux based
* The image is stored on a remote server which the client can access via curl command
* The power status is accessible via psutils command
* After failing the downloading or the installation stage the Device state is set to idle
* The installation image can be invoked via the command line

## Improvements

* The logger could be saved to a file.
* Adapt the code to the real file storage of the images and also ping the route IP instead of google.com for the connectivity check.
* The command for the installation is just running a dummy script.
* Adapt the code to the available interfaces for the power supply check.
* Expand the test cases to achieve a coverage of 100%.
* Add a variable which indicates whether or not an update is currently running or consolidate the updating states.