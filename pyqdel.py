#!/usr/bin/env python

import sys
import subprocess
import time
import xml.etree.ElementTree as ET
import paramiko


def pyqdel(jobid: int):

    result = subprocess.Popen(["qstat", "-x", str(jobid)],
                              stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    xml = result.communicate()[0].decode("utf-8")
    # print(xml)

    if xml == "":
        raise Exception(f"not found jobid : {jobid}")

    # parse check
    root = ET.fromstring(xml)
    # print_element(root)
    try:
        print("Job/Resource_List/exec_host : ",
              root.find("Job").find("exec_host").text)
        print("Job/euser : ", root.find("Job").find("euser").text)
        print("Job/Job_Name : ", root.find("Job").find("Job_Name").text)
    except:
        result = subprocess.Popen(["qdel", str(jobid)],
                                  stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return

    # user check
    result = subprocess.Popen(["whoami"],
                              stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    myname = result.communicate()[0].decode("utf-8").strip()
    if myname != root.find("Job").find("euser").text:
        print(myname)
        raise Exception(f"the owner of job {jobid} is not me!")

    # qdel
    result = subprocess.Popen(["qdel", str(jobid)],
                              stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    time.sleep(2)
    nodes = root.find("Job").find("exec_host").text.split("+")
    job_name = root.find("Job").find("Job_Name").text
    for node in nodes:
        node_info = node.split("/")
        print(node_info)
        with paramiko.SSHClient() as ssh:
            # 初回ログイン時に「Are you sure you want to continue connecting (yes/no)?」と
            # きかれても問題なく接続できるように。
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

            # ssh接続
            ssh.connect(node_info[0])

            stdin, stdout, stderr = ssh.exec_command("ps xg | grep qdeal")
            for o in stdout:
                print('[std]', o, end='')

            cmd = "ps aux | grep {} | grep -v grep | awk '{{ print \"kill -9\", $2 }}' | sh".format(
                job_name)
            # コマンド実行
            stdin, stdout, stderr = ssh.exec_command(cmd)
            # コマンド実行後に標準入力が必要な場合
            # stdin.write('password\n')
            # stdin.flush()

            # 実行結果を表示
            for o in stdout:
                print('stdout : ', o, end='')
            for e in stderr:
                print('stderr : ', e, end='')

    return


def print_element(element, path="/"):
    print(path + element.tag, ":", element.text)
    for sub in element:
        print_element(sub, path + element.tag + "/")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        raise Exception("Need to input Job ID")
    for jobid in sys.argv[1:]:
        pyqdel(int(jobid))
