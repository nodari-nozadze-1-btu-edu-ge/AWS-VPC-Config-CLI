import boto3
import os
from os import getenv
from dotenv import load_dotenv
import logging
from botocore.exceptions import ClientError
from boto3.s3.transfer import TransferConfig
import argparse
from pprint import pprint
load_dotenv()
import time
parser = argparse.ArgumentParser()
parser.add_argument('-npu', type=int, help='number of public subnet')
parser.add_argument('-npr', type=int, help='number of private subnet')
parser.add_argument('--create_vpc_with_subnets', "-cvws", nargs='?', const='true', help='create vpc with subnets' )
parser.add_argument('--create_vpc', "-cv", nargs='?', const='true', help='create vpc' )
parser.add_argument('--tag_vpc', "-tv", type=str, help='Name of vpc')
parser.add_argument('--vpc_id', "-vi", type=str, help='vpc ID')
parser.add_argument('--create_IGW', "-cIGW", nargs='?', const='true', help='create IGW' )
parser.add_argument('--attach_IGW', "-aIGW", nargs='?', const='true', help='attach IGW to vpc' )
s3 = boto3.client('s3')
args = parser.parse_args()

ec2_client = boto3.client(
  "ec2",
  aws_access_key_id=getenv("aws_access_key_id"),
  aws_secret_access_key=getenv("aws_secret_access_key"),
  aws_session_token=getenv("aws_session_token"),
  region_name=getenv("aws_region_name")
)

def create_vpc():
  result = ec2_client.create_vpc(CidrBlock="10.22.0.0/16")
  vpc = result.get("Vpc")
  print(vpc)
  vpc = result.get("Vpc")
  vpc_id = vpc.get("VpcId")

def add_name_tag(vpc_id):
  ec2_client.create_tags(Resources=[vpc_id],
                         Tags=[{
                           "Key": "Name",
                           "Value": args.tag_vpc
                         }])
  print(f'{args.tag_vpc} tag created')
def create_igw():
  result = ec2_client.create_internet_gateway()
  print("InternetGateway created")
  return result.get("InternetGateway").get("InternetGatewayId")
def create_or_get_igw(vpc_id):
  igw_id = None
  igw_response = ec2_client.describe_internet_gateways(
    Filters=[{
      'Name': 'attachment.vpc-id',
      'Values': [vpc_id]
    }])

  if 'InternetGateways' in igw_response and igw_response['InternetGateways']:
    igw = igw_response['InternetGateways'][0]
    igw_id = igw['InternetGatewayId']
  else:
    response = ec2_client.create_internet_gateway()
    pprint(response)
    igw = response.get("InternetGateway")
    igw_id = igw.get("InternetGatewayId")
    response = ec2_client.attach_internet_gateway(InternetGatewayId=igw_id,
                                                  VpcId=vpc_id)
    print("attached")
    pprint(response)
  return igw_id
def create_route_table_with_route(vpc_id, route_table_name, igw_id):
  response = ec2_client.create_route_table(VpcId=vpc_id)
  route_table = response.get("RouteTable")
  pprint(route_table)
  route_table_id = route_table.get("RouteTableId")
  print("Route table id", route_table_id)
  time.sleep(2)
  ec2_client.create_tags(
    Resources=[route_table_id],
    Tags=[
      {
        "Key": "Name",
        "Value": route_table_name
      },
    ],
  )
  response = ec2_client.create_route(
    DestinationCidrBlock='0.0.0.0/0',
    GatewayId=igw_id,
    RouteTableId=route_table_id,
  )
  return route_table_id
def associate_route_table_to_subnet(route_table_id, subnet_id):
  response = ec2_client.associate_route_table(RouteTableId=route_table_id,
                                              SubnetId=subnet_id)
  print("Route table associated")
  pprint(response)
def enable_auto_public_ips(subnet_id, action):
  new_state = True if action == "enable" else False
  response = ec2_client.modify_subnet_attribute(
    MapPublicIpOnLaunch={"Value": new_state}, SubnetId=subnet_id)
  print("Public IP association state changed to", new_state)
def create_route_table_without_route(vpc_id):
  response = ec2_client.create_route_table(VpcId=vpc_id)
  route_table = response.get("RouteTable")
  pprint(route_table)
  route_table_id = route_table.get("RouteTableId")
  print("Route table id", route_table_id)
  time.sleep(2)
  ec2_client.create_tags(
    Resources=[route_table_id],
    Tags=[
      {
        "Key": "Name",
        "Value": "private-route-table"
      },
    ],
  )
  return route_table_id
def attach_igw_to_vpc(vpc_id, igw_id):
  ec2_client.attach_internet_gateway(InternetGatewayId=igw_id, VpcId=vpc_id)
def create_subnet(vpc_id, cidr_block, subnet_name):
  time.sleep(2)
  response = ec2_client.create_subnet(VpcId=vpc_id, CidrBlock=cidr_block)
  subnet = response.get("Subnet")
  pprint(subnet)
  subnet_id = subnet.get("SubnetId")
  time.sleep(2)
  ec2_client.create_tags(
    Resources=[subnet_id],
    Tags=[
      {
        "Key": "Name",
        "Value": subnet_name
      },
    ],
  )
  return subnet_id


if args.create_vpc:
  create_vpc()
if args.tag_vpc:
  add_name_tag(args.vpc_id)
if args.create_IGW:
  igw_id = create_igw()
  if args.attach_IGW:
    attach_igw_to_vpc(args.vpc_id, igw_id)
    print(f'internet gateway{igw_id} attached to vpc{args.vpc_id}')
if args.create_vpc_with_subnets:
  if args.npr + args.npu < 200:
    result = ec2_client.create_vpc(CidrBlock="10.22.0.0/16")
    vpc = result.get("Vpc")
    print(vpc)
    vpc = result.get("Vpc")
    vpc_id = vpc.get("VpcId")
    for i in range(args.npr):
      subnet_id = create_subnet(vpc_id, f'10.22.{i}.0/24', f'private_sub_{i}')
      time.sleep(2)
      rtb_id = create_route_table_without_route(vpc_id)
      time.sleep(2)
      associate_route_table_to_subnet(rtb_id, subnet_id)
      time.sleep(2)
    for i in range(args.npu):
      subnet_id = create_subnet(vpc_id, f'10.22.{i+args.npr}.0/24', f'public_sub_{i+args.npr}')
      time.sleep(2)
      rtb_id = create_route_table_with_route(vpc_id, 'my_route_name',
                                            create_or_get_igw(vpc_id))
      time.sleep(2)
      associate_route_table_to_subnet(rtb_id, subnet_id)
      time.sleep(2)
      enable_auto_public_ips(subnet_id, 'enable')
      time.sleep(2)
  else:
    print("subnet_ების რაოდენობა არ უნდა აღემატებოდეს 200")