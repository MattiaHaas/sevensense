from sevensense_device.device import Device, DeviceState, UpgradeStatus
import time


def test_upgrade_not_allowed_for_same_version():
    """
    Test case to ensure that an upgrade is not allowed if the device is already on the same version.
    The upgrade should be rejected, and the last upgrade status should be No_Update.
    """
    # initialize device and call update
    device = Device()
    device.initiate_update(new_version=device.get_current_version())
    assert (
        device.last_upgrade_status == UpgradeStatus.No_Update
    ), "Upgrade accepted despite DUT already on the same version"


def test_upgrade_in_state_positioning():
    """
    Test case to ensure that an upgrade is not allowed when the device is in the 'Positioning' state.
    The device should remain in the 'Positioning' state if an upgrade is initiated in this state.
    """
    # initialize device
    device = Device()

    # set device state to Positioning
    device.state = DeviceState.Positioning

    # call update
    device.initiate_update(new_version=4)
    assert device.get_current_state() == DeviceState.Positioning, "Upgrade accepted despite DUT being in DUT mode"


def test_upgrade_switching_state_to_idle():
    """
    Test case to ensure that the upgrade is allowed when the device switches from the 'Positioning' state to the 'Idle' state.
    """
    # initialize device and call update
    device = Device()

    # set device state to Positioning
    device.state = DeviceState.Positioning

    # call update
    device.initiate_update(new_version=4)

    # switch device state to Idle and make sure update starts
    device.state = DeviceState.Idle
    time.sleep(0.2)
    assert (
        device.get_current_state() != DeviceState.Idle
    ), "Upgrade not accepted despite DUT switching from Positioning to Idle mode"


def test_downgrade():
    """
    Test case to ensure that a downgrade (when the new version is lower than the current version) is allowed.
    """
    # initialize device and call update
    device = Device()
    device.initiate_update(new_version=1)

    # make sure downgrade update starts
    time.sleep(0.1)
    assert (
        device.get_current_state() != DeviceState.Idle
    ), "Upgrade not accepted despite DUT switching from Positioning to Idle mode"


def test_done_notification():
    """
    Test case to ensure that after an upgrade attempt, a notification is sent indicating success or failure.
    The device should notify about the upgrade result, and it should be either 'Success' or 'Failed' based on the outcome.
    """
    new_version = 3

    # initialize device and call update
    device = Device()
    device.initiate_update(new_version=new_version)

    # wait for result
    time.sleep(0.1)
    while device.get_current_state() != DeviceState.Idle:
        time.sleep(0.1)

    if device.get_current_version() == new_version:
        assert (
            device.get_last_upgrade_result() == UpgradeStatus.Success
        ), "Upgrade successful but no notification or failure notification"
    else:
        assert (
            device.get_last_upgrade_result() == UpgradeStatus.Failed
        ), "Upgrade unsuccessful but no notification or success notification"


def test_power_interruption(mocker):
    """
    Test case to simulate a power interruption during the upgrade process.
    The upgrade should fail if the power status indicates that the device is no longer powered.
    """
    # mock signals from power status to fail the update
    mock_method = mocker.patch.object(Device, "get_power_status", return_value=False)

    # initialize device and call update
    device = Device()
    device.initiate_update(new_version=3)

    # wait for result
    while device.get_last_upgrade_result() == UpgradeStatus.No_Update:
        time.sleep(0.1)
    assert device.get_last_upgrade_result() == UpgradeStatus.Failed, "Upgrade successful despite power loss"


def test_connection_interruption(mocker):
    """
    Test case to simulate a connection interruption during the upgrade process.
    The upgrade should fail if the device loses its internet connection.
    """
    # mock signals from connection status to fail the update
    mock_method = mocker.patch.object(Device, "get_connection_status", return_value=False)

    # initialize device and call update
    device = Device()
    device.initiate_update(new_version=3)

    # wait for result
    while device.get_last_upgrade_result() == UpgradeStatus.No_Update:
        time.sleep(0.1)
    assert device.get_last_upgrade_result() == UpgradeStatus.Failed, "Upgrade successful despite connection loss"


def test_download_timeout(mocker):
    """
    Test case to simulate a download timeout during the firmware download process.
    The upgrade should fail if the download exceeds the maximum allowed time.
    """
    # mock call from download timeout to fail the update
    mock_method = mocker.patch.object(Device, "check_download_timeout", return_value=False)

    # initialize device and call update
    device = Device()
    device.initiate_update(new_version=3)

    # wait for result
    while device.get_last_upgrade_result() == UpgradeStatus.No_Update:
        time.sleep(0.1)
    assert device.get_last_upgrade_result() == UpgradeStatus.Failed, "Upgrade successful despite download timeout"


def test_install_timeout(mocker):
    """
    Test case to simulate an installation timeout during the firmware installation process.
    The upgrade should fail if the installation exceeds the maximum allowed time.
    """
    # mock call from install timeout to fail the update
    mock_method = mocker.patch.object(Device, "check_install_timeout", return_value=False)

    # initialize device and call update
    device = Device()
    device.initiate_update(new_version=3)

    # wait for result
    while device.get_last_upgrade_result() == UpgradeStatus.No_Update:
        time.sleep(0.1)
    assert device.get_last_upgrade_result() == UpgradeStatus.Failed, "Upgrade successful despite install timeout"


def test_connection_interruption_recovery(mocker):
    """
    Test case to simulate recovery from a connection interruption during the upgrade.
    After the connection is restored, the upgrade should continue successfully.
    """
    # mock signals from power status
    mock_method_connection = mocker.patch.object(Device, "get_connection_status", return_value=False)

    # mock signals from connection status to fail the update
    mock_method_power = mocker.patch.object(Device, "get_power_status", return_value=True)

    # initialize device and call update
    device = Device()
    device.initiate_update(new_version=3)

    # wait for result
    while device.get_last_upgrade_result() == UpgradeStatus.No_Update:
        time.sleep(0.1)

    # stop mocking the connection status call
    mocker.stop(mock_method_connection)

    # call update again and wait for result
    device.initiate_update(new_version=3)

    # wait for result
    time.sleep(0.1)
    while device.get_current_state() != DeviceState.Idle:
        time.sleep(0.1)

    assert (
        device.get_last_upgrade_result() == UpgradeStatus.Success
    ), "Upgrade successful but no notification or failure notification"
