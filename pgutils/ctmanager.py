# -*- coding: utf-8 -*-
# @Time    : 2021/10/7 10:57
# @Author  : He Ruizhi
# @File    : ctmanager.py
# @Software: PyCharm

from pgutils.pgcontrols.ctbase import CtBase
import pygame


class CtManager:
    def __init__(self):
        self.controls = {}

    def register(self, control_name: str, control: CtBase) -> None:
        """
        控件注册

        :param control_name: 注册名称
        :param control: pygame控件
        :return:
        """
        self.controls[control_name] = control
        return None

    def update(self, event: pygame.event) -> None:
        """
        对所有注册的激活控件进行更新

        :param event: pygame事件
        :return:
        """
        for control_name in self.controls:
            if self.controls[control_name].active:
                self.controls[control_name].update(event)
        return None
