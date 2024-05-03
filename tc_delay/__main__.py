import yaml
import argparse
import subprocess
import os
import sys


def parse_arguments():
    parser = argparse.ArgumentParser(
        description="tc_delay allows you to easily emulate wan connections "
                    "between groups of hosts."
    )
    parser.add_argument("--action", "-a",
                        required=True,
                        type=str,
                        default="create",
                        choices=["create", "delete", "reload", "show"],
                        help="Specify the action to be taken. Create creates "
                             "shaper rules, Delete removes the default "
                             "qdisc, removing all rules. Reload runs delete, "
                             "and then create.")
    parser.add_argument("--config",
                        "-c",
                        required=True,
                        type=str,
                        help="Path to the yaml config file")
    return parser.parse_args()


def load_config_file(path):
    with open(path) as file:
        raw_text = file.read()
    return yaml.safe_load(raw_text)


def exec_command(command, stdout_supress=True):
    if stdout_supress:
        stdout_location = subprocess.DEVNULL
    else:
        stdout_location = subprocess.STDOUT
    print(f"Executing command: {command}")
    command = command.split(" ")
    subprocess.run(command, check=True, stdout=stdout_location)


def delete_existing_config(interface):
    try:
        exec_command(f"tc qdisc del dev {interface} root")
    except subprocess.CalledProcessError:
        pass


def create_htb_queue(interface):
    # Create an HTB qdisc on the root interface
    exec_command(f"tc qdisc add dev {interface} root handle 1: htb")
    # Create a default class on the root qdisc so normal traffic will not
    # be messed with
    exec_command(
        f"tc class add dev {interface} parent 1: classid 1:1 htb rate 1000Mbps"
    )


def check_if_root():
    if os.geteuid() != 0:
        print("You need root permissions to run this. Please run this again "
              "with root or sudo.")
        sys.exit(1)


def create_htb_class(class_number, interface, group_dict):
    # Create the class to classify traffic
    exec_command(f"tc class add dev {interface} parent 1:1 "
                 f"classid 1:{class_number} htb rate 1000Mbps")
    # Create the netem qdisc on top of the new class
    exec_command(f"tc qdisc "
                 f"add dev {interface} handle {class_number}: parent "
                 f"1:{class_number} "
                 f"netem {group_dict['netem_args']}")
    for ip_address in group_dict['ips']:
        exec_command(f"tc filter add dev {interface} pref {class_number} "
                     f"protocol ip parent 1:0 u32 match ip dst {ip_address} "
                     f"flowid 1:{class_number}")


def create_queues(config):
    create_htb_queue(config['interface'])
    for group in config['groups']:
        class_number = config['groups'].index(group) + 2
        create_htb_class(class_number, config['interface'], group)


def main():
    check_if_root()
    args = parse_arguments()
    config = load_config_file(args.config)
    if args.action == "delete":
        delete_existing_config(config['interface'])
    elif args.action == "create":
        create_queues(config)
    elif args.action == "reload":
        delete_existing_config(config['interface'])
        create_queues(config)
    elif args.action == "show":
        exec_command(['tc', 'qdisc', 'show'], stdout_supress=False)


if __name__ == "__main__":
    main()
