#!/usr/bin/env python3

import binascii
import logging
from time import sleep
from typing import Tuple
from enum import Flag
from google.protobuf.json_format import MessageToJson
from google.protobuf.message import DecodeError

# Why is this include so disgusting?
import nfcreader.nfcreader.nfcreader as nfc
import time

# Syspath hack so that generated protobuf files can be imported.
import os
import sys
sys.path.append(os.path.join(os.path.dirname(
    __file__), "../../integration-test/halter"))
sys.path.append(os.path.join(os.path.dirname(
    __file__), "integration-test/halter"))

import responses_pb2 as responses  # nopep8
import commands_pb2 as commands  # nopep8

logging.basicConfig(level=logging.INFO)


def decode_to_json(payload: str):
    try:
        payload_hex = bytes.fromhex(payload)
        decoded = responses.Response.FromString(payload_hex)
        decoded_json = MessageToJson(decoded,
                                     # Make sure original names are kept.
                                     preserving_proto_field_name=True,
                                     including_default_value_fields=True)   # Include fields that were empty are printed.
        return decoded_json
    except ParseError as e:
        logging.warning('Unable to decode: {}, {}'.format(payload, e))
        return None


def enableMailbox() -> bool:
    nfc.SendReceive(b'02AE020D00')  # Clear all flags in dynamic config.
    return (nfc.SendReceive(b'02AE020D01')[0] == 0)


def sendMailboxCommand(command: str) -> bool:
    enableMailbox()
    command_length = len(command)
    command = binascii.hexlify(command)
    nfc_prefix = str.encode('02AA02{:02X}'.format(command_length - 1))
    command = nfc_prefix + command
    return (nfc.SendReceive(command)[0] == 0)


def readMailbox() -> Tuple[bool, str]:
    result, mailbox_content = nfc.SendReceive(b'02AC020000')
    if (result == 0 and len(mailbox_content) > 12):
        # Remove extra NFC wrapping bytes
        mailbox_content = mailbox_content[6:-6]
        # Add space every 2 characters.
        mailbox_content = ' '.join([mailbox_content[i:i+2]
                                   for i in range(0, len(mailbox_content), 2)])
        return True, mailbox_content
    return False, ''


class NfcDynamicConfig(Flag):
    MB_EN = 0
    HOST_PUT_MSG = 1
    RF_PUT_MSG = 2
    RFU = 3
    HOST_MISS_MSG = 4
    RF_MISS_MSG = 5
    HOST_CURRENT_MSG = 6
    RF_CURRENT_MSG = 7


def readNfcDynamicConfig():
    result, response = nfc.SendReceive(b'02AD020D')
    if result == 0 and len(response) > 12:
        response = response[6:-6]
        response = int(response, 16)

        # Convert the returned integer string into the bitmask flags.
        bits = [flag for flag in NfcDynamicConfig if (
            (1 << flag.value) & response)]

        return bits


def messageWaitingInMailbox():
    bits = readNfcDynamicConfig()
    return (bits is not None) and ((NfcDynamicConfig.HOST_PUT_MSG in bits) or (NfcDynamicConfig.RF_MISS_MSG in bits))


def waitForResponse(timeout_seconds: int, polling_interval_seconds: int):
    # HACK: Without this sleep the collar doesn't process the mailbox message.
    sleep(0.1)

    elapsed = 0
    while(not messageWaitingInMailbox()):
        sleep(polling_interval_seconds)
        elapsed += polling_interval_seconds

        if (elapsed >= timeout_seconds):
            return False

    return True


def printMailbox():
    result, string = readMailbox()
    if (result):
        logging.info(decode_to_json(string))
    else:
        logging.warning('Failed to read mailbox')


def sendCommand(command: commands.Command, timeout_seconds: int = 10) -> Tuple[bool, responses.Response]:
    message_sent = sendMailboxCommand(command.SerializeToString())
    if message_sent is False:
        logging.warning('Failed to send message')
        return False, None

    if not waitForResponse(timeout_seconds=timeout_seconds, polling_interval_seconds=1):
        logging.warning('Failed to receive response')
        return False, None

    result, response = readMailbox()
    if result is False:
        logging.warning('Failed to read mailbox')
        return False, None

    try:
        response = responses.Response.FromString(bytes.fromhex(response))
        if (response is not None):
            return True, response
    except DecodeError as e:
        logging.warning('Unable to decode response: {}'.format(e))
        return False, None

    logging.warning('Failed to decode response')
    return False, None


def sendShockCommand(pulses: int = 4) -> Tuple[bool, responses.ShockResult]:
    shock_command = commands.Command(
        type=commands.SHOCK_CMD,
        shock=commands.ShockCmd(
            side=commands.ACTUATION_OUTPUT_MASTER,
            charge_percent=100,
            pulses=pulses,
            energy_level=commands.SHOCK_ENERGY_HIGH))

    send_successful, response = sendCommand(shock_command)

    if (send_successful) and (response.type == responses.SHOCK_RESULT):
        return True, response.shock_result

    return False, None


def testShockOpenCircuit():
    test_passed = False
    result, shock_result = sendShockCommand(pulses=4)

    if result:
        test_passed = True
        test_passed &= (shock_result.pulses_requested == 4)
        test_passed &= (shock_result.pulses_attempted == 4)
        test_passed &= (shock_result.pulses_delivered == 0)
        for pulse in shock_result.pulse_results:
            # TODO: Verify the thresholds used in production.
            test_passed &= (pulse.charge_time_ms < 1000)
            test_passed &= (pulse.confirm_level < 10)

    return test_passed


def testShockClosedCircuit():
    test_passed = False
    result, shock_result = sendShockCommand(pulses=4)

    if result:
        test_passed = True
        test_passed &= (shock_result.pulses_requested == 4)
        test_passed &= (shock_result.pulses_attempted == 4)
        test_passed &= (shock_result.pulses_delivered == 4)
        for pulse in shock_result.pulse_results:
            # TODO: Verify the thresholds used in production.
            test_passed &= (pulse.charge_time_ms < 1000)
            test_passed &= (pulse.confirm_level > 1000)

    return test_passed

def getCurrents():
    general_status_request_cmd=commands.Command(type=commands.GENERAL_STATUS_REQUEST)
    general_status_request_cmd.confirmation_beep_required=False
    send_successful, response = sendCommand(general_status_request_cmd)

    if (send_successful) and (response.type == responses.GENERAL_STATUS_RESPONSE):
        logging.info('Battery voltage: {} mV, Generation current: {} mA, Load current {} mA, Power {}'.format(
            response.general_status.power.battery_mv,
            response.general_status.power.generation_ma,
            response.general_status.power.load_ma,
            (response.general_status.power.battery_mv * response.general_status.power.generation_ma)/1000
            ))

def testBatteryVoltage(voltage_threshold: int):
    battery_test_cmd = commands.Command(
        type=commands.BATTERY_TEST_CMD,
        battery_test=commands.BatteryTest(
            voltage_threshold=voltage_threshold))
    battery_test_cmd.confirmation_beep_required=False

    send_successful, response = sendCommand(battery_test_cmd)

    if (send_successful) and (response.type == responses.TEST_RESULT) and (response.test_result.test == commands.BATTERY_TEST_CMD):
        logging.info('Battery voltage: {} mV, Charging current: {} mA'.format(
            response.test_result.battery.voltage_reported,
            response.test_result.battery.charging_current_reported))
        return response.test_result.test_passed

    return False


def testWifiConnection():
    wifi_test_cmd = commands.Command(type=commands.WIFI_CONNECTION_TEST_CMD)

    send_successful, response = sendCommand(
        command=wifi_test_cmd, timeout_seconds=45)

    if (send_successful) and (response.type == responses.TEST_RESULT) and (response.test_result.test == commands.WIFI_CONNECTION_TEST_CMD):
        logging.info('Wifi connection: BSSID - {}, RSSI: {}'.format(
            binascii.hexlify(response.test_result.wifi.bssid, ':'), response.test_result.wifi.rssi))
        return response.test_result.test_passed

    return False


def main():
    connection_successful = (nfc.USBConnect() == 0)
    if connection_successful:
        while True:
            time.sleep(0.5)
            getCurrents()
            #testBatteryVoltage(3000)
            time.sleep(0.5)
    else:
        logging.warning('Connection failed')


if __name__ == "__main__":
    main()
