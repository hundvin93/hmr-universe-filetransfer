# !/usr/bin/env python
#
import glob
import logging
import os
import shutil
import sys
import subprocess as sp
import time
import xml.etree.ElementTree as ET

log = logging.getLogger(__name__)


def is_mounted(dir, flow_dir, hmr_share_dir):
    mdir = False
    fdir = False
    hdir = False
    for i in range(10):
        if os.path.exists(dir):
            log.info(f"Mount OK: {dir}")
            mdir = True
            if os.path.exists(flow_dir):
                log.info(f"Mount OK: {flow_dir}")
                fdir = True
                if os.path.exists(dir):
                    log.info(f"Mount OK: {dir}")
                    hdir = True
                    return True
        else:
            mount = "mount -a"
            sp.call(mount, shell=True)
            log.info(f"Mount not OK, trying to Mount")
            time.sleep(2)
    if not mdir:
        log.error("Cannot mount %s", dir)
    if not fdir:
        log.error("Cannot mount %s", flow_dir)
    if not hdir:
        log.error("Cannot mount %s", hmr_share_dir)
    return False

def is_xml_pool(f):
    with open(f, "r") as file:
        xml_data = file.read()
    root = ET.XML(xml_data)
    for i, child in enumerate(root[1:]):
        for subchild in child:
            if subchild.tag == "SampleID":
                if len(subchild.text.split(';')) > 1:
                    return True
    return False


def process_file(file, singel_dir, pool_dir, flow_dir):
    pool = False
    surname = os.path.splitext(file)[1]
    if surname == '.csv':
        pool = True
    else:
        pool = is_xml_pool(file)

    target_dir = pool_dir if pool else singel_dir

    new_file = os.path.join(target_dir, os.path.basename(file))
    num = 2
    while os.path.exists(new_file):
        if os.path.exists(new_file.replace(surname, "_" + str(num) + surname)):
            num += 1
        else:
            new_file = new_file.replace(surname, "_" + str(num) + surname)

    log.info(f"moving {file} into {target_dir}")


    if os.path.exists(file):
        if not pool:
            try:
                shutil.copy2(file, flow_dir)
            except Exception as err:
                log.error(err)
                time.sleep(2)
        try:
            shutil.move(file, new_file)
        except Exception as err:
            log.error(err)
            time.sleep(2)

    while os.path.exists(file):
        log.info(f"File {file} still exists after moving")
        try:
            os.remove(file)
        except Exception as err:
            log.error(err)


def process_dir(dir, single_dir, pool_dir, flow_dir):
    files = glob.glob(os.path.join(dir, "*.xml"), recursive=False)
    files = files + glob.glob(os.path.join(dir, "*.csv"), recursive=False)
    for file in files:
        log.info(f"Processing {file}")
        try:
            process_file(file, single_dir, pool_dir, flow_dir)
        except Exception as inst:
            log.exception(f"Cannot process {file}")


def process_hmr_share(hmr_share, single_dir):
    files = glob.glob(os.path.join(hmr_share, "*.xml"), recursive=False)
    for file in files:
        log.info(f"Moving {file} to {single_dir}")
        try:
            shutil.move(file, single_dir)
        except Exception as err:
            log.exception(err)
            time.sleep(1)
        while os.path.exists(file):
            log.info(f"File {file} still exists after moving")
            try:
                os.remove(file)
            except Exception as err:
                log.error(err)


def process_order_files(order_dir, flow_dir):
    files = glob.glob(os.path.join(order_dir, "*.xml"), recursive=False)
    arkiv_dir = os.path.join(order_dir,"Arkiv")
    if not os.path.exists(arkiv_dir):
        os.mkdir(arkiv_dir)
    for file in files:
        log.info(f"Moving {file} to {flow_dir}")
        try:
            shutil.copy2(file,flow_dir)
        except Exception as err:
            log.error(err)
        try:
            shutil.move(file,arkiv_dir)
        except Exception as err:
            log.error(err)
        while os.path.exists(file):
            log.info(f"File {file} still exists after moving")
            try:
                os.remove(file)
            except Exception as err:
                log.error(err)



if __name__ == '__main__':
    import argparse

    root = logging.getLogger()
    root.setLevel(logging.DEBUG)

    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(logging.INFO)
    ch_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    ch.setFormatter(ch_formatter)

    log_dir = os.getenv('LOG_DIR', '/var/tmp/')
    log_file = os.path.join(log_dir, "hmr_file_sort.log")

    fh = logging.FileHandler(log_file)
    fh.setLevel(logging.DEBUG)
    fh_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    fh.setFormatter(fh_formatter)

    root.addHandler(ch)
    root.addHandler(fh)

    parser = argparse.ArgumentParser(
        description='Listens for files and moves them to the correct folder')

    parser.add_argument('--maindir', dest='dir', required=True,
                        help='Root directory where to listen for files')
    parser.add_argument('--singledir', dest='single_dir', required=True,
                        help='Directory where to place the files used for single runs eg. PSH')
    parser.add_argument("--pooldir", dest='pool_dir', required=True,
                        help='Directory where to place the files used for pooling')
    parser.add_argument("--orderfilesdir", dest='order_dir', required=True,
                        help='Directory where the order files are sent to the MP96(FLOW dir)')
    parser.add_argument("--flowdir", dest='flow_dir', required=True,
                        help='Directory that receives the order files from order_dir')
    parser.add_argument("--hmrsharedir", dest='hmr_share_dir', required=True,
                        help='Directory where the psh files are sent from to the single_dir')

    args = parser.parse_args()

    check_mount = is_mounted(args.dir, args.flow_dir, args.hmr_share_dir)

    while check_mount:
        process_dir(args.dir, args.single_dir, args.pool_dir, args.flow_dir)
        process_hmr_share(args.hmr_share_dir,args.single_dir)
        process_order_files(args.order_dir, args.flow_dir)
        time.sleep(10)
