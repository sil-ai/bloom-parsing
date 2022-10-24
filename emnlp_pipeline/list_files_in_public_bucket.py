import boto3

# CDL: just a quick script to see what files are in our bucket.

s3client = boto3.client("s3", region_name="us-east-1")
objects = s3client.list_objects(Bucket="bloom-vist")
for object in objects["Contents"]:
    print(object)

