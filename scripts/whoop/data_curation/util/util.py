import pandas as pd
import os
import datetime
from time import strptime
import gzip
import csv
import pytz
from shutil import copyfile
from datetime import timedelta

date_time_format = '%Y-%m-%dT%H:%M:%S.%f'
date_format = '%Y-%m-%d'

pt = pytz.timezone('US/Pacific')
utc = pytz.timezone('UTC')


def return_last_name_id(last_name_id, id):
    if 'G' not in last_name_id:
        if '5' in id:
            last_name_id = 'G102'
        elif id == '6036':
            last_name_id = 'G116'
        else:
            last_name_id = 'G101'
    return last_name_id

def read_iso_timestr(date_data):
    if len(date_data) < 10:
        return ''
    time_str = date_data.split('.')[2].split(' ')[1]
    if len(time_str.split(':')) != 3:
        return ''

    # convert timestamp to ISO format
    day, month, year = int(date_data.split('.')[0]), int(date_data.split('.')[1]), int(date_data.split('.')[2].split(' ')[0])
    hour, minute, second = int(time_str.split(':')[0]), int(time_str.split(':')[1]), int(time_str.split(':')[2])
    time = pd.datetime(year=year, month=month, day=day, hour=hour, minute=minute, second=second)
    # time_str = utc.localize(time).astimezone(pt).strftime('%Y-%m-%dT%H:%M:%S')
    time_str = pd.to_datetime(time).tz_localize('UTC').tz_convert('US/Pacific').strftime('%Y-%m-%dT%H:%M:%S')

    return time_str

def read_csv(data_path):
    week_data_df = pd.read_csv(data_path, index_col=0)
    if 'Heartrate' not in list(week_data_df.columns):
        week_data_df.columns = ['Heartrate', 'Acc X', 'Acc Y', 'Acc Z', 'Acc Mag', 'RRs']
    if 'Timestamp' in list(week_data_df.index):
        week_data_df = week_data_df.drop(index=['Timestamp'])
    return week_data_df


def make_dir(data_path):
    if os.path.exists(data_path) is False:
        os.mkdir(data_path)


def make_output_data_dir(output_root_path):
    make_dir(os.path.join(output_root_path, 'data'))
    make_dir(os.path.join(output_root_path, 'data', 'raw_data'))
    make_dir(os.path.join(output_root_path, 'data', 'raw_data', 'csv'))
    make_dir(os.path.join(output_root_path, 'data', 'raw_data', 'tsv'))
    make_dir(os.path.join(output_root_path, 'data', 'raw_data', 'tmp'))


def check_recording_valid(data_month_folder, start_date, end_date):
    # read recording date for the folder
    month = strptime(data_month_folder.split(' ')[0][:3], '%b').tm_mon
    day = int(data_month_folder.split(' ')[1])
    year = int(data_month_folder.split(' ')[-1])

    record_end = datetime.datetime(year=year, month=month, day=day)
    record_start = record_end - timedelta(days=7)

    # make sure the recording is within the range
    cond1 = (pd.to_datetime(end_date) - record_end).total_seconds() > -3600 * 24 * 7
    cond2 = (record_start - pd.to_datetime(start_date)).total_seconds() > -3600 * 24 * 7

    return (cond1 and cond2)


def check_zip_file_valid(data_month_folder, start_date, end_date):
    # read recording date for the folder
    month = int(data_month_folder.split('_')[1])
    day = int(data_month_folder.split('_')[2])
    year = int(data_month_folder.split('_')[-1].split('.zip')[0])

    record_end = datetime.datetime(year=year, month=month, day=day)
    record_start = record_end - timedelta(days=7)

    # make sure the recording is within the range
    cond1 = (pd.to_datetime(end_date) - record_end).total_seconds() > -3600 * 24 * 14
    cond2 = (record_start - pd.to_datetime(start_date)).total_seconds() > -3600 * 24 * 14

    return (cond1 and cond2)


def check_tar_file_valid(tar_gz_file, start_date, end_date):
    record_start = pd.to_datetime(tar_gz_file.split('Z')[0])
    record_end = pd.to_datetime(tar_gz_file.split('to_')[-1].split('Z')[0])

    # make sure the recording is within the range
    cond1 = (pd.to_datetime(end_date) - record_end).total_seconds() > -3600 * 24 * 14
    cond2 = (record_start - pd.to_datetime(start_date)).total_seconds() > -3600 * 24 * 14

    return (cond1 and cond2)


def gunzip_tar_files(raw_data_path, tar_gz_file):
    copyfile(os.path.join(raw_data_path, tar_gz_file), os.path.join('tmp', tar_gz_file))
    make_dir(os.path.join('..', 'tmp', tar_gz_file.split('.tar.gz')[0]))
    os.system('tar -xzvf ' + os.path.join('..', 'tmp', tar_gz_file) + ' -C ' + os.path.join('..', 'tmp', tar_gz_file.split('.tar.gz')[0]))

    for tmp_file in os.listdir(os.path.join('..', 'tmp', tar_gz_file.split('.tar.gz')[0])):
        if 'DS' in tmp_file:
            continue

        src = os.path.join('..', 'tmp', tar_gz_file.split('.tar.gz')[0], tmp_file)
        dst = os.path.join('..', 'tmp', tar_gz_file.split('.tar.gz')[0], tmp_file.split('.gz')[0] + '.csv')

        with gzip.open(src, "rt") as f_in:
            lines = f_in.readlines()

            with open(dst, 'w') as csv_output:
                csv_writer = csv.writer(csv_output, delimiter=',')
                csv_writer.writerow(['Timestamp', 'Heartrate',
                                     'Acc X', 'Acc Y', 'Acc Z', 'Acc Mag', 'RRs'])

                for line in lines[1:-1]:
                    line_list = [data for data in line.split('[')[0].split(',')[:-1]]
                    last = '[' + line.split('[')[1].split(']')[0] + ']'
                    line_list.append(last)
                    csv_writer.writerow(line_list)
