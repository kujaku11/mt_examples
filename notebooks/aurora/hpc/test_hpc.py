import sys
print(sys.path)
sys.path=[ '/opt/conda/envs/geophys/lib/python39.zip',
 '/opt/conda/envs/geophys/lib/python3.9',
 '/opt/conda/envs/geophys/lib/python3.9/lib-dynload',
    '/opt/conda/envs/geophys/lib/python3.9/site-packages',
 '/opt/conda/envs/geophys/lib/python3.9/site-packages/petgem-1.0-py3.9.egg',
 '/opt/conda/envs/geophys/lib/python3.9/site-packages/meshio-5.3.4-py3.9.egg',
 '/opt/conda/envs/geophys/lib/python3.9/site-packages/singleton_decorator-1.0.0-py3.9.egg']
print(sys.path)
import aurora
print(aurora.__version__)
print(aurora.__file__)

##############################################

import argparse
import os
import pathlib
import pandas as pd

from aurora.config.config_creator import ConfigCreator
from aurora.config import BANDS_DEFAULT_FILE
from aurora.general_helper_functions import BAND_SETUP_PATH
from aurora.pipelines.process_mth5 import process_mth5
from aurora.pipelines.run_summary import RunSummary
from aurora.transfer_function.kernel_dataset import KernelDataset

### Set Up Paths
nci_user_name = "abc123"   ### change this to your NCI user name
work_path = pathlib.Path("/g/data/nm05/workspace/").joinpath(nci_user_name)

### Comment these two lines below
work_path = pathlib.Path().home().joinpath("aurora_test_folder")
work_path.mkdir(parents=True, exist_ok=True)

my80_path = pathlib.Path("/g/data/my80")
au_scope_mt_collection_path = my80_path.joinpath("AuScope_MT_collection")
auslamp_path = au_scope_mt_collection_path.joinpath("AuScope_AusLAMP")
musgraves_path = auslamp_path.joinpath("Musgraves_APY")
data_dir = musgraves_path
assert data_dir.exists()

USE_PANDARALEL = True
RESULTS_PATH = work_path



def none_or_str(value):
    if value == 'None':
        return None
    return value

def none_or_int(value):
    if value == 'None':
        return None
    return int(value)

def get_musgraves_availability_df(data_dir):
    """
    recusively search for h5 files in data_dir, tabulate and return a dataframe
    """
    all_mth5_files = list(data_dir.rglob("*h5"))
    num_mth5 = len(all_mth5_files)
    print(f"Found {num_mth5} h5 files")
    levels = num_mth5 * [""]
    station_ids = num_mth5 * [""]
    territories = num_mth5 * [""]
    paths = num_mth5 * [""]

    for i_filepath, filepath in enumerate(all_mth5_files):
        levels[i_filepath] = str(filepath).split("level_")[1][0]
        station_ids[i_filepath] = filepath.stem
        territories[i_filepath] = str(filepath).split("Musgraves_APY/")[1][0:2]
        paths[i_filepath] = filepath
    df_dict = {"level": levels, "territory": territories, "station_id": station_ids, "path": paths}
    df = pd.DataFrame(data=df_dict)

    return df


def enrich_row_with_processing(row):
    mth5_files = [row.path,]
    print("path", row.path, "type", type(row.path))
    my_h5 = pathlib.Path(row.path)
    print(f"{my_h5.exists()} my_h5.exists()")
    xml_file_path = RESULTS_PATH.joinpath(f"{row.station_id}.xml")
    print(xml_file_path)
    
    # if xml_file_path.exists():
    #     if not self.force_reprocess:
    #         print("WARNING: Skipping processing as xml results alread exist")
    #         print("set force_reprocess True to avoid this")
    #         return row
    
    try:
        mth5_run_summary = RunSummary()
        mth5_run_summary.from_mth5s(mth5_files)
        run_summary = mth5_run_summary.clone()
        #run_summary.check_runs_are_valid(drop=True)
        kernel_dataset = KernelDataset()
        kernel_dataset.from_run_summary(run_summary, row.station_id, None)
        print("WORKAROUND")
        kernel_dataset.df["survey"] = "AusLAMP_Musgraves"
        kernel_dataset.df["run_id"] = "001"
        print("/WORKAROUND")
        
        
        print(kernel_dataset.df)
        
        # kernel_dataset.drop_runs_shorter_than(5000)
        # if len(kernel_dataset.df) == 0:
        #     print("No RR Coverage, casting to single station processing")
        #     kernel_dataset.from_run_summary(run_summary, row.station_id)

        cc = ConfigCreator()
        config = cc.create_from_kernel_dataset(kernel_dataset,
                                              emtf_band_file=BAND_SETUP_PATH.joinpath("bs_six_level.cfg"))
#                                               emtf_band_file=BANDS_TEST_FAST_FILE)
        config.channel_nomenclature.keyword = "musgraves"
        config.set_default_input_output_channels()
        show_plot = False
              
        z_file = str(xml_file_path).replace("xml", "zss")
        tf_cls = process_mth5(config,
                              kernel_dataset,
                              units="MT",
                              show_plot=show_plot,
                              z_file_path=z_file,
                              )
        tf_cls.write(fn=xml_file_path, file_type="emtfxml")
    
    except Exception as e:
        row.exception = e.__class__.__name__
        row.error_message = e.args[0]
    return row



def process_lots_of_mth5s(df, use_pandarallel=False):
    """

    Parameters
    ----------
    df : pd.DataFrame
        This is a list of the files

    Returns
    -------
    df:  pd.DataFrame
        SAme as input but with new columns

    """
    df["exception"] = ""
    df["error"] = ""
    if use_pandarallel:
        from pandarallel import pandarallel
        pandarallel.initialize(verbose=3)
        enriched_df = df.parallel_apply(enrich_row_with_processing, axis=1)
    else:
        enriched_df = df.apply(enrich_row_with_processing, axis=1)

    return enriched_df


def parse_args():
    parser = argparse.ArgumentParser(description="Wide Scale Musgraves Test")
    parser.add_argument("--startrow", help="First row to process (zero-indexed)", type=int, default=0)
    parser.add_argument("--endrow", help="Last row to process (zero-indexed)", type=none_or_int, default=None,
                        nargs='?', )
    parser.add_argument("--use_pandarallel", help="Will use default pandarallel if True", type=bool,
                        default=False)
    args, unknown = parser.parse_known_args()


    print(f"startrow = {args.startrow}")
    print(f"endrow = {args.endrow}")
    print(f"use_pandarallel = {args.use_pandarallel}")
    return args

def main():
    processing_csv = work_path.joinpath("l1_processing_list.csv")
    processing_df = pd.read_csv(processing_csv)
    print(processing_df)

    #processing_df = processing_df[0:2]
    args = parse_args()
    enriched_df = process_lots_of_mth5s(processing_df, use_pandarallel=args.use_pandarallel)
    print(enriched_df)


if __name__ == "__main__":
    main()



