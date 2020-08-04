import sys
import time
import json
import logging
from pprint import pprint

import boto3

from colorlog import ColoredFormatter


zone = 'a'


def aws_client(region_name,resource=True, aws_service='ec2'):
    if resource:
        return boto3.resource(aws_service, region_name=region_name)
    else:
        return boto3.client(aws_service, region_name=region_name)


# Setting up a logger
def setup_logger(verbose=False):
    """Return a logger with a default ColoredFormatter."""
    logging.addLevelName(21, 'SUCCESS')
    logging.addLevelName(11, 'PROCESS')
    formatter = ColoredFormatter(
        "%(log_color)s%(levelname)-8s%(reset)s - %(name)-5s -  %(message)s",
        datefmt=None,
        reset=True,
        log_colors={
            'ERROR':    'red',      # LEVEL: 40
            'CRITICAL': 'red',      # LEVEL: 50
            'INFO':     'cyan',     # LEVEL: 20
            'DEBUG':    'white',    # LEVEL: 10
            'SUCCESS':  'green',    # LEVEL: 21
            'PROCESS':  'purple',   # LEVEL: 11
            'WARNING':  'yellow',}) # LEVEL: 30

    logger = logging.getLogger('AWS-Inst')
    setattr(logger, 'success', lambda *args: logger.log(21, *args))
    setattr(logger, 'process', lambda *args: logger.log(11, *args))
    fh = logging.FileHandler('AWS-Inst.log')
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(formatter)
    handler = logging.StreamHandler()
    handler.setFormatter(formatter)
    logger.addHandler(fh)
    logger.addHandler(handler)
    if not verbose:
        logger.setLevel(logging.INFO)
    else:
        logger.setLevel(logging.DEBUG)
    return logger




def convert_region_name(region, logger):
    try:
        client = aws_client(resource=False, aws_service="ssm", region_name=region)
        region_name = client.get_parameter(Name='/aws/service/global-infrastructure/regions/{}/longName'.format(region))['Parameter']['Value']
        return region_name
    except:
        err = str(sys.exc_info()[1])
        logger.error('{0}. Please check the Region name.'.format(err))
        logger.info('Check if the region you entered exsist:(Please wait while collecting all the Regions names...)')
        pprint(get_all_regions(RegionName=region, logger=logger))
        sys.exit(0)


def get_all_regions(RegionName,logger):
    region_dict = {}
    client = aws_client(resource=False, region_name=RegionName)
    response = client.describe_regions()['Regions']
    for region in response:
        region_api_id = region['Endpoint'].split('.')[1]
        regionname = convert_region_name(region_api_id, logger)
        region_dict[regionname] = region_api_id
    return region_dict

def check_spot_status(client, SpotId, region, logger):
    status_code = get_spot_info(SpotId, region=region)["Status"]["Code"]
    while status_code != "fulfilled":
        status_code = get_spot_info(SpotId, region=region)["Status"]["Code"]
        status_msg = get_spot_info(SpotId, region=region)["Status"]["Message"]
        if status_code == 'pending-fulfillment' or status_code == 'fulfilled':
            logger.info('{0}...'.format(status_code))
            time.sleep(1)
        else:
            logger.error("{0}\n{1}".format(status_code, status_msg))
            logger.process("Canceling spot request - {0}".format(SpotId))
            client.cancel_spot_instance_requests(SpotInstanceRequestIds=[SpotId])
            sys.exit(0)


def get_spot_info(spotid, region):
    client = aws_client(resource=False, region_name=region)
    spot_status = client.describe_spot_instance_requests(SpotInstanceRequestIds=[spotid])
    return spot_status["SpotInstanceRequests"][0]
#
#
def get_spot_price(type, region, logger):
    client = aws_client(resource=False, region_name=region)
    try:
        price = client.describe_spot_price_history(InstanceTypes=[type], MaxResults=1, ProductDescriptions=['Linux/UNIX (Amazon VPC)'])["SpotPriceHistory"][0]["SpotPrice"]
        return price
    except IndexError:
        logger.error('Can\'t get spot price. Check if the instance type exists in region.')
        sys.exit(0)

def get_price(instance, region, operationsystem):
    FLT = '[{{"Field": "tenancy", "Value": "shared", "Type": "TERM_MATCH"}},' \
          '{{"Field": "operatingSystem", "Value": "{o}", "Type": "TERM_MATCH"}},' \
          '{{"Field": "preInstalledSw", "Value": "NA", "Type": "TERM_MATCH"}},' \
          '{{"Field": "instanceType", "Value": "{t}", "Type": "TERM_MATCH"}},' \
          '{{"Field": "locationType", "Value": "AWS Region", "Type": "TERM_MATCH"}},' \
          '{{"Field": "capacitystatus", "Value": "Used", "Type": "TERM_MATCH"}}]'
    f = FLT.format(t=instance, o=operationsystem)
    data = aws_client(resource=False, aws_service='pricing', region_name='us-east-1').get_products(
        ServiceCode='AmazonEC2', Filters=json.loads(f))
    od = json.loads(data['PriceList'][0])['terms']['OnDemand']
    id1 = list(od)[0]
    id2 = list(od[id1]['priceDimensions'])[0]
    return od[id1]['priceDimensions'][id2]['pricePerUnit']['USD']



def start_instance(instancetype, ami, key, region, name, user, IamInstanceProfile, SecurityGroup, logger, prod='True'):
    client = aws_client(region_name=region)
    region_name = convert_region_name(region=region, logger=logger)
    # instanceprice = get_price(region=region, instance=instancetype, operationsystem='Linux')
    logger.process('Waiting for instance to boot...')
    try:
        instance = client.create_instances(
            ImageId=ami,
            TagSpecifications=[{'ResourceType': 'instance',
                                'Tags': [{'Key': 'Prod',
                                          'Value': prod},
                                         {'Key': 'User',
                                          'Value': user},
                                         {'Key': 'Name',
                                          'Value': name}]}],
            IamInstanceProfile={"Name": IamInstanceProfile},
            MinCount=1,
            MaxCount=1,
            InstanceType=instancetype,
            KeyName=key,
            SecurityGroups=[SecurityGroup],
            InstanceInitiatedShutdownBehavior='terminate')[0]
    except:
        err = str(sys.exc_info()[1])
        if 'InvalidAMIID' in err:
            logger.error('AMI Id \'{0}\' does not exist in Region \'{1}\'.'.format(ami, region_name))
        logger.error('{0}'.format(err))
        sys.exit(0)
    instance.wait_until_running()
    instance.load()
    logger.info('Machine Details:\n\t\t\t  DNS: {0}.\n\t\t\t  IP: {1}.\n\t\t\t  Price: {2}$ per hour.'.format(instance.public_dns_name, instance.public_ip_address, 'instanceprice'))
    return instance.public_dns_name


def start_spot_instance(instancetype, ami,user, key, name, logger, region, IamInstanceProfile, SecurityGroup,  prod='True'):
    client = aws_client(resource=False, region_name=region)
    region_name = convert_region_name(region=region, logger=logger)
    AvailabilityZone = '{0}{1}'.format(region, zone)
    LaunchSpecifications = {
        "ImageId": ami,
        "IamInstanceProfile": {"Name": IamInstanceProfile},
        "InstanceType": instancetype,
        "KeyName": key,
        "SecurityGroups": [SecurityGroup],
        "Placement": {"AvailabilityZone": AvailabilityZone}}
    SpotPrice = get_spot_price(type=instancetype, region=region, logger=logger)
    try:
        logger.info('Request Details:\n\t\t\t  Region: {0}.\n\t\t\t  Type: {1}.\n\t\t\t  Price: {2}$ per hour.'.format(region_name, instancetype, SpotPrice))
        spot_instance = client.request_spot_instances(
            SpotPrice=SpotPrice,
            Type="one-time",
            InstanceCount=1,
            LaunchSpecification=LaunchSpecifications)
    except:
        err = str(sys.exc_info()[1])
        if 'InvalidAMIID' in err:
            logger.error('AMI Id \'{0}\' does not exist in Region \'{1}\'.'.format(ami, region_name))
        elif 'Invalid availability zone' in err: # todo: auto fix zone
            logger.error('Invalid availability zone: \'{0}\'.'.format(AvailabilityZone))
        logger.error('{0}'.format(err))
        sys.exit(0)

    SpotId = spot_instance["SpotInstanceRequests"][0]["SpotInstanceRequestId"]
    check_spot_status(client=client, SpotId=SpotId, region=region, logger=logger)
    client.create_tags(Resources=[SpotId], Tags=[{'Key': 'Prod',
                                                  'Value': prod},
                                                 {'Key': 'User',
                                                  'Value': user},
                                                 {'Key': 'Name',
                                                  'Value': name}])

    instance = aws_client(region_name=region).Instance(id=get_spot_info(SpotId, region=region)["InstanceId"])
    instance.create_tags(Tags=[{'Key': 'Prod',
                                'Value': prod},
                               {'Key': 'User',
                                'Value': user},
                               {'Key': 'Name',
                                'Value': name}])
    logger.process('Waiting for the machine to start running...')
    instance.wait_until_running()
    instance.load()
    logger.success('Machine Details:\n\t\t\t  DNS: {0}.\n\t\t\t  IP: {1}.\n\t\t\t  Price: {2}$ per hour.\n\t\t\t  SpotId: {3}.'.format(instance.public_dns_name, instance.public_ip_address, SpotPrice, SpotId))
    return instance.public_dns_name, SpotId



def inst(verbose, spot, key, region, ami, instancetype, SecurityGroup, IamInstanceProfile, name, prod,user='User'):

    """Creating a regular\spot instance on AWS and run commands.
    """
    # TODO: Handle error when instance creation failed.
    logger = setup_logger(verbose=verbose)

    if "True" in spot:
        logger.info('Starting spot instance...')
        _ = start_spot_instance(user=user, instancetype=instancetype, IamInstanceProfile=IamInstanceProfile, SecurityGroup=SecurityGroup, ami=ami, key=key,  region=region, logger=logger, prod=prod, name=name)
    elif "False" in spot:
        logger.info('Startint regular instance...')
        _ = start_instance(user=user, instancetype=instancetype, ami=ami, key=key, IamInstanceProfile=IamInstanceProfile, SecurityGroup=SecurityGroup, region=region, logger=logger, prod=prod, name=name)