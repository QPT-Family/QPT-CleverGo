# -*- coding: utf-8 -*-
# @Time    : 2021/10/7 10:57
# @Author  : He Ruizhi
# @File    : ctmanager.py
# @Software: PyCharm

from pgutils.pgcontrols.ctbase import CtBase


class CtManager:
    def __init__(self):
        self.controls = []

    def register(self, control: CtBase, gc_state: str) -> None:
        """
        控件注册

        :param control: pygame控件
        :param gc_state: 游戏控制状态
        :return:
        """
        self.controls.append((control, gc_state))
        return None

    def update(self, gc_state: str) -> None:
        """
        对所有注册到指定gc_state下的控件进行更新

        :param gc_state: 游戏控制状态
        :return:
        """
        for control, ct_state in self.controls:
            if ct_state == gc_state:
                control.update()
        return None
