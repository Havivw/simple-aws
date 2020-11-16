import os
import pickle
import re
import json
import queue
import threading
from dateutil import parser
from multiprocessing.pool import ThreadPool

import boto3
from botocore.exceptions import ClientError

try:
    from .utils import *
except:
    from utils import *

try:
    from .Vars import *
except:
    from Vars import *


def get_thread_queue(thread_func, list_of_args=None):
    '''
    return the thread object and the result queue. to retrieve the result call t.join() and queue_res.get()
    thread_func should get a queue obj as a last parameter and add result to queue instead of return it
    '''
    queue_res = queue.Queue()
    list_of_args.append(queue_res)
    t = threading.Thread(target=thread_func, args=tuple(list_of_args))
    t.start()
    return t, queue_res

def run_func_in_threads_pool(func, args_lists):
    '''
    for each arg_list in args_lists opens a thread for func(*arg_list)
    return list of results
    '''
    pool = ThreadPool()
    threads_list = []
    for args_tup in args_lists:
        args_tup = tuple(args_tup)
        threads_list.append(pool.apply_async(func, args_tup))
    l = [t.get() for t in threads_list]
    return l


def aws_client(resource=True, region_name="eu-west-1", aws_service="ec2"):
    session = boto3.Session()
    if resource:
        return session.resource(aws_service, region_name=region_name)
    else:
        return session.client(aws_service, region_name=region_name)


def get_all_regions():
    region_list = []
    response = aws_client(resource=False).describe_regions()['Regions']
    for region in response:
        region_api_id = region['Endpoint'].split('.')[1]
        region_list.append(region_api_id)
    return region_list


def convert_region_name(region_endpoint):
    return aws_client(resource=False, aws_service="ssm").get_parameter(
        Name=f'/aws/service/global-infrastructure/regions/{region_endpoint}/longName')['Parameter']['Value']


def fetch_instances(instance_state, region, queue=None):
    client = aws_client(region_name=region).instances.filter(
        Filters=[{'Name': 'instance-state-name', 'Values': instance_state}])
    if queue:
        queue.put(client)
    return client


def create_region_name(ec2_site, queue=None):
    region_name = convert_region_name(ec2_site)
    site_city = find_string_between_strings(string=region_name, first='(', last=')')
    region = f"{site_city} ({ec2_site})"
    if queue:
        queue.put(region)
    return region


def count_instances(instances_state=["running", "stopped"], region=False):
    region_list = []
    if region:
        region_list.append(region)
    else:
        all_regions = get_all_regions()
        for region in all_regions:
            try:
                region_list.append(region)
            except ClientError:
                print(f"Skipping region: {region}")
    all_instances = {}
    threads_dict_names = {}
    threads_dict_instances = {}

    # start threads
    for region in region_list:
        threads_dict_names[region] = get_thread_queue(create_region_name, [region])
        threads_dict_instances[region] = get_thread_queue(fetch_instances, [instances_state, region])

    # get results from the threads
    for region in region_list:

        # get region name
        thread_for_name, name_queue = threads_dict_names[region]
        thread_for_name.join()
        region_name = name_queue.get()

        # get region instances
        thread_for_instances, instances_queue = threads_dict_instances[region]
        thread_for_instances.join()
        instances = instances_queue.get()

        if list(instances):
            all_instances[region_name] = len(list(instances))
    return all_instances


def create_instance_dict(instance, site):
    # print("%s create_instance_dict start" % site)
    instance_dict = {}
    tags = []
    instance_dict['ID'] = instance.id
    instance_dict['site'] = site
    instance_dict['State'] = instance.state['Name']
    if instance.instance_lifecycle:
        instance_dict['Spot'] = "Spot"
    else:
        instance_dict['Spot'] = "On-Demand"
    instance_dict['Type'] = instance.instance_type
    ip_address = nslookup(instance.public_dns_name)
    instance_dict['PublicIP'] = ip_address
    instance_dict['CreationDate'] = str(instance.launch_time)
    try:
        for tag in instance.tags:
            if tag['Key'] == 'Name':
                instance_dict['Name'] = tag['Value']
            else:
                tags.append(tag)
    except:
        tags = ''
    if isinstance(tags, list):
        stags = ''
        for tag in tags:
            stags += f"{tag['Key']}: {tag['Value']}, "
        stags = stags[:-2]
        tags = stags
    instance_dict['Tags'] = tags
    # print("%s create_instance_dict end" % site)#
    return instance_dict


def handle_site_instances(instances_state, site, q=None):
    try:
        # print(site) # todo:del
        # start thread for region_name
        region_name_thread, region_name_queue = get_thread_queue(create_region_name, [site])

        # get instances
        instances_list = []
        instances = fetch_instances(instances_state, site)
        if list(instances):
            # print("thread %s: instances %s" % (site, instances))
            lists_of_args = [[instance, site] for instance in instances]
            instance_dicts = run_func_in_threads_pool(create_instance_dict, lists_of_args)
            # print("thread %s: instance_dicts %s" % (site, instance_dicts))

            # get region_name
            region_name_thread.join()
            region_name = region_name_queue.get()
            # print("thread %s: region_name %s" % (site, region_name))

            # update dicts
            for instance_dict in instance_dicts:
                instance_dict['region'] = region_name
                instances_list.append(instance_dict)

            if q:
                q.put((region_name, instances_list))
                # print((region_name, instances_list))
                with open("%s_%s.txt" % (instances_state, site), "wb") as f:
                    pickle.dump((region_name, instances_list), f)
            else:
                return region_name, instances_list
        else:
            if q:
                q.put((None,None))
    except Exception as e:
        print(e)


def get_instances(instances_state=["running", "stopped", "terminated", "pending", "shutting-down"], site=False):
    region_list = []
    if site:
        region_list.append(site)
    else:
        for region in get_all_regions():
            try:
                region_list.append(region)
            except ClientError:
                print(f"Skipping region: {site}")
    all_instances = {}
    sites_threads = []
    for site in region_list:
        # file_name = "%s_%s.txt" % (instances_state,site)
        # if os.path.exists(file_name):
        #     with open(file_name,"rb") as f:
        #         region_name, instances_list = pickle.load(f)
        #     all_instances[region_name] = instances_list
        # else:
        sites_threads.append(get_thread_queue(handle_site_instances, list_of_args=[instances_state, site]))
    for thread, q in sites_threads:
        thread.join(timeout=1)
        region_name, instances_list = q.get()
        if region_name and instances_list:
            all_instances[region_name] = instances_list
    return all_instances


def update_tags(instance, tags_list, region):
    aws_client(region_name=region).create_tags(Resources=[instance], Tags=tags_list)


def start_instnace(instance, region):
    print(f'Starting instance: {instance}')
    aws_client(region_name=region).instances.filter(InstanceIds=[instance]).start()


def stop_instnace(instance, region):
    print(f'Stopping instance: {instance}')
    aws_client(region_name=region).instances.filter(InstanceIds=[instance]).stop()


def terminate_instnace(instance, region):
    print(f'Terminating instance: {instance}')
    aws_client(region_name=region).instances.filter(InstanceIds=[instance]).terminate()


def get_bill(year, month, last_day_in_month):
    client = aws_client(resource=False, region_name='us-east-1', aws_service='ce')
    if len(str(month)) < 2:
        month = f'0{month}'
    response = client.get_cost_and_usage(TimePeriod={'Start': f'{year}-{month}-01',
                                                     'End': f'{year}-{month}-{last_day_in_month}'},
                                         Granularity='MONTHLY', Metrics=['AmortizedCost'])
    cost = response['ResultsByTime'][0]['Total']['AmortizedCost']['Amount']
    cost = truncate(float(cost), 2)
    date = f'{month}/{year}'
    bill = f'{cost} $'
    return date, bill


def get_bill_by_month(current_month=True, queue=None):
    year, month, last_day_in_month = get_current_date(current=current_month)
    date, bill = get_bill(year=year, month=month, last_day_in_month=last_day_in_month)
    if queue:
        queue.put((date, bill))
    return date, bill


def pretty_default_ami_name(name, description):
    if 'Ubuntu' in description:
        version = re.search('[0-9]{2}\.[0-9]{2}\sLTS', str(description)).group()
        Name = f'Ubuntu {version}'
    elif 'SUSE' in description:
        Name = re.search('SUSE Linux Enterprise Server\s[0-9][0-9]\s?[S]?[P]?[0-9]{0,4}', str(description)).group()
        Name = Name.replace(' Linux ', ' ')
    elif 'Microsoft' in description:
        Name = re.search('Microsoft Windows Server\s[0-9]{0,4}', str(description)).group()
    elif 'Amazon' in description:
        Name = re.search('Amazon Linux\s[0-9]{0,4}', str(description)).group()
    elif 'RHEL' in name:
        Name = re.search('RHEL[-_\.][0-9]\.[0-9]', str(name)).group()
        Name = Name.replace('RHEL-', 'Red Hat Enterprise ')
    else:
        Name = name
    return Name


def extract_image_details(counter, site, image, all_images_details, threaded=False, public=False):
    counter = int(counter)
    image_details = {}
    image_details['Architecture'] = image['Architecture']
    image_details['Region'] = create_region_name(site)
    image_details['Site'] = site
    image_details['ImageId'] = image['ImageId']
    image_details['PlatformDetails'] = image['PlatformDetails']
    try:
        image_details['Description'] = image['Description']
    except:
        image_details['Description'] = ''
    try:
        image_details['Name'] = image['Name']
        if public:
            image_details['Public'] = 'True'
            image_details['Name'] = pretty_default_ami_name(image['Name'], image['Description'])
        else:
            image_details['Public'] = 'False'
    except:
        image_details['Name'] = ''

    if threaded:
        return image_details
    counter += 1
    all_images_details[str(counter)] = image_details
    return all_images_details, counter


def get_images_details(site, counter, all_images_details):
    client = aws_client(resource=False, region_name=site, aws_service="ec2")
    images = client.describe_images(Owners=['self'])

    # open thread for each image
    lists_of_args = [[counter, site, image, all_images_details, True, False] for image in images['Images']]
    images_dicts_list = run_func_in_threads_pool(extract_image_details, lists_of_args)
    for i, image_details in enumerate(images_dicts_list):
        all_images_details[str(counter + i)] = image_details
    return all_images_details


def newest_image(list_of_images):
    latest = None
    for image in list_of_images:
        if not latest:
            latest = image
            continue
        if parser.parse(image['CreationDate']) > parser.parse(latest['CreationDate']):
            latest = image
    return latest


def get_latest_image_details(site, aws_filter):  # Take_Time
    # todo: maybe create a shared pool of aws_clients? creating them once and save them of re-use?
    client = aws_client(resource=False, region_name=site, aws_service="ec2")
    response = client.describe_images(Owners=[], Filters=aws_filter)
    return (newest_image(response['Images']))


def get_latest_image_details_for_filter(site, all_images_details, filter):
    UBUNTU_AMI = get_latest_image_details(site, aws_filter=filter)
    image_details = extract_image_details(0, site, UBUNTU_AMI, all_images_details, threaded=True, public=True)
    return image_details


def get_all_images_details(site):
    all_images_details = {}
    try:
        # open thread for each filter
        lists_of_args = [[site, all_images_details, filter_option] for filter_option in
                         [UBUNTU_filters, SUSE_filters, WIN_filters, AWS_filters, RHEL_filters]]
        image_details_list = run_func_in_threads_pool(get_latest_image_details_for_filter, lists_of_args)
        all_images_details = {}
        for i, image_details in enumerate(image_details_list):
            i += 1
            all_images_details[str(i)] = image_details

        all_images_details = get_images_details(site=site, counter=len(image_details_list) + 1,
                                                all_images_details=all_images_details)
        return all_images_details
    except Exception as e:
        print("get_all_images_details Exception %s" % e)


def get_keypairs_details(site="eu-central-1", que=None):
    keypairs = {}
    counter = 1
    client = aws_client(resource=False, region_name=site, aws_service="ec2")
    key_pairs = client.describe_key_pairs()
    for key in key_pairs['KeyPairs']:
        keypair_info = {}
        keypair_info['Name'] = key['KeyName']
        keypair_info['Site'] = site

        keypairs[counter] = keypair_info
        counter += 1
    if que:
        que.put(keypairs)
    else:
        return keypairs


def get_s3_bucket_names(site="eu-central-1", que=None):
    buckets = {}
    counter = 1
    client = aws_client(region_name=site, aws_service="s3")
    for bucket in client.buckets.all():
        bucket_info = {}
        bucket_info['Name'] = bucket.name
        bucket_info['Site'] = site

        buckets[counter] = bucket_info
        counter += 1
    if que:
        que.put(buckets)
    else:
        return buckets


def get_instance_profiles_names(site="eu-central-1", que=None):
    instance_profiles = {}
    counter = 1
    client = aws_client(resource=False, region_name=site, aws_service="iam")
    InstanceProfiles = client.list_instance_profiles()
    for profile in InstanceProfiles['InstanceProfiles']:
        profile_info = {}
        profile_info['Name'] = profile['InstanceProfileName']
        profile_info['Site'] = site

        instance_profiles[counter] = profile_info
        counter += 1
    if que:
        que.put(instance_profiles)
    else:
        return instance_profiles




def extract_SG_details(counter, site, sec_group, all_SG_details, threaded=False):
    counter = int(counter)
    # SG_counter = 0
    sec_group_details = {}
    # all_rules_details = {}
    sec_group_details['Region'] = create_region_name(site)
    sec_group_details['Site'] = site
    sec_group_details['GroupId'] = sec_group['GroupId']
    sec_group_details['Description'] = sec_group['Description']
    sec_group_details['Name'] = sec_group['GroupName']
    #
    # for rule in sec_group['IpPermissions']:
    #     if rule['FromPort']:
    #         if rule['FromPort'] == rule['ToPort']:
    #             ports = rule['FromPort']
    #         else:
    #             ports = f"{rule['FromPort']}-{rule['ToPort']}"
    #     else:
    #         port = '0-65535 (all)'
    #
    #     inbound_details = {}
    #     ips = rule['IpRanges']
    # sec_group_details['Inbound'] = ''
    # sec_group_details['Outbound'] = ''
    # all_rules_details[str(counter)] = sec_group_details
    if threaded:
        return sec_group_details
    all_SG_details[str(counter)] = sec_group_details
    counter += 1
    return all_SG_details, counter


def get_all_SG(site="eu-central-1", que=None):
    counter = 1
    all_SG_details = {}
    client = aws_client(resource=False, region_name=site, aws_service="ec2")
    security_groups = client.describe_security_groups(GroupIds=[])

    lists_of_args = [[counter, site, sec_group, all_SG_details, True] for sec_group in
                     security_groups['SecurityGroups']]
    sec_group_dicts_list = run_func_in_threads_pool(extract_SG_details, lists_of_args)

    all_SG_details = {}
    for counter, sec_group_details in enumerate(sec_group_dicts_list):
        all_SG_details[str(counter)] = sec_group_details

    if que:
        que.put(all_SG_details)
    else:
        return all_SG_details


def conv_MB_to_GB(input_megabyte):
    gigabyte = 1.0 / 1024
    convert_gb = gigabyte * input_megabyte
    return convert_gb


def get_EC2_types_price(instance, region, operationsystem):
    try:
        FLT = '[{{"Field": "tenancy", "Value": "shared", "Type": "TERM_MATCH"}},' \
              '{{"Field": "operatingSystem", "Value": "{o}", "Type": "TERM_MATCH"}},' \
              '{{"Field": "preInstalledSw", "Value": "NA", "Type": "TERM_MATCH"}},' \
              '{{"Field": "instanceType", "Value": "{t}", "Type": "TERM_MATCH"}},' \
              '{{"Field": "locationType", "Value": "AWS Region", "Type": "TERM_MATCH"}},' \
              '{{"Field": "capacitystatus", "Value": "Used", "Type": "TERM_MATCH"}}]'
        f = FLT.format(t=instance, o=operationsystem)
        data = aws_client(resource=False, aws_service='pricing',
                          region_name='us-east-1').get_products(
            ServiceCode='AmazonEC2', Filters=json.loads(f))
        od = json.loads(data['PriceList'][0])['terms']['OnDemand']
        id1 = list(od)[0]
        id2 = list(od[id1]['priceDimensions'])[0]
        price = od[id1]['priceDimensions'][id2]['pricePerUnit']['USD']
    except:
        price = 0.0
    return price

def extract_EC2_types_details(os, site, instance, region_name):
    try:
        sec_group_details = {}
        sec_group_details['Region'] = region_name
        sec_group_details['Site'] = site
        sec_group_details['Name'] = instance['InstanceType']
        sec_group_details['Price'] = truncate(
            float(get_EC2_types_price(region=site, instance=instance['InstanceType'],
                                      operationsystem=os)), 4)
        sec_group_details['NetworkPerformance'] = instance['NetworkInfo']['NetworkPerformance']
        try:
            sec_group_details['CPUCore'] = instance['VCpuInfo']['DefaultCores']
        except KeyError:
            sec_group_details['CPUCore'] = instance['VCpuInfo']['DefaultVCpus']

        sec_group_details['Memory'] = conv_MB_to_GB(int(instance['MemoryInfo']['SizeInMiB']))

        return sec_group_details
    except Exception as e:
        print("Exception in main extract_EC2_types_details %s"%e)


def get_all_EC2_types(os, site="eu-central-1", all=True, que=None):
    counter = 1
    all_EC2_types_details = {}
    region_name = create_region_name(site)
    client = aws_client(resource=False, region_name=site, aws_service="ec2")
    if all:
        InstanceTypes = client.describe_instance_types()
    else:
        ec2_type_base = ['t*', 'c5*', 'c6*', 'm*', 'g3*', 'g4*']
        InstanceTypes = client.describe_instance_types(Filters=[{"Name": "instance-type",
                                                                 "Values": ec2_type_base}])

    lists_of_args = [[os, counter, site, instance, region_name,
                      all_EC2_types_details, True] for instance in InstanceTypes['InstanceTypes']]
    all_EC2_types_dicts_list = run_func_in_threads_pool(extract_EC2_types_details, lists_of_args)
    t2nano_p = truncate(float(get_EC2_types_price(region=site, instance='t2.nano',
                                                  operationsystem=os)), 4)
    t2micro_p = truncate(float(get_EC2_types_price(region=site, instance='t2.micro',
                                                   operationsystem=os)), 4)
    t2small_p = truncate(float(get_EC2_types_price(region=site, instance='t2.small',
                                                   operationsystem=os)), 4)
    t2medium_p = truncate(float(get_EC2_types_price(region=site, instance='t2.medium',
                                                    operationsystem=os)), 4)


    add_minor_ec2_type = [{'Region': region_name, 'Site': site, 'Name': 't2.nano', 'Price': t2nano_p,
                           'NetworkPerformance': 'Low to Moderate', 'CPUCore': 1, 'Memory': 0.5},
                        {'Region': region_name, 'Site': site, 'Name': 't2.micro', 'Price': t2micro_p,
                         'NetworkPerformance': 'Low to Moderate', 'CPUCore': 1, 'Memory': 1.0},
                        {'Region': region_name, 'Site': site, 'Name': 't2.small', 'Price': t2small_p,
                         'NetworkPerformance': 'Low to Moderate', 'CPUCore': 1, 'Memory': 2.0},
                        {'Region': region_name, 'Site': site, 'Name': 't2.medium', 'Price': t2medium_p,
                         'NetworkPerformance': 'Low to Moderate', 'CPUCore': 2, 'Memory': 4.0}]
    all_EC2_types_dicts_list.extend(add_minor_ec2_type)
    # sorted()
    # print(all_EC2_types_dicts_list)

    all_EC2_types_details = {}
    for counter, sec_group_details in enumerate(all_EC2_types_dicts_list):
        all_EC2_types_details[str(counter)] = sec_group_details

    if que:
        que.put(all_EC2_types_details)
    else:
        return all_EC2_types_details
