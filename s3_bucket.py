#!/usr/bin/python
# -*- coding: utf-8 -*-
from json import loads, dump as json_dump
from os import path, environ

import boto3

obj_path = path.dirname(path.realpath(__file__)) + '/obj/'
s3_client = boto3.client('s3')
s3_resource = boto3.resource('s3')
s3_bucket = s3_resource.Bucket(environ['S3_BUCKET_NAME'])


def save_dict(obj, file_name):
    """Save dictionary to bucket"""
    print(f">> Uploading \"{file_name}\" to S3 bucket")
    try:
        with open(f"{obj_path}{file_name}.json", 'w') as f:
            json_dump(obj, f)
        s3_bucket.upload_file(f'{obj_path}{file_name}.json', f'{file_name}.json')
    except ValueError as e:
        print(f"Dictionary save failure in ObjectManagement::save_dict: {e}")


def load_dict(file_name):
    """Load dictionary from bucket"""
    print(f">> Downloading  \"{file_name}\" from S3 bucket")
    boto3.client('s3').download_file(environ['S3_BUCKET_NAME'], f'{file_name}.json', f'{obj_path}{file_name}.json')
    try:
        file_path = f"{obj_path}{file_name}.json"
        if path.getsize(file_path) > 0:
            with open(f"{obj_path}{file_name}.json", 'r') as file:
                return loads(file.read())
    except FileNotFoundError:
        print(f"Dictionary load fail for [{file_name}].")
    return {}
