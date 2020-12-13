import pandas as pd
import util
import os
from shutil import copyfile
from datetime import timedelta


def read_raw_data(raw_data_path, device_ids, start_date, end_date):
	raw_df = pd.DataFrame()

	for device_id in device_ids:
		# 1. read folder in 2018 folder
		data_month_folder_list = [folder for folder in os.listdir(os.path.join(raw_data_path, '2018')) if '.DS' not in folder]
		for data_month_folder in data_month_folder_list:

			for file in os.listdir(os.path.join(raw_data_path, '2018', data_month_folder)):
				if str(device_id) not in file or 'csv' not in file:
					continue

				if util.check_recording_valid(data_month_folder, start_date, end_date):
					week_data_df = util.read_csv(os.path.join(raw_data_path, '2018', data_month_folder, file))
					raw_df = raw_df.append(week_data_df)

		# 2. read folder in 2019 folder
		data_month_folder_list = ['February 4 2019', 'February 11 2019', 'February 18 2019', 'January 28 2019', 'March 20 2019']
		for data_month_folder in data_month_folder_list:

			for file in os.listdir(os.path.join(raw_data_path, data_month_folder)):
				if str(device_id) not in file or 'csv' not in file:
					continue
				if util.check_recording_valid(data_month_folder, start_date, end_date):
					week_data_df = util.read_csv(os.path.join(raw_data_path, data_month_folder, file))
					raw_df = raw_df.append(week_data_df)

		# 3. read tar.gz files
		tar_gz_list = [file for file in os.listdir(os.path.join(raw_data_path)) if '.tar.gz' in file]
		for tar_gz_file in tar_gz_list:

			if util.check_tar_file_valid(tar_gz_file, start_date, end_date) is False:
				continue
			if os.path.exists(os.path.join('..', 'tmp', tar_gz_file.split('.tar.gz')[0])) is False:
				util.gunzip_tar_files(raw_data_path, tar_gz_file)
			for file in os.listdir(os.path.join('..', 'tmp', tar_gz_file.split('.tar.gz')[0])):
				if '.csv' in file and str(device_id) in file:
					data_path = os.path.join('..', 'tmp', tar_gz_file.split('.tar.gz')[0], file)
					week_data_df = util.read_csv(data_path)
					raw_df = raw_df.append(week_data_df)

		# 4. read tar.gz files
		zip_list = [file for file in os.listdir(os.path.join(raw_data_path)) if '.zip' in file]
		for zip_file in zip_list:

			if util.check_zip_file_valid(zip_file, start_date, end_date) is False:
				continue

			if os.path.exists(os.path.join('..', 'tmp', zip_file.split('.zip')[0])) is False:
				copyfile(os.path.join(raw_data_path, zip_file), os.path.join('..', 'tmp', zip_file))
				os.system('unzip ' + os.path.join('..', 'tmp', zip_file) + ' -d ' + os.path.join('..', 'tmp', zip_file.split('.zip')[0]))

			for file in os.listdir(os.path.join('..', 'tmp', tar_gz_file.split('.tar.gz')[0])):
				if '.csv' in file and str(device_id) in file:
					data_path = os.path.join('..', 'tmp', tar_gz_file.split('.tar.gz')[0], file)
					week_data_df = util.read_csv(data_path)
					raw_df = raw_df.append(week_data_df)

	return raw_df


def read_subject_data(subject_data_path):
	xl_file = pd.ExcelFile(os.path.join(subject_data_path, 'Task_Completion_log.xlsx'))

	subject_df = pd.DataFrame()
	for sheet_name in xl_file.sheet_names:

		week_df = xl_file.parse(sheet_name)
		if 'updated_by' not in list(week_df.columns):
			continue
		week_df = week_df.dropna(subset=['updated_by'])

		for index in list(week_df.index):
			if sheet_name == 'week1':
				row_df = pd.DataFrame(index=[str(int(week_df.loc[index, 'subject_id']))])
				row_df['start_date'] = pd.to_datetime(week_df.loc[index, 'Date']).strftime(util.date_time_format)[:-3]
				row_df['end_date'] = (pd.to_datetime(week_df.loc[index, 'Date']) + timedelta(weeks=7)).strftime(util.date_time_format)[:-3]
				subject_df = pd.concat([subject_df, row_df])
			elif sheet_name == 'week2':

				subject_id = str(week_df.loc[index, 'subject_ID'])[:4]
				intervention_date = pd.to_datetime(week_df.loc[index, 'Date'])
				intervention_time = week_df.loc[index, 'End_Time']
				if str(intervention_time) == 8:
					hour = intervention_time.hour
					minute = intervention_time.minute
					subject_df.loc[subject_id, 'intervention'] = (pd.to_datetime(intervention_date) + timedelta(hours=hour, minutes=minute)).strftime(util.date_time_format)[:-3]
				else:
					subject_df.loc[subject_id, 'intervention'] = (pd.to_datetime(intervention_date) + timedelta(hours=24)).strftime(util.date_time_format)[:-3]
	return subject_df