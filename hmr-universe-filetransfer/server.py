# !/usr/bin/env python
#
import logging
import os
import shlex
import sys
import subprocess as sp
from subprocess import Popen, PIPE
from time import sleep

log = logging.getLogger(__name__)


####################################################################
#                                                                  #
#         FOR THE SSH TO WORK, REMEMBER TO GENERATE SSH KEY        #
#                                                                  #
####################################################################


def check_connection(ip):
    call = f"ping -c 1 -W 1 {ip}"
    pingtest = Popen(shlex.split(call), stdout=PIPE)
    pingtest.wait()
    return not pingtest.poll()


def is_mounted(pi_dir):
    for i in range(10):
        if os.path.exists(pi_dir):
            return True
        else:
            mount = "mount -a"
            sp.call(mount, shell=True)
            log.info(f"Mount not OK, trying to Mount: {pi_dir}")
            sleep(2)
    log.error("Cannot mount %s", pi_dir)
    return False


def process_dir(ip, dir, user, target_ip, target_dir, target_user, arkiv_dir):
    files = []
    log.info("calling SSH")
    call = f"ssh {user}@{ip}"
    log.info("CALLED ssh")
    sshProcess = Popen(shlex.split(call), stdin=sp.PIPE, stdout=sp.PIPE, universal_newlines=True, bufsize=0)
    sshProcess.stdin.write(f'cd {dir}\n')
    sshProcess.stdin.write('echo START\n')
    sshProcess.stdin.write('ls\n')
    sshProcess.stdin.write("echo END\n")
    start = False
    for line in sshProcess.stdout:
        if line == "END\n":
            break
        if start:
            filetype = os.path.splitext(line.strip())[-1]
            if filetype == ".xml":
                files.append(line.strip())

        if line == "START\n":
            start = True
    for file in files:
        scp_call = f'scp {file} {target_user}@{target_ip}:{target_dir}'
        mv_call = f'mv {file} {arkiv_dir}'
        sshProcess.stdin.write(f'{scp_call}\n')
        sshProcess.stdin.write(f'{mv_call}\n')
        log.info(f'moving and copying {file}')
    sshProcess.stdin.write("logout\n")
    sshProcess.stdin.close()


if __name__ == '__main__':
    import argparse
    # arkiv = "archive"
    # ip_err = "10.251.176.31"
    # ip = "127.0.0.1"
    # tar_ip = "127.0.0.1"
    # dir = "PycharmProjects/hmr-universe-filetransfer/Test/Desktop/csv/Run_Finished"
    # tar_dir = "/home/kristoffer/PycharmProjects/hmr-universe-filetransfer/Test/Target/"
    # user = "kristoffer"
    # tar_user = "kristoffer"
    #
    # process_dir(ip, user, dir, arkiv, tar_ip, tar_user, tar_dir)
    # exit()
    # process_file("PSH 210520 coro 2.xml", "test/PLRN")
    # process_file("210520 coro 6.xml", "test/PLRN")

    root = logging.getLogger()
    root.setLevel(logging.DEBUG)

    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(logging.INFO)
    ch_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    ch.setFormatter(ch_formatter)

    log_dir = os.getenv('LOG_DIR', '/var/tmp/')
    log_file = os.path.join(log_dir, "hmr_universe_filetransfer.log")

    fh = logging.FileHandler(log_file)
    fh.setLevel(logging.DEBUG)
    fh_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    fh.setFormatter(fh_formatter)

    root.addHandler(ch)
    root.addHandler(fh)

    parser = argparse.ArgumentParser(
        description='Listens for PSH XML files and converts to PRLN and simple format')

    parser.add_argument('--univ-ip', dest='univ_ip', required=True,
                        help='fill in')
    parser.add_argument('--univ-dir', dest='univ_dir', required=True,
                        help='fill in')
    parser.add_argument("--univ-user", dest='univ_user', required=True,
                        help='fill in')
    parser.add_argument("--pi-ip", dest='pi_ip', required=True,
                        help='fill in')
    parser.add_argument("--pi-dir", dest='pi_dir', required=True,
                        help='fill in')
    parser.add_argument("--pi-user", dest='pi_user', required=True,
                        help='Ffill in')
    parser.add_argument("--univ-arkiv", dest='univ_arkiv', required=True,
                        help='fill in')

    args = parser.parse_args()

    log_delay_counter = 0
    while is_mounted(args.pi_dir):
        if check_connection(args.univ_ip):
            try:
                process_dir(args.univ_ip, args.univ_dir, args.univ_user,
                            args.pi_ip, args.pi_dir, args.pi_user, args.univ_arkiv)
            except Exception as err:
                log.error(err)
        else:
            if log_delay_counter == 0:
                log.info(f'cannot connect to {args.univ_ip}')
            log_delay_counter = (log_delay_counter + 1) % 120
            sleep(20)
        sleep(10)
