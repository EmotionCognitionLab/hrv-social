### The code is used to curate whoop wearable data

#### clean_raw_data.py is to map data in different format to standard csv data file for each participant

<br />


```
python3 clean_raw_data.py -data_path "PUT THE DATA PATH"

-data_path: raw data dump path
```

#### Sample saved csv format


timestamp            |  heart_rate  |    acc_x   |    acc_y   |    acc_z   |   acc_mag  |     rr     |
---------------------|--------------|------------|------------|------------|------------|------------|
2018-08-08T06:51:00  |      68      |  0.215664  |  0.751406  |  0.594922  |   2.44561  |     []     |
2018-08-08T06:51:01  |      68      |  0.162305  |  0.644727  |  0.694023  |   0.65779  |     []     |


#### save_data.py is to save data in csv/tsv format in pre/post session from data created clean_raw_data.py, no input args required

```
python3 save_data.py
```
