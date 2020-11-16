
UBUNTU_filters = [ {
        'Name': 'name',
        'Values': ['ubuntu/images/*']
    },{
        'Name': 'description',
        'Values': ['* Ubuntu* LTS*']
    },{
        'Name': 'architecture',
        'Values': ['x86_64']
    },{
        'Name': 'owner-id',
        'Values': ['099720109477']
    },{
        'Name': 'state',
        'Values': ['available']
    }]

SUSE_filters = [ {
        'Name': 'name',
        'Values': ['suse*']
    },{
        'Name': 'description',
        'Values': ['SUSE Linux Enterprise*']
    },{
        'Name': 'architecture',
        'Values': ['x86_64']
    },{
        'Name': 'owner-id',
        'Values': ['013907871322']
    },{
        'Name': 'state',
        'Values': ['available']
    }]

WIN_filters = [{
    'Name': 'name',
    'Values': ['Windows_Server*']
}, {
    'Name': 'description',
    'Values': ['Microsoft Windows*']
}, {
    'Name': 'architecture',
    'Values': ['x86_64']
}, {
    'Name': 'owner-id',
    'Values': ['801119661308']
}, {
    'Name': 'state',
    'Values': ['available']
}]
AWS_filters = [{
    'Name': 'name',
    'Values': ['amzn2-ami-hvm*']
}, {
    'Name': 'description',
    'Values': ['Amazon Linux*']
}, {
    'Name': 'architecture',
    'Values': ['x86_64']
}, {
    'Name': 'owner-id',
    'Values': ['137112412989']
}, {
    'Name': 'state',
    'Values': ['available']
}]

RHEL_filters = [{
    'Name': 'name',
    'Values': ['RHEL*']
}, {
    'Name': 'description',
    'Values': ['Provided by Red Hat*']
}, {
    'Name': 'architecture',
    'Values': ['x86_64']
}, {
    'Name': 'owner-id',
    'Values': ['309956199498']
}, {
    'Name': 'state',
    'Values': ['available']
}]

