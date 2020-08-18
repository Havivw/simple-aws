# AWSforDummies
​
AWS Simple is a web tool for basic action in your AWS account, Funny easy to use with MFA or without.

#### Prerequisites

Please install Docker if wanted
​
## AWSforDummies Installation
Download the AWSforDummies folder and install with pip.
​
```shell
$ sudo pip install -r requirement.txt
```
​
## Usage

### Docker use

#### Build
__Clone repo and build__
```
$ git clone https://github.com/Havivw/simple-aws.git
$ cd simple-aws
$ docker build . -t simple-aws`
```

#### Run
`docker run -d -e AWS_ACCESS_KEY_ID=<ACCESS_KEY> -e AWS_SECRET_ACCESS_KEY=<SECRET_KEY> -p 80:5000/tcp --restart on-failure simple-aws`

### without Docker with MFA
```shell
$ python3 app.py
```
### without Docker without MFA #TODO:test!
```shell
$ python3 app_no_mfa.py
```
​
## Additional Info
​
* Need to run with API Keys

#### Aws policies:
* The AWS account has to include that roles:
    * Crate an instance role that allows full access to your S3 buckets.
        * AmazonEC2FullAccess
        * IAMFullAccess
        * AmazonS3FullAccess
        * AmazonSSMReadOnlyAccess
        * AWSPriceListServiceFullAccess
 
#### Custom Policies:
  
PricingRoles (custom) 
  ```shell
  {
         "Version": "2012-10-17",
         "Statement": [
             {
                 "Sid": "VisualEditor0",
                 "Effect": "Allow",
                 "Action": [
                     "pricing:DescribeServices",
                     "pricing:GetAttributeValues",
                     "pricing:GetProducts"
                 ],
                 "Resource": "*"
             }
         ]
     }
  ```

AWSPriceListServiceFullAccess
  ```shell 
  {
           "Version": "2012-10-17",
           "Statement": [
               {
                   "Action": [
                       "pricing:*"
                   ],
                   "Effect": "Allow",
                   "Resource": "*"
               }
           ]
       }
   ```
   
​
## Supported 
​
 * Get Total and current bill (Today and last month) #authenticated user not neededr
 * Count active instance by Reigon #authenticated user not needed
 * Get instances details
 * Allow Stop, Start, Terminate actions
 * Create Spot or On-Demand machine from custom AMI or basic AMI 
 
  
## TODO
​
 * Change security Groups for Machine
 * Create New security Group
 * Get Windows Password
 * Add Instances Tag
 * Offline and once a day update price table (for decrease process time)

## Editinals Information
Remember PLEASE KEEP IT SIMPLE!
 
## Contributions..
​
..are always welcome.
