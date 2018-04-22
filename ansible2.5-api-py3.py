import json
import os
from collections import namedtuple
from ansible.parsing.dataloader import DataLoader
from ansible.vars.manager import VariableManager
from ansible.inventory.manager import InventoryManager
from ansible.executor.playbook_executor import PlaybookExecutor
from ansible.playbook.play import Play
from ansible.errors import AnsibleParserError
from ansible.executor.task_queue_manager import TaskQueueManager
from ansible.plugins.callback import CallbackBase


class ResultCallback(CallbackBase):
    '''A sample callback plugin used for performing an action as results come in
    If you want to collect all results into a single object for processing at
    the end of the execution, look into utilizing the ``json`` callback plugin
    or writing your own custom callback plugin
    '''

    def __init__(self, *args):
        super(ResultCallback, self).__init__(display=None)
        self.status_ok = json.dumps({})
        self.status_fail = json.dumps({})
        self.status_unreachable = json.dumps({})
        self.status_playbook = ''
        self.status_no_hosts = False
        self.host_ok = {}
        self.host_failed = {}
        self.host_unreachable = {}

    def v2_runner_on_ok(self, result):
        host = result._host.get_name()
        self.runner_on_ok(host, result._result)
        self.host_ok[host] = result

    def v2_runner_on_failed(self, result, ignore_errors=False):
        host = result._host.get_name()
        self.runner_on_failed(host, result._result, ignore_errors)
        self.host_failed[host] = result

    def v2_runner_on_unreachable(self, result):
        host = result._host.get_name()
        self.runner_on_unreachable(host, result._result)
        self.host_unreachable[host] = result

    def v2_playbook_on_no_hosts_matched(self):
        self.playbook_on_no_hosts_matched()
        self.status_no_hosts = True

    def v2_playbook_on_play_start(self, play):
        self.playbook_on_play_start(play.name)
        self.playbook_path = play.name


class my_ansible_play():
    # 这里是ansible运行
    # 初始化各项参数，大部分都定义好，只有几个参数是必须要传入的
    def __init__(self,
                 host_list='/etc/ansible/hosts',
                 connection='ssh',
                 become=False,
                 become_user=None,
                 remote_user="root",
                 module_path=None,
                 private_key_file=None,
                 fork=50,
                 ansible_cfg=None,
                 passwords={},
                 check=False):
        self.results_callback = ResultCallback()
        self.passwords = passwords
        self.host_list = host_list
        Options = namedtuple('Options',
                             ['connection', 'module_path', 'forks', 'private_key_file', 'ssh_common_args', 'become',
                              'become_method', 'remote_user', 'become_user', 'check', 'diff'])
        '''
        ['listtags', 'listtasks', 'listhosts', 'syntax', 'connection', 'module_path','forks', 'private_key_file', 'ssh_common_args',
         'ssh_extra_args', 'sftp_extra_args', 'scp_extra_args', 'become', 'become_method', 'become_user', 'verbosity', 'check'])'''
        self.options = Options(connection=connection, module_path=module_path,
                               forks=fork, private_key_file=private_key_file, ssh_common_args=None,
                               become=become, become_method=None, become_user=become_user, remote_user=remote_user,
                               check=check, diff=False)

        if ansible_cfg != None:
            os.environ["ANSIBLE_CONFIG"] = ansible_cfg

        self.loader = DataLoader()

        self.inventory = InventoryManager(loader=self.loader, sources=self.host_list)
        self.variable_manager = VariableManager(loader=self.loader, inventory=self.inventory)

    def run_playbook(self, playbooks):
        self.playbook_path = playbooks

        for i in self.playbook_path:
            if not os.path.exists(i):
                code = 1000
                results = {'playbook': i, 'msg': i + 'playbook is not exist', 'flag': False}
                return [code, results]
        pbex = PlaybookExecutor(playbooks=self.playbook_path,
                                inventory=self.inventory,
                                variable_manager=self.variable_manager,
                                loader=self.loader,
                                options=self.options,
                                passwords=self.passwords)
        # self.results_callback = ResultCallback()
        pbex._tqm._stdout_callback = self.results_callback
        try:
            code = pbex.run()
        except AnsibleParserError:
            code = 1001
            results = {'playbook': self.playbook_path, 'msg': self.playbook_path + ' playbook have syntax error',
                       'flag': False}
            return [code, results]
        if self.results_callback.status_no_hosts:
            code = 1002
            results = {'playbook': self.playbook_path, 'msg': self.results_callback.status_no_hosts, 'flag': False,
                       'executed': False}
            return [code, results]

    def run_adhoc(self, task_list):
        # self.results_callback = ResultCallback()
        play_source = dict(
            name="Ansible Play",
            hosts=self.host_list,
            gather_facts='no',
            tasks=task_list
        )

        play = Play().load(data=play_source, variable_manager=self.variable_manager, loader=self.loader)
        tqm = None
        try:
            tqm = TaskQueueManager(
                inventory=self.inventory, variable_manager=self.variable_manager,
                loader=self.loader, options=self.options, passwords=self.passwords,
                stdout_callback=self.results_callback,
            )
            code = tqm.run(play)
            return code
        finally:
            if tqm is not None:
                tqm.cleanup()
            print('complete')

    def get_result(self):
        self.result_all = {'success': {}, 'failed': {}, 'unreachable': {}}
        for host, result in self.results_callback.host_ok.items():
            self.result_all['success'][host] = result._result
        for host, result in self.results_callback.host_failed.items():
            self.result_all['failed'][host] = result._result['msg']
        for host, result in self.results_callback.host_unreachable.items():
            self.result_all['unreachable'][host] = result._result['msg']

        return self.result_all

    # Remove ansible tmpdir
    # shutil.rmtree(C.DEFAULT_LOCAL_TMP, True)
def get_hardware_info(assts_ip):
    rst = {}
    #host_list = assts_ip
    if isinstance(assts_ip, str):
        if ',' in assts_ip:
            host_list = assts_ip.split(',')
        else:
            host_list = [assts_ip]
            assts_ip = assts_ip+','
    elif isinstance(assts_ip, list):
        host_list = assts_ip
        assts_ip = assts_ip.join(',')
    else:
        return None

    newplay = my_ansible_play(host_list=assts_ip, private_key_file='/home/opsmgt/.id_rsa_ansible')
    task_list = [
        dict(action=dict(module='setup', args='')),
    ]
    code = newplay.run_adhoc(task_list=task_list)
    ret = newplay.get_result()
    for i in host_list:
        g = ret['success'].get(i)
        if g:
            g = g.get('ansible_facts')
            rst[i] = {}
            rst[i]['mac'] = g['ansible_default_ipv4']['macaddress']
            rst[i]['cpu'] = '%s*%d' % (g['ansible_processor'][1], g['ansible_processor_vcpus'])
            rst[i]['memory'] = g['ansible_memtotal_mb']
            disk=g['ansible_devices']
            if disk.get('sda'):
                 rst[i]['disk'] = disk['vda']['size']
            elif disk.get('sda'):
                 rst[i]['disk'] = disk['sda']['size']
            else:
                 rst[i]['disk'] = 0
            rst[i]['other_ip'] = ','.join(g['ansible_all_ipv4_addresses'])
            rst[i]['system_type'] = g['ansible_distribution']
            rst[i]['system_version'] = g['ansible_distribution_version']
            rst[i]['system_arch'] = g['ansible_system']
        else:
            print(ret['unreachable'].get(assts_ip))

    return rst

if __name__ == '__main__':
    host_list = '10.1.1.202, 10.1.1.201,10.1.1.203,10.1.1.222'
    task_list = [
        dict(action=dict(module='setup', args='filter=facter_*')),
        # dict(action=dict(module='shell', args='python sleep.py')),
        # dict(action=dict(module='synchronize', args='src=/home/op/test dest=/home/op/ delete=yes')),
    ]
    playbook = ['/root/playbook.yml', ]

    mytest = my_ansible_play(host_list=host_list, private_key_file='/home/kk/id_rsa_ansible')  #
    # print(mytest.loader)#passwords={'conn_pass':'kexirong','become_pass':'kexirong'}
    code = mytest.run_adhoc(task_list=task_list)
    # code,result=mytest.run_playbook(playbooks=playbook)
    ret = mytest.get_result()
    print(ret)
