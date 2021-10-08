# -*- coding: utf-8 -*-
# @Time    : 2021/10/7 10:57
# @Author  : He Ruizhi
# @File    : ctmanager.py
# @Software: PyCharm

from pgutils.pgcontrols.ctbase import CtBase
from typing import List
import pygame


class CtManager:
    def __init__(self):
        self.controls = {}

    def register(self, control_name: str, control: CtBase, surface_states: List[str]) -> None:
        """
        控件注册

        :param control_name: 注册名称
        :param control: pygame控件
        :param surface_states: 游戏界面状态
        :return:
        """
        self.controls[control_name] = [control, surface_states]
        return None

    def update(self, surface_state: str, event: pygame.event) -> None:
        """
        对所有注册到指定surface_state下的控件进行更新

        :param surface_state: 游戏界面状态
        :param event: pygame事件
        :return:
        """
        for control_name in self.controls:
            if surface_state in self.controls[control_name][1]:
                self.controls[control_name][0].update(event)
        return None
