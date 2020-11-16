import pickle
import time
from Main import *

import timeit


def AMI_details_run_thread():
    t = threading.Thread(target=AMI_details_i, args=tuple())
    t.start()
    print("AMI_details_run_thread started")


def get_s3_bucket_names_run_thread():
    t = threading.Thread(target=get_s3_bucket_names_i, args=tuple())
    t.start()
    print("get_s3_bucket_names_run_thread started")


def get_all_EC2_types_run_thread():
    l1 = ['linux']
    l2 = ['windows']
    t_linux = threading.Thread(target=get_all_EC2_types_i, args=l1)
    t_linux.start()
    t_windows = threading.Thread(target=get_all_EC2_types_i, args=l2)
    t_windows.start()
    print("get_all_EC2_types_run_thread started")


def get_instance_profiles_names_run_thread():
    t = threading.Thread(target=get_instance_profiles_names_i, args=tuple())
    t.start()
    print("get_instance_profiles_names_run_thread started")


def get_all_SG_run_thread():
    t = threading.Thread(target=get_all_SG_i, args=tuple())
    t.start()
    print("get_all_SG_run_thread started")


def get_keypairs_details_run_thread():
    t = threading.Thread(target=get_keypairs_details_i, args=tuple())
    t.start()
    print("get_keypairs_details_run_thread started")


def get_keypairs_details_i(site="eu-central-1", interval=5 * 60, filename="get_keypairs_details"):
    while True:
        try:
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

                with open(filename, 'wb') as f:
                    pickle.dump(keypairs, f)

        except Exception as e:
            print("get_all_SG_i Exception %s" % e)

        time.sleep(interval)


def get_all_SG_i(site="eu-central-1", interval=5 * 60, filename="get_all_SG"):
    while True:
        try:
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

            with open(filename, 'wb') as f:
                pickle.dump(all_SG_details, f)

        except Exception as e:
            print("get_all_SG_i Exception %s" % e)

        time.sleep(interval)


def get_instance_profiles_names_i(site="eu-central-1", interval=5 * 60, filename="get_instance_profiles_names"):
    while True:
        try:
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
            with open(filename, 'wb') as f:
                pickle.dump(instance_profiles, f)

        except Exception as e:
            print("get_s3_bucket_names_i Exception %s" % e)

        time.sleep(interval)


def get_s3_bucket_names_i(site="eu-central-1", interval=5 * 60, filename="get_s3_bucket_names"):
    while True:
        try:
            buckets = {}
            counter = 1
            client = aws_client(region_name=site, aws_service="s3")
            for bucket in client.buckets.all():
                bucket_info = {}
                bucket_info['Name'] = bucket.name
                bucket_info['Site'] = site
                buckets[counter] = bucket_info
                counter += 1

            with open(filename, 'wb') as f:
                pickle.dump(buckets, f)

        except Exception as e:
            print("get_s3_bucket_names_i Exception %s" % e)

        time.sleep(interval)


def AMI_details_i(interval=5 * 60, filename="AMI_details"):
    print("AMI_details_i started")
    while True:
        try:
            all_images = get_all_images_details('eu-central-1')
            with open(filename, 'wb') as f:
                pickle.dump(all_images, f)

        except Exception as e:
            print("AMI_details Exception %s" % e)

        time.sleep(interval)


def get_name_priority(name):
    name_priorities = ["t2", "t3", "t3a", "g3", "g4d", "g4dn", "m5", "m5a", "m5n", "m5d", "m5dn", "m5ad", "m6g", "m4",
                       "c5", "c5a", "c5n", "c5d", "c6g"]
    priority = 0
    for n in name_priorities:
        if name.startswith(n):
            return priority
        priority+=1
    print("error: not a known name: %s"% name)
    return len(name_priorities)+1


def sort_by_name(all_EC2_types_dicts_lists):
    sorted_list = sorted(all_EC2_types_dicts_lists, key=lambda x: get_name_priority(x['Name']))
    return sorted_list


def get_all_EC2_types_i(os, site="eu-central-1", all=False, interval=5 * 60, filename="get_all_EC2_types"):
    print("get_all_EC2_types_i started")
    print(os)
    while True:
        try:
            all_EC2_types_dicts_lists = []
            all_EC2_types_details = {}
            region_name = create_region_name(site)
            client = aws_client(resource=False, region_name=site, aws_service="ec2")
            if all:
                InstanceTypes = client.describe_instance_types()
            else:
                ec2_type_base = ['t*', 'c5*', 'c6*', 'm*', 'g3*', 'g4*']
                InstanceTypes = client.describe_instance_types(Filters=[{"Name": "instance-type",
                                                                         "Values": ec2_type_base}])
            print("InstanceTypes %s" % len(InstanceTypes))
            lists_of_args = [[os, site, instance, region_name] for instance in InstanceTypes['InstanceTypes']]
            try:
                all_EC2_types_dicts_lists = run_func_in_threads_pool(extract_EC2_types_details, lists_of_args)
                for c, EC2_types_dicts_list in enumerate(all_EC2_types_dicts_lists):
                    all_EC2_types_details[str(c)] = EC2_types_dicts_list
            except Exception as e:
                print("1 %s" % e)

            try:
                t2nano_p = truncate(float(get_EC2_types_price(region=site, instance='t2.nano',
                                                              operationsystem=os)), 4)
                t2micro_p = truncate(float(get_EC2_types_price(region=site, instance='t2.micro',
                                                               operationsystem=os)), 4)
                t2small_p = truncate(float(get_EC2_types_price(region=site, instance='t2.small',
                                                               operationsystem=os)), 4)
                t2medium_p = truncate(float(get_EC2_types_price(region=site, instance='t2.medium',
                                                                operationsystem=os)), 4)
            except Exception as e:
                print("2 %s" % e)

            try:
                add_minor_ec2_type = [{'Region': region_name, 'Site': site, 'Name': 't2.nano', 'Price': t2nano_p,
                                       'NetworkPerformance': 'Low to Moderate', 'CPUCore': 1, 'Memory': 0.5},
                                      {'Region': region_name, 'Site': site, 'Name': 't2.micro', 'Price': t2micro_p,
                                       'NetworkPerformance': 'Low to Moderate', 'CPUCore': 1, 'Memory': 1.0},
                                      {'Region': region_name, 'Site': site, 'Name': 't2.small', 'Price': t2small_p,
                                       'NetworkPerformance': 'Low to Moderate', 'CPUCore': 1, 'Memory': 2.0},
                                      {'Region': region_name, 'Site': site, 'Name': 't2.medium', 'Price': t2medium_p,
                                       'NetworkPerformance': 'Low to Moderate', 'CPUCore': 2, 'Memory': 4.0}]
                all_EC2_types_dicts_lists.extend(add_minor_ec2_type)
                print("all_EC2_types_dicts_list")
                # sorted()
                # print(all_EC2_types_dicts_list)

                all_EC2_types_details = {}
                all_EC2_types_dicts_lists = sort_by_name(all_EC2_types_dicts_lists)
                for c, sec_group_details in enumerate(all_EC2_types_dicts_lists):
                    print(c)
                    all_EC2_types_details[str(c)] = sec_group_details
                print("all_EC2_types_details")

                with open("%s_%s" % (os, filename), 'wb') as f:
                    pickle.dump(all_EC2_types_details, f)

            except Exception as e:
                print("get_all_EC2_types Exception %s" % e)

        except Exception as e:
            print("3 %s" % e)

        time.sleep(interval)


AMI_details_run_thread()
get_all_EC2_types_run_thread()
get_s3_bucket_names_run_thread()
get_instance_profiles_names_run_thread()
get_all_SG_run_thread()
get_keypairs_details_run_thread()
