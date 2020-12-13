#!/usr/bin/env python3

import os
import sys
import pandas as pd
from pathlib import Path

###########################################################
# Add package path
###########################################################
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), 'util')))

import load_data, util


def main(subject_data_path):
    ###########################################################
    # 1.1 Read subject data
    ###########################################################
    subject_df = load_data.read_subject_data(subject_data_path)
    unique_ids = list(subject_df.index)
    unique_ids.sort()

    ###########################################################
    # 1.1 save data paths
    ###########################################################
    util.make_output_data_dir(Path.cwd().parent)
    csv_data_path = Path.cwd().parent.joinpath('data', 'raw_data', 'csv')
    tsv_data_path = Path.cwd().parent.joinpath('data', 'raw_data', 'tsv')
    tmp_data_path = Path.cwd().parent.joinpath('data', 'raw_data', 'tmp')

    ###########################################################
    # 1.2 Iterate all participant
    ###########################################################
    for id in unique_ids[:]:

        for file in tmp_data_path.iterdir():
            if str(id) not in file.stem:
                continue

            data_df = pd.read_csv(Path(file))
            data_df = data_df.sort_values(by='timestamp')

            start_date = subject_df.loc[id, 'start_date']
            end_date = subject_df.loc[id, 'end_date']
            intervention_date = subject_df.loc[id, 'intervention']

            if len(str(intervention_date)) < 5:
                print('no intervention data for %s' % (file.parts[-1]))
                continue

            print('save data for %s' % (file.parts[-1]))
            pre_data_df = data_df[data_df['timestamp'].between(start_date, intervention_date, inclusive=False)]
            post_data_df = data_df[data_df['timestamp'].between(intervention_date, end_date, inclusive=False)]

            pre_str = file.parts[-1].split('.')[0] + '_pre'
            post_str = file.parts[-1].split('.')[0] + '_post'

            # save pre intervention data
            pre_data_df.to_csv(csv_data_path.joinpath(pre_str+'.csv.gz'), sep=',', compression='gzip', index=False)
            pre_data_df.to_csv(tsv_data_path.joinpath(pre_str+'.tsv.gz'), sep='\t', compression='gzip', index=False)

            # save post intervention data
            post_data_df.to_csv(csv_data_path.joinpath(post_str+'.csv.gz'), sep=',', compression='gzip', index=False)
            post_data_df.to_csv(tsv_data_path.joinpath(post_str+'.tsv.gz'), sep='\t', compression='gzip', index=False)


if __name__ == "__main__":
    subject_data_path = Path('subject_data')
    main(subject_data_path)
