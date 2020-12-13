#!/usr/bin/env python3

import os
import sys
import pandas as pd
import csv
import argparse

###########################################################
# Add package path
###########################################################
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), 'util')))

import load_data, util
from datetime import timedelta


def main(raw_data_path, recovery_data_path, subject_data_path):
    ###########################################################
    # 1.1 Read subject data
    ###########################################################
    subject_df = load_data.read_subject_data(subject_data_path)

    ###########################################################
    # 1.1 Read recovery report
    ###########################################################
    participant_info_df = pd.read_csv(os.path.join(recovery_data_path, 'USC_Mind_Body_Study-recovery_user-Lifetime.csv'))
    unique_ids = list(set(subject_df.index))
    unique_ids.sort()

    util.make_output_data_dir(os.path.join(os.getcwd(), '..'))
    save_tmp_root_path = os.path.join(os.getcwd(), '..', 'data', 'raw_data', 'tmp')

    ###########################################################
    # 1.2 Iterate all participant
    ###########################################################
    for id in unique_ids[:1]:

        # get user information
        user_df = participant_info_df.loc[participant_info_df['First Name'] == int(id)]

        # get device information
        device_ids = list(set(user_df['User ID']))
        last_name_ids = list(set(user_df['Last Name']))
        if len(device_ids) == 0 or len(last_name_ids) == 0:
            continue

        # Special case
        last_name_id = last_name_ids[0]
        last_name_id = util.return_last_name_id(last_name_id, id)
        print('process %s' % (str(id) + str(last_name_id)))

        # get possible start and end time range
        start_date = (pd.to_datetime(subject_df.loc[id, 'start_date']) - timedelta(days=7)).strftime(util.date_time_format)[:-3]
        end_date = (pd.to_datetime(subject_df.loc[id, 'end_date']) + timedelta(days=7)).strftime(util.date_time_format)[:-3]

        # Read raw data for a participant
        raw_df = load_data.read_raw_data(raw_data_path, device_ids, start_date, end_date)

        # write data
        with open(os.path.join(save_tmp_root_path, str(id) + str(last_name_id) + '.csv'), 'w', encoding='utf8') as csv_output:
            csv_writer = csv.writer(csv_output, delimiter=',')
            csv_writer.writerow(["timestamp", "heart_rate", 'acc_x', 'acc_y', 'acc_z', 'acc_mag', 'rr'])

            # process this data as small segments
            for i, data_time in enumerate(list(raw_df.index)):

                tmp_row_df = raw_df.iloc[i, :]
                time_str = util.read_iso_timestr(data_time)

                if time_str != '':
                    # write row data
                    csv_writer.writerow([time_str, tmp_row_df['Heartrate'],
                                         tmp_row_df['Acc X'], tmp_row_df['Acc Y'], tmp_row_df['Acc Z'],
                                         tmp_row_df['Acc Mag'], tmp_row_df['RRs']])
                    if i % 1000 == 0:
                        print('process %s, %s at %.2f %%' % (str(id) + str(last_name_id), time_str, i / len(raw_df) * 100))

        os.system('gzip ' + os.path.join(save_tmp_root_path, str(id) + str(last_name_id) + '.csv'))


if __name__ == "__main__":
    # read input args
    parser = argparse.ArgumentParser()
    parser.add_argument("--data_path", required=False, help="Path to the root folder containing Whoop data")
    args = parser.parse_args()

    data_path = os.path.join('/Users/tiantian/University of Southern California/Shai Porat - Whoop_Uploads') if args.data_path is None else args.data_path

    # configure raw data path, recovery report path, and subject_data path
    raw_data_path = os.path.join(data_path, 'Raw Data')
    recovery_data_path = os.path.join(data_path, 'Recovery Reports')
    subject_data_path = os.path.join('subject_data')

    main(raw_data_path, recovery_data_path, subject_data_path)
