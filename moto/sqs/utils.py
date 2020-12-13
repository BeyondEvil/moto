from __future__ import unicode_literals
import os
import random
import string
import moto

from .exceptions import MessageAttributesInvalid
from moto.settings import TEST_SERVER_MODE

try:
    import configparser
except ModuleNotFoundError:
    # why are you using python 2.7?
    import ConfigParser as configparser


def generate_receipt_handle():
    # http://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/ImportantIdentifiers.html#ImportantIdentifiers-receipt-handles
    length = 185
    return "".join(random.choice(string.ascii_lowercase) for x in range(length))


def extract_input_message_attributes(querystring):
    message_attributes = []
    index = 1
    while True:
        # Loop through looking for message attributes
        name_key = "MessageAttributeName.{0}".format(index)
        name = querystring.get(name_key)
        if not name:
            # Found all attributes
            break
        message_attributes.append(name[0])
        index = index + 1
    return message_attributes


def parse_message_attributes(querystring, base="", value_namespace="Value."):
    message_attributes = {}
    index = 1
    while True:
        # Loop through looking for message attributes
        name_key = base + "MessageAttribute.{0}.Name".format(index)
        name = querystring.get(name_key)
        if not name:
            # Found all attributes
            break

        data_type_key = base + "MessageAttribute.{0}.{1}DataType".format(
            index, value_namespace
        )
        data_type = querystring.get(data_type_key)
        if not data_type:
            raise MessageAttributesInvalid(
                "The message attribute '{0}' must contain non-empty message attribute value.".format(
                    name[0]
                )
            )

        data_type_parts = data_type[0].split(".")
        if data_type_parts[0] not in ["String", "Binary", "Number"]:
            raise MessageAttributesInvalid(
                "The message attribute '{0}' has an invalid message attribute type, the set of supported type prefixes is Binary, Number, and String.".format(
                    name[0]
                )
            )

        type_prefix = "String"
        if data_type_parts[0] == "Binary":
            type_prefix = "Binary"

        value_key = base + "MessageAttribute.{0}.{1}{2}Value".format(
            index, value_namespace, type_prefix
        )
        value = querystring.get(value_key)
        if not value:
            raise MessageAttributesInvalid(
                "The message attribute '{0}' must contain non-empty message attribute value for message attribute type '{1}'.".format(
                    name[0], data_type[0]
                )
            )

        message_attributes[name[0]] = {
            "data_type": data_type[0],
            type_prefix.lower() + "_value": value[0],
        }

        index += 1

    return message_attributes


def read_config():
    section = os.getenv("MOTO_ENVIRONMENT", "production")
    parser = configparser.ConfigParser()
    filename = "configuration.ini"
    config_path = os.path.join(os.getcwd(), "moto", filename)

    if TEST_SERVER_MODE:
        # in server mode the config resides in the package
        config_path = os.path.join(os.path.dirname(moto.__file__), filename)

    parser.read(config_path)
    return parser[section]
