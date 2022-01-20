import os
import shutil

import ansible.constants as C
from ansible.executor.task_queue_manager import TaskQueueManager
from ansible.module_utils.common.collections import ImmutableDict
from ansible.inventory.manager import InventoryManager
from ansible.parsing.dataloader import DataLoader
from ansible.playbook.play import Play
from ansible.plugins.callback import CallbackBase
from ansible.vars.manager import VariableManager
from ansible import context
from ansible.executor.playbook_executor import PlaybookExecutor


class ResultCallback(CallbackBase):

    def __init__(self, *args, **kwargs):
        super(ResultCallback, self).__init__(*args, **kwargs)
        self.host_ok = {}
        self.host_unreachable = {}
        self.host_failed = {}

    def runner_on_unreachable(self, host, result):
        self.host_unreachable[host] = result

    def runner_on_ok(self, host, result):
        self.host_ok[host] = result

    def runner_on_failed(self, host, result, ignore_errors=False):
        self.host_failed[host] = result


class AnsibleAPI(object):
    def __init__(self, sources=None, vars=None,
                 connection='smart',  # 连接方式 local,smart,ssh
                 remote_user='root',  # 远程用户
                 ack_pass=None,  # 提示输入密码
                 passwords: dict = None,
                 sudo=None, sudo_user=None, ask_sudo_pass=None,
                 module_path=None,  # 模块路径，可以指定一个自定义模块的路径
                 become=None,  # 是否提权
                 become_method=None,  # 提权方式 默认 sudo 可以是 su
                 become_user=None,  # 提权后，要成为的用户，并非登录用户
                 check=False, diff=False,
                 verbosity=3,
                 syntax=None,
                 start_at_task=None):

        context.CLIARGS = ImmutableDict(
            connection=connection,
            remote_user=remote_user,
            ack_pass=ack_pass,
            sudo=sudo,
            sudo_user=sudo_user,
            ask_sudo_pass=ask_sudo_pass,
            module_path=module_path,
            become=become,
            become_method=become_method,
            become_user=become_user,
            check=check,
            diff=diff,
            verbosity=verbosity,
            syntax=syntax,
            start_at_task=start_at_task,
        )

        self.loader = DataLoader()

        self.inventory = InventoryManager(loader=self.loader, sources=sources)

        if isinstance(vars, dict):
            inventory = self.inventory._inventory
            for k, v in vars.items():
                if isinstance(v, dict):
                    for _k, _v in v.items():
                        inventory.set_variable(k, _k, _v)

        self.passwords = passwords or dict()

        self.results_callback = ResultCallback()

        self.variable_manager = VariableManager(self.loader, self.inventory)

    def run_adhoc(self, hosts: list = 'localhost', gather_facts="no", tasks=None):
        play_source = dict(
            name="Ad-hoc",
            hosts=hosts,
            gather_facts=gather_facts,
            tasks=tasks)

        play = Play().load(play_source, variable_manager=self.variable_manager, loader=self.loader)

        tqm = None
        try:
            tqm = TaskQueueManager(
                inventory=self.inventory,
                variable_manager=self.variable_manager,
                loader=self.loader,
                passwords=self.passwords,
                stdout_callback=self.results_callback)

            return tqm.run(play)
        finally:
            if tqm is not None:
                tqm.cleanup()
            shutil.rmtree(C.DEFAULT_LOCAL_TMP, True)

    def run_playbook(self, playbooks):

        pbex = PlaybookExecutor(playbooks=playbooks,
                                inventory=self.inventory,
                                variable_manager=self.variable_manager,
                                loader=self.loader,
                                passwords=self.passwords)

        # 使用回调函数
        pbex._tqm._stdout_callback = self.results_callback

        return pbex.run()

    def get_result(self):
        results = {'success': {}, 'failed': {}, 'unreachable': {}}

        for host, result in self.results_callback.host_ok.items():
            results['success'][host] = result
        for host, result in self.results_callback.host_failed.items():
            results['failed'][host] = result
        for host, result in self.results_callback.host_unreachable.items():
            results['unreachable'][host] = result

        return results


def get_hardware_info(hosts):
    host_list = list(hosts.keys())
    ok = {}
    failed = {}
    sources = ','.join(host_list)
    if len(host_list) == 1:
        sources += ','
    api = AnsibleAPI(sources=sources, vars=hosts)

    task_lists = [
        dict(action=dict(module='setup', args='')),
    ]

    api.run_adhoc(tasks=task_lists, hosts=host_list)

    for host, result in api.results_callback.host_failed.items():
        failed[host] = result['msg']

    for host, result in api.results_callback.host_unreachable.items():
        failed[host] = result['msg']

    for host, result in api.results_callback.host_ok.items():
        g = result.get('ansible_facts')
        ok[host] = {}
        ok[host]['mac'] = g['ansible_default_ipv4']['macaddress']
        ok[host]['cpu_type'] = g['ansible_processor'][-1]
        ok[host]['cpu_count'] = g['ansible_processor_count']
        ok[host]['cpu_cores'] = g['ansible_processor_cores']
        ok[host]['cpu_threads'] = g['ansible_processor_threads_per_core']
        ok[host]['memory'] = '%dMB' % (g['ansible_memtotal_mb'])
        disk = g['ansible_devices']
        if disk.get('vda'):
            ok[host]['disk'] = disk['vda']['size']
        elif disk.get('sda'):
            ok[host]['disk'] = disk['sda']['size']
        else:
            ok[host]['disk'] = 0
        ok[host]['other_ip'] = ','.join(g['ansible_all_ipv4_addresses'])
        ok[host]['os_type'] = g['ansible_distribution']
        ok[host]['os_version'] = g['ansible_distribution_version']
        ok[host]['os_arch'] = g['ansible_system']

    return ok, failed

