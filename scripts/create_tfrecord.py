"""
Usage:
  # From tensorflow/models/
  # Create train data:
  python create_tfrecord.py --csv_input=data/train_labels.csv  --output_path=train.record
  # Create test data:
  python create_tfrecord.py --csv_input=data/test_labels.csv  --output_path=test.record
"""
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

import argparse

import os
import io
import pandas as pd
import tensorflow as tf

from PIL import Image
import sys
sys.path.append('../')
from object_detection.utils import dataset_util
from collections import namedtuple, OrderedDict
from object_detection.utils import label_map_util
from collections import namedtuple, OrderedDict

def class_text_to_int(label_dict, row_label):
    return label_dict.get(row_label, 0)

from sklearn.model_selection import train_test_split

def split2(df, group):
    data = namedtuple('data', ['filename', 'object'])
    gb = df.groupby(group)
    filenames = list(gb.groups.keys())
    groups = list(gb.groups.values())
    train_filenames, test_filenames, train_groups, test_groups = train_test_split(filenames, groups, test_size=0.3, random_state=42)
    train_data = [data(filename, gb.get_group(x)) for filename, x in zip(train_filenames, train_groups)]
    test_data = [data(filename, gb.get_group(x)) for filename, x in zip(test_filenames, test_groups)]
    return train_data, test_data

def split(df, group):
    data = namedtuple('data', ['filename', 'object'])
    gb = df.groupby(group)
    return [data(filename, gb.get_group(x)) for filename, x in zip(gb.groups.keys(), gb.groups)]


def create_tf_example(group, path, label_dict):
    with tf.io.gfile.GFile(os.path.join(path, '{}'.format(group.filename)), 'rb') as fid:
        encoded_jpg = fid.read()
    encoded_jpg_io = io.BytesIO(encoded_jpg)
    image = Image.open(encoded_jpg_io)
    width, height = image.size

    filename = group.filename.encode('utf8')
    image_format = b'jpg'
    xmins = []
    xmaxs = []
    ymins = []
    ymaxs = []
    classes_text = []
    classes = []

    for index, row in group.object.iterrows():
        xmins.append(row['xmin'] / width)
        xmaxs.append(row['xmax'] / width)
        ymins.append(row['ymin'] / height)
        ymaxs.append(row['ymax'] / height)
        classes_text.append(row['class'].encode('utf8'))
        classes.append(class_text_to_int(label_dict, row['class']))

    tf_example = tf.train.Example(features=tf.train.Features(feature={
        'image/height': dataset_util.int64_feature(height),
        'image/width': dataset_util.int64_feature(width),
        'image/filename': dataset_util.bytes_feature(filename),
        'image/source_id': dataset_util.bytes_feature(filename),
        'image/encoded': dataset_util.bytes_feature(encoded_jpg),
        'image/format': dataset_util.bytes_feature(image_format),
        'image/object/bbox/xmin': dataset_util.float_list_feature(xmins),
        'image/object/bbox/xmax': dataset_util.float_list_feature(xmaxs),
        'image/object/bbox/ymin': dataset_util.float_list_feature(ymins),
        'image/object/bbox/ymax': dataset_util.float_list_feature(ymaxs),
        'image/object/class/text': dataset_util.bytes_list_feature(classes_text),
        'image/object/class/label': dataset_util.int64_list_feature(classes),
    }))
    return tf_example

if __name__ == '__main__':

    parser = argparse.ArgumentParser(description='Process an json file and convert to png.')
    parser.add_argument('--output_name', '-o', type=str, default="train.record", required=False, help='Provide out folder elative to input image folder.')
    parser.add_argument('--csv_input', '-c', type=str, required=False, default="info.csv", help='Provide a csv file name.')
    parser.add_argument('--image_dir', '-i', type=str, required=True, help='Provide image folder.')
    parser.add_argument('--label_map', '-l', type=str, default="label_map.pbtxt", help='Provide label map.')
    args = parser.parse_args()

    output_path = os.path.join(args.image_dir, args.output_name)
    label_map_path = os.path.join(args.image_dir, args.label_map)
    csv_path = os.path.join(args.image_dir, args.csv_input)
    writer = tf.io.TFRecordWriter(output_path)
    examples = pd.read_csv(csv_path)
    grouped = split(examples, 'filename')
    label_dict = label_map_util.get_label_map_dict(label_map_path)

    for group in grouped:
        tf_example = create_tf_example(group, args.image_dir, label_dict)
        writer.write(tf_example.SerializeToString())

    writer.close()
    print('Successfully created the TFRecords: {}'.format(output_path))


