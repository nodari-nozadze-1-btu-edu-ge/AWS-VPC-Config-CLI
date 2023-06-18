# AWS VPC Configuration Script

This script allows you to create and configure an AWS VPC (Virtual Private Cloud) with subnets using the Boto3 library in Python.

## Prerequisites

Before running the script, make sure you have the following:

- Python installed
- Boto3 library installed
- AWS access key, secret access key, and session token
- Required environment variables set (aws_access_key_id, aws_secret_access_key, aws_session_token, aws_region_name)

## Usage

The script provides several command-line options:

- `-npu` (number of public subnets): Specify the number of public subnets to create.
- `-npr` (number of private subnets): Specify the number of private subnets to create.
- `--create_vpc_with_subnets` (`-cvws`): Create a VPC with the specified number of subnets (public and private).
- `--create_vpc` (`-cv`): Create a VPC without subnets.
- `--tag_vpc` (`-tv`): Specify the name of the VPC (to be used as a tag).
- `--vpc_id` (`-vi`): Specify the ID of an existing VPC.
- `--create_IGW` (`-cIGW`): Create an Internet Gateway (IGW).
- `--attach_IGW` (`-aIGW`): Attach the IGW to the VPC.
  
## Example Usage

To create a VPC with 2 public subnets and 3 private subnets, and attach an Internet Gateway, you can use the following command:




