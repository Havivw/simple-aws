## simple-aws

Web page to give you stats on your AWS account and basic functions

## Build
Clone repo and build.

```
$ git clone https://github.com/seekrets/simple-aws.git
$ cd simple-aws
$ docker build . -t simple-aws`
```

## Run
`docker run -d -e AWS_ACCESS_KEY_ID=<ACCESS_KEY> -e AWS_SECRET_ACCESS_KEY=<SECRET_KEY> -p 80:5000/tcp --restart on-failure simple-aws`

Now navigate to host IP and find the current and last totals under http://<IP>/bill
