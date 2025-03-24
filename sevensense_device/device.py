from enum import Enum
from collections.abc import Callable
import requests, psutil
import subprocess
import time, threading
import os
import logging

# Define timeouts and polling time
MAX_UPGRADE_TIME = 10 * 60  # [s]
MAX_DOWNLOAD_TIME = 5 * 60  # [s]
MAX_WAIT_FOR_IDLE_TIME = 10 * 60  # [s]
POLLING_TIME = 0.1  # [s]

# Define Download URL
DOWNLOAD_URL = "https://raw.githubusercontent.com/MattiaHaas/sevensense/refs/heads/main/images/install.sh"
INTERNET_CONNECTION_CHECK_URL = "https://www.google.com"

# Set up the logger
logger = logging.getLogger("DeviceLogger")
logger.setLevel(logging.INFO)

# Create a console handler with timestamped log format
ch = logging.StreamHandler()
formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
ch.setFormatter(formatter)

# Add the handler to the logger
logger.addHandler(ch)


class DeviceState(Enum):
    """
    Enum representing the possible states of a device during its lifecycle.
    """

    Positioning = 0
    Idle = 1
    Downloading = 2
    Upgrading = 3
    Downgrading = 4


class UpgradeStatus(Enum):
    """
    Enum representing the possible outcomes of a device's upgrade attempt.
    """

    No_Update = 0
    Success = 1
    Failed = 2


class Device:
    """
    A class representing a device with methods to manage its state and update the image.
    """

    def __init__(self):
        """
        Initializes the device with software version, type, last upgrade status, and state.
        """
        # Get current software version and type from environmental variables
        self.software_version = int(os.environ.get("INITIAL_VERSION"))
        self.device_type = os.environ.get("DUT")

        # Initialize the member variables
        self.last_upgrade_status = UpgradeStatus.No_Update
        self.state = DeviceState.Idle

    def get_last_upgrade_result(self) -> UpgradeStatus:
        """
        Returns the last upgrade result status.

        Returns:
            UpgradeStatus: The last upgrade status.
        """
        return self.last_upgrade_status

    def get_current_state(self) -> DeviceState:
        """
        Returns the current state of the device.

        Returns:
            DeviceState: The current state of the device.
        """
        return self.state

    def get_current_version(self) -> int:
        """
        Returns the current software version of the device.

        Returns:
            int: The current software version of the device.
        """
        return self.software_version

    def get_connection_status(self) -> bool:
        """
        Checks the internet connection by making a request to a URL.

        Returns:
            bool: True if internet connection is available, False otherwise.
        """
        try:
            response = requests.get(INTERNET_CONNECTION_CHECK_URL, timeout=5)
            return response.status_code == 200
        except requests.RequestException:
            return False

    def get_power_status(self) -> bool:
        """
        Checks if the device is plugged into a power source.

        Returns:
            bool: True if device is plugged into power, False otherwise.
        """
        battery = psutil.sensors_battery()
        if battery is not None:
            # Check if the system is plugged into AC power
            return battery.power_plugged
        else:
            logger.warning("Unable to determine battery status.")
            return False

    def check_install_timeout(self, start_time: float):
        """
        Checks if the upgrade time has exceeded the allowed maximum upgrade time.

        Args:
            start_time (float): The start time of the upgrade.

        Returns:
            bool: True if the upgrade time has not exceeded the maximum, False otherwise.
        """
        return self.check_time_not_exceeded(start_time=start_time, duration=MAX_UPGRADE_TIME)

    def check_download_timeout(self, start_time: float):
        """
        Checks if the download time has exceeded the allowed maximum download time.

        Args:
            start_time (float): The start time of the download.

        Returns:
            bool: True if the download time has not exceeded the maximum, False otherwise.
        """
        return self.check_time_not_exceeded(start_time=start_time, duration=MAX_DOWNLOAD_TIME)

    def check_time_not_exceeded(self, start_time: float, duration: float):
        """
        Checks if the elapsed time has exceeded the specified duration.

        Args:
            start_time (float): The start time.
            duration (float): The maximum allowed time duration.

        Returns:
            bool: True if the elapsed time is less than the duration, False otherwise.
        """
        if start_time - time.time() < duration:
            return True
        else:
            return False

    def wait(self, target, get_current: Callable, timeout_duration: float) -> bool:
        """
        Waits for a certain condition to be met within the specified timeout.

        Args:
            target: The target state or value to wait for.
            get_current (Callable): A callable function that returns the current state or value.
            timeout_duration (float): The maximum time to wait before timing out.

        Returns:
            bool: True if the target is reached before the timeout, False otherwise.
        """

        start_time = time.time()
        while self.check_time_not_exceeded(start_time, timeout_duration):
            if target == get_current():
                return True
            time.sleep(POLLING_TIME)
        return False

    def initiate_update(self, *args, **kwargs):
        """
        Initiates the update process in a separate thread.

        Args:
            *args: Arguments to pass to the update function.
            **kwargs: Keyword arguments to pass to the update function.
        """
        t = threading.Thread(target=self.update, args=args, kwargs=kwargs, daemon=True)
        t.start()

    def update(self, new_version: int) -> bool:
        """
        Manages the update process: downloading and installing the new version.

        Args:
            new_version (int): The version to upgrade or downgrade to.

        Returns:
            bool: True if the update was successful, False otherwise.
        """

        transitioned_to_idle = self.wait(DeviceState.Idle, self.get_current_state, MAX_WAIT_FOR_IDLE_TIME)
        if not transitioned_to_idle:
            logger.error("The update could not be performed as the device state is not idle.")
            return False

        # Only perform software update if the new version differs from current version
        if self.software_version == new_version:
            logger.info("The current version and the new version are the same.")
            return False

        # Stage 1, download the image from remote
        download_success = self.download_image(new_version=new_version)
        if not download_success:
            self.last_upgrade_status = UpgradeStatus.Failed
            self.state = DeviceState.Idle
            return False

        # Stage 2, install the downloaded image if download was successful
        upgrade_success = self.install_image(new_version=new_version)
        if not upgrade_success:
            self.last_upgrade_status = UpgradeStatus.Failed
            self.state = DeviceState.Idle
            return False

        # Update the upgrade notification and current software version
        self.last_upgrade_status = UpgradeStatus.Success
        self.software_version = new_version
        self.state = DeviceState.Idle

        logger.info(f"Software update to version {new_version} complete.")
        return True

    def download_image(self, new_version: int):
        """
        Downloads the firmware image from a remote server.

        Args:
            new_version (int): The version to be downloaded.

        Returns:
            bool: True if the download completed successfully, False if it failed.
        """

        # Double check if we are indeed in the idle state
        if self.state != DeviceState.Idle:
            return False

        logger.info(f"Starting software version {new_version} download.")
        self.state = DeviceState.Downloading

        # Create process for downloading the image
        command = ["curl", "-O", DOWNLOAD_URL]
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

        start_time = time.time()

        while True:
            # Check if the internet connection is still active
            if not self.get_connection_status():
                logger.error("Internet connection lost during download.")
                process.terminate()
                process.wait()
                return False

            # If the timeout is exceeded, terminate the process
            if not self.check_download_timeout(start_time):
                logger.error(f"Download timed out after {MAX_DOWNLOAD_TIME} seconds.")
                process.terminate()
                process.wait()
                return False

            # Check if the download process is still running
            if process.poll() is not None:
                logger.info("Download completed successfully.")
                break

            # Sleep before checking again
            time.sleep(POLLING_TIME)
        return True

    def install_image(self, new_version: int):
        """
        Installs the downloaded firmware image onto the device.

        Args:
            new_version (int): The version to be installed.

        Returns:
            bool: True if the installation completed successfully, False if it failed.
        """

        # Double check if we are indeed in the idle state
        if self.state != DeviceState.Downloading:
            return False

        logger.info(f"Starting software update version {new_version} installation.")

        # Check if we are upgrading or downgrading the software
        if self.software_version > new_version:
            self.state = DeviceState.Downgrading
        else:
            self.state = DeviceState.Upgrading

        # Set up the process for installing the image
        command = ["sh", "install.sh"]
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

        start_time = time.time()

        while True:
            # Check if power is still available
            if not self.get_power_status():
                logger.error("Power loss detected during the upgrade.")
                process.terminate()
                process.wait()
                return False

            # If the timeout is exceeded, terminate the process
            if not self.check_install_timeout(start_time):
                logger.error(f"Upgrade timed out after {MAX_UPGRADE_TIME} seconds.")
                process.terminate()
                process.wait()
                return False

            output = process.stdout.readline()
            while output:
                logger.debug(output.strip())  # Print each line from stdout
                output = process.stdout.readline()

            # Check if the upgrade process is still running
            if process.poll() is not None:
                logger.info("Upgrade completed successfully.")
                break

            # Sleep before checking again
            time.sleep(POLLING_TIME)
        return True
